// 智能任务管理系统 - Go 后台任务处理服务
// 提供异步任务处理、定时任务调度、消息队列消费等功能
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/go-redis/redis/v8"
	_ "github.com/go-sql-driver/mysql"
	"github.com/robfig/cron/v3"
)

// ==================== 常量定义 ====================

const (
	// Redis键前缀
	RedisKeyPrefix        = "task_manager:"
	RedisKeyTaskQueue     = RedisKeyPrefix + "task_queue"
	RedisKeyNotification  = RedisKeyPrefix + "notifications"
	RedisKeyTaskLock      = RedisKeyPrefix + "task_lock:"
	RedisKeyWorkerStatus  = RedisKeyPrefix + "worker_status"

	// 任务类型
	TaskTypeSendEmail     = "send_email"
	TaskTypeSendSMS       = "send_sms"
	TaskTypeGenerateReport = "generate_report"
	TaskTypeCleanExpired  = "clean_expired"
	TaskTypeSyncData      = "sync_data"
	TaskTypeNotification  = "notification"

	// 任务状态
	TaskStatusPending     = "pending"
	TaskStatusProcessing  = "processing"
	TaskStatusCompleted   = "completed"
	TaskStatusFailed      = "failed"

	// 最大重试次数
	MaxRetryCount         = 3
)

// ==================== 配置结构体 ====================

// Config 应用配置结构体
type Config struct {
	// 数据库配置
	Database DatabaseConfig `json:"database"`
	// Redis配置
	Redis RedisConfig `json:"redis"`
	// Worker配置
	Worker WorkerConfig `json:"worker"`
	// 日志配置
	Logging LoggingConfig `json:"logging"`
}

// DatabaseConfig 数据库配置
type DatabaseConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	User     string `json:"user"`
	Password string `json:"password"`
	Database string `json:"database"`
	MaxConns int    `json:"max_connections"`
}

// RedisConfig Redis配置
type RedisConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Password string `json:"password"`
	DB       int    `json:"db"`
}

// WorkerConfig Worker配置
type WorkerConfig struct {
	Concurrency   int `json:"concurrency"`    // 并发数
	PollInterval  int `json:"poll_interval"`  // 轮询间隔(毫秒)
	RetryDelay    int `json:"retry_delay"`    // 重试延迟(秒)
	LockTimeout   int `json:"lock_timeout"`   // 锁超时(秒)
}

// LoggingConfig 日志配置
type LoggingConfig struct {
	Level  string `json:"level"`
	Format string `json:"format"`
	Output string `json:"output"`
}

// ==================== 任务结构体 ====================

// Task 任务结构体
type Task struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Payload     map[string]interface{} `json:"payload"`
	Priority    int                    `json:"priority"`
	Status      string                 `json:"status"`
	RetryCount  int                    `json:"retry_count"`
	MaxRetry    int                    `json:"max_retry"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	ScheduledAt *time.Time             `json:"scheduled_at,omitempty"`
	StartedAt   *time.Time             `json:"started_at,omitempty"`
	CompletedAt *time.Time             `json:"completed_at,omitempty"`
	Error       string                 `json:"error,omitempty"`
}

// TaskResult 任务处理结果
type TaskResult struct {
	TaskID  string      `json:"task_id"`
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

// ==================== 通知结构体 ====================

// Notification 通知结构体
type Notification struct {
	ID        string                 `json:"id"`
	UserID    string                 `json:"user_id"`
	Type      string                 `json:"type"`
	Title     string                 `json:"title"`
	Content   string                 `json:"content"`
	Data      map[string]interface{} `json:"data,omitempty"`
	Read      bool                   `json:"read"`
	CreatedAt time.Time              `json:"created_at"`
}

// EmailPayload 邮件任务载荷
type EmailPayload struct {
	To      string `json:"to"`
	Subject string `json:"subject"`
	Body    string `json:"body"`
	IsHTML  bool   `json:"is_html"`
}

// SMSPayload 短信任务载荷
type SMSPayload struct {
	PhoneNumber string `json:"phone_number"`
	TemplateID  string `json:"template_id"`
	Params      map[string]string `json:"params"`
}

// ReportPayload 报告生成任务载荷
type ReportPayload struct {
	UserID    string    `json:"user_id"`
	ReportType string   `json:"report_type"`
	StartDate time.Time `json:"start_date"`
	EndDate   time.Time `json:"end_date"`
	Format    string    `json:"format"`
}

// ==================== 数据库管理器 ====================

// DatabaseManager 数据库管理器
type DatabaseManager struct {
	db *sql.DB
}

// NewDatabaseManager 创建数据库管理器
func NewDatabaseManager(cfg *DatabaseConfig) (*DatabaseManager, error) {
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%d)/%s?charset=utf8mb4&parseTime=True&loc=Local",
		cfg.User, cfg.Password, cfg.Host, cfg.Port, cfg.Database)

	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return nil, fmt.Errorf("连接数据库失败: %w", err)
	}

	// 设置连接池参数
	db.SetMaxOpenConns(cfg.MaxConns)
	db.SetMaxIdleConns(cfg.MaxConns / 2)
	db.SetConnMaxLifetime(time.Hour)

	// 测试连接
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("数据库连接测试失败: %w", err)
	}

	log.Println("数据库连接成功")
	return &DatabaseManager{db: db}, nil
}

// Close 关闭数据库连接
func (dm *DatabaseManager) Close() error {
	return dm.db.Close()
}

// CreateTask 创建任务记录
func (dm *DatabaseManager) CreateTask(ctx context.Context, task *Task) error {
	query := `
		INSERT INTO background_tasks (id, type, payload, priority, status, retry_count, max_retry, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	payloadJSON, _ := json.Marshal(task.Payload)
	_, err := dm.db.ExecContext(ctx, query,
		task.ID, task.Type, payloadJSON, task.Priority, task.Status,
		task.RetryCount, task.MaxRetry, task.CreatedAt, task.UpdatedAt)
	return err
}

