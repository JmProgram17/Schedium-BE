-- ===============================================
-- SCHEDIUM DATABASE - VIEWS
-- Vistas para consultas optimizadas y reportes del sistema
-- ===============================================

USE schedium;

-- Eliminar vistas existentes si existen
DROP VIEW IF EXISTS view_schedule_matrix;
DROP VIEW IF EXISTS view_instructor_schedule;
DROP VIEW IF EXISTS view_classroom_schedule;
DROP VIEW IF EXISTS view_group_schedule;
DROP VIEW IF EXISTS view_general_search;
DROP VIEW IF EXISTS view_instructor_workload;
DROP VIEW IF EXISTS view_instructor_availability;
DROP VIEW IF EXISTS view_classroom_availability;
DROP VIEW IF EXISTS view_potential_conflicts;
DROP VIEW IF EXISTS view_executive_summary;
DROP VIEW IF EXISTS view_classroom_utilization;
DROP VIEW IF EXISTS schedule_detail;

-- ===============================================
-- VISTA 1: MATRIZ DE HORARIOS SEMANAL
-- ===============================================
-- Razón: Visualización tipo calendario de todas las clases programadas

CREATE VIEW view_schedule_matrix AS
SELECT
    tb.time_block_id,
    CONCAT(TIME_FORMAT(tb.start_time, '%H:%i'), ' - ',
           TIME_FORMAT(tb.end_time, '%H:%i')) AS bloque_horario,
    tb.start_time,
    tb.end_time,
    tb.duration_minutes,
    -- Lunes
    GROUP_CONCAT(
        CASE WHEN d.name = 'Monday' THEN
            CONCAT(cs.subject, ' (', i.last_name, ' - Grupo ',
                   sg.group_number, ' - Aula ', cl.room_number, ')')
        END SEPARATOR ' | '
    ) AS lunes,
    -- Martes
    GROUP_CONCAT(
        CASE WHEN d.name = 'Tuesday' THEN
            CONCAT(cs.subject, ' (', i.last_name, ' - Grupo ',
                   sg.group_number, ' - Aula ', cl.room_number, ')')
        END SEPARATOR ' | '
    ) AS martes,
    -- Miércoles
    GROUP_CONCAT(
        CASE WHEN d.name = 'Wednesday' THEN
            CONCAT(cs.subject, ' (', i.last_name, ' - Grupo ',
                   sg.group_number, ' - Aula ', cl.room_number, ')')
        END SEPARATOR ' | '
    ) AS miercoles,
    -- Jueves
    GROUP_CONCAT(
        CASE WHEN d.name = 'Thursday' THEN
            CONCAT(cs.subject, ' (', i.last_name, ' - Grupo ',
                   sg.group_number, ' - Aula ', cl.room_number, ')')
        END SEPARATOR ' | '
    ) AS jueves,
    -- Viernes
    GROUP_CONCAT(
        CASE WHEN d.name = 'Friday' THEN
            CONCAT(cs.subject, ' (', i.last_name, ' - Grupo ',
                   sg.group_number, ' - Aula ', cl.room_number, ')')
        END SEPARATOR ' | '
    ) AS viernes,
    -- Sábado
    GROUP_CONCAT(
        CASE WHEN d.name = 'Saturday' THEN
            CONCAT(cs.subject, ' (', i.last_name, ' - Grupo ',
                   sg.group_number, ' - Aula ', cl.room_number, ')')
        END SEPARATOR ' | '
    ) AS sabado
FROM time_block tb
LEFT JOIN day_time_block dtb ON tb.time_block_id = dtb.time_block_id
LEFT JOIN day d ON dtb.day_id = d.day_id
LEFT JOIN class_schedule cs ON dtb.day_time_block_id = cs.day_time_block_id
LEFT JOIN instructor i ON cs.instructor_id = i.instructor_id
LEFT JOIN student_group sg ON cs.group_id = sg.group_id
LEFT JOIN classroom cl ON cs.classroom_id = cl.classroom_id
GROUP BY tb.time_block_id, tb.start_time, tb.end_time, tb.duration_minutes
ORDER BY tb.start_time;

