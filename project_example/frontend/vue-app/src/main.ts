/**
 * 智能任务管理系统 - Vue.js 前端应用
 * 提供用户界面、任务管理、实时通知等功能
 * 使用 Vue 3 Composition API + TypeScript + Pinia + Vue Router
 */

// ==================== 类型定义 ====================

/**
 * 任务状态枚举
 */
export enum TaskStatus {
  PENDING = 'pending',           // 待处理
  IN_PROGRESS = 'in_progress',   // 进行中
  COMPLETED = 'completed',       // 已完成
  CANCELLED = 'cancelled',       // 已取消
  ARCHIVED = 'archived'          // 已归档
}

/**
 * 任务优先级枚举
 */
export enum TaskPriority {
  LOW = 'low',        // 低优先级
  MEDIUM = 'medium',  // 中优先级
  HIGH = 'high',      // 高优先级
  URGENT = 'urgent'   // 紧急
}

/**
 * 用户角色枚举
 */
export enum UserRole {
  ADMIN = 'admin',     // 管理员
  MANAGER = 'manager', // 经理
  USER = 'user',       // 普通用户
  GUEST = 'guest'      // 访客
}

/**
 * 用户接口定义
 */
export interface User {
  id: string
  email: string
  username: string
  role: UserRole
  createdAt: Date
  updatedAt: Date
  isActive: boolean
  avatarUrl?: string
}

/**
 * 任务接口定义
 */
export interface Task {
  id: string
  title: string
  description?: string
  status: TaskStatus
  priority: TaskPriority
  dueDate?: Date
  tags: string[]
  assigneeIds: string[]
  parentTaskId?: string
  creatorId: string
  createdAt: Date
  updatedAt: Date
  completedAt?: Date
  progress: number
  subtaskCount: number
  commentCount: number
}

/**
 * 评论接口定义
 */
export interface Comment {
  id: string
  taskId: string
  userId: string
  content: string
  parentCommentId?: string
  createdAt: Date
  updatedAt: Date
}

/**
 * 分页响应接口
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
}

/**
 * API响应接口
 */
export interface ApiResponse<T = unknown> {
  success: boolean
  message: string
  data?: T
  errors?: Array<{ detail: string; statusCode?: number }>
}

/**
 * 认证令牌接口
 */
export interface Token {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
}

/**
 * 登录表单接口
 */
export interface LoginForm {
  email: string
  password: string
  rememberMe?: boolean
}

/**
 * 注册表单接口
 */
export interface RegisterForm {
  email: string
  username: string
  password: string
  confirmPassword: string
  role?: UserRole
}

/**
 * 任务创建表单接口
 */
export interface TaskCreateForm {
  title: string
  description?: string
  priority: TaskPriority
  dueDate?: Date
  tags: string[]
  assigneeIds: string[]
  parentTaskId?: string
}

/**
 * 任务筛选参数接口
 */
export interface TaskFilterParams {
  status?: TaskStatus
  priority?: TaskPriority
  page?: number
  pageSize?: number
  searchKeyword?: string
}

/**
 * WebSocket消息接口
 */
export interface WebSocketMessage {
  type: 'task_assigned' | 'task_updated' | 'task_deleted' | 'comment_added' | 'pong' | 'subscribed'
  data?: Task | Comment | { taskId: string }
  taskId?: string
}

// ==================== API 客户端 ====================

/**
 * HTTP客户端类
 * 封装所有API请求，支持认证、错误处理、请求拦截
 */
class HttpClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
    // 从本地存储恢复令牌
    this.token = localStorage.getItem('access_token')
  }

  /**
   * 设置认证令牌
   * @param token - 访问令牌
   */
  setToken(token: string | null): void {
    this.token = token
    if (token) {
      localStorage.setItem('access_token', token)
    } else {
      localStorage.removeItem('access_token')
    }
  }

  /**
   * 获取请求头
   * @returns 请求头对象
   */
  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    return headers
  }

  /**
   * 发送GET请求
   * @param endpoint - API端点
   * @param params - 查询参数
   * @returns 响应数据
   */
  async get<T>(endpoint: string, params?: Record<string, string | number | boolean>): Promise<T> {
    let url = `${this.baseUrl}${endpoint}`

    if (params) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
      url += `?${searchParams.toString()}`
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders()
    })

    return this.handleResponse<T>(response)
  }

  /**
   * 发送POST请求
   * @param endpoint - API端点
   * @param data - 请求体数据
   * @returns 响应数据
   */
  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined
    })

    return this.handleResponse<T>(response)
  }

  /**
   * 发送PUT请求
   * @param endpoint - API端点
   * @param data - 请求体数据
   * @returns 响应数据
   */
  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined
    })

    return this.handleResponse<T>(response)
  }

  /**
   * 发送DELETE请求
   * @param endpoint - API端点
   * @returns 响应数据
   */
  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders()
    })

    return this.handleResponse<T>(response)
  }

  /**
   * 处理响应
   * @param response - Fetch响应对象
   * @returns 解析后的数据
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: '网络错误' }))
      throw new ApiError(
        error.message || `HTTP Error: ${response.status}`,
        response.status,
        error.errors
      )
    }

    return response.json()
  }
}

/**
 * API错误类
 */
class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public errors?: Array<{ detail: string }>
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// 创建HTTP客户端实例
const apiClient = new HttpClient(import.meta.env.VITE_API_URL || 'http://localhost:8000')

// ==================== 认证服务 ====================

/**
 * 认证服务
 * 处理用户登录、注册、令牌刷新等认证相关功能
 */
export class AuthService {
  private refreshTimer: number | null = null

  /**
   * 用户登录
   * @param form - 登录表单数据
   * @returns 认证令牌
   */
  async login(form: LoginForm): Promise<Token> {
    const formData = new URLSearchParams()
    formData.append('email', form.email)
    formData.append('password', form.password)

    const token = await apiClient.post<Token>('/api/auth/login', {
      email: form.email,
      password: form.password
    })

    this.setTokens(token)

    if (form.rememberMe) {
      localStorage.setItem('refresh_token', token.refreshToken)
    }

    this.scheduleTokenRefresh(token.expiresIn)

    return token
  }

  /**
   * 用户注册
   * @param form - 注册表单数据
   * @returns API响应
   */
  async register(form: RegisterForm): Promise<ApiResponse> {
    if (form.password !== form.confirmPassword) {
      throw new Error('两次输入的密码不一致')
    }

    return apiClient.post<ApiResponse>('/api/auth/register', {
      email: form.email,
      username: form.username,
      password: form.password,
      role: form.role || UserRole.USER
    })
  }

  /**
   * 用户登出
   */
  logout(): void {
    apiClient.setToken(null)
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')

    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
      this.refreshTimer = null
    }
  }

  /**
   * 刷新访问令牌
   * @returns 新的认证令牌
   */
  async refreshToken(): Promise<Token> {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      throw new Error('无刷新令牌')
    }

    const token = await apiClient.post<Token>('/api/auth/refresh', { refresh_token: refreshToken })
    this.setTokens(token)
    this.scheduleTokenRefresh(token.expiresIn)

    return token
  }

  /**
   * 获取当前用户信息
   * @returns 用户信息
   */
  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/api/users/me')
  }

  /**
   * 设置令牌
   * @param token - 认证令牌
   */
  private setTokens(token: Token): void {
    apiClient.setToken(token.accessToken)
  }

  /**
   * 安排令牌刷新
   * @param expiresIn - 过期时间（秒）
   */
  private scheduleTokenRefresh(expiresIn: number): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
    }

    // 在过期前5分钟刷新令牌
    const refreshTime = (expiresIn - 300) * 1000

    this.refreshTimer = window.setTimeout(() => {
      this.refreshToken().catch(console.error)
    }, refreshTime)
  }

  /**
   * 检查是否已认证
   * @returns 是否已认证
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  }
}

// ==================== 任务服务 ====================

/**
 * 任务服务
 * 处理任务的增删改查、状态管理、筛选等功能
 */
export class TaskService {
  /**
   * 创建新任务
   * @param form - 任务创建表单
   * @returns 创建的任务
   */
  async createTask(form: TaskCreateForm): Promise<Task> {
    const response = await apiClient.post<ApiResponse<Task>>('/api/tasks', {
      title: form.title,
      description: form.description,
      priority: form.priority,
      due_date: form.dueDate?.toISOString(),
      tags: form.tags,
      assignee_ids: form.assigneeIds,
      parent_task_id: form.parentTaskId
    })

    return response.data!
  }

  /**
   * 获取任务列表
   * @param params - 筛选参数
   * @returns 分页任务列表
   */
  async getTasks(params: TaskFilterParams = {}): Promise<PaginatedResponse<Task>> {
    return apiClient.get<PaginatedResponse<Task>>('/api/tasks', {
      status: params.status,
      priority: params.priority,
      page: params.page || 1,
      page_size: params.pageSize || 20
    })
  }

  /**
   * 获取单个任务详情
   * @param taskId - 任务ID
   * @returns 任务详情
   */
  async getTaskById(taskId: string): Promise<Task> {
    return apiClient.get<Task>(`/api/tasks/${taskId}`)
  }

  /**
   * 更新任务
   * @param taskId - 任务ID
   * @param updates - 更新数据
   * @returns 更新后的任务
   */
  async updateTask(taskId: string, updates: Partial<Task>): Promise<Task> {
    const response = await apiClient.put<ApiResponse<Task>>(`/api/tasks/${taskId}`, {
      title: updates.title,
      description: updates.description,
      status: updates.status,
      priority: updates.priority,
      due_date: updates.dueDate?.toISOString(),
      tags: updates.tags,
      assignee_ids: updates.assigneeIds,
      progress: updates.progress
    })

    return response.data!
  }

  /**
   * 删除任务
   * @param taskId - 任务ID
   */
  async deleteTask(taskId: string): Promise<void> {
    await apiClient.delete<ApiResponse>(`/api/tasks/${taskId}`)
  }

  /**
   * 获取任务统计数据
   * @returns 统计数据
   */
  async getStatistics(): Promise<Record<string, unknown>> {
    const response = await apiClient.get<ApiResponse<Record<string, unknown>>>('/api/tasks/stats/overview')
    return response.data!
  }

  /**
   * 更新任务状态
   * @param taskId - 任务ID
   * @param status - 新状态
   * @returns 更新后的任务
   */
  async updateStatus(taskId: string, status: TaskStatus): Promise<Task> {
    return this.updateTask(taskId, { status })
  }

  /**
   * 更新任务进度
   * @param taskId - 任务ID
   * @param progress - 进度值（0-100）
   * @returns 更新后的任务
   */
  async updateProgress(taskId: string, progress: number): Promise<Task> {
    return this.updateTask(taskId, { progress: Math.min(100, Math.max(0, progress)) })
  }
}

// ==================== 评论服务 ====================

/**
 * 评论服务
 * 处理任务评论的创建、查询等功能
 */
export class CommentService {
  /**
   * 创建评论
   * @param taskId - 任务ID
   * @param content - 评论内容
   * @param parentCommentId - 父评论ID（回复时使用）
   * @returns 创建的评论
   */
  async createComment(taskId: string, content: string, parentCommentId?: string): Promise<Comment> {
    const response = await apiClient.post<ApiResponse<Comment>>(`/api/tasks/${taskId}/comments`, {
      content,
      parent_comment_id: parentCommentId
    })

    return response.data!
  }

  /**
   * 获取任务评论列表
   * @param taskId - 任务ID
   * @param page - 页码
   * @param pageSize - 每页数量
   * @returns 评论列表
   */
  async getComments(taskId: string, page: number = 1, pageSize: number = 20): Promise<Comment[]> {
    return apiClient.get<Comment[]>(`/api/tasks/${taskId}/comments`, {
      page,
      page_size: pageSize
    })
  }
}

// ==================== WebSocket 服务 ====================

/**
 * WebSocket服务
 * 提供实时通信功能，接收任务更新通知
 */
