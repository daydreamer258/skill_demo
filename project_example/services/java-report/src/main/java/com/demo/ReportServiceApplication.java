// 智能任务管理系统 - Java Spring Boot 报表服务
// 提供任务统计报表生成、数据导出、定时报表等功能

package com.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * 报表服务应用入口
 *
 * @author TaskManager Team
 * @version 1.0.0
 */
@SpringBootApplication
@EnableScheduling
@EnableTransactionManagement
public class ReportServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(ReportServiceApplication.class, args);
        System.out.println("====================================");
        System.out.println("报表服务启动成功!");
        System.out.println("====================================");
    }
}