-- ===============================================
-- VISTA 2: PROGRAMACIÓN POR INSTRUCTOR
-- ===============================================
-- Razón: Consulta del horario completo de cada instructor

CREATE VIEW view_instructor_schedule AS
SELECT
    cs.class_schedule_id,
    i.instructor_id,
    CONCAT(i.first_name, ' ', i.last_name) AS instructor_completo,
    i.first_name AS instructor_nombre,
    i.last_name AS instructor_apellido,
    cs.subject AS materia,
    sg.group_id AS ficha_id,
    sg.group_number AS ficha_numero,
    n.code AS ficha_nomenclatura,
    p.name AS programa,
    cl.classroom_id AS ambiente_id,
    cl.room_number AS ambiente_numero,
    cam.address AS sede,
    cl.classroom_type AS tipo_ambiente,
    d.name AS dia,
    TIME_FORMAT(tb.start_time, '%H:%i') AS hora_inicio,
    TIME_FORMAT(tb.end_time, '%H:%i') AS hora_fin,
    CONCAT(TIME_FORMAT(tb.start_time, '%H:%i'), ' - ',
           TIME_FORMAT(tb.end_time, '%H:%i')) AS bloque_horario,
    tb.duration_minutes AS duracion_minutos,
    (tb.duration_minutes / 60.0) AS duracion_horas,
    q.name AS trimestre
FROM class_schedule cs
JOIN instructor i ON cs.instructor_id = i.instructor_id
JOIN student_group sg ON cs.group_id = sg.group_id
JOIN program p ON sg.program_id = p.program_id
LEFT JOIN nomenclature n ON p.nomenclature_id = n.nomenclature_id
JOIN classroom cl ON cs.classroom_id = cl.classroom_id
JOIN campus cam ON cl.campus_id = cam.campus_id
JOIN day_time_block dtb ON cs.day_time_block_id = dtb.day_time_block_id
JOIN day d ON dtb.day_id = d.day_id
JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
JOIN quarter q ON cs.quarter_id = q.quarter_id
ORDER BY i.last_name, i.first_name, d.day_id, tb.start_time;

-- ===============================================
-- VISTA 3: BÚSQUEDA GENERAL DEL SISTEMA
-- ===============================================
-- Razón: Funcionalidad de búsqueda unificada para instructores, grupos y aulas

CREATE VIEW view_general_search AS
-- Búsqueda de instructores
SELECT
    'instructor' AS tipo_resultado,
    i.instructor_id AS id,
    CONCAT(i.first_name, ' ', i.last_name) AS texto_principal,
    i.email AS texto_secundario,
    CONCAT('Instructor: ', i.first_name, ' ', i.last_name, ' - ', COALESCE(d.name, 'Sin departamento')) AS descripcion_completa,
    i.first_name AS search_field_1,
    i.last_name AS search_field_2,
    d.name AS search_field_3
FROM instructor i
LEFT JOIN department d ON i.department_id = d.department_id
WHERE i.active = TRUE

UNION ALL

-- Búsqueda de fichas/grupos
SELECT
    'ficha' AS tipo_resultado,
    sg.group_id AS id,
    CONCAT('Ficha ', sg.group_number) AS texto_principal,
    COALESCE(n.code, 'Sin nomenclatura') AS texto_secundario,
    CONCAT('Ficha ', sg.group_number, ' - ', COALESCE(n.code, ''), ' - ', p.name) AS descripcion_completa,
    CAST(sg.group_number AS CHAR) AS search_field_1,
    n.code AS search_field_2,
    p.name AS search_field_3
