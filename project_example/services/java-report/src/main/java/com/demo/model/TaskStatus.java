package com.demo.model;

/**
 * 任务状态枚举
 * 定义任务在生命周期中可能的状态
 *
 * @author TaskManager Team
 * @version 1.0.0
 */
public enum TaskStatus {

    /** 待处理状态 */
    PENDING("pending", "待处理"),

    /** 进行中状态 */
    IN_PROGRESS("in_progress", "进行中"),

    /** 已完成状态 */
    COMPLETED("completed", "已完成"),

    /** 已取消状态 */
    CANCELLED("cancelled", "已取消"),

    /** 已归档状态 */
    ARCHIVED("archived", "已归档");

    /** 状态代码 */
    private final String code;

    /** 状态显示名称 */
    private final String displayName;

    /**
     * 构造函数
     *
     * @param code        状态代码
     * @param displayName 状态显示名称
     */
    TaskStatus(String code, String displayName) {
        this.code = code;
        this.displayName = displayName;
    }

    /**
     * 获取状态代码
     *
     * @return 状态代码
     */
    public String getCode() {
        return code;
    }

    /**
     * 获取状态显示名称
     *
     * @return 状态显示名称
     */
    public String getDisplayName() {
        return displayName;
    }

    /**
     * 根据代码获取状态枚举
     *
     * @param code 状态代码
     * @return 对应的状态枚举，如果不存在则返回null
     */
    public static TaskStatus fromCode(String code) {
        if (code == null) {
            return null;
        }
        for (TaskStatus status : values()) {
            if (status.code.equalsIgnoreCase(code)) {
                return status;
            }
        }
        return null;
    }

    /**
     * 检查是否为终态
     * 终态的任务不能再转换为其他状态
     *
     * @return 如果是终态返回true，否则返回false
     */
    public boolean isFinalState() {
        return this == CANCELLED || this == ARCHIVED;
    }

    /**
     * 检查是否可以转换到目标状态
     *
     * @param target 目标状态
     * @return 如果可以转换返回true，否则返回false
     */
    public boolean canTransitionTo(TaskStatus target) {
        if (this.isFinalState()) {
            return false;
        }

        // 定义状态转换规则
        switch (this) {
            case PENDING:
                return target == IN_PROGRESS || target == CANCELLED;
            case IN_PROGRESS:
                return target == COMPLETED || target == CANCELLED || target == PENDING;
            case COMPLETED:
                return target == ARCHIVED;
            default:
                return false;
        }
    }
}