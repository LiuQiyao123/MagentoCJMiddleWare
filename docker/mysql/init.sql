-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS magento_cj CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE magento_cj;

-- 创建用户并授权（如果不存在）
CREATE USER IF NOT EXISTS 'magento_user'@'%' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON magento_cj.* TO 'magento_user'@'%';
FLUSH PRIVILEGES;

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection=utf8mb4; 