FROM student_group sg
JOIN program p ON sg.program_id = p.program_id
LEFT JOIN nomenclature n ON p.nomenclature_id = n.nomenclature_id
WHERE sg.active = TRUE

UNION ALL

-- Búsqueda de ambientes/aulas
SELECT
    'ambiente' AS tipo_resultado,
    cl.classroom_id AS id,
    CONCAT('Aula ', cl.room_number) AS texto_principal,
    cam.address AS texto_secundario,
    CONCAT('Aula ', cl.room_number, ' - ', cam.address, ' - ', cl.classroom_type) AS descripcion_completa,
    cl.room_number AS search_field_1,
    cam.address AS search_field_2,
    cl.classroom_type AS search_field_3
FROM classroom cl
JOIN campus cam ON cl.campus_id = cam.campus_id
ORDER BY tipo_resultado, texto_principal;

-- ===============================================
-- VISTA 4: CARGA HORARIA POR INSTRUCTOR
-- ===============================================
-- Razón: Dashboard de carga laboral y estado contractual de instructores

CREATE VIEW view_instructor_workload AS
SELECT
    i.instructor_id,
    CONCAT(i.first_name, ' ', i.last_name) AS instructor_completo,
    i.first_name AS nombre,
    i.last_name AS apellido,
    i.email,
    d_inst.name AS departamento,
    c.contract_type AS tipo_contrato,
    c.hour_limit AS limite_contractual,
    i.hour_count AS horas_totales_asignadas,
    COALESCE(c.hour_limit - i.hour_count, 0) AS horas_disponibles,
    CASE
        WHEN c.hour_limit IS NOT NULL THEN
            ROUND((i.hour_count / c.hour_limit) * 100, 1)
        ELSE NULL
    END AS porcentaje_ocupacion,
    CASE
        WHEN c.hour_limit IS NULL THEN 'SIN LÍMITE'
        WHEN i.hour_count = 0 THEN 'SIN ASIGNACIONES'
        WHEN i.hour_count > c.hour_limit THEN 'EXCEDE LÍMITE'
        WHEN i.hour_count = c.hour_limit THEN 'LÍMITE ALCANZADO'
        WHEN i.hour_count >= (c.hour_limit * 0.9) THEN 'CERCA DEL LÍMITE'
        WHEN i.hour_count >= (c.hour_limit * 0.7) THEN 'CARGA ALTA'
        WHEN i.hour_count >= (c.hour_limit * 0.5) THEN 'CARGA MEDIA'
        ELSE 'CARGA BAJA'
    END AS estado_carga,
    COUNT(cs.class_schedule_id) AS total_clases_asignadas
FROM instructor i
LEFT JOIN contract c ON i.contract_id = c.contract_id
LEFT JOIN department d_inst ON i.department_id = d_inst.department_id
LEFT JOIN class_schedule cs ON i.instructor_id = cs.instructor_id
WHERE i.active = TRUE
GROUP BY i.instructor_id, i.first_name, i.last_name, i.email, d_inst.name,
         c.contract_type, c.hour_limit, i.hour_count
ORDER BY i.hour_count DESC, i.last_name, i.first_name;

-- ===============================================
-- VISTA 5: DISPONIBILIDAD DE INSTRUCTORES
-- ===============================================
-- Razón: Facilita la asignación mostrando qué instructores están libres

CREATE VIEW view_instructor_availability AS
SELECT
    i.instructor_id,
    CONCAT(i.first_name, ' ', i.last_name) AS instructor_nombre,
    i.email,
    d.name AS departamento,
    c.contract_type,
    dtb.day_time_block_id,
    day.name AS dia,
    TIME_FORMAT(tb.start_time, '%H:%i') AS hora_inicio,
    TIME_FORMAT(tb.end_time, '%H:%i') AS hora_fin,
    CASE 
        WHEN cs.class_schedule_id IS NOT NULL THEN 'OCUPADO'
        ELSE 'DISPONIBLE'
    END AS estado,
    CASE 
        WHEN cs.class_schedule_id IS NOT NULL THEN cs.subject
        ELSE NULL
    END AS materia_asignada,
    i.hour_count AS horas_actuales,
    c.hour_limit AS limite_horas,
    CASE 
        WHEN c.hour_limit IS NOT NULL THEN (c.hour_limit - i.hour_count)
        ELSE 999
    END AS horas_disponibles_contrato
