-- ===============================================
-- SCHEDIUM DATABASE - INITIAL DATA
-- Datos iniciales para el sistema de programación académica
-- ===============================================

USE schedium;

-- ===============================================
-- INITIAL DATA
-- ===============================================

-- Insert days of the week
INSERT INTO day (name) VALUES
    ('Monday'),
    ('Tuesday'),
    ('Wednesday'),
    ('Thursday'),
    ('Friday'),
    ('Saturday'),
    ('Sunday');

-- Insert initial roles
INSERT INTO role (name) VALUES
    ('Administrator'),
    ('Coordinator'),
    ('Secretary');

-- Insert sample campus
INSERT INTO campus (address, phone_number, email) VALUES
    ('Campus Principal - Calle 123', '3001234567', 'campus.principal@schedium.edu'),
    ('Campus Norte - Av. 456', '3007654321', 'campus.norte@schedium.edu');

-- Insert sample departments
INSERT INTO department (name, phone_number, email) VALUES
    ('Departamento de Sistemas', '3001111111', 'sistemas@schedium.edu'),
    ('Departamento de Administración', '3002222222', 'administracion@schedium.edu'),
    ('Departamento de Inglés', '3003333333', 'ingles@schedium.edu');

-- Insert sample levels
INSERT INTO level (study_type, duration) VALUES
    ('Técnico', 24),
    ('Tecnólogo', 30),
    ('Especialización', 12);

-- Insert sample chains
INSERT INTO chain (name) VALUES
    ('Cadena de Tecnología'),
    ('Cadena de Negocios'),
    ('Cadena de Idiomas');

-- Insert sample nomenclatures
INSERT INTO nomenclature (code, description, active) VALUES
    ('ADSI', 'Análisis y Desarrollo de Sistemas de Información', TRUE),
    ('CONT', 'Contabilidad y Finanzas', TRUE),
    ('ING', 'Inglés', TRUE);

-- Insert sample programs
INSERT INTO program (name, nomenclature_id, chain_id, department_id, level_id) VALUES
    ('Análisis y Desarrollo de Sistemas de Información', 1, 1, 1, 2),
    ('Contabilidad y Finanzas', 2, 2, 2, 1),
    ('Inglés Técnico', 3, 3, 3, 1);

-- Insert sample schedules
INSERT INTO schedule (name, start_time, end_time) VALUES
    ('Mañana', '06:00:00', '12:00:00'),
    ('Tarde', '12:00:00', '18:00:00'),
    ('Noche', '18:00:00', '22:00:00');

-- Insert sample contracts
INSERT INTO contract (contract_type, hour_limit) VALUES
    ('Planta', 40),
    ('Contrato', 30),
    ('Hora Cátedra', 20);

-- Insert sample time blocks
INSERT INTO time_block (start_time, end_time) VALUES
    ('06:00:00', '08:00:00'),
    ('08:00:00', '10:00:00'),
    ('10:00:00', '12:00:00'),
    ('12:00:00', '14:00:00'),
    ('14:00:00', '16:00:00'),
    ('16:00:00', '18:00:00'),
    ('18:00:00', '20:00:00'),
    ('20:00:00', '22:00:00');

-- Insert sample classrooms
INSERT INTO classroom (room_number, capacity, campus_id, classroom_type) VALUES
    ('101', 30, 1, 'Aula Teórica'),
    ('102', 25, 1, 'Laboratorio'),
    ('201', 35, 1, 'Aula Teórica'),
    ('301', 20, 2, 'Laboratorio'),
    ('302', 40, 2, 'Aula Teórica');

-- Create day-time block associations (only weekdays)
INSERT INTO day_time_block (day_id, time_block_id)
SELECT d.day_id, tb.time_block_id
FROM day d
CROSS JOIN time_block tb
WHERE d.name IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday');

-- Insert sample student groups
INSERT INTO student_group (group_number, program_id, start_date, end_date, capacity, schedule_id, active) VALUES
    (2486521, 1, '2025-01-15', '2026-07-15', 25, 1, TRUE),
    (2486522, 2, '2025-01-15', '2026-07-15', 30, 2, TRUE),
    (2486523, 3, '2025-02-01', '2025-08-01', 20, 3, TRUE);

-- Insert sample instructors
INSERT INTO instructor (first_name, last_name, phone_number, email, hour_count, contract_id, department_id, active) VALUES
    ('Juan', 'Pérez', '3001111111', 'juan.perez@schedium.edu', 0, 1, 1, TRUE),
    ('María', 'García', '3002222222', 'maria.garcia@schedium.edu', 0, 2, 2, TRUE),
    ('Carlos', 'López', '3003333333', 'carlos.lopez@schedium.edu', 0, 3, 3, TRUE),
    ('Ana', 'Martínez', '3004444444', 'ana.martinez@schedium.edu', 0, 1, 1, TRUE);

-- Insert sample quarters
INSERT INTO quarter (start_date, end_date) VALUES
    ('2025-01-15', '2025-04-15'),
    ('2025-04-16', '2025-07-15'),
    ('2025-07-16', '2025-10-15'),
    ('2025-10-16', '2026-01-15');

-- Create department-classroom relationships
INSERT INTO department_classroom (department_id, classroom_id, priority, is_primary) VALUES
    (1, 1, 1, TRUE),   -- Sistemas -> Aula 101
    (1, 2, 1, FALSE),  -- Sistemas -> Lab 102
    (2, 3, 1, TRUE),   -- Administración -> Aula 201
    (3, 4, 1, TRUE),   -- Inglés -> Lab 301
    (3, 5, 1, FALSE);  -- Inglés -> Aula 302

-- Insert a default admin user (password: admin123)
INSERT INTO user (first_name, last_name, document_number, password, email, role_id, active) VALUES
    ('Admin', 'Sistema', '00000000', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYpfBVGJlKrpSH2', 'admin@schedium.edu', 1, TRUE);

-- Insert sample coordinator user (password: coord123)
INSERT INTO user (first_name, last_name, document_number, password, email, role_id, active) VALUES
    ('Coordinador', 'Académico', '11111111', '$2b$12$wKgGJfYk3ZfQ8SfFzDJGfOq4tYzNzJQmF3J4Hx5K8lMnOpQrStUvW', 'coordinador@schedium.edu', 2, TRUE);

SELECT 'Initial data loaded successfully' AS status;