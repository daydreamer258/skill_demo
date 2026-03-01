package com.demo.repository;

import com.demo.model.Task;
import com.demo.model.TaskPriority;
import com.demo.model.TaskStatus;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * 任务数据访问层
 * 提供任务的CRUD操作和查询功能
 *
 * @author TaskManager Team
 * @version 1.0.0
 */
@Repository
public class TaskRepository {

    /** 内存数据存储（实际应用中应使用数据库） */
    private final Map<String, Task> taskStore = new ConcurrentHashMap<>();

    /**
     * 保存任务
     *
     * @param task 任务对象
     * @return 保存后的任务
     */
    public Task save(Task task) {
        if (task == null) {
            throw new IllegalArgumentException("任务不能为空");
        }
        if (task.getId() == null || task.getId().isEmpty()) {
            task.setId(UUID.randomUUID().toString());
        }
        task.setUpdatedAt(LocalDateTime.now());
        taskStore.put(task.getId(), task);
        return task;
    }

    /**
     * 根据ID查找任务
     *
     * @param id 任务ID
     * @return 任务对象，不存在则返回Optional.empty()
     */
    public Optional<Task> findById(String id) {
        if (id == null) {
            return Optional.empty();
        }
        return Optional.ofNullable(taskStore.get(id));
    }

    /**
     * 查找所有任务
     *
     * @return 任务列表
     */
    public List<Task> findAll() {
        return new ArrayList<>(taskStore.values());
    }

    /**
     * 根据创建者ID查找任务
     *
     * @param creatorId 创建者ID
     * @return 任务列表
     */
    public List<Task> findByCreatorId(String creatorId) {
        return taskStore.values().stream()
                .filter(task -> creatorId.equals(task.getCreatorId()))
                .collect(Collectors.toList());
    }

    /**
     * 根据指派人ID查找任务
     *
     * @param assigneeId 指派人ID
     * @return 任务列表
     */
    public List<Task> findByAssigneeId(String assigneeId) {
        return taskStore.values().stream()
                .filter(task -> task.getAssigneeIds().contains(assigneeId))
                .collect(Collectors.toList());
    }

    /**
     * 根据状态查找任务
     *
     * @param status 任务状态
     * @return 任务列表
     */
    public List<Task> findByStatus(TaskStatus status) {
        return taskStore.values().stream()
                .filter(task -> status.equals(task.getStatus()))
                .collect(Collectors.toList());
    }

    /**
     * 根据优先级查找任务
     *
     * @param priority 任务优先级
     * @return 任务列表
     */
    public List<Task> findByPriority(TaskPriority priority) {
        return taskStore.values().stream()
                .filter(task -> priority.equals(task.getPriority()))
                .collect(Collectors.toList());
    }

    /**
     * 查找逾期任务
     *
     * @return 逾期任务列表
     */
    public List<Task> findOverdueTasks() {
        LocalDateTime now = LocalDateTime.now();
        return taskStore.values().stream()
                .filter(task -> task.getDueDate() != null)
                .filter(task -> task.getDueDate().isBefore(now))
                .filter(task -> !TaskStatus.COMPLETED.equals(task.getStatus()))
                .filter(task -> !TaskStatus.CANCELLED.equals(task.getStatus()))
                .collect(Collectors.toList());
    }

    /**
     * 根据标签查找任务
     *
     * @param tag 标签名称
     * @return 任务列表
     */
    public List<Task> findByTag(String tag) {
        return taskStore.values().stream()
                .filter(task -> task.getTags().contains(tag))
                .collect(Collectors.toList());
    }

    /**
     * 根据时间范围查找任务
     *
     * @param start 开始时间
     * @param end   结束时间
     * @return 任务列表
     */
    public List<Task> findByCreatedAtBetween(LocalDateTime start, LocalDateTime end) {
        return taskStore.values().stream()
                .filter(task -> task.getCreatedAt() != null)
                .filter(task -> !task.getCreatedAt().isBefore(start))
                .filter(task -> !task.getCreatedAt().isAfter(end))
                .collect(Collectors.toList());
    }

    /**
     * 删除任务
     *
     * @param id 任务ID
     * @return 是否删除成功
     */
    public boolean deleteById(String id) {
        return taskStore.remove(id) != null;
    }

    /**
     * 统计任务总数
     *
     * @return 任务总数
     */
    public long count() {
        return taskStore.size();
    }

    /**
     * 按状态统计任务数量
     *
     * @return 状态统计Map
     */
    public Map<TaskStatus, Long> countByStatus() {
        return taskStore.values().stream()
                .collect(Collectors.groupingBy(Task::getStatus, Collectors.counting()));
    }

    /**
     * 按优先级统计任务数量
     *
     * @return 优先级统计Map
     */
    public Map<TaskPriority, Long> countByPriority() {
        return taskStore.values().stream()
                .collect(Collectors.groupingBy(Task::getPriority, Collectors.counting()));
    }

    /**
     * 按创建者统计任务数量
     *
     * @return 创建者统计Map
     */
    public Map<String, Long> countByCreator() {
        return taskStore.values().stream()
                .collect(Collectors.groupingBy(Task::getCreatorId, Collectors.counting()));
    }

    /**
     * 查找子任务
     *
     * @param parentId 父任务ID
     * @return 子任务列表
     */
    public List<Task> findSubtasks(String parentId) {
        return taskStore.values().stream()
                .filter(task -> parentId.equals(task.getParentTaskId()))
                .collect(Collectors.toList());
    }

    /**
     * 批量保存任务
     *
     * @param tasks 任务列表
     * @return 保存后的任务列表
     */
    public List<Task> saveAll(List<Task> tasks) {
        List<Task> savedTasks = new ArrayList<>();
        for (Task task : tasks) {
            savedTasks.add(save(task));
        }
        return savedTasks;
    }

    /**
     * 检查任务是否存在
     *
     * @param id 任务ID
     * @return 是否存在
     */
    public boolean existsById(String id) {
        return taskStore.containsKey(id);
    }

    /**
     * 清空所有任务（用于测试）
     */
    public void deleteAll() {
        taskStore.clear();
    }
}