export class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private listeners: Map<string, Set<(data: unknown) => void>> = new Map()

  /**
   * 连接WebSocket
   * @param userId - 用户ID
   */
  connect(userId: string): void {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    this.ws = new WebSocket(`${wsUrl}/ws/${userId}`)

    this.ws.onopen = () => {
      console.log('WebSocket连接已建立')
      this.reconnectAttempts = 0
      this.startHeartbeat()
    }

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        this.handleMessage(message)
      } catch (error) {
        console.error('解析WebSocket消息失败:', error)
      }
    }

    this.ws.onclose = () => {
      console.log('WebSocket连接已关闭')
      this.stopHeartbeat()
      this.attemptReconnect(userId)
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.stopHeartbeat()
    this.listeners.clear()
  }

  /**
   * 订阅事件
   * @param eventType - 事件类型
   * @param callback - 回调函数
   * @returns 取消订阅函数
   */
  subscribe(eventType: string, callback: (data: unknown) => void): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set())
    }
    this.listeners.get(eventType)!.add(callback)

    return () => {
      this.listeners.get(eventType)?.delete(callback)
    }
  }

  /**
   * 订阅任务更新
   * @param taskId - 任务ID
   */
  subscribeToTask(taskId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe_task',
        task_id: taskId
      }))
    }
  }

  /**
   * 发送心跳
   */
  private heartbeatTimer: number | null = null

  private startHeartbeat(): void {
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 处理消息
   * @param message - WebSocket消息
   */
  private handleMessage(message: WebSocketMessage): void {
    const callbacks = this.listeners.get(message.type)
    if (callbacks) {
      callbacks.forEach(callback => callback(message.data))
    }

    // 广播到通用监听器
    const allCallbacks = this.listeners.get('*')
    if (allCallbacks) {
      allCallbacks.forEach(callback => callback(message))
    }
  }

  /**
   * 尝试重连
   * @param userId - 用户ID
   */
  private attemptReconnect(userId: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket重连失败次数过多')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    setTimeout(() => {
      console.log(`尝试WebSocket重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      this.connect(userId)
    }, delay)
  }
}

// ==================== 状态管理 (Pinia Store) ====================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 认证状态存储
 */
export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === UserRole.ADMIN)
  const isManager = computed(() => user.value?.role === UserRole.MANAGER || isAdmin.value)

  // 服务实例
  const authService = new AuthService()

  // 操作方法
  /**
   * 用户登录
   */
  async function login(form: LoginForm): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      const tokenData = await authService.login(form)
      token.value = tokenData.accessToken

      // 获取用户信息
      user.value = await authService.getCurrentUser()

      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '登录失败'
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 用户注册
   */
  async function register(form: RegisterForm): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      await authService.register(form)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '注册失败'
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 用户登出
   */
  function logout(): void {
    authService.logout()
    user.value = null
    token.value = null
  }

  /**
   * 刷新用户信息
   */
  async function refreshUser(): Promise<void> {
    if (!token.value) return

    try {
      user.value = await authService.getCurrentUser()
    } catch (err) {
      console.error('刷新用户信息失败:', err)
    }
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    isManager,
    login,
    register,
    logout,
    refreshUser
  }
})

/**
 * 任务状态存储
 */
export const useTaskStore = defineStore('task', () => {
  // 状态
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const pagination = ref({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0
  })
  const filters = ref<TaskFilterParams>({
    status: undefined,
    priority: undefined,
    page: 1,
    pageSize: 20
  })

  // 统计数据
  const statistics = ref({
    total: 0,
    byStatus: {
      pending: 0,
      in_progress: 0,
      completed: 0,
      cancelled: 0
    },
    byPriority: {
      urgent: 0,
      high: 0,
      medium: 0,
      low: 0
    },
    averageProgress: 0
  })

  // 服务实例
  const taskService = new TaskService()

  // 计算属性
  const pendingTasks = computed(() =>
    tasks.value.filter(t => t.status === TaskStatus.PENDING)
  )

  const inProgressTasks = computed(() =>
    tasks.value.filter(t => t.status === TaskStatus.IN_PROGRESS)
  )

  const completedTasks = computed(() =>
    tasks.value.filter(t => t.status === TaskStatus.COMPLETED)
  )

  const urgentTasks = computed(() =>
    tasks.value.filter(t => t.priority === TaskPriority.URGENT)
  )

  // 操作方法
  /**
   * 加载任务列表
   */
  async function loadTasks(params?: TaskFilterParams): Promise<void> {
    loading.value = true
    error.value = null

    try {
      if (params) {
        filters.value = { ...filters.value, ...params }
      }

      const response = await taskService.getTasks(filters.value)
      tasks.value = response.items
      pagination.value = {
        page: response.page,
        pageSize: response.pageSize,
        total: response.total,
        totalPages: response.totalPages
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载任务失败'
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载单个任务
   */
  async function loadTask(taskId: string): Promise<void> {
    loading.value = true
    error.value = null

    try {
      currentTask.value = await taskService.getTaskById(taskId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载任务失败'
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建任务
   */
  async function createTask(form: TaskCreateForm): Promise<Task | null> {
    loading.value = true
    error.value = null

    try {
      const task = await taskService.createTask(form)
      tasks.value.unshift(task)
      return task
    } catch (err) {
      error.value = err instanceof Error ? err.message : '创建任务失败'
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新任务
   */
  async function updateTask(taskId: string, updates: Partial<Task>): Promise<Task | null> {
    loading.value = true
    error.value = null

    try {
      const task = await taskService.updateTask(taskId, updates)
      const index = tasks.value.findIndex(t => t.id === taskId)
      if (index !== -1) {
        tasks.value[index] = task
      }
      if (currentTask.value?.id === taskId) {
        currentTask.value = task
      }
      return task
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新任务失败'
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除任务
   */
  async function deleteTask(taskId: string): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      await taskService.deleteTask(taskId)
      tasks.value = tasks.value.filter(t => t.id !== taskId)
      if (currentTask.value?.id === taskId) {
        currentTask.value = null
      }
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除任务失败'
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载统计数据
   */
  async function loadStatistics(): Promise<void> {
    try {
      const stats = await taskService.getStatistics()
      statistics.value = stats as typeof statistics.value
    } catch (err) {
      console.error('加载统计数据失败:', err)
    }
  }

  /**
   * 重置筛选条件
   */
  function resetFilters(): void {
    filters.value = {
      status: undefined,
      priority: undefined,
      page: 1,
      pageSize: 20
    }
  }

  /**
   * 设置筛选条件
   */
  function setFilter(key: keyof TaskFilterParams, value: unknown): void {
    filters.value[key] = value as never
    filters.value.page = 1
  }

  return {
    tasks,
    currentTask,
    loading,
    error,
    pagination,
    filters,
    statistics,
    pendingTasks,
    inProgressTasks,
    completedTasks,
    urgentTasks,
    loadTasks,
    loadTask,
    createTask,
    updateTask,
    deleteTask,
    loadStatistics,
    resetFilters,
    setFilter
  }
})

// ==================== Vue 组件 ====================

import { defineComponent, h, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

/**
 * 任务列表组件
 */
export const TaskListComponent = defineComponent({
  name: 'TaskList',

  setup() {
    const taskStore = useTaskStore()
    const router = useRouter()
    const route = useRoute()

    // 加载任务列表
    onMounted(() => {
      taskStore.loadTasks()
      taskStore.loadStatistics()
    })

    // 监听路由参数变化
    watch(
      () => route.query,
      (query) => {
        const params: TaskFilterParams = {}
        if (query.status) params.status = query.status as TaskStatus
        if (query.priority) params.priority = query.priority as TaskPriority
        if (query.page) params.page = Number(query.page)

        taskStore.loadTasks(params)
      },
      { immediate: true }
    )

    // 处理分页
    const handlePageChange = (page: number) => {
      router.push({ query: { ...route.query, page: String(page) } })
    }

    // 处理状态筛选
    const handleStatusFilter = (status?: TaskStatus) => {
      taskStore.setFilter('status', status)
      taskStore.loadTasks()
    }

    // 处理优先级筛选
    const handlePriorityFilter = (priority?: TaskPriority) => {
      taskStore.setFilter('priority', priority)
      taskStore.loadTasks()
    }

    // 查看任务详情
    const viewTask = (taskId: string) => {
      router.push({ name: 'task-detail', params: { id: taskId } })
    }

    // 创建新任务
    const createTask = () => {
      router.push({ name: 'task-create' })
    }

    // 获取状态标签颜色
    const getStatusColor = (status: TaskStatus): string => {
      const colors: Record<TaskStatus, string> = {
        [TaskStatus.PENDING]: 'gray',
        [TaskStatus.IN_PROGRESS]: 'blue',
        [TaskStatus.COMPLETED]: 'green',
        [TaskStatus.CANCELLED]: 'red',
        [TaskStatus.ARCHIVED]: 'slate'
      }
      return colors[status]
    }

    // 获取优先级标签颜色
    const getPriorityColor = (priority: TaskPriority): string => {
      const colors: Record<TaskPriority, string> = {
        [TaskPriority.LOW]: 'gray',
        [TaskPriority.MEDIUM]: 'blue',
        [TaskPriority.HIGH]: 'orange',
        [TaskPriority.URGENT]: 'red'
      }
      return colors[priority]
    }

    // 格式化日期
    const formatDate = (date?: Date): string => {
      if (!date) return '-'
      return new Date(date).toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      })
    }

    return () => {
      const { tasks, loading, error, pagination, statistics } = taskStore

      return h('div', { class: 'task-list-container' }, [
        // 头部统计卡片
        h('div', { class: 'stats-grid' }, [
          h('div', { class: 'stat-card' }, [
            h('div', { class: 'stat-value' }, statistics.total),
            h('div', { class: 'stat-label' }, '总任务数')
          ]),
          h('div', { class: 'stat-card' }, [
            h('div', { class: 'stat-value text-blue' }, statistics.byStatus.in_progress),
            h('div', { class: 'stat-label' }, '进行中')
          ]),
          h('div', { class: 'stat-card' }, [
            h('div', { class: 'stat-value text-green' }, statistics.byStatus.completed),
            h('div', { class: 'stat-label' }, '已完成')
          ]),
          h('div', { class: 'stat-card' }, [
            h('div', { class: 'stat-value text-red' }, statistics.byPriority.urgent),
            h('div', { class: 'stat-label' }, '紧急任务')
          ])
        ]),

        // 筛选和操作栏
        h('div', { class: 'toolbar' }, [
          h('div', { class: 'filters' }, [
            h('select', {
              class: 'filter-select',
              onChange: (e: Event) => handleStatusFilter((e.target as HTMLSelectElement).value as TaskStatus || undefined)
            }, [
              h('option', { value: '' }, '全部状态'),
              h('option', { value: TaskStatus.PENDING }, '待处理'),
              h('option', { value: TaskStatus.IN_PROGRESS }, '进行中'),
              h('option', { value: TaskStatus.COMPLETED }, '已完成'),
              h('option', { value: TaskStatus.CANCELLED }, '已取消')
            ]),
            h('select', {
              class: 'filter-select',
              onChange: (e: Event) => handlePriorityFilter((e.target as HTMLSelectElement).value as TaskPriority || undefined)
            }, [
              h('option', { value: '' }, '全部优先级'),
              h('option', { value: TaskPriority.LOW }, '低'),
              h('option', { value: TaskPriority.MEDIUM }, '中'),
              h('option', { value: TaskPriority.HIGH }, '高'),
              h('option', { value: TaskPriority.URGENT }, '紧急')
            ])
          ]),
          h('button', { class: 'btn-primary', onClick: createTask }, [
            h('span', { class: 'icon' }, '+'),
            '创建任务'
          ])
        ]),

        // 错误提示
        error && h('div', { class: 'error-message' }, error),

        // 加载状态
        loading && h('div', { class: 'loading' }, '加载中...'),

        // 任务列表
        !loading && tasks.length > 0 && h('div', { class: 'task-list' },
          tasks.map(task =>
            h('div', {
              class: 'task-card',
              key: task.id,
              onClick: () => viewTask(task.id)
            }, [
              h('div', { class: 'task-header' }, [
                h('h3', { class: 'task-title' }, task.title),
                h('span', {
                  class: `status-badge status-${getStatusColor(task.status)}`
                }, task.status)
              ]),
              h('div', { class: 'task-meta' }, [
                h('span', {
                  class: `priority-badge priority-${getPriorityColor(task.priority)}`
                }, task.priority),
                task.dueDate && h('span', { class: 'due-date' }, [
                  h('span', { class: 'icon' }, '📅'),
                  formatDate(task.dueDate)
                ]),
                h('span', { class: 'progress' }, `进度: ${task.progress}%`)
              ]),
              task.tags.length > 0 && h('div', { class: 'task-tags' },
                task.tags.map(tag =>
                  h('span', { class: 'tag', key: tag }, tag)
                )
              )
            ])
          )
        ),

        // 空状态
        !loading && tasks.length === 0 && h('div', { class: 'empty-state' }, [
          h('p', '暂无任务'),
          h('button', { class: 'btn-primary', onClick: createTask }, '创建第一个任务')
        ]),

        // 分页
        pagination.totalPages > 1 && h('div', { class: 'pagination' }, [
          h('button', {
            class: 'page-btn',
            disabled: pagination.page <= 1,
            onClick: () => handlePageChange(pagination.page - 1)
          }, '上一页'),
          h('span', { class: 'page-info' }, `第 ${pagination.page} / ${pagination.totalPages} 页`),
          h('button', {
            class: 'page-btn',
            disabled: pagination.page >= pagination.totalPages,
            onClick: () => handlePageChange(pagination.page + 1)
          }, '下一页')
        ])
      ])
    }
  }
})

/**
 * 任务详情组件
 */
export const TaskDetailComponent = defineComponent({
  name: 'TaskDetail',

  setup() {
    const taskStore = useTaskStore()
    const authStore = useAuthStore()
    const route = useRoute()
    const router = useRouter()
    const commentService = new CommentService()
    const wsService = new WebSocketService()

    const comments = ref<Comment[]>([])
    const newComment = ref('')
    const showEditModal = ref(false)

    // 加载任务详情
    onMounted(() => {
      const taskId = route.params.id as string
      taskStore.loadTask(taskId)
      loadComments(taskId)

      // 订阅任务更新
      if (authStore.user) {
        wsService.connect(authStore.user.id)
        wsService.subscribeToTask(taskId)
        wsService.subscribe('task_updated', (data) => {
          if (data) {
            taskStore.currentTask = data as Task
          }
        })
      }
    })

    onUnmounted(() => {
      wsService.disconnect()
    })

    // 加载评论
    const loadComments = async (taskId: string) => {
      try {
        comments.value = await commentService.getComments(taskId)
      } catch (err) {
        console.error('加载评论失败:', err)
      }
    }

    // 提交评论
    const submitComment = async () => {
      if (!newComment.value.trim() || !taskStore.currentTask) return

      try {
        const comment = await commentService.createComment(
          taskStore.currentTask.id,
          newComment.value.trim()
        )
        comments.value.unshift(comment)
        newComment.value = ''
      } catch (err) {
        console.error('提交评论失败:', err)
      }
    }

    // 更新任务状态
    const updateStatus = async (status: TaskStatus) => {
      if (!taskStore.currentTask) return
      await taskStore.updateTask(taskStore.currentTask.id, { status })
    }

    // 更新任务进度
    const updateProgress = async (progress: number) => {
      if (!taskStore.currentTask) return
      await taskStore.updateTask(taskStore.currentTask.id, { progress })
    }

    // 返回列表
    const goBack = () => {
      router.push({ name: 'task-list' })
    }

    // 编辑任务
    const editTask = () => {
      showEditModal.value = true
    }

    return () => {
      const { currentTask, loading, error } = taskStore

      if (loading) {
        return h('div', { class: 'loading-container' }, '加载中...')
      }

      if (error) {
        return h('div', { class: 'error-container' }, [
          h('p', error),
          h('button', { onClick: goBack }, '返回列表')
        ])
      }

      if (!currentTask) {
        return h('div', { class: 'not-found' }, [
          h('p', '任务不存在'),
          h('button', { onClick: goBack }, '返回列表')
        ])
      }

      return h('div', { class: 'task-detail-container' }, [
        // 头部操作栏
        h('div', { class: 'detail-header' }, [
          h('button', { class: 'btn-secondary', onClick: goBack }, '← 返回'),
          h('div', { class: 'header-actions' }, [
            h('button', { class: 'btn-primary', onClick: editTask }, '编辑'),
            h('button', {
              class: 'btn-danger',
              onClick: () => taskStore.deleteTask(currentTask.id).then(goBack)
            }, '删除')
          ])
        ]),

        // 任务信息
        h('div', { class: 'task-info' }, [
          h('h1', { class: 'task-title' }, currentTask.title),
          currentTask.description && h('p', { class: 'task-description' }, currentTask.description),

          // 元信息
          h('div', { class: 'meta-grid' }, [
            h('div', { class: 'meta-item' }, [
              h('label', '状态'),
              h('select', {
                class: 'status-select',
                value: currentTask.status,
                onChange: (e: Event) => updateStatus((e.target as HTMLSelectElement).value as TaskStatus)
              }, [
                h('option', { value: TaskStatus.PENDING }, '待处理'),
                h('option', { value: TaskStatus.IN_PROGRESS }, '进行中'),
                h('option', { value: TaskStatus.COMPLETED }, '已完成'),
                h('option', { value: TaskStatus.CANCELLED }, '已取消')
              ])
            ]),
            h('div', { class: 'meta-item' }, [
              h('label', '优先级'),
              h('span', { class: `priority-badge priority-${currentTask.priority}` }, currentTask.priority)
            ]),
            h('div', { class: 'meta-item' }, [
              h('label', '截止日期'),
              h('span', currentTask.dueDate ? new Date(currentTask.dueDate).toLocaleDateString('zh-CN') : '未设置')
            ]),
            h('div', { class: 'meta-item' }, [
              h('label', '创建时间'),
              h('span', new Date(currentTask.createdAt).toLocaleString('zh-CN'))
            ])
          ]),

          // 进度条
          h('div', { class: 'progress-section' }, [
            h('label', `进度: ${currentTask.progress}%`),
            h('div', { class: 'progress-bar' }, [
              h('div', {
                class: 'progress-fill',
                style: { width: `${currentTask.progress}%` }
              })
            ]),
            h('input', {
              type: 'range',
              min: 0,
              max: 100,
              value: currentTask.progress,
              onInput: (e: Event) => updateProgress(Number((e.target as HTMLInputElement).value))
            })
          ]),

          // 标签
          currentTask.tags.length > 0 && h('div', { class: 'tags-section' }, [
            h('label', '标签'),
            h('div', { class: 'tags-list' },
              currentTask.tags.map(tag =>
                h('span', { class: 'tag', key: tag }, tag)
              )
            )
          ])
        ]),

        // 评论区域
        h('div', { class: 'comments-section' }, [
          h('h2', '评论'),
          h('div', { class: 'comment-form' }, [
            h('textarea', {
              class: 'comment-input',
              placeholder: '写下你的评论...',
              value: newComment.value,
              onInput: (e: Event) => { newComment.value = (e.target as HTMLTextAreaElement).value }
            }),
            h('button', {
              class: 'btn-primary',
              onClick: submitComment,
              disabled: !newComment.value.trim()
            }, '发表评论')
          ]),
          h('div', { class: 'comments-list' },
            comments.value.map(comment =>
              h('div', { class: 'comment-item', key: comment.id }, [
                h('div', { class: 'comment-header' }, [
                  h('span', { class: 'comment-author' }, comment.userId),
                  h('span', { class: 'comment-time' }, new Date(comment.createdAt).toLocaleString('zh-CN'))
                ]),
                h('p', { class: 'comment-content' }, comment.content)
              ])
            )
          )
        ])
      ])
    }
  }
})

// ==================== 路由配置 ====================

import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

/**
 * 应用路由配置
 */
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/tasks'
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('./views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('./views/RegisterView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/tasks',
    name: 'task-list',
    component: TaskListComponent,
    meta: { requiresAuth: true }
  },
  {
    path: '/tasks/create',
    name: 'task-create',
    component: () => import('./views/TaskCreateView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tasks/:id',
    name: 'task-detail',
    component: TaskDetailComponent,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('./views/ProfileView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('./views/NotFoundView.vue')
  }
]

/**
 * 创建路由实例
 */
const router = createRouter({
  history: createWebHistory(),
  routes
})

/**
 * 路由守卫 - 认证检查
 */
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (!to.meta.requiresAuth && authStore.isAuthenticated) {
    next({ name: 'task-list' })
  } else {
    next()
  }
})

// ==================== 应用入口 ====================

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

// 创建应用实例
const app = createApp(App)

// 使用插件
app.use(createPinia())
app.use(router)

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue错误:', err)
  console.error('错误信息:', info)
}

// 挂载应用
app.mount('#app')

// 导出模块
export default app