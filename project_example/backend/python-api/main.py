# -*- coding: utf-8 -*-
"""
智能任务管理系统 - FastAPI 后端服务
提供 RESTful API 接口，支持任务的增删改查、用户认证、WebSocket 实时通信
"""

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import hashlib
import uuid
import json
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
import redis
import aiomysql
from contextlib import asynccontextmanager

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 枚举和数据模型定义 ====================

class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 待处理
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"   # 已完成
    CANCELLED = "cancelled"   # 已取消
    ARCHIVED = "archived"     # 已归档


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"           # 低优先级
    MEDIUM = "medium"     # 中优先级
    HIGH = "high"         # 高优先级
    URGENT = "urgent"     # 紧急


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"       # 管理员
    MANAGER = "manager"   # 经理
    USER = "user"         # 普通用户
    GUEST = "guest"       # 访客


# ==================== Pydantic 模型定义 ====================

class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: str

    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用户名长度必须在3-50个字符之间')
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v


class UserCreate(UserBase):
    """用户创建模型"""
    password: str
    role: UserRole = UserRole.USER

    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度至少8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class User(UserBase):
    """完整用户模型"""
    id: str
    role: UserRole
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    """任务基础模型"""
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    tags: List[str] = []
    assignee_ids: List[str] = []

    @validator('title')
    def validate_title(cls, v):
        """验证任务标题"""
        if len(v) < 1 or len(v) > 200:
            raise ValueError('任务标题长度必须在1-200个字符之间')
        return v


class TaskCreate(TaskBase):
    """任务创建模型"""
    parent_task_id: Optional[str] = None


class TaskUpdate(BaseModel):
    """任务更新模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    assignee_ids: Optional[List[str]] = None
    progress: Optional[int] = None

    @validator('progress')
    def validate_progress(cls, v):
        """验证进度值"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('进度值必须在0-100之间')
        return v


class Task(TaskBase):
    """完整任务模型"""
    id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    parent_task_id: Optional[str] = None
    creator_id: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    subtask_count: int = 0
    comment_count: int = 0

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    """评论创建模型"""
    content: str
    parent_comment_id: Optional[str] = None

    @validator('content')
    def validate_content(cls, v):
        """验证评论内容"""
        if len(v.strip()) < 1:
            raise ValueError('评论内容不能为空')
        if len(v) > 2000:
            raise ValueError('评论内容不能超过2000字符')
        return v.strip()


