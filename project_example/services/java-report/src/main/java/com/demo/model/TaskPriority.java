package com.demo.model;

/**
 * 任务优先级枚举
 * 定义任务的优先级级别
 *
 * @author TaskManager Team
 * @version 1.0.0
 */
public enum TaskPriority {

    /** 低优先级 */
    LOW("low", "低", 1),

    /** 中优先级 */
    MEDIUM("medium", "中", 2),

    /** 高优先级 */
    HIGH("high", "高", 3),

    /** 紧急 */
    URGENT("urgent", "紧急", 4);

    /** 优先级代码 */
    private final String code;

    /** 优先级显示名称 */
    private final String displayName;

    /** 优先级数值（用于排序和比较） */
    private final int level;

    /**
     * 构造函数
     *
     * @param code        优先级代码
     * @param displayName 优先级显示名称
     * @param level       优先级数值
     */
    TaskPriority(String code, String displayName, int level) {
        this.code = code;
        this.displayName = displayName;
        this.level = level;
    }

    public String getCode() {
        return code;
    }

    public String getDisplayName() {
        return displayName;
    }

    public int getLevel() {
        return level;
    }

    /**
     * 根据代码获取优先级枚举
     *
     * @param code 优先级代码
     * @return 对应的优先级枚举
     */
    public static TaskPriority fromCode(String code) {
        if (code == null) {
            return MEDIUM; // 默认返回中优先级
        }
        for (TaskPriority priority : values()) {
            if (priority.code.equalsIgnoreCase(code)) {
                return priority;
            }
        }
        return MEDIUM;
    }

    /**
     * 检查当前优先级是否高于目标优先级
     *
     * @param other 目标优先级
     * @return 如果当前优先级更高返回true
     */
    public boolean isHigherThan(TaskPriority other) {
        return this.level > other.level;
    }

    /**
     * 检查当前优先级是否低于目标优先级
     *
     * @param other 目标优先级
     * @return 如果当前优先级更低返回true
     */
    public boolean isLowerThan(TaskPriority other) {
        return this.level < other.level;
    }
}