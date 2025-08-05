-- MySQL数据库初始化脚本
-- 用于Magento-CJ-Middleware项目

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS magento_cj_middleware CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE magento_cj_middleware;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 产品表
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    magento_id VARCHAR(50) UNIQUE,
    cj_product_id VARCHAR(50),
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    stock_quantity INT DEFAULT 0,
    status ENUM('active', 'inactive', 'pending') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    magento_order_id VARCHAR(50) UNIQUE,
    cj_order_id VARCHAR(50),
    customer_email VARCHAR(100),
    total_amount DECIMAL(10,2),
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 同步日志表
CREATE TABLE IF NOT EXISTS sync_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sync_type ENUM('products', 'orders', 'inventory') NOT NULL,
    status ENUM('success', 'failed', 'partial') NOT NULL,
    records_processed INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_sync_logs_type ON sync_logs(sync_type);
CREATE INDEX idx_sync_logs_created ON sync_logs(created_at);

-- 插入默认管理员用户（密码需要在应用层处理）
INSERT IGNORE INTO users (username, email, password_hash) 
VALUES ('admin', 'admin@example.com', 'temporary_hash_needs_update'); 