// UpdateTaskStatus 更新任务状态
func (dm *DatabaseManager) UpdateTaskStatus(ctx context.Context, taskID string, status string, errMsg string) error {
	query := `
		UPDATE background_tasks
		SET status = ?, error = ?, updated_at = ?
		WHERE id = ?
	`
	_, err := dm.db.ExecContext(ctx, query, status, errMsg, time.Now(), taskID)
	return err
}

// GetPendingTasks 获取待处理任务
func (dm *DatabaseManager) GetPendingTasks(ctx context.Context, limit int) ([]*Task, error) {
	query := `
		SELECT id, type, payload, priority, status, retry_count, max_retry, created_at, updated_at
		FROM background_tasks
		WHERE status = ? AND (scheduled_at IS NULL OR scheduled_at <= ?)
		ORDER BY priority DESC, created_at ASC
		LIMIT ?
	`
	rows, err := dm.db.QueryContext(ctx, query, TaskStatusPending, time.Now(), limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tasks []*Task
	for rows.Next() {
		task := &Task{}
		var payloadJSON []byte
		if err := rows.Scan(
			&task.ID, &task.Type, &payloadJSON, &task.Priority,
			&task.Status, &task.RetryCount, &task.MaxRetry,
			&task.CreatedAt, &task.UpdatedAt,
		); err != nil {
			return nil, err
		}
		json.Unmarshal(payloadJSON, &task.Payload)
		tasks = append(tasks, task)
	}
	return tasks, nil
}

// CreateNotification 创建通知记录
func (dm *DatabaseManager) CreateNotification(ctx context.Context, notification *Notification) error {
	query := `
		INSERT INTO notifications (id, user_id, type, title, content, data, read, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?)
	`
	dataJSON, _ := json.Marshal(notification.Data)
	_, err := dm.db.ExecContext(ctx, query,
		notification.ID, notification.UserID, notification.Type,
		notification.Title, notification.Content, dataJSON,
		notification.Read, notification.CreatedAt)
	return err
}

// CleanExpiredTasks 清理过期任务
func (dm *DatabaseManager) CleanExpiredTasks(ctx context.Context, before time.Time) (int64, error) {
	query := `DELETE FROM background_tasks WHERE status IN (?, ?) AND updated_at < ?`
	result, err := dm.db.ExecContext(ctx, query, TaskStatusCompleted, TaskStatusFailed, before)
	if err != nil {
		return 0, err
	}
	return result.RowsAffected()
}

// ==================== Redis管理器 ====================

// RedisManager Redis管理器
type RedisManager struct {
	client *redis.Client
}

// NewRedisManager 创建Redis管理器
func NewRedisManager(cfg *RedisConfig) (*RedisManager, error) {
	client := redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%d", cfg.Host, cfg.Port),
		Password: cfg.Password,
		DB:       cfg.DB,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("Redis连接失败: %w", err)
	}

	log.Println("Redis连接成功")
	return &RedisManager{client: client}, nil
}

