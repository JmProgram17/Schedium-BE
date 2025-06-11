-- ===============================================
-- SCHEDIUM DATABASE - TRIGGERS
-- Triggers para validación y control automático del sistema
-- ===============================================

USE schedium;

-- Configuración para triggers
SET SQL_SAFE_UPDATES = 0;

-- Eliminar triggers existentes si existen
DROP TRIGGER IF EXISTS validate_schedule_conflicts;
DROP TRIGGER IF EXISTS update_instructor_hours_insert;
DROP TRIGGER IF EXISTS update_instructor_hours_delete;
DROP TRIGGER IF EXISTS update_instructor_hours_update;
DROP TRIGGER IF EXISTS check_instructor_hour_limit;
DROP TRIGGER IF EXISTS validate_classroom_capacity;
DROP TRIGGER IF EXISTS audit_class_schedule_insert;
DROP TRIGGER IF EXISTS audit_class_schedule_update;
DROP TRIGGER IF EXISTS audit_class_schedule_delete;

-- Cambiar el delimitador para poder definir triggers con múltiples statements
DELIMITER $$

-- ===============================================
-- TRIGGER 1: VALIDACIÓN DE CONFLICTOS DE PROGRAMACIÓN
-- ===============================================
-- Razón: Previene conflictos de horarios automáticamente
-- - Instructor no puede estar en dos clases simultáneas
-- - Grupo no puede estar en dos clases simultáneas  
-- - Aula no puede ser usada por dos clases simultáneas

CREATE TRIGGER validate_schedule_conflicts
BEFORE INSERT ON class_schedule
FOR EACH ROW
BEGIN
    DECLARE conflict_count INT DEFAULT 0;
    DECLARE instructor_fname VARCHAR(100);
    DECLARE instructor_lname VARCHAR(100);
    DECLARE group_number_conflict INT;
    DECLARE classroom_number_conflict VARCHAR(20);
    DECLARE campus_address VARCHAR(255);
    DECLARE error_message VARCHAR(500);

    -- Verificar conflicto de INSTRUCTOR
    SELECT COUNT(*) INTO conflict_count
    FROM class_schedule cs
    WHERE cs.day_time_block_id = NEW.day_time_block_id
        AND cs.instructor_id = NEW.instructor_id
        AND cs.quarter_id = NEW.quarter_id;

    IF conflict_count > 0 THEN
        SELECT first_name, last_name INTO instructor_fname, instructor_lname
        FROM instructor
        WHERE instructor_id = NEW.instructor_id;

        SET error_message = CONCAT('CONFLICTO INSTRUCTOR: ', instructor_fname, ' ',
            instructor_lname, ' ya tiene una clase asignada en este horario y trimestre.');

        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;

    -- Verificar conflicto de GRUPO
    SELECT COUNT(*) INTO conflict_count
    FROM class_schedule cs
    WHERE cs.day_time_block_id = NEW.day_time_block_id
        AND cs.group_id = NEW.group_id
        AND cs.quarter_id = NEW.quarter_id;

    IF conflict_count > 0 THEN
        SELECT group_number INTO group_number_conflict
        FROM student_group
        WHERE group_id = NEW.group_id;

        SET error_message = CONCAT('CONFLICTO GRUPO: El grupo ', group_number_conflict,
            ' ya tiene una clase asignada en este horario y trimestre.');

        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;

    -- Verificar conflicto de AULA
    SELECT COUNT(*) INTO conflict_count
    FROM class_schedule cs
    WHERE cs.day_time_block_id = NEW.day_time_block_id
        AND cs.classroom_id = NEW.classroom_id
        AND cs.quarter_id = NEW.quarter_id;

    IF conflict_count > 0 THEN
        SELECT c.room_number, cam.address INTO classroom_number_conflict, campus_address
        FROM classroom c
        INNER JOIN campus cam ON c.campus_id = cam.campus_id
        WHERE c.classroom_id = NEW.classroom_id;

        SET error_message = CONCAT('CONFLICTO AULA: El aula ', classroom_number_conflict,
            ' en ', campus_address, ' ya está ocupada en este horario y trimestre.');

        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
END$$

-- ===============================================
-- TRIGGER 2: CONTEO DE HORAS - INSERCIÓN
-- ===============================================
-- Razón: Mantiene automáticamente el conteo de horas asignadas por instructor

CREATE TRIGGER update_instructor_hours_insert
AFTER INSERT ON class_schedule
FOR EACH ROW
BEGIN
    DECLARE class_duration_minutes INT DEFAULT 0;
    DECLARE class_duration_hours DECIMAL(10,2) DEFAULT 0;

    SELECT COALESCE(tb.duration_minutes, 0) INTO class_duration_minutes
    FROM day_time_block dtb
    INNER JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
    WHERE dtb.day_time_block_id = NEW.day_time_block_id;

    SET class_duration_hours = class_duration_minutes / 60.0;

    UPDATE instructor
    SET hour_count = hour_count + class_duration_hours
    WHERE instructor_id = NEW.instructor_id;
