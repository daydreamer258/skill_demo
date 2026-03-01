package com.demo.service;

import com.demo.model.Task;
import com.demo.model.TaskPriority;
import com.demo.model.TaskStatus;
import com.demo.model.TaskStatistics;
import com.demo.repository.TaskRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 任务服务层
 * 提供任务管理的核心业务逻辑
 *
 * @author TaskManager Team
 * @version 1.0.0
 */
@Service
@Transactional
public class TaskService {

    private final TaskRepository taskRepository;

    @Autowired
    public TaskService(TaskRepository taskRepository) {
        this.taskRepository = taskRepository;
    }

    // ==================== 基础CRUD操作 ====================

    /**
     * 创建新任务
     *
     * @param task 任务对象
     * @return 创建后的任务
     */
    public Task createTask(Task task) {
        validateTask(task);
        task.setStatus(TaskStatus.PENDING);
        task.setProgress(0);
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        return taskRepository.save(task);
    }

    /**
     * 更新任务
     *
     * @param id   任务ID
     * @param task 更新的任务数据
     * @return 更新后的任务
     */
    public Task updateTask(String id, Task task) {
        Task existingTask = taskRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("任务不存在: " + id));

        // 更新字段
        if (task.getTitle() != null) {
            existingTask.setTitle(task.getTitle());
        }
        if (task.getDescription() != null) {
            existingTask.setDescription(task.getDescription());
        }
        if (task.getPriority() != null) {
            existingTask.setPriority(task.getPriority());
        }
        if (task.getDueDate() != null) {
            existingTask.setDueDate(task.getDueDate());
        }
        if (task.getTags() != null) {
            existingTask.setTags(task.getTags());
        }
        if (task.getAssigneeIds() != null) {
            existingTask.setAssigneeIds(task.getAssigneeIds());
        }