// Close 关闭Redis连接
func (rm *RedisManager) Close() error {
	return rm.client.Close()
}

// PushTask 将任务推入队列
func (rm *RedisManager) PushTask(ctx context.Context, task *Task) error {
	taskJSON, err := json.Marshal(task)
	if err != nil {
		return err
	}
	return rm.client.LPush(ctx, RedisKeyTaskQueue, taskJSON).Err()
}

// PopTask 从队列弹出任务
func (rm *RedisManager) PopTask(ctx context.Context, timeout time.Duration) (*Task, error) {
	result, err := rm.client.BRPop(ctx, timeout, RedisKeyTaskQueue).Result()
	if err != nil {
		if err == redis.Nil {
			return nil, nil
		}
		return nil, err
	}

	var task Task
	if err := json.Unmarshal([]byte(result[1]), &task); err != nil {
		return nil, err
	}
	return &task, nil
}

// AcquireLock 获取分布式锁
func (rm *RedisManager) AcquireLock(ctx context.Context, key string, timeout time.Duration) (bool, error) {
	lockKey := RedisKeyTaskLock + key
	return rm.client.SetNX(ctx, lockKey, "locked", timeout).Result()
}

// ReleaseLock 释放分布式锁
func (rm *RedisManager) ReleaseLock(ctx context.Context, key string) error {
	lockKey := RedisKeyTaskLock + key
	return rm.client.Del(ctx, lockKey).Err()
}

// PublishNotification 发布通知到频道
func (rm *RedisManager) PublishNotification(ctx context.Context, channel string, notification *Notification) error {
	notificationJSON, err := json.Marshal(notification)
	if err != nil {
		return err
	}
	return rm.client.Publish(ctx, channel, notificationJSON).Err()
}

// ==================== 任务处理器 ====================

// TaskHandler 任务处理接口
type TaskHandler interface {
	Handle(ctx context.Context, task *Task) (*TaskResult, error)
}

// EmailTaskHandler 邮件任务处理器
type EmailTaskHandler struct{}

func NewEmailTaskHandler() *EmailTaskHandler {
	return &EmailTaskHandler{}
}

// Handle 处理邮件发送任务
func (h *EmailTaskHandler) Handle(ctx context.Context, task *Task) (*TaskResult, error) {
	// 解析邮件载荷
	payloadBytes, _ := json.Marshal(task.Payload)
	var payload EmailPayload
	if err := json.Unmarshal(payloadBytes, &payload); err != nil {
		return nil, fmt.Errorf("解析邮件载荷失败: %w", err)
	}

	// 模拟邮件发送
	log.Printf("发送邮件到: %s, 主题: %s", payload.To, payload.Subject)

	// 这里应该调用实际的邮件发送服务
	// 例如: smtp.Send(payload.To, payload.Subject, payload.Body)

	return &TaskResult{
		TaskID:  task.ID,
		Success: true,
		Data:    map[string]string{"message_id": fmt.Sprintf("msg_%d", time.Now().UnixNano())},
	}, nil
}

// SMSTaskHandler 短信任务处理器
type SMSTaskHandler struct{}

func NewSMSTaskHandler() *SMSTaskHandler {
	return &SMSTaskHandler{}
}

// Handle 处理短信发送任务
func (h *SMSTaskHandler) Handle(ctx context.Context, task *Task) (*TaskResult, error) {
	payloadBytes, _ := json.Marshal(task.Payload)
	var payload SMSPayload
	if err := json.Unmarshal(payloadBytes, &payload); err != nil {
		return nil, fmt.Errorf("解析短信载荷失败: %w", err)
	}

	log.Printf("发送短信到: %s, 模板ID: %s", payload.PhoneNumber, payload.TemplateID)

	// 模拟短信发送
	return &TaskResult{
		TaskID:  task.ID,
		Success: true,
		Data:    map[string]string{"message_id": fmt.Sprintf("sms_%d", time.Now().UnixNano())},
	}, nil
}

// ReportTaskHandler 报告生成任务处理器
type ReportTaskHandler struct {
	db *DatabaseManager
}

func NewReportTaskHandler(db *DatabaseManager) *ReportTaskHandler {
	return &ReportTaskHandler{db: db}
}