FROM instructor i
LEFT JOIN department d ON i.department_id = d.department_id
LEFT JOIN contract c ON i.contract_id = c.contract_id
CROSS JOIN day_time_block dtb
JOIN day ON dtb.day_id = day.day_id
JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
LEFT JOIN class_schedule cs ON i.instructor_id = cs.instructor_id 
    AND dtb.day_time_block_id = cs.day_time_block_id
WHERE i.active = TRUE
    AND day.name IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
ORDER BY i.last_name, i.first_name, day.day_id, tb.start_time;

-- ===============================================
-- VISTA 6: DISPONIBILIDAD DE AULAS
-- ===============================================
-- Razón: Facilita encontrar aulas libres para programación

CREATE VIEW view_classroom_availability AS
SELECT
    cl.classroom_id,
    cl.room_number,
    cl.capacity,
    cl.classroom_type,
    cam.address AS campus,
    dtb.day_time_block_id,
    d.name AS dia,
    TIME_FORMAT(tb.start_time, '%H:%i') AS hora_inicio,
    TIME_FORMAT(tb.end_time, '%H:%i') AS hora_fin,
    CONCAT(TIME_FORMAT(tb.start_time, '%H:%i'), ' - ',
           TIME_FORMAT(tb.end_time, '%H:%i')) AS bloque_horario,
    CASE 
        WHEN cs.class_schedule_id IS NOT NULL THEN 'OCUPADA'
        ELSE 'DISPONIBLE'
    END AS estado,
    CASE 
        WHEN cs.class_schedule_id IS NOT NULL THEN cs.subject
        ELSE NULL
    END AS materia_asignada,
    CASE 
        WHEN cs.class_schedule_id IS NOT NULL THEN 
            CONCAT(i.first_name, ' ', i.last_name)
        ELSE NULL
    END AS instructor_asignado,
    GROUP_CONCAT(DISTINCT dept.name SEPARATOR ', ') AS departamentos_autorizados
FROM classroom cl
JOIN campus cam ON cl.campus_id = cam.campus_id
CROSS JOIN day_time_block dtb
JOIN day d ON dtb.day_id = d.day_id
JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
LEFT JOIN class_schedule cs ON cl.classroom_id = cs.classroom_id 
    AND dtb.day_time_block_id = cs.day_time_block_id
LEFT JOIN instructor i ON cs.instructor_id = i.instructor_id
LEFT JOIN department_classroom dc ON cl.classroom_id = dc.classroom_id
LEFT JOIN department dept ON dc.department_id = dept.department_id
WHERE d.name IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
GROUP BY cl.classroom_id, cl.room_number, cl.capacity, cl.classroom_type, 
         cam.address, dtb.day_time_block_id, d.name, d.day_id,
         tb.start_time, tb.end_time, cs.class_schedule_id, cs.subject,
         i.first_name, i.last_name
ORDER BY cam.address, cl.room_number, d.day_id, tb.start_time;

-- ===============================================
-- VISTA 7: DETECCIÓN DE CONFLICTOS POTENCIALES
-- ===============================================
-- Razón: Identifica problemas en la programación antes de que se conviertan en errores

CREATE VIEW view_potential_conflicts AS
SELECT
    'INSTRUCTOR_DOBLE_ASIGNACION' AS tipo_conflicto,
    cs1.class_schedule_id AS clase_1,
    cs2.class_schedule_id AS clase_2,
    CONCAT('Instructor ', i.first_name, ' ', i.last_name, ' asignado en el mismo horario') AS descripcion,
    d.name AS dia,
    TIME_FORMAT(tb.start_time, '%H:%i') AS hora_inicio,
    q.name AS trimestre
FROM class_schedule cs1
JOIN class_schedule cs2 ON cs1.day_time_block_id = cs2.day_time_block_id
    AND cs1.instructor_id = cs2.instructor_id
    AND cs1.quarter_id = cs2.quarter_id
    AND cs1.class_schedule_id < cs2.class_schedule_id
JOIN instructor i ON cs1.instructor_id = i.instructor_id
JOIN day_time_block dtb ON cs1.day_time_block_id = dtb.day_time_block_id
JOIN day d ON dtb.day_id = d.day_id
JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
JOIN quarter q ON cs1.quarter_id = q.quarter_id

UNION ALL

SELECT
    'AULA_DOBLE_OCUPACION' AS tipo_conflicto,
    cs1.class_schedule_id AS clase_1,
    cs2.class_schedule_id AS clase_2,
    CONCAT('Aula ', cl.room_number, ' ocupada por dos clases simultáneamente') AS descripcion,
    d.name AS dia,
    TIME_FORMAT(tb.start_time, '%H:%i') AS hora_inicio,
    q.name AS trimestre
FROM class_schedule cs1
JOIN class_schedule cs2 ON cs1.day_time_block_id = cs2.day_time_block_id
    AND cs1.classroom_id = cs2.classroom_id
    AND cs1.quarter_id = cs2.quarter_id
    AND cs1.class_schedule_id < cs2.class_schedule_id
JOIN classroom cl ON cs1.classroom_id = cl.classroom_id
JOIN day_time_block dtb ON cs1.day_time_block_id = dtb.day_time_block_id
JOIN day d ON dtb.day_id = d.day_id
JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
JOIN quarter q ON cs1.quarter_id = q.quarter_id;

-- ===============================================
-- VISTA 8: DASHBOARD EJECUTIVO
-- ===============================================
-- Razón: Métricas clave para la dirección académica

CREATE VIEW view_executive_summary AS
SELECT
    'INSTRUCTORES' AS categoria,
    'Total Activos' AS metrica,
    COUNT(*) AS valor,
    'instructores' AS unidad
FROM instructor WHERE active = TRUE

UNION ALL

SELECT
    'INSTRUCTORES' AS categoria,
    'Con Sobrecarga' AS metrica,
    COUNT(*) AS valor,
    'instructores' AS unidad
FROM instructor i
JOIN contract c ON i.contract_id = c.contract_id
WHERE i.active = TRUE AND i.hour_count > c.hour_limit

UNION ALL

SELECT
    'AULAS' AS categoria,
    'Total Disponibles' AS metrica,
    COUNT(*) AS valor,
    'aulas' AS unidad
FROM classroom

UNION ALL

SELECT
    'GRUPOS' AS categoria,
    'Total Activos' AS metrica,
    COUNT(*) AS valor,
    'grupos' AS unidad
FROM student_group WHERE active = TRUE

UNION ALL

SELECT
    'CLASES' AS categoria,
    'Total Programadas' AS metrica,
    COUNT(*) AS valor,
    'clases' AS unidad
FROM class_schedule

UNION ALL

SELECT
    'UTILIZACIÓN' AS categoria,
    'Promedio Horas por Instructor' AS metrica,
    ROUND(AVG(hour_count), 1) AS valor,
    'horas' AS unidad
FROM instructor WHERE active = TRUE;

-- ===============================================
-- VISTA 9: UTILIZACIÓN DE AULAS
-- ===============================================
-- Razón: Optimización del uso de recursos físicos

CREATE VIEW view_classroom_utilization AS
SELECT
    cl.classroom_id,
    cl.room_number,
    cl.capacity,
    cl.classroom_type,
    cam.address AS campus,
    COUNT(cs.class_schedule_id) AS total_clases_asignadas,
    40 AS total_bloques_disponibles, -- 5 días x 8 bloques de tiempo
    ROUND((COUNT(cs.class_schedule_id) / 40.0) * 100, 1) AS porcentaje_utilizacion,
    -- Distribución por días
    COUNT(CASE WHEN d.name = 'Monday' THEN 1 END) AS clases_lunes,
    COUNT(CASE WHEN d.name = 'Tuesday' THEN 1 END) AS clases_martes,
    COUNT(CASE WHEN d.name = 'Wednesday' THEN 1 END) AS clases_miercoles,
    COUNT(CASE WHEN d.name = 'Thursday' THEN 1 END) AS clases_jueves,
    COUNT(CASE WHEN d.name = 'Friday' THEN 1 END) AS clases_viernes,
    CASE 
        WHEN COUNT(cs.class_schedule_id) = 0 THEN 'SIN USO'
        WHEN (COUNT(cs.class_schedule_id) / 40.0) * 100 < 25 THEN 'BAJA UTILIZACIÓN'
        WHEN (COUNT(cs.class_schedule_id) / 40.0) * 100 < 50 THEN 'UTILIZACIÓN MEDIA'
        WHEN (COUNT(cs.class_schedule_id) / 40.0) * 100 < 75 THEN 'ALTA UTILIZACIÓN'
        ELSE 'UTILIZACIÓN MÁXIMA'
    END AS estado_utilizacion,
    GROUP_CONCAT(DISTINCT dept.name SEPARATOR ', ') AS departamentos_usuarios
FROM classroom cl
JOIN campus cam ON cl.campus_id = cam.campus_id
LEFT JOIN class_schedule cs ON cl.classroom_id = cs.classroom_id
LEFT JOIN day_time_block dtb ON cs.day_time_block_id = dtb.day_time_block_id
LEFT JOIN day d ON dtb.day_id = d.day_id
LEFT JOIN instructor i ON cs.instructor_id = i.instructor_id
LEFT JOIN department dept ON i.department_id = dept.department_id
GROUP BY cl.classroom_id, cl.room_number, cl.capacity, cl.classroom_type, cam.address
ORDER BY porcentaje_utilizacion DESC, cam.address, cl.room_number;

-- ===============================================
-- VISTA 10: DETALLE DE CLASES PROGRAMADAS
-- ===============================================
-- Razón: Vista completa para reportes detallados

CREATE VIEW schedule_detail AS
SELECT
    cs.class_schedule_id,
    cs.subject AS materia,
    CONCAT(i.first_name, ' ', i.last_name) AS instructor,
    sg.group_number AS grupo,
    cl.room_number AS aula,
    cam.address AS campus,
    d.name AS dia,
    TIME_FORMAT(tb.start_time, '%H:%i') AS hora_inicio,
    TIME_FORMAT(tb.end_time, '%H:%i') AS hora_fin,
    tb.duration_minutes AS duracion_minutos,
    (tb.duration_minutes / 60.0) AS duracion_horas,
    q.name AS trimestre
FROM class_schedule cs
JOIN instructor i ON cs.instructor_id = i.instructor_id
JOIN student_group sg ON cs.group_id = sg.group_id
JOIN classroom cl ON cs.classroom_id = cl.classroom_id
JOIN campus cam ON cl.campus_id = cam.campus_id
JOIN day_time_block dtb ON cs.day_time_block_id = dtb.day_time_block_id
JOIN day d ON dtb.day_id = d.day_id
JOIN time_block tb ON dtb.time_block_id = tb.time_block_id
JOIN quarter q ON cs.quarter_id = q.quarter_id
ORDER BY d.day_id, tb.start_time, i.last_name;

SELECT 'Total views created: 10' AS status;
SELECT 'Vistas para programación, búsqueda, disponibilidad, reportes y dashboard ejecutivo' AS description;