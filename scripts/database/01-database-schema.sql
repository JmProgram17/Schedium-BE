-- ===============================================
-- SCHEDIUM DATABASE - MAIN SCHEMA
-- Base de datos principal del sistema de programación académica
-- ===============================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS schedium;
USE schedium;

-- ===============================================
-- CLEAN EXISTING STRUCTURE (IF ANY)
-- ===============================================
SET FOREIGN_KEY_CHECKS = 0;

-- Drop existing tables in reverse dependency order
DROP TABLE IF EXISTS class_schedule_audit;
DROP TABLE IF EXISTS class_schedule;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS role;
DROP TABLE IF EXISTS quarter;
DROP TABLE IF EXISTS instructor;
DROP TABLE IF EXISTS contract;
DROP TABLE IF EXISTS day_time_block;
DROP TABLE IF EXISTS day;
DROP TABLE IF EXISTS department_classroom;
DROP TABLE IF EXISTS classroom;
DROP TABLE IF EXISTS time_block;
DROP TABLE IF EXISTS student_group;
DROP TABLE IF EXISTS schedule;
DROP TABLE IF EXISTS program;
DROP TABLE IF EXISTS nomenclature;
DROP TABLE IF EXISTS chain;
DROP TABLE IF EXISTS level;
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS campus;

SET FOREIGN_KEY_CHECKS = 1;

-- ===============================================
-- CREATE TABLES
-- ===============================================

-- Campus table
CREATE TABLE campus (
    campus_id       INT AUTO_INCREMENT PRIMARY KEY,
    address         VARCHAR(255) NOT NULL,
    phone_number    VARCHAR(20),
    email           VARCHAR(100),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX ix_campus_email (email)
) COMMENT 'Physical locations where classes are held';

-- Department table
CREATE TABLE department (
    department_id   INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    phone_number    VARCHAR(20),
    email           VARCHAR(100),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX ix_department_name (name),
    INDEX ix_department_email (email)
) COMMENT 'Academic departments that manage programs and instructors';

-- Level table
CREATE TABLE level (
    level_id        INT AUTO_INCREMENT PRIMARY KEY,
    study_type      VARCHAR(100) NOT NULL,
    duration        INT COMMENT 'Duration in months',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX ix_level_study_type (study_type)
) COMMENT 'Academic levels for programs';

-- Chain table
CREATE TABLE chain (
    chain_id        INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX uq_chain_name (name)
) COMMENT 'Program chains or learning paths';

-- Nomenclature table
CREATE TABLE nomenclature (
    nomenclature_id INT AUTO_INCREMENT PRIMARY KEY,
    code            VARCHAR(20) NOT NULL COMMENT 'Abbreviation or short code for programs',
    description     VARCHAR(255) COMMENT 'Optional description of this nomenclature code',
    active          BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX uq_nomenclature_code (code)
) COMMENT 'Standardized abbreviations or codes for academic programs';