// Handle 处理报告生成任务
func (h *ReportTaskHandler) Handle(ctx context.Context, task *Task) (*TaskResult, error) {
	payloadBytes, _ := json.Marshal(task.Payload)
	var payload ReportPayload
	if err := json.Unmarshal(payloadBytes, &payload); err != nil {
		return nil, fmt.Errorf("解析报告载荷失败: %w", err)
	}

	log.Printf("生成报告: 用户=%s, 类型=%s, 时间范围=%s~%s",
		payload.UserID, payload.ReportType, payload.StartDate.Format("2006-01-02"), payload.EndDate.Format("2006-01-02"))

	// 模拟报告生成
	reportID := fmt.Sprintf("report_%d", time.Now().UnixNano())

	return &TaskResult{
		TaskID:  task.ID,
		Success: true,
		Data: map[string]interface{}{
			"report_id":   reportID,
			"format":      payload.Format,
			"download_url": fmt.Sprintf("/reports/%s.%s", reportID, payload.Format),
		},
	}, nil
}

// NotificationTaskHandler 通知任务处理器
type NotificationTaskHandler struct {
	db    *DatabaseManager
	redis *RedisManager
}

func NewNotificationTaskHandler(db *DatabaseManager, redis *RedisManager) *NotificationTaskHandler {
	return &NotificationTaskHandler{db: db, redis: redis}
}

// Handle 处理通知任务
func (h *NotificationTaskHandler) Handle(ctx context.Context, task *Task) (*TaskResult, error) {
	notification := &Notification{
		ID:        task.ID,
		UserID:    task.Payload["user_id"].(string),
		Type:      task.Payload["notification_type"].(string),
		Title:     task.Payload["title"].(string),
		Content:   task.Payload["content"].(string),
		Data:      task.Payload["data"].(map[string]interface{}),
		Read:      false,
		CreatedAt: time.Now(),
	}

	// 保存通知到数据库
	if err := h.db.CreateNotification(ctx, notification); err != nil {
		return nil, fmt.Errorf("保存通知失败: %w", err)
	}

	// 发布通知到Redis频道（用于实时推送）
	if err := h.redis.PublishNotification(ctx, "notifications:"+notification.UserID, notification); err != nil {
		log.Printf("发布通知失败: %v", err)
	}

	return &TaskResult{
		TaskID:  task.ID,
		Success: true,
		Data:    notification,
	}, nil
}

// ==================== Worker ====================

// Worker 后台任务工作者
type Worker struct {
	id       string
	db       *DatabaseManager
	redis    *RedisManager
	handlers map[string]TaskHandler
	config   *WorkerConfig
	wg       sync.WaitGroup
	stopCh   chan struct{}
}

// NewWorker 创建Worker实例
func NewWorker(id string, db *DatabaseManager, redis *RedisManager, config *WorkerConfig) *Worker {
	worker := &Worker{
		id:       id,
		db:       db,
		redis:    redis,
		handlers: make(map[string]TaskHandler),
		config:   config,
		stopCh:   make(chan struct{}),
	}

	// 注册任务处理器
	worker.RegisterHandler(TaskTypeSendEmail, NewEmailTaskHandler())
	worker.RegisterHandler(TaskTypeSendSMS, NewSMSTaskHandler())
	worker.RegisterHandler(TaskTypeGenerateReport, NewReportTaskHandler(db))
	worker.RegisterHandler(TaskTypeNotification, NewNotificationTaskHandler(db, redis))

	return worker
}

// RegisterHandler 注册任务处理器
func (w *Worker) RegisterHandler(taskType string, handler TaskHandler) {
	w.handlers[taskType] = handler
}

// Start 启动Worker
func (w *Worker) Start(ctx context.Context) {
	log.Printf("Worker %s 启动，并发数: %d", w.id, w.config.Concurrency)

	for i := 0; i < w.config.Concurrency; i++ {
		w.wg.Add(1)
		go w.runWorker(ctx, i)
	}
}

// Stop 停止Worker
func (w *Worker) Stop() {
	log.Printf("Worker %s 正在停止...", w.id)
	close(w.stopCh)
	w.wg.Wait()
	log.Printf("Worker %s 已停止", w.id)
}