END$$

-- ===============================================
-- TRIGGER 3: CONTEO DE HORAS - ELIMINACIÓN
-- ===============================================
-- Razón: Resta automáticamente las horas cuando se elimina una clase

CREATE TRIGGER update_instructor_hours_delete
AFTER DELETE ON class_schedule
FOR EACH ROW
BEGIN
    DECLARE class_duration_minutes INT DEFAULT 0;
    DECLARE class_duration_hours DECIMAL(10,2) DEFAULT 0;

    SELECT COALESCE(tb.duration_minutes, 0) INTO class_duration_minutes
    FROM day_time_block dtb
    INNER JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
    WHERE dtb.day_time_block_id = OLD.day_time_block_id;

    SET class_duration_hours = class_duration_minutes / 60.0;

    UPDATE instructor
    SET hour_count = GREATEST(0, hour_count - class_duration_hours)
    WHERE instructor_id = OLD.instructor_id;
END$$

-- ===============================================
-- TRIGGER 4: CONTEO DE HORAS - ACTUALIZACIÓN
-- ===============================================
-- Razón: Ajusta automáticamente las horas cuando se modifica una clase

CREATE TRIGGER update_instructor_hours_update
AFTER UPDATE ON class_schedule
FOR EACH ROW
BEGIN
    DECLARE old_duration_minutes INT DEFAULT 0;
    DECLARE new_duration_minutes INT DEFAULT 0;
    DECLARE old_duration_hours DECIMAL(10,2) DEFAULT 0;
    DECLARE new_duration_hours DECIMAL(10,2) DEFAULT 0;

    -- Si cambió el instructor, ajustar horas en ambos instructores
    IF OLD.instructor_id != NEW.instructor_id THEN
        -- Obtener duración del bloque anterior
        SELECT COALESCE(tb.duration_minutes, 0) INTO old_duration_minutes
        FROM day_time_block dtb
        INNER JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
        WHERE dtb.day_time_block_id = OLD.day_time_block_id;

        SET old_duration_hours = old_duration_minutes / 60.0;

        -- Restar horas del instructor anterior
        UPDATE instructor
        SET hour_count = GREATEST(0, hour_count - old_duration_hours)
        WHERE instructor_id = OLD.instructor_id;

        -- Obtener duración del nuevo bloque
        SELECT COALESCE(tb.duration_minutes, 0) INTO new_duration_minutes
        FROM day_time_block dtb
        INNER JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
        WHERE dtb.day_time_block_id = NEW.day_time_block_id;

        SET new_duration_hours = new_duration_minutes / 60.0;

        -- Sumar horas al nuevo instructor
        UPDATE instructor
        SET hour_count = hour_count + new_duration_hours
        WHERE instructor_id = NEW.instructor_id;

    -- Si cambió el horario pero no el instructor, ajustar la diferencia
    ELSEIF OLD.day_time_block_id != NEW.day_time_block_id THEN
        -- Obtener duración del bloque anterior
        SELECT COALESCE(tb.duration_minutes, 0) INTO old_duration_minutes
        FROM day_time_block dtb
        INNER JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
        WHERE dtb.day_time_block_id = OLD.day_time_block_id;

        -- Obtener duración del nuevo bloque
        SELECT COALESCE(tb.duration_minutes, 0) INTO new_duration_minutes
        FROM day_time_block dtb
        INNER JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
        WHERE dtb.day_time_block_id = NEW.day_time_block_id;

        SET old_duration_hours = old_duration_minutes / 60.0;
        SET new_duration_hours = new_duration_minutes / 60.0;

        -- Ajustar la diferencia de horas
        UPDATE instructor
        SET hour_count = GREATEST(0, hour_count - old_duration_hours + new_duration_hours)
        WHERE instructor_id = NEW.instructor_id;
    END IF;
END$$

-- ===============================================
-- TRIGGER 5: CONTROL DE LÍMITE DE HORAS CONTRACTUALES
-- ===============================================
-- Razón: Previene que instructores excedan sus límites contractuales

