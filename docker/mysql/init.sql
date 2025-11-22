-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS magento_cj_middleware CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE magento_cj_middleware;

-- 创建用户并授权（如果不存在）
CREATE USER IF NOT EXISTS 'magento_user'@'%' IDENTIFIED BY 'magento123456';
GRANT ALL PRIVILEGES ON magento_cj_middleware.* TO 'magento_user'@'%';
FLUSH PRIVILEGES;

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection=utf8mb4; 