// runWorker 运行单个worker goroutine
func (w *Worker) runWorker(ctx context.Context, workerNum int) {
	defer w.wg.Done()

	workerID := fmt.Sprintf("%s-%d", w.id, workerNum)
	log.Printf("Worker %s 开始运行", workerID)

	for {
		select {
		case <-w.stopCh:
			log.Printf("Worker %s 收到停止信号", workerID)
			return
		case <-ctx.Done():
			log.Printf("Worker %s 上下文取消", workerID)
			return
		default:
			// 从Redis队列获取任务
			task, err := w.redis.PopTask(ctx, time.Duration(w.config.PollInterval)*time.Millisecond)
			if err != nil {
				log.Printf("Worker %s 获取任务失败: %v", workerID, err)
				time.Sleep(time.Second)
				continue
			}

			if task == nil {
				continue
			}

			// 处理任务
			w.processTask(ctx, task)
		}
	}
}

// processTask 处理单个任务
func (w *Worker) processTask(ctx context.Context, task *Task) {
	log.Printf("处理任务: ID=%s, 类型=%s", task.ID, task.Type)

	// 获取任务处理器
	handler, ok := w.handlers[task.Type]
	if !ok {
		log.Printf("未知的任务类型: %s", task.Type)
		w.db.UpdateTaskStatus(ctx, task.ID, TaskStatusFailed, "未知的任务类型")
		return
	}

	// 更新任务状态为处理中
	now := time.Now()
	task.Status = TaskStatusProcessing
	task.StartedAt = &now
	w.db.UpdateTaskStatus(ctx, task.ID, TaskStatusProcessing, "")

	// 执行任务处理
	result, err := handler.Handle(ctx, task)
	if err != nil {
		w.handleTaskError(ctx, task, err)
		return
	}

	// 更新任务状态为完成
	task.Status = TaskStatusCompleted
	completedAt := time.Now()
	task.CompletedAt = &completedAt
	w.db.UpdateTaskStatus(ctx, task.ID, TaskStatusCompleted, "")

	log.Printf("任务完成: ID=%s", task.ID)
}

// handleTaskError 处理任务错误
func (w *Worker) handleTaskError(ctx context.Context, task *Task, err error) {
	log.Printf("任务失败: ID=%s, 错误: %v", task.ID, err)

	task.RetryCount++
	if task.RetryCount >= task.MaxRetry {
		// 超过最大重试次数，标记为失败
		w.db.UpdateTaskStatus(ctx, task.ID, TaskStatusFailed, err.Error())
		log.Printf("任务最终失败: ID=%s, 重试次数: %d", task.ID, task.RetryCount)
		return
	}

	// 重新加入队列等待重试
	task.Status = TaskStatusPending
	task.Error = err.Error()
	time.Sleep(time.Duration(w.config.RetryDelay) * time.Second)
	w.redis.PushTask(ctx, task)
	log.Printf("任务重新入队: ID=%s, 重试次数: %d/%d", task.ID, task.RetryCount, task.MaxRetry)
}

// ==================== 定时任务调度器 ====================

// Scheduler 定时任务调度器
type Scheduler struct {
	cron   *cron.Cron
	db     *DatabaseManager
	redis  *RedisManager
}

// NewScheduler 创建调度器
func NewScheduler(db *DatabaseManager, redis *RedisManager) *Scheduler {
	return &Scheduler{
		cron:  cron.New(cron.WithSeconds()),
		db:    db,
		redis: redis,
	}
}

// Start 启动调度器
func (s *Scheduler) Start() {
	log.Println("定时任务调度器启动")

	// 注册定时任务
	s.registerJobs()

	s.cron.Start()
}

// Stop 停止调度器
func (s *Scheduler) Stop() {
	log.Println("定时任务调度器停止")
	s.cron.Stop()
}

// registerJobs 注册定时任务
func (s *Scheduler) registerJobs() {
	// 每天凌晨2点清理过期任务
	s.cron.AddFunc("0 0 2 * * *", s.cleanExpiredTasks)

	// 每5分钟同步任务状态
	s.cron.AddFunc("0 */5 * * * *", s.syncTaskStatus)

	// 每小时发送任务统计报告
	s.cron.AddFunc("0 0 * * * *", s.sendHourlyReport)

	// 每10秒检查待处理任务
	s.cron.AddFunc("*/10 * * * * *", s.checkPendingTasks)
}