-- Program table
CREATE TABLE program (
    program_id      INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    nomenclature_id INT,
    chain_id        INT,
    department_id   INT,
    level_id        INT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (nomenclature_id) REFERENCES nomenclature(nomenclature_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (chain_id) REFERENCES chain(chain_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (department_id) REFERENCES department(department_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (level_id) REFERENCES level(level_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    
    INDEX ix_program_name (name),
    INDEX ix_program_nomenclature_id (nomenclature_id)
) COMMENT 'Academic programs offered by the institution';

-- Schedule table
CREATE TABLE schedule (
    schedule_id     INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(50) NOT NULL,
    start_time      TIME NOT NULL,
    end_time        TIME NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX uq_schedule_name (name)
) COMMENT 'Daily schedules for classes (morning, afternoon, evening, etc.)';

-- Student Group table
CREATE TABLE student_group (
    group_id        INT AUTO_INCREMENT PRIMARY KEY,
    group_number    INT NOT NULL,
    program_id      INT,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    capacity        INT NOT NULL,
    schedule_id     INT,
    active          BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (program_id) REFERENCES program(program_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES schedule(schedule_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    
    UNIQUE INDEX uq_student_group_group_number (group_number),
    INDEX ix_student_group_program_id (program_id),
    INDEX ix_student_group_start_date (start_date),
    INDEX ix_student_group_end_date (end_date)
) COMMENT 'Student groups assigned to specific programs';

-- Time Block table
CREATE TABLE time_block (
    time_block_id       INT AUTO_INCREMENT PRIMARY KEY,
    start_time          TIME NOT NULL,
    end_time            TIME NOT NULL,
    duration_minutes    INT GENERATED ALWAYS AS
                        (TIMESTAMPDIFF(MINUTE, start_time, end_time)) STORED,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX uq_time_block_start_time_end_time (start_time, end_time)
) COMMENT 'Time blocks for class scheduling';

-- Classroom table
CREATE TABLE classroom (
    classroom_id    INT AUTO_INCREMENT PRIMARY KEY,
    room_number     VARCHAR(20) NOT NULL,
    capacity        INT NOT NULL,
    campus_id       INT NOT NULL,
    classroom_type  VARCHAR(50) DEFAULT 'Standard',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (campus_id) REFERENCES campus(campus_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    
    UNIQUE INDEX uq_classroom_room_number_campus_id (room_number, campus_id)
) COMMENT 'Physical classrooms where classes are held';

-- Department Classroom relationship table
CREATE TABLE department_classroom (
    department_id   INT,
    classroom_id    INT,
    priority        INT DEFAULT 0 COMMENT 'Booking priority level',
    is_primary      BOOLEAN DEFAULT FALSE COMMENT 'Is primary classroom for department',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (department_id, classroom_id),
    
    FOREIGN KEY (department_id) REFERENCES department(department_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (classroom_id) REFERENCES classroom(classroom_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    INDEX ix_department_classroom_classroom_id (classroom_id, department_id)
) COMMENT 'Many-to-many relationship between departments and classrooms';

-- Day table
CREATE TABLE day (
    day_id      INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(20) NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX uq_day_name (name)
) COMMENT 'Days of the week';

-- Day Time Block table
CREATE TABLE day_time_block (
    day_time_block_id   INT AUTO_INCREMENT PRIMARY KEY,
    time_block_id       INT NOT NULL,
    day_id              INT NOT NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (time_block_id) REFERENCES time_block(time_block_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (day_id) REFERENCES day(day_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    UNIQUE INDEX uq_day_time_block_day_id_time_block_id (day_id, time_block_id)
) COMMENT 'Association between days and time blocks for scheduling';

-- Contract table
CREATE TABLE contract (
    contract_id     INT AUTO_INCREMENT PRIMARY KEY,
    contract_type   VARCHAR(100) NOT NULL,
    hour_limit      INT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX ix_contract_contract_type (contract_type)
) COMMENT 'Instructor contract types';

-- Instructor table
CREATE TABLE instructor (
    instructor_id   INT AUTO_INCREMENT PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    phone_number    VARCHAR(20),
    email           VARCHAR(100) NOT NULL,
    hour_count      DECIMAL(10,2) DEFAULT 0,
    contract_id     INT,
    department_id   INT,
    active          BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES contract(contract_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (department_id) REFERENCES department(department_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    
    UNIQUE INDEX uq_instructor_email (email),
    INDEX ix_instructor_last_name (last_name),
    INDEX ix_instructor_first_name (first_name)
) COMMENT 'Instructors who teach courses';

-- Quarter table
CREATE TABLE quarter (
    quarter_id  INT AUTO_INCREMENT PRIMARY KEY,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    name        VARCHAR(50) GENERATED ALWAYS AS
                (CONCAT('Q', QUARTER(start_date), '-', YEAR(start_date))) STORED,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX uq_quarter_start_date_end_date (start_date, end_date),
    INDEX ix_quarter_name (name)
) COMMENT 'Academic quarters for scheduling';

-- Role table
CREATE TABLE role (
    role_id     INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50) NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX uq_role_name (name)
) COMMENT 'User roles for system access control';

-- User table
CREATE TABLE user (
    user_id         INT AUTO_INCREMENT PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    document_number VARCHAR(20) NOT NULL,
    password        VARCHAR(255) NOT NULL,
    email           VARCHAR(100) NOT NULL,
    role_id         INT,
    active          BOOLEAN DEFAULT TRUE,
    last_login      DATETIME,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (role_id) REFERENCES role(role_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    
    UNIQUE INDEX uq_user_email (email),
    UNIQUE INDEX uq_user_document_number (document_number),
    INDEX ix_user_last_name (last_name),
    INDEX ix_user_first_name (first_name)
) COMMENT 'System users with access credentials';

-- Class Schedule table
CREATE TABLE class_schedule (
    class_schedule_id   INT AUTO_INCREMENT PRIMARY KEY,
    subject             VARCHAR(255) NOT NULL,
    quarter_id          INT NOT NULL,
    day_time_block_id   INT NOT NULL,
    group_id            INT NOT NULL,
    instructor_id       INT NOT NULL,
    classroom_id        INT NOT NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (quarter_id) REFERENCES quarter(quarter_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (day_time_block_id) REFERENCES day_time_block(day_time_block_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (group_id) REFERENCES student_group(group_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (instructor_id) REFERENCES instructor(instructor_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (classroom_id) REFERENCES classroom(classroom_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    
    -- Unique constraints for conflict prevention
    UNIQUE INDEX uq_class_schedule_day_time_block_id_instructor_id_quarter_id (day_time_block_id, instructor_id, quarter_id),
    UNIQUE INDEX uq_class_schedule_day_time_block_id_classroom_id_quarter_id (day_time_block_id, classroom_id, quarter_id),
    UNIQUE INDEX uq_class_schedule_day_time_block_id_group_id_quarter_id (day_time_block_id, group_id, quarter_id),
    INDEX ix_class_schedule_group_id (group_id),
    INDEX ix_class_schedule_quarter_id (quarter_id)
) COMMENT 'Class schedules linking instructors, groups, classrooms, and time slots';

-- Audit table for class schedule changes
CREATE TABLE class_schedule_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    class_schedule_id INT,
    action_type ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    old_subject VARCHAR(255),
    new_subject VARCHAR(255),
    old_instructor_id INT,
    new_instructor_id INT,
    old_classroom_id INT,
    new_classroom_id INT,
    old_quarter_id INT,
    new_quarter_id INT,
    changed_by VARCHAR(100) DEFAULT 'system',
    change_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    change_reason VARCHAR(500)
) COMMENT 'Audit trail for class schedule changes';

SELECT 'Database schema created successfully' AS status;