class Comment(BaseModel):
    """评论模型"""
    id: str
    task_id: str
    user_id: str
    content: str
    parent_comment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """令牌模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class ApiResponse(BaseModel):
    """通用API响应模型"""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[Dict[str, Any]]] = None


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# ==================== 数据库连接管理 ====================

class DatabaseManager:
    """数据库连接管理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据库管理器

        Args:
            config: 数据库配置字典
        """
        self.config = config
        self.pool = None

    async def connect(self):
        """建立数据库连接池"""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                db=self.config['database'],
                minsize=5,
                maxsize=20,
                autocommit=True
            )
            logger.info("数据库连接池创建成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise

    async def disconnect(self):
        """关闭数据库连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("数据库连接池已关闭")

    async def execute(self, query: str, params: tuple = None):
        """
        执行SQL查询

        Args:
            query: SQL语句
            params: 参数元组

        Returns:
            执行结果
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    async def execute_one(self, query: str, params: tuple = None):
        """执行查询并返回单条结果"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

    async def execute_many(self, query: str, params_list: List[tuple]):
        """批量执行SQL语句"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(query, params_list)
                return cur.rowcount


# ==================== 缓存管理 ====================

class CacheManager:
    """Redis缓存管理器"""

    def __init__(self, redis_url: str):
        """
        初始化缓存管理器

        Args:
            redis_url: Redis连接URL
        """
        self.redis_url = redis_url
        self.client = None

    async def connect(self):
        """连接Redis服务器"""
        try:
            self.client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            raise

    async def disconnect(self):
        """断开Redis连接"""
        if self.client:
            await self.client.close()
            logger.info("Redis连接已关闭")

    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        return await self.client.get(key)

    async def set(self, key: str, value: str, expire: int = 3600):
        """设置缓存值"""
        await self.client.setex(key, expire, value)

    async def delete(self, key: str):
        """删除缓存"""
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.client.exists(key)

    async def get_json(self, key: str) -> Optional[Dict]:
        """获取JSON格式的缓存"""
        value = await self.get(key)
        return json.loads(value) if value else None

    async def set_json(self, key: str, value: Dict, expire: int = 3600):
        """设置JSON格式的缓存"""
        await self.set(key, json.dumps(value), expire)


# ==================== 认证服务 ====================

class AuthService:
    """用户认证服务"""

    SECRET_KEY = "your-secret-key-here-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    def __init__(self, db: DatabaseManager, cache: CacheManager):
        """
        初始化认证服务

        Args:
            db: 数据库管理器
            cache: 缓存管理器
        """
        self.db = db
        self.cache = cache

    def hash_password(self, password: str) -> str:
        """
        对密码进行哈希加密

        Args:
            password: 原始密码

        Returns:
            加密后的密码哈希值
        """
        salt = uuid.uuid4().hex
        return f"{salt}:{hashlib.sha256((salt + password).encode()).hexdigest()}"

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        验证密码是否正确

        Args:
            password: 原始密码
            hashed: 存储的密码哈希值

        Returns:
            验证结果
        """
        try:
            salt, hash_value = hashed.split(':')
            return hash_value == hashlib.sha256((salt + password).encode()).hexdigest()
        except ValueError:
            return False

    def create_access_token(self, user_id: str, role: str) -> str:
        """
        创建访问令牌

        Args:
            user_id: 用户ID
            role: 用户角色

        Returns:
            JWT访问令牌
        """
        expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_refresh_token(self, user_id: str) -> str:
        """
        创建刷新令牌

        Args:
            user_id: 用户ID

        Returns:
            JWT刷新令牌
        """
        expire = datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def decode_token(self, token: str) -> Optional[Dict]:
        """
        解码并验证令牌

        Args:
            token: JWT令牌

        Returns:
            解码后的载荷，验证失败返回None
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("无效的令牌")
            return None

    async def register_user(self, user_data: UserCreate) -> User:
        """
        注册新用户

        Args:
            user_data: 用户注册数据

        Returns:
            创建的用户对象

        Raises:
            HTTPException: 用户已存在或创建失败
        """
        # 检查邮箱是否已存在
        existing = await self.db.execute_one(
            "SELECT id FROM users WHERE email = %s",
            (user_data.email,)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册"
            )

        # 检查用户名是否已存在
        existing = await self.db.execute_one(
            "SELECT id FROM users WHERE username = %s",
            (user_data.username,)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用户名已被使用"
            )

        # 创建用户
        user_id = str(uuid.uuid4())
        hashed_password = self.hash_password(user_data.password)
        now = datetime.utcnow()

        await self.db.execute(
            """
            INSERT INTO users (id, email, username, password_hash, role, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, user_data.email, user_data.username,
             hashed_password, user_data.role.value, now, now)
        )

        return User(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            role=user_data.role,
            created_at=now,
            updated_at=now
        )

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        验证用户登录

        Args:
            email: 用户邮箱
            password: 用户密码

        Returns:
            验证成功返回用户对象，失败返回None
        """
        user_data = await self.db.execute_one(
            "SELECT * FROM users WHERE email = %s AND is_active = TRUE",
            (email,)
        )

        if not user_data:
            return None

        if not self.verify_password(password, user_data['password_hash']):
            return None

        return User(
            id=user_data['id'],
            email=user_data['email'],
            username=user_data['username'],
            role=UserRole(user_data['role']),
            created_at=user_data['created_at'],
            updated_at=user_data['updated_at'],
            is_active=user_data['is_active'],
            avatar_url=user_data.get('avatar_url')
        )


# ==================== 任务服务 ====================

class TaskService:
    """任务管理服务"""

    def __init__(self, db: DatabaseManager, cache: CacheManager):
        """
        初始化任务服务

        Args:
            db: 数据库管理器
            cache: 缓存管理器
        """
        self.db = db
        self.cache = cache

    async def create_task(self, task_data: TaskCreate, creator_id: str) -> Task:
        """
        创建新任务

        Args:
            task_data: 任务创建数据
            creator_id: 创建者ID

        Returns:
            创建的任务对象
        """
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()

        await self.db.execute(
            """
            INSERT INTO tasks (
                id, title, description, status, priority, due_date,
                tags, assignee_ids, parent_task_id, creator_id,
                created_at, updated_at, progress
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                task_id, task_data.title, task_data.description,
                TaskStatus.PENDING.value, task_data.priority.value,
                task_data.due_date, json.dumps(task_data.tags),
                json.dumps(task_data.assignee_ids), task_data.parent_task_id,
                creator_id, now, now, 0
            )
        )

        # 更新父任务的子任务计数
        if task_data.parent_task_id:
            await self.db.execute(
                "UPDATE tasks SET subtask_count = subtask_count + 1 WHERE id = %s",
                (task_data.parent_task_id,)
            )

        # 清除相关缓存
        await self.cache.delete(f"user_tasks:{creator_id}")

        return Task(
            id=task_id,
            title=task_data.title,
            description=task_data.description,
            status=TaskStatus.PENDING,
            priority=task_data.priority,
            due_date=task_data.due_date,
            tags=task_data.tags,
            assignee_ids=task_data.assignee_ids,
            parent_task_id=task_data.parent_task_id,
            creator_id=creator_id,
            created_at=now,
            updated_at=now,
            progress=0
        )

    async def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        根据ID获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象，不存在则返回None
        """
        # 先尝试从缓存获取
        cached = await self.cache.get_json(f"task:{task_id}")
        if cached:
            return Task(**cached)

        task_data = await self.db.execute_one(
            "SELECT * FROM tasks WHERE id = %s",
            (task_id,)
        )

        if not task_data:
            return None

        task = Task(
            id=task_data['id'],
            title=task_data['title'],
            description=task_data['description'],
            status=TaskStatus(task_data['status']),
            priority=TaskPriority(task_data['priority']),
            due_date=task_data['due_date'],
            tags=json.loads(task_data['tags']) if task_data['tags'] else [],
            assignee_ids=json.loads(task_data['assignee_ids']) if task_data['assignee_ids'] else [],
            parent_task_id=task_data['parent_task_id'],
            creator_id=task_data['creator_id'],
            created_at=task_data['created_at'],
            updated_at=task_data['updated_at'],
            completed_at=task_data['completed_at'],
            progress=task_data['progress'],
            subtask_count=task_data['subtask_count'],
            comment_count=task_data['comment_count']
        )

        # 缓存任务数据
        await self.cache.set_json(f"task:{task_id}", task.model_dump(), expire=300)

        return task

    async def update_task(self, task_id: str, update_data: TaskUpdate, user_id: str) -> Task:
        """
        更新任务信息

        Args:
            task_id: 任务ID
            update_data: 更新数据
            user_id: 操作用户ID

        Returns:
            更新后的任务对象

        Raises:
            HTTPException: 任务不存在或无权限
        """
        task = await self.get_task_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        # 构建更新语句
        updates = []
        params = []
        now = datetime.utcnow()

        update_fields = {
            'title': update_data.title,
            'description': update_data.description,
            'status': update_data.status.value if update_data.status else None,
            'priority': update_data.priority.value if update_data.priority else None,
            'due_date': update_data.due_date,
            'tags': json.dumps(update_data.tags) if update_data.tags is not None else None,
            'assignee_ids': json.dumps(update_data.assignee_ids) if update_data.assignee_ids is not None else None,
            'progress': update_data.progress
        }

        for field, value in update_fields.items():
            if value is not None:
                updates.append(f"{field} = %s")
                params.append(value)

        if not updates:
            return task

        # 如果状态变为完成，记录完成时间
        if update_data.status == TaskStatus.COMPLETED:
            updates.append("completed_at = %s")
            params.append(now)

        updates.append("updated_at = %s")
        params.append(now)
        params.append(task_id)

        await self.db.execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s",
            tuple(params)
        )

        # 清除缓存
        await self.cache.delete(f"task:{task_id}")

        return await self.get_task_by_id(task_id)

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID
            user_id: 操作用户ID

        Returns:
            删除是否成功

        Raises:
            HTTPException: 任务不存在或无权限
        """
        task = await self.get_task_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        # 软删除：将状态改为已归档
        await self.db.execute(
            "UPDATE tasks SET status = %s, updated_at = %s WHERE id = %s",
            (TaskStatus.ARCHIVED.value, datetime.utcnow(), task_id)
        )

        await self.cache.delete(f"task:{task_id}")

        return True

    async def get_user_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponse:
        """
        获取用户任务列表

        Args:
            user_id: 用户ID
            status: 按状态筛选
            priority: 按优先级筛选
            page: 页码
            page_size: 每页数量

        Returns:
            分页的任务列表
        """
        conditions = ["(creator_id = %s OR JSON_CONTAINS(assignee_ids, %s))"]
        params = [user_id, f'"{user_id}"']

        if status:
            conditions.append("status = %s")
            params.append(status.value)

        if priority:
            conditions.append("priority = %s")
            params.append(priority.value)

        where_clause = " AND ".join(conditions)

        # 获取总数
        count_result = await self.db.execute_one(
            f"SELECT COUNT(*) as total FROM tasks WHERE {where_clause}",
            tuple(params)
        )
        total = count_result['total']

        # 获取分页数据
        offset = (page - 1) * page_size
        params.extend([offset, page_size])

        tasks_data = await self.db.execute(
            f"""
            SELECT * FROM tasks
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s, %s
            """,
            tuple(params)
        )

        tasks = []
        for task_data in tasks_data:
            tasks.append(Task(
                id=task_data['id'],
                title=task_data['title'],
                description=task_data['description'],
                status=TaskStatus(task_data['status']),
                priority=TaskPriority(task_data['priority']),
                due_date=task_data['due_date'],
                tags=json.loads(task_data['tags']) if task_data['tags'] else [],
                assignee_ids=json.loads(task_data['assignee_ids']) if task_data['assignee_ids'] else [],
                parent_task_id=task_data['parent_task_id'],
                creator_id=task_data['creator_id'],
                created_at=task_data['created_at'],
                updated_at=task_data['updated_at'],
                completed_at=task_data['completed_at'],
                progress=task_data['progress'],
                subtask_count=task_data['subtask_count'],
                comment_count=task_data['comment_count']
            ))

        total_pages = (total + page_size - 1) // page_size

        return PaginatedResponse(
            items=tasks,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

    async def get_task_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        获取任务统计数据

        Args:
            user_id: 用户ID

        Returns:
            统计数据字典
        """
        stats = await self.db.execute_one(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(CASE WHEN priority = 'urgent' THEN 1 ELSE 0 END) as urgent,
                SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) as high,
                AVG(progress) as avg_progress
            FROM tasks
            WHERE creator_id = %s OR JSON_CONTAINS(assignee_ids, %s)
            """,
            (user_id, f'"{user_id}"')
        )

        return {
            "total": stats['total'] or 0,
            "by_status": {
                "pending": stats['pending'] or 0,
                "in_progress": stats['in_progress'] or 0,
                "completed": stats['completed'] or 0,
                "cancelled": stats['cancelled'] or 0
            },
            "by_priority": {
                "urgent": stats['urgent'] or 0,
                "high": stats['high'] or 0,
                "medium": 0,  # 需要额外查询
                "low": 0
            },
            "average_progress": round(stats['avg_progress'] or 0, 2)
        }