// cleanExpiredTasks 清理过期任务
func (s *Scheduler) cleanExpiredTasks() {
	ctx := context.Background()
	before := time.Now().AddDate(0, 0, -30) // 保留30天

	count, err := s.db.CleanExpiredTasks(ctx, before)
	if err != nil {
		log.Printf("清理过期任务失败: %v", err)
		return
	}

	log.Printf("清理了 %d 个过期任务", count)
}

// syncTaskStatus 同步任务状态
func (s *Scheduler) syncTaskStatus() {
	log.Println("同步任务状态...")
	// 这里可以添加状态同步逻辑
}

// sendHourlyReport 发送小时报告
func (s *Scheduler) sendHourlyReport() {
	log.Println("发送小时任务统计报告...")
	// 这里可以添加报告生成和发送逻辑
}

// checkPendingTasks 检查待处理任务
func (s *Scheduler) checkPendingTasks() {
	ctx := context.Background()

	// 从数据库获取待处理任务
	tasks, err := s.db.GetPendingTasks(ctx, 100)
	if err != nil {
		log.Printf("获取待处理任务失败: %v", err)
		return
	}

	// 将任务推入Redis队列
	for _, task := range tasks {
		if err := s.redis.PushTask(ctx, task); err != nil {
			log.Printf("推送任务失败: %v", err)
		}
	}

	if len(tasks) > 0 {
		log.Printf("处理了 %d 个待处理任务", len(tasks))
	}
}

// ==================== 服务主程序 ====================

// Service 后台服务
type Service struct {
	config     *Config
	db         *DatabaseManager
	redis      *RedisManager
	worker     *Worker
	scheduler  *Scheduler
}

// NewService 创建服务实例
func NewService(configPath string) (*Service, error) {
	// 加载配置
	config, err := loadConfig(configPath)
	if err != nil {
		return nil, fmt.Errorf("加载配置失败: %w", err)
	}

	// 初始化数据库
	db, err := NewDatabaseManager(&config.Database)
	if err != nil {
		return nil, fmt.Errorf("初始化数据库失败: %w", err)
	}

	// 初始化Redis
	redis, err := NewRedisManager(&config.Redis)
	if err != nil {
		return nil, fmt.Errorf("初始化Redis失败: %w", err)
	}

	// 创建Worker
	worker := NewWorker("worker-1", db, redis, &config.Worker)

	// 创建调度器
	scheduler := NewScheduler(db, redis)

	return &Service{
		config:    config,
		db:        db,
		redis:     redis,
		worker:    worker,
		scheduler: scheduler,
	}, nil
}

// Start 启动服务
func (s *Service) Start(ctx context.Context) {
	log.Println("后台任务服务启动...")

	// 启动Worker
	s.worker.Start(ctx)

	// 启动调度器
	s.scheduler.Start()

	log.Println("后台任务服务已启动")
}

// Stop 停止服务
func (s *Service) Stop() {
	log.Println("后台任务服务停止中...")

	s.scheduler.Stop()
	s.worker.Stop()
	s.db.Close()
	s.redis.Close()

	log.Println("后台任务服务已停止")
}

// loadConfig 加载配置文件
func loadConfig(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		// 使用默认配置
		return &Config{
			Database: DatabaseConfig{
				Host:     getEnv("DB_HOST", "localhost"),
				Port:     3306,
				User:     getEnv("DB_USER", "root"),
				Password: getEnv("DB_PASSWORD", "password"),
				Database: getEnv("DB_NAME", "task_management"),
				MaxConns: 10,
			},
			Redis: RedisConfig{
				Host:     getEnv("REDIS_HOST", "localhost"),
				Port:     6379,
				Password: getEnv("REDIS_PASSWORD", ""),
				DB:       0,
			},
			Worker: WorkerConfig{
				Concurrency:  5,
				PollInterval: 1000,
				RetryDelay:   60,
				LockTimeout:  300,
			},
			Logging: LoggingConfig{
				Level:  "info",
				Format: "text",
				Output: "stdout",
			},
		}, nil
	}

	var config Config
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, err
	}

	return &config, nil
}

// getEnv 获取环境变量
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// ==================== 主函数 ====================

func main() {
	// 初始化日志
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.Println("智能任务管理系统 - 后台任务处理服务")

	// 创建服务
	service, err := NewService("config.json")
	if err != nil {
		log.Fatalf("创建服务失败: %v", err)
	}

	// 创建上下文
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// 启动服务
	service.Start(ctx)

	// 等待中断信号
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	// 停止服务
	service.Stop()
	log.Println("服务退出")
}