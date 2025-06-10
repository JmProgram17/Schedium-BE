-- Initial database setup for Schedium
-- This script is executed when the MySQL container starts

-- Set UTF-8 encoding
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Create database if it doesn't exist (Docker entrypoint creates it, but just in case)
-- CREATE DATABASE IF NOT EXISTS schedium CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Switch to the database
USE schedium;

-- Enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Set timezone
SET time_zone = '+00:00';

-- Log the initialization
SELECT 'Database initialization completed' as status;