# ==================== WebSocket 连接管理 ====================

class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        """初始化连接管理器"""
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        接受新的WebSocket连接

        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
        """
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"用户 {user_id} 建立WebSocket连接")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        断开WebSocket连接

        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"用户 {user_id} 断开WebSocket连接")

    async def send_personal_message(self, message: dict, user_id: str):
        """
        发送个人消息

        Args:
            message: 消息内容
            user_id: 目标用户ID
        """
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"发送消息失败: {str(e)}")

    async def broadcast(self, message: dict):
        """
        广播消息给所有连接

        Args:
            message: 消息内容
        """
        for user_id in self.active_connections:
            await self.send_personal_message(message, user_id)


# ==================== 全局实例和依赖 ====================

db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'password',
    'database': 'task_management'
}

db = DatabaseManager(db_config)
cache = CacheManager("redis://localhost:6379/0")
auth_service = AuthService(db, cache)
task_service = TaskService(db, cache)
manager = ConnectionManager()

security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时连接数据库和缓存
    await db.connect()
    await cache.connect()
    logger.info("应用启动完成")
    yield
    # 关闭时断开连接
    await db.disconnect()
    await cache.disconnect()
    logger.info("应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="智能任务管理系统 API",
    description="提供任务的增删改查、用户认证、实时通信等功能",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    获取当前登录用户

    Args:
        credentials: HTTP认证凭据

    Returns:
        当前用户对象

    Raises:
        HTTPException: 认证失败
    """
    token = credentials.credentials
    payload = auth_service.decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data = await db.execute_one(
        "SELECT * FROM users WHERE id = %s AND is_active = TRUE",
        (payload['sub'],)
    )

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(
        id=user_data['id'],
        email=user_data['email'],
        username=user_data['username'],
        role=UserRole(user_data['role']),
        created_at=user_data['created_at'],
        updated_at=user_data['updated_at'],
        is_active=user_data['is_active'],
        avatar_url=user_data.get('avatar_url')
    )