        existingTask.setUpdatedAt(LocalDateTime.now());
        return taskRepository.save(existingTask);
    }

    /**
     * 获取任务详情
     *
     * @param id 任务ID
     * @return 任务对象
     */
    @Transactional(readOnly = true)
    public Optional<Task> getTaskById(String id) {
        return taskRepository.findById(id);
    }

    /**
     * 获取所有任务
     *
     * @return 任务列表
     */
    @Transactional(readOnly = true)
    public List<Task> getAllTasks() {
        return taskRepository.findAll();
    }

    /**
     * 删除任务
     *
     * @param id 任务ID
     */
    public void deleteTask(String id) {
        Task task = taskRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("任务不存在: " + id));

        // 软删除：归档任务
        task.setStatus(TaskStatus.ARCHIVED);
        task.setUpdatedAt(LocalDateTime.now());
        taskRepository.save(task);
    }

    // ==================== 状态管理 ====================

    /**
     * 更新任务状态
     *
     * @param id     任务ID
     * @param status 新状态
     * @return 更新后的任务
     */
    public Task updateStatus(String id, TaskStatus status) {
        Task task = taskRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("任务不存在: " + id));

        if (!task.getStatus().canTransitionTo(status)) {
            throw new RuntimeException(
                    String.format("无法从 %s 状态转换到 %s 状态", task.getStatus(), status));
        }

        task.setStatus(status);
        task.setUpdatedAt(LocalDateTime.now());

        if (TaskStatus.COMPLETED.equals(status)) {
            task.setCompletedAt(LocalDateTime.now());
            task.setProgress(100);
        }

        return taskRepository.save(task);
    }

    /**
     * 开始任务
     *
     * @param id 任务ID
     * @return 更新后的任务
     */
    public Task startTask(String id) {
        return updateStatus(id, TaskStatus.IN_PROGRESS);
    }

    /**
     * 完成任务
     *
     * @param id 任务ID
     * @return 更新后的任务
     */
    public Task completeTask(String id) {
        return updateStatus(id, TaskStatus.COMPLETED);
    }

    /**
     * 取消任务
     *
     * @param id 任务ID
     * @return 更新后的任务
     */
    public Task cancelTask(String id) {
        return updateStatus(id, TaskStatus.CANCELLED);
    }

    // ==================== 进度管理 ====================

    /**
     * 更新任务进度
     *
     * @param id       任务ID
     * @param progress 进度值（0-100）
     * @return 更新后的任务
     */
    public Task updateProgress(String id, int progress) {
        Task task = taskRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("任务不存在: " + id));

        task.setProgress(Math.max(0, Math.min(100, progress)));
        task.setUpdatedAt(LocalDateTime.now());

        // 自动更新状态
        if (progress == 100 && TaskStatus.IN_PROGRESS.equals(task.getStatus())) {
            task.setStatus(TaskStatus.COMPLETED);
            task.setCompletedAt(LocalDateTime.now());
        } else if (progress > 0 && TaskStatus.PENDING.equals(task.getStatus())) {
            task.setStatus(TaskStatus.IN_PROGRESS);
        }

        return taskRepository.save(task);
    }

    // ==================== 查询操作 ====================

    /**
     * 根据用户ID获取任务
     *
     * @param userId 用户ID
     * @return 任务列表
     */
    @Transactional(readOnly = true)
    public List<Task> getTasksByUser(String userId) {
        List<Task> createdTasks = taskRepository.findByCreatorId(userId);
        List<Task> assignedTasks = taskRepository.findByAssigneeId(userId);

        // 合并并去重
        Set<String> taskIds = new HashSet<>();
        List<Task> result = new ArrayList<>();

        for (Task task : createdTasks) {
            if (taskIds.add(task.getId())) {
                result.add(task);
            }
        }
        for (Task task : assignedTasks) {
            if (taskIds.add(task.getId())) {
                result.add(task);
            }
        }

        return result;
    }

    /**
     * 获取逾期任务
     *
     * @return 逾期任务列表
     */
    @Transactional(readOnly = true)
    public List<Task> getOverdueTasks() {
        return taskRepository.findOverdueTasks();
    }

    /**
     * 根据条件筛选任务
     *
     * @param status   状态（可选）
     * @param priority 优先级（可选）
     * @param userId   用户ID（可选）
     * @return 筛选后的任务列表
     */
    @Transactional(readOnly = true)
    public List<Task> filterTasks(TaskStatus status, TaskPriority priority, String userId) {
        List<Task> tasks = userId != null ? getTasksByUser(userId) : taskRepository.findAll();

        return tasks.stream()
                .filter(task -> status == null || status.equals(task.getStatus()))
                .filter(task -> priority == null || priority.equals(task.getPriority()))
                .collect(Collectors.toList());
    }

    // ==================== 统计操作 ====================

    /**
     * 获取任务统计概览
     *
     * @param userId 用户ID（可选）
     * @return 统计数据
     */
    @Transactional(readOnly = true)
    public Map<String, Object> getTaskOverview(String userId) {
        List<Task> tasks = userId != null ? getTasksByUser(userId) : taskRepository.findAll();

        Map<String, Object> overview = new HashMap<>();

        // 基础统计
        overview.put("total", tasks.size());
        overview.put("completed", tasks.stream().filter(Task::isCompleted).count());
        overview.put("inProgress", tasks.stream().filter(Task::isInProgress).count());
        overview.put("pending", tasks.stream()
                .filter(t -> TaskStatus.PENDING.equals(t.getStatus())).count());
        overview.put("overdue", tasks.stream().filter(Task::isOverdue).count());

        // 按状态统计
        Map<String, Long> byStatus = tasks.stream()
                .collect(Collectors.groupingBy(t -> t.getStatus().getCode(), Collectors.counting()));
        overview.put("byStatus", byStatus);

        // 按优先级统计
        Map<String, Long> byPriority = tasks.stream()
                .collect(Collectors.groupingBy(t -> t.getPriority().getCode(), Collectors.counting()));
        overview.put("byPriority", byPriority);

        // 平均进度
        double avgProgress = tasks.stream()
                .mapToInt(Task::getProgress)
                .average()
                .orElse(0.0);
        overview.put("averageProgress", Math.round(avgProgress * 100.0) / 100.0);

        // 完成率
        double completionRate = tasks.isEmpty() ? 0.0 :
                (double) (Long) overview.get("completed") / tasks.size() * 100;
        overview.put("completionRate", Math.round(completionRate * 100.0) / 100.0);

        return overview;
    }

    // ==================== 辅助方法 ====================

    /**
     * 验证任务数据
     *
     * @param task 任务对象
     */
    private void validateTask(Task task) {
        if (task == null) {
            throw new IllegalArgumentException("任务不能为空");
        }
        if (task.getTitle() == null || task.getTitle().trim().isEmpty()) {
            throw new IllegalArgumentException("任务标题不能为空");
        }
        if (task.getCreatorId() == null || task.getCreatorId().trim().isEmpty()) {
            throw new IllegalArgumentException("创建者ID不能为空");
        }
    }

    /**
     * 计算任务完成时间（小时）
     *
     * @param task 任务对象
     * @return 完成时间（小时）
     */
    public double calculateCompletionTime(Task task) {
        if (task.getCreatedAt() == null || task.getCompletedAt() == null) {
            return 0.0;
        }
        Duration duration = Duration.between(task.getCreatedAt(), task.getCompletedAt());
        return duration.toMinutes() / 60.0;
    }
}