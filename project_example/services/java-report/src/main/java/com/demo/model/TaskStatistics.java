package com.demo.model;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 任务统计报表实体类
 * 用于存储任务统计数据
 *
 * @author TaskManager Team
 * @version 1.0.0
 */
public class TaskStatistics {

    /** 报表ID */
    private String reportId;

    /** 用户ID */
    private String userId;

    /** 报表类型 */
    private String reportType;

    /** 报表周期开始时间 */
    private LocalDateTime periodStart;

    /** 报表周期结束时间 */
    private LocalDateTime periodEnd;

    /** 总任务数 */
    private Integer totalTasks;

    /** 已完成任务数 */
    private Integer completedTasks;

    /** 进行中任务数 */
    private Integer inProgressTasks;

    /** 待处理任务数 */
    private Integer pendingTasks;

    /** 已取消任务数 */
    private Integer cancelledTasks;

    /** 逾期任务数 */
    private Integer overdueTasks;

    /** 平均完成时间（小时） */
    private Double averageCompletionTime;

    /** 按状态统计 */
    private Map<String, Integer> tasksByStatus;

    /** 按优先级统计 */
    private Map<String, Integer> tasksByPriority;

    /** 按标签统计 */
    private Map<String, Integer> tasksByTag;

    /** 按指派人统计 */
    private Map<String, Integer> tasksByAssignee;

    /** 平均进度 */
    private Double averageProgress;

    /** 完成率 */
    private Double completionRate;

    /** 报表生成时间 */
    private LocalDateTime generatedAt;

    /**
     * 默认构造函数
     */
    public TaskStatistics() {
        this.tasksByStatus = new HashMap<>();
        this.tasksByPriority = new HashMap<>();
        this.tasksByTag = new HashMap<>();
        this.tasksByAssignee = new HashMap<>();
        this.generatedAt = LocalDateTime.now();
    }

    // ==================== 计算方法 ====================

    /**
     * 计算完成率
     *
     * @return 完成率百分比
     */
    public double calculateCompletionRate() {
        if (totalTasks == null || totalTasks == 0) {
            return 0.0;
        }
        return (completedTasks != null ? completedTasks : 0) * 100.0 / totalTasks;
    }

    /**
     * 计算平均进度
     *
     * @return 平均进度百分比
     */
    public double calculateAverageProgress() {
        if (totalTasks == null || totalTasks == 0) {
            return 0.0;
        }
        // 简化计算，实际应从具体任务数据计算
        return averageProgress != null ? averageProgress : 0.0;
    }

    /**
     * 获取活跃任务数（待处理+进行中）
     *
     * @return 活跃任务数
     */
    public int getActiveTasksCount() {
        int pending = pendingTasks != null ? pendingTasks : 0;
        int inProgress = inProgressTasks != null ? inProgressTasks : 0;
        return pending + inProgress;
    }

    /**
     * 获取高优先级任务数
     *
     * @return 高优先级和紧急任务总数
     */
    public int getHighPriorityTasksCount() {
        int high = tasksByPriority.getOrDefault("high", 0);
        int urgent = tasksByPriority.getOrDefault("urgent", 0);
        return high + urgent;
    }

    // ==================== Getter 和 Setter 方法 ====================

    public String getReportId() {
        return reportId;
    }

    public void setReportId(String reportId) {
        this.reportId = reportId;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getReportType() {
        return reportType;
    }

    public void setReportType(String reportType) {
        this.reportType = reportType;
    }

    public LocalDateTime getPeriodStart() {
        return periodStart;
    }

    public void setPeriodStart(LocalDateTime periodStart) {
        this.periodStart = periodStart;
    }

    public LocalDateTime getPeriodEnd() {
        return periodEnd;
    }

    public void setPeriodEnd(LocalDateTime periodEnd) {
        this.periodEnd = periodEnd;
    }

    public Integer getTotalTasks() {
        return totalTasks;
    }

    public void setTotalTasks(Integer totalTasks) {
        this.totalTasks = totalTasks;
    }

    public Integer getCompletedTasks() {
        return completedTasks;
    }

    public void setCompletedTasks(Integer completedTasks) {
        this.completedTasks = completedTasks;
    }

    public Integer getInProgressTasks() {
        return inProgressTasks;
    }

    public void setInProgressTasks(Integer inProgressTasks) {
        this.inProgressTasks = inProgressTasks;
    }

    public Integer getPendingTasks() {
        return pendingTasks;
    }

    public void setPendingTasks(Integer pendingTasks) {
        this.pendingTasks = pendingTasks;
    }

    public Integer getCancelledTasks() {
        return cancelledTasks;
    }

    public void setCancelledTasks(Integer cancelledTasks) {
        this.cancelledTasks = cancelledTasks;
    }

    public Integer getOverdueTasks() {
        return overdueTasks;
    }

    public void setOverdueTasks(Integer overdueTasks) {
        this.overdueTasks = overdueTasks;
    }

    public Double getAverageCompletionTime() {
        return averageCompletionTime;
    }

    public void setAverageCompletionTime(Double averageCompletionTime) {
        this.averageCompletionTime = averageCompletionTime;
    }

    public Map<String, Integer> getTasksByStatus() {
        return tasksByStatus;
    }

    public void setTasksByStatus(Map<String, Integer> tasksByStatus) {
        this.tasksByStatus = tasksByStatus != null ? tasksByStatus : new HashMap<>();
    }

    public Map<String, Integer> getTasksByPriority() {
        return tasksByPriority;
    }

    public void setTasksByPriority(Map<String, Integer> tasksByPriority) {
        this.tasksByPriority = tasksByPriority != null ? tasksByPriority : new HashMap<>();
    }

    public Map<String, Integer> getTasksByTag() {
        return tasksByTag;
    }

    public void setTasksByTag(Map<String, Integer> tasksByTag) {
        this.tasksByTag = tasksByTag != null ? tasksByTag : new HashMap<>();
    }

    public Map<String, Integer> getTasksByAssignee() {
        return tasksByAssignee;
    }

    public void setTasksByAssignee(Map<String, Integer> tasksByAssignee) {
        this.tasksByAssignee = tasksByAssignee != null ? tasksByAssignee : new HashMap<>();
    }

    public Double getAverageProgress() {
        return averageProgress;
    }

    public void setAverageProgress(Double averageProgress) {
        this.averageProgress = averageProgress;
    }

    public Double getCompletionRate() {
        return completionRate;
    }

    public void setCompletionRate(Double completionRate) {
        this.completionRate = completionRate;
    }

    public LocalDateTime getGeneratedAt() {
        return generatedAt;
    }

    public void setGeneratedAt(LocalDateTime generatedAt) {
        this.generatedAt = generatedAt;
    }

    @Override
    public String toString() {
        return "TaskStatistics{" +
                "reportId='" + reportId + '\'' +
                ", userId='" + userId + '\'' +
                ", reportType='" + reportType + '\'' +
                ", totalTasks=" + totalTasks +
                ", completedTasks=" + completedTasks +
                ", completionRate=" + completionRate +
                '}';
    }
}