# ==================== API 路由定义 ====================

@app.get("/", tags=["根路由"])
async def root():
    """根路由 - 健康检查"""
    return {"message": "智能任务管理系统 API 服务运行中", "version": "1.0.0"}


@app.post("/api/auth/register", response_model=ApiResponse, tags=["认证"])
async def register(user_data: UserCreate):
    """
    用户注册

    - **email**: 用户邮箱
    - **username**: 用户名（3-50个字符，仅字母数字）
    - **password**: 密码（至少8字符，包含大写字母和数字）
    - **role**: 用户角色（可选，默认为普通用户）
    """
    try:
        user = await auth_service.register_user(user_data)
        return ApiResponse(
            success=True,
            message="用户注册成功",
            data={"user_id": user.id, "username": user.username}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        return ApiResponse(
            success=False,
            message="注册失败，请稍后重试",
            errors=[{"detail": str(e)}]
        )


@app.post("/api/auth/login", response_model=Token, tags=["认证"])
async def login(email: str, password: str):
    """
    用户登录

    - **email**: 用户邮箱
    - **password**: 用户密码
    """
    user = await auth_service.authenticate_user(email, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(user.id, user.role.value)
    refresh_token = auth_service.create_refresh_token(user.id)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/api/auth/refresh", response_model=Token, tags=["认证"])
async def refresh_token(refresh_token: str):
    """
    刷新访问令牌

    - **refresh_token**: 刷新令牌
    """
    payload = auth_service.decode_token(refresh_token)

    if not payload or payload.get('type') != 'refresh':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data = await db.execute_one(
        "SELECT * FROM users WHERE id = %s AND is_active = TRUE",
        (payload['sub'],)
    )

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token = auth_service.create_access_token(
        user_data['id'],
        user_data['role']
    )
    new_refresh_token = auth_service.create_refresh_token(user_data['id'])

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.get("/api/users/me", response_model=User, tags=["用户"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@app.put("/api/users/me", response_model=ApiResponse, tags=["用户"])
async def update_current_user(
    username: Optional[str] = None,
    avatar_url: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    更新当前用户信息

    - **username**: 新用户名
    - **avatar_url**: 头像URL
    """
    updates = []
    params = []

    if username:
        # 检查用户名是否已存在
        existing = await db.execute_one(
            "SELECT id FROM users WHERE username = %s AND id != %s",
            (username, current_user.id)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
        updates.append("username = %s")
        params.append(username)

    if avatar_url:
        updates.append("avatar_url = %s")
        params.append(avatar_url)

    if not updates:
        return ApiResponse(success=True, message="无更新内容", data=current_user.model_dump())

    updates.append("updated_at = %s")
    params.append(datetime.utcnow())
    params.append(current_user.id)

    await db.execute(
        f"UPDATE users SET {', '.join(updates)} WHERE id = %s",
        tuple(params)
    )

    return ApiResponse(success=True, message="用户信息更新成功")


@app.post("/api/tasks", response_model=ApiResponse, tags=["任务"])
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user)
):
    """
    创建新任务

    - **title**: 任务标题
    - **description**: 任务描述
    - **priority**: 优先级（low/medium/high/urgent）
    - **due_date**: 截止日期
    - **tags**: 标签列表
    - **assignee_ids**: 指派人ID列表
    - **parent_task_id**: 父任务ID
    """
    task = await task_service.create_task(task_data, current_user.id)

    # 通知相关人员
    for assignee_id in task_data.assignee_ids:
        await manager.send_personal_message(
            {
                "type": "task_assigned",
                "data": task.model_dump()
            },
            assignee_id
        )

    return ApiResponse(
        success=True,
        message="任务创建成功",
        data=task.model_dump()
    )


@app.get("/api/tasks", response_model=PaginatedResponse, tags=["任务"])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    获取任务列表

    - **status**: 按状态筛选
    - **priority**: 按优先级筛选
    - **page**: 页码
    - **page_size**: 每页数量
    """
    return await task_service.get_user_tasks(
        current_user.id, status, priority, page, page_size
    )


@app.get("/api/tasks/{task_id}", response_model=Task, tags=["任务"])
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取单个任务详情"""
    task = await task_service.get_task_by_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    return task


@app.put("/api/tasks/{task_id}", response_model=ApiResponse, tags=["任务"])
async def update_task(
    task_id: str,
    update_data: TaskUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新任务信息"""
    task = await task_service.update_task(task_id, update_data, current_user.id)

    # 通知相关人员
    await manager.send_personal_message(
        {
            "type": "task_updated",
            "data": task.model_dump()
        },
        current_user.id
    )

    return ApiResponse(
        success=True,
        message="任务更新成功",
        data=task.model_dump()
    )


@app.delete("/api/tasks/{task_id}", response_model=ApiResponse, tags=["任务"])
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除任务（软删除）"""
    await task_service.delete_task(task_id, current_user.id)

    return ApiResponse(success=True, message="任务已删除")


@app.get("/api/tasks/stats/overview", tags=["任务"])
async def get_task_stats(current_user: User = Depends(get_current_user)):
    """获取任务统计概览"""
    stats = await task_service.get_task_statistics(current_user.id)
    return ApiResponse(success=True, message="获取统计成功", data=stats)


@app.post("/api/tasks/{task_id}/comments", response_model=ApiResponse, tags=["评论"])
async def create_comment(
    task_id: str,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user)
):
    """
    创建任务评论

    - **content**: 评论内容
    - **parent_comment_id**: 父评论ID（回复时使用）
    """
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    comment_id = str(uuid.uuid4())
    now = datetime.utcnow()

    await db.execute(
        """
        INSERT INTO comments (id, task_id, user_id, content, parent_comment_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (comment_id, task_id, current_user.id, comment_data.content,
         comment_data.parent_comment_id, now, now)
    )

    # 更新任务评论计数
    await db.execute(
        "UPDATE tasks SET comment_count = comment_count + 1 WHERE id = %s",
        (task_id,)
    )

    comment = Comment(
        id=comment_id,
        task_id=task_id,
        user_id=current_user.id,
        content=comment_data.content,
        parent_comment_id=comment_data.parent_comment_id,
        created_at=now,
        updated_at=now
    )

    return ApiResponse(
        success=True,
        message="评论创建成功",
        data=comment.model_dump()
    )


@app.get("/api/tasks/{task_id}/comments", response_model=List[Comment], tags=["评论"])
async def get_task_comments(
    task_id: str,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user)
):
    """获取任务评论列表"""
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    offset = (page - 1) * page_size

    comments_data = await db.execute(
        """
        SELECT * FROM comments
        WHERE task_id = %s
        ORDER BY created_at DESC
        LIMIT %s, %s
        """,
        (task_id, offset, page_size)
    )

    comments = []
    for comment_data in comments_data:
        comments.append(Comment(
            id=comment_data['id'],
            task_id=comment_data['task_id'],
            user_id=comment_data['user_id'],
            content=comment_data['content'],
            parent_comment_id=comment_data['parent_comment_id'],
            created_at=comment_data['created_at'],
            updated_at=comment_data['updated_at']
        ))

    return comments


# ==================== WebSocket 路由 ====================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket连接端点

    提供实时任务更新通知
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()

            # 处理心跳
            if data.get('type') == 'ping':
                await websocket.send_json({'type': 'pong'})

            # 处理其他消息类型
            elif data.get('type') == 'subscribe_task':
                task_id = data.get('task_id')
                # 订阅任务更新通知
                await websocket.send_json({
                    'type': 'subscribed',
                    'task_id': task_id
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
        manager.disconnect(websocket, user_id)


# ==================== 错误处理 ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    return ApiResponse(
        success=False,
        message=exc.detail,
        errors=[{"status_code": exc.status_code}]
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return ApiResponse(
        success=False,
        message="服务器内部错误",
        errors=[{"detail": str(exc)}]
    )


# ==================== 应用入口 ====================

if __name__ == "__main__":
    import uvicorn

    # 启动开发服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )