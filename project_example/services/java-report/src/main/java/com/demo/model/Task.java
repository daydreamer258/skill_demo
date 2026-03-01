package com.demo.model;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 任务实体类
 * 用于表示任务管理系统中的任务对象
 *
 * @author TaskManager Team
 * @version 1.0.0
 */
public class Task {

    /** 任务唯一标识符 */
    private String id;

    /** 任务标题 */
    private String title;

    /** 任务描述 */
    private String description;

    /** 任务状态 */
    private TaskStatus status;

    /** 任务优先级 */
    private TaskPriority priority;

    /** 截止日期 */
    private LocalDateTime dueDate;

    /** 任务标签列表 */
    private List<String> tags;

    /** 指派人ID列表 */
    private List<String> assigneeIds;

    /** 父任务ID */
    private String parentTaskId;

    /** 创建者ID */
    private String creatorId;

    /** 创建时间 */
    private LocalDateTime createdAt;

    /** 更新时间 */
    private LocalDateTime updatedAt;

    /** 完成时间 */
    private LocalDateTime completedAt;

    /** 任务进度 (0-100) */
    private Integer progress;

    /** 子任务数量 */
    private Integer subtaskCount;

    /** 评论数量 */
    private Integer commentCount;

    /**
     * 默认构造函数
     */
    public Task() {
        this.tags = new ArrayList<>();
        this.assigneeIds = new ArrayList<>();
        this.progress = 0;
        this.subtaskCount = 0;
        this.commentCount = 0;
    }

    /**
     * 带参数的构造函数
     *
     * @param id          任务ID
     * @param title       任务标题
     * @param creatorId   创建者ID
     */
    public Task(String id, String title, String creatorId) {
        this();
        this.id = id;
        this.title = title;
        this.creatorId = creatorId;
        this.status = TaskStatus.PENDING;
        this.priority = TaskPriority.MEDIUM;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    // ==================== Getter 和 Setter 方法 ====================

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public TaskStatus getStatus() {
        return status;
    }

    public void setStatus(TaskStatus status) {
        this.status = status;
    }

    public TaskPriority getPriority() {
        return priority;
    }

    public void setPriority(TaskPriority priority) {
        this.priority = priority;
    }

    public LocalDateTime getDueDate() {
        return dueDate;
    }

    public void setDueDate(LocalDateTime dueDate) {
        this.dueDate = dueDate;
    }

    public List<String> getTags() {
        return tags;
    }

    public void setTags(List<String> tags) {
        this.tags = tags != null ? tags : new ArrayList<>();
    }

    public List<String> getAssigneeIds() {
        return assigneeIds;
    }

    public void setAssigneeIds(List<String> assigneeIds) {
        this.assigneeIds = assigneeIds != null ? assigneeIds : new ArrayList<>();
    }

    public String getParentTaskId() {
        return parentTaskId;
    }

    public void setParentTaskId(String parentTaskId) {
        this.parentTaskId = parentTaskId;
    }

    public String getCreatorId() {
        return creatorId;
    }

    public void setCreatorId(String creatorId) {
        this.creatorId = creatorId;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    public LocalDateTime getCompletedAt() {
        return completedAt;
    }

    public void setCompletedAt(LocalDateTime completedAt) {
        this.completedAt = completedAt;
    }

    public Integer getProgress() {
        return progress;
    }

    public void setProgress(Integer progress) {
        this.progress = Math.max(0, Math.min(100, progress));
    }

    public Integer getSubtaskCount() {
        return subtaskCount;
    }

    public void setSubtaskCount(Integer subtaskCount) {
        this.subtaskCount = subtaskCount;
    }

    public Integer getCommentCount() {
        return commentCount;
    }

    public void setCommentCount(Integer commentCount) {
        this.commentCount = commentCount;
    }

    // ==================== 业务方法 ====================

    /**
     * 检查任务是否已完成
     *
     * @return 如果任务已完成返回true，否则返回false
     */
    public boolean isCompleted() {
        return TaskStatus.COMPLETED.equals(this.status);
    }

    /**
     * 检查任务是否逾期
     *
     * @return 如果任务逾期返回true，否则返回false
     */
    public boolean isOverdue() {
        if (this.dueDate == null) {
            return false;
        }
        return LocalDateTime.now().isAfter(this.dueDate) && !isCompleted();
    }

    /**
     * 检查任务是否正在进行中
     *
     * @return 如果任务正在进行中返回true，否则返回false
     */
    public boolean isInProgress() {
        return TaskStatus.IN_PROGRESS.equals(this.status);
    }

    /**
     * 标记任务为进行中
     */
    public void markAsInProgress() {
        this.status = TaskStatus.IN_PROGRESS;
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 标记任务为已完成
     */
    public void markAsCompleted() {
        this.status = TaskStatus.COMPLETED;
        this.progress = 100;
        this.completedAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 取消任务
     */
    public void cancel() {
        this.status = TaskStatus.CANCELLED;
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 添加标签
     *
     * @param tag 标签名称
     */
    public void addTag(String tag) {
        if (tag != null && !tag.trim().isEmpty() && !this.tags.contains(tag)) {
            this.tags.add(tag);
            this.updatedAt = LocalDateTime.now();
        }
    }

    /**
     * 移除标签
     *
     * @param tag 标签名称
     */
    public void removeTag(String tag) {
        if (this.tags.remove(tag)) {
            this.updatedAt = LocalDateTime.now();
        }
    }

    /**
     * 添加指派人
     *
     * @param assigneeId 用户ID
     */
    public void addAssignee(String assigneeId) {
        if (assigneeId != null && !this.assigneeIds.contains(assigneeId)) {
            this.assigneeIds.add(assigneeId);
            this.updatedAt = LocalDateTime.now();
        }
    }

    /**
     * 移除指派人
     *
     * @param assigneeId 用户ID
     */
    public void removeAssignee(String assigneeId) {
        if (this.assigneeIds.remove(assigneeId)) {
            this.updatedAt = LocalDateTime.now();
        }
    }

    /**
     * 增加进度
     *
     * @param increment 增加的进度值
     */
    public void incrementProgress(int increment) {
        this.progress = Math.min(100, this.progress + increment);
        this.updatedAt = LocalDateTime.now();
    }

    @Override
    public String toString() {
        return "Task{" +
                "id='" + id + '\'' +
                ", title='" + title + '\'' +
                ", status=" + status +
                ", priority=" + priority +
                ", progress=" + progress +
                '}';
    }
}