CREATE TRIGGER check_instructor_hour_limit
BEFORE INSERT ON class_schedule
FOR EACH ROW
BEGIN
    DECLARE current_hours DECIMAL(10,2) DEFAULT 0;
    DECLARE class_duration_minutes INT DEFAULT 0;
    DECLARE class_duration_hours DECIMAL(10,2) DEFAULT 0;
    DECLARE hour_limit INT DEFAULT NULL;
    DECLARE instructor_fname VARCHAR(100);
    DECLARE instructor_lname VARCHAR(100);
    DECLARE total_after_class DECIMAL(10,2) DEFAULT 0;
    DECLARE error_message VARCHAR(500);

    -- Obtener horas actuales del instructor
    SELECT COALESCE(hour_count, 0) INTO current_hours
    FROM instructor
    WHERE instructor_id = NEW.instructor_id;

    -- Obtener duración de la nueva clase en minutos
    SELECT COALESCE(tb.duration_minutes, 0) INTO class_duration_minutes
    FROM day_time_block dtb
    INNER JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
    WHERE dtb.day_time_block_id = NEW.day_time_block_id;

    SET class_duration_hours = class_duration_minutes / 60.0;

    -- Obtener límite de horas del contrato del instructor
    SELECT c.hour_limit INTO hour_limit
    FROM instructor i
    INNER JOIN contract c ON i.contract_id = c.contract_id
    WHERE i.instructor_id = NEW.instructor_id;

    -- Calcular total después de agregar la nueva clase
    SET total_after_class = current_hours + class_duration_hours;

    -- Si excede el límite, generar error
    IF hour_limit IS NOT NULL AND total_after_class > hour_limit THEN
        SELECT first_name, last_name INTO instructor_fname, instructor_lname
        FROM instructor
        WHERE instructor_id = NEW.instructor_id;

        SET error_message = CONCAT('LIMITE HORAS EXCEDIDO: El instructor ', instructor_fname, ' ',
            instructor_lname, ' superaría su límite contractual (',
            hour_limit, ' horas). Total actual: ', current_hours,
            ' horas. Esta clase agregaría ', class_duration_hours,
            ' horas para un total de ', total_after_class, ' horas.');

        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
END$$

-- ===============================================
-- TRIGGER 6: VALIDACIÓN DE CAPACIDAD DE AULA
-- ===============================================
-- Razón: Asegura que la capacidad del aula sea suficiente para el grupo

CREATE TRIGGER validate_classroom_capacity
BEFORE INSERT ON class_schedule
FOR EACH ROW
BEGIN
    DECLARE classroom_capacity INT DEFAULT 0;
    DECLARE group_capacity INT DEFAULT 0;
    DECLARE classroom_number VARCHAR(20);
    DECLARE group_number_val INT;
    DECLARE error_message VARCHAR(500);

    -- Obtener capacidad del aula
    SELECT capacity, room_number INTO classroom_capacity, classroom_number
    FROM classroom
    WHERE classroom_id = NEW.classroom_id;

    -- Obtener capacidad del grupo
    SELECT capacity, group_number INTO group_capacity, group_number_val
    FROM student_group
    WHERE group_id = NEW.group_id;

    -- Validar que el aula tenga capacidad suficiente
    IF group_capacity > classroom_capacity THEN
        SET error_message = CONCAT('CAPACIDAD INSUFICIENTE: El aula ', classroom_number,
            ' tiene capacidad para ', classroom_capacity, ' estudiantes, pero el grupo ',
            group_number_val, ' tiene ', group_capacity, ' estudiantes.');

        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
END$$

-- ===============================================
-- TRIGGERS 7-9: AUDITORÍA DE CAMBIOS EN CLASES
-- ===============================================
-- Razón: Mantiene un registro completo de cambios para auditoría y trazabilidad

CREATE TRIGGER audit_class_schedule_insert
AFTER INSERT ON class_schedule
FOR EACH ROW
BEGIN
    INSERT INTO class_schedule_audit (
        class_schedule_id, action_type, new_subject, 
        new_instructor_id, new_classroom_id, new_quarter_id
    ) VALUES (
        NEW.class_schedule_id, 'INSERT', NEW.subject,
        NEW.instructor_id, NEW.classroom_id, NEW.quarter_id
    );
END$$

CREATE TRIGGER audit_class_schedule_update
AFTER UPDATE ON class_schedule
FOR EACH ROW
BEGIN
    INSERT INTO class_schedule_audit (
        class_schedule_id, action_type, 
        old_subject, new_subject,
        old_instructor_id, new_instructor_id,
        old_classroom_id, new_classroom_id,
        old_quarter_id, new_quarter_id
    ) VALUES (
        NEW.class_schedule_id, 'UPDATE',
        OLD.subject, NEW.subject,
        OLD.instructor_id, NEW.instructor_id,
        OLD.classroom_id, NEW.classroom_id,
        OLD.quarter_id, NEW.quarter_id
    );
END$$

CREATE TRIGGER audit_class_schedule_delete
AFTER DELETE ON class_schedule
FOR EACH ROW
BEGIN
    INSERT INTO class_schedule_audit (
        class_schedule_id, action_type, old_subject,
        old_instructor_id, old_classroom_id, old_quarter_id
    ) VALUES (
        OLD.class_schedule_id, 'DELETE', OLD.subject,
        OLD.instructor_id, OLD.classroom_id, OLD.quarter_id
    );
END$$

-- Restablecer el delimitador
DELIMITER ;

-- Restaurar configuración
SET SQL_SAFE_UPDATES = 1;

SELECT 'Total triggers created: 9' AS status;
SELECT 'Triggers para validación, conteo de horas, límites contractuales, capacidad y auditoría' AS description;