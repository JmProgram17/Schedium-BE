# 🚀 Schedium - Sistema Containerizado

## 📋 Resumen del Sistema

**Schedium** es un sistema completo de programación académica containerizado con Docker, que incluye:

- **Backend API**: FastAPI con autenticación y autorización
- **Base de Datos**: MySQL 8.0 con 19 tablas, 9 triggers y 10 vistas
- **Cache**: Redis para sesiones y rate limiting
- **Proxy**: Nginx (opcional para producción)

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │────│   Nginx         │────│   FastAPI       │
│   (Externo)     │    │   (Proxy)       │    │   (Backend)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Redis         │────│   MySQL 8.0     │
                       │   (Cache)       │    │   (Database)    │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Inicio Rápido

### 1. Levantar el Sistema Completo

```bash
# Usar puertos por defecto (puede haber conflictos)
docker compose up -d

# O usar puertos alternativos (recomendado)
DB_PORT=3307 REDIS_PORT=6380 API_PORT=8001 docker compose up -d
```

### 2. Verificar Estado de los Servicios

```bash
docker compose ps
```

### 3. Acceder a los Servicios

- **API**: http://localhost:8001
- **Documentación**: http://localhost:8001/api/v1/docs
- **Health Check**: http://localhost:8001/health
- **MySQL**: localhost:3307 (usuario: `root`, password: `rootpassword123`)
- **Redis**: localhost:6380

## 📊 Base de Datos

### Estructura de la Base de Datos

```
schedium/
├── 19 Tablas Principales
├── 1 Tabla de Auditoría
├── 9 Triggers de Control
└── 10 Vistas Especializadas
```

### 🔧 Triggers Implementados

1. **`validate_schedule_conflicts`** - Previene conflictos de horarios
2. **`validate_classroom_capacity`** - Valida capacidad de aulas
3. **`check_instructor_hour_limit`** - Controla límites contractuales
4. **`update_instructor_hours_insert`** - Suma horas automáticamente
5. **`update_instructor_hours_delete`** - Resta horas automáticamente
6. **`update_instructor_hours_update`** - Ajusta horas en modificaciones
7. **`audit_class_schedule_insert`** - Auditoría de nuevas clases
8. **`audit_class_schedule_update`** - Auditoría de modificaciones
9. **`audit_class_schedule_delete`** - Auditoría de eliminaciones

### 📈 Vistas Disponibles

1. **`view_schedule_matrix`** - Matriz de horarios semanal
2. **`view_instructor_schedule`** - Programación por instructor
3. **`view_classroom_schedule`** - Programación por aula
4. **`view_group_schedule`** - Horarios por grupo/ficha
5. **`view_instructor_availability`** - Disponibilidad de instructores
6. **`view_classroom_availability`** - Disponibilidad de aulas
7. **`view_instructor_workload`** - Carga horaria por instructor
8. **`view_general_search`** - Búsqueda unificada
9. **`view_executive_summary`** - Dashboard ejecutivo
10. **`view_classroom_utilization`** - Utilización de aulas

## 👥 Usuarios del Sistema

### Usuarios Pre-configurados

| Usuario | Email | Password | Rol |
|---------|-------|----------|-----|
| Admin Sistema | `admin@schedium.edu` | `admin123` | Administrator |
| Coordinador Académico | `coordinador@schedium.edu` | `coord123` | Coordinator |

### Instructores de Muestra

- **Juan Pérez** - `juan.perez@schedium.edu` (Departamento de Sistemas)
- **María García** - `maria.garcia@schedium.edu` (Departamento de Administración)
- **Carlos López** - `carlos.lopez@schedium.edu` (Departamento de Inglés)
- **Ana Martínez** - `ana.martinez@schedium.edu` (Departamento de Sistemas)

## 🏢 Datos de Muestra

### Campus
- **Campus Principal** - Calle 123
- **Campus Norte** - Av. 456

### Aulas Disponibles
- **Aula 101** (30 estudiantes) - Campus Principal
- **Lab 102** (25 estudiantes) - Campus Principal
- **Aula 201** (35 estudiantes) - Campus Principal
- **Lab 301** (20 estudiantes) - Campus Norte
- **Aula 302** (40 estudiantes) - Campus Norte

### Programas Académicos
- **ADSI** - Análisis y Desarrollo de Sistemas de Información (Tecnólogo)
- **CONT** - Contabilidad y Finanzas (Técnico)
- **ING** - Inglés Técnico (Técnico)

## 🔧 Administración del Sistema

### Comandos Útiles

```bash
# Ver logs de un servicio específico
docker logs schedium-mysql --tail 50
docker logs schedium-api --tail 50
docker logs schedium-redis --tail 50

# Acceder a la base de datos
docker exec -it schedium-mysql mysql -uroot -prootpassword123 schedium

# Acceder al contenedor de la API
docker exec -it schedium-api bash

# Reiniciar un servicio específico
docker compose restart mysql
docker compose restart api
docker compose restart redis

# Detener todo el sistema
docker compose down

# Detener y eliminar volúmenes (CUIDADO: Borra todos los datos)
docker compose down -v
```

### Backup de la Base de Datos

```bash
# Crear backup
docker exec schedium-mysql mysqldump -uroot -prootpassword123 schedium > schedium_backup.sql

# Restaurar backup
docker exec -i schedium-mysql mysql -uroot -prootpassword123 schedium < schedium_backup.sql
```

## 🔍 Verificación del Sistema

### Health Checks

```bash
# API Health
curl http://localhost:8001/health

# MySQL Connection
docker exec schedium-mysql mysql -uroot -prootpassword123 -e "SELECT 'MySQL OK' as status;"

# Redis Connection
docker exec schedium-redis redis-cli ping
```

### Verificar Integridad de la Base de Datos

```bash
# Contar elementos importantes
docker exec schedium-mysql mysql -uroot -prootpassword123 schedium -e "
SELECT 'Tables' as item, COUNT(*) as count FROM information_schema.tables WHERE table_schema = 'schedium'
UNION ALL
SELECT 'Triggers', COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = 'schedium'
UNION ALL
SELECT 'Views', COUNT(*) FROM information_schema.VIEWS WHERE TABLE_SCHEMA = 'schedium'
UNION ALL
SELECT 'Users', COUNT(*) FROM user
UNION ALL
SELECT 'Instructors', COUNT(*) FROM instructor
UNION ALL
SELECT 'Classrooms', COUNT(*) FROM classroom;"
```

## 🚨 Solución de Problemas

### Problemas Comunes

1. **Puerto en uso**: Cambiar puertos usando variables de entorno
2. **Contenedor no inicia**: Verificar logs con `docker logs [container_name]`
3. **Base de datos no inicializa**: Eliminar volúmenes y recrear
4. **API no conecta a DB**: Verificar health checks de MySQL

### Variables de Entorno Importantes

```env
# Puertos alternativos
DB_PORT=3307
REDIS_PORT=6380
API_PORT=8001

# Credenciales de base de datos
DB_ROOT_PASSWORD=rootpassword123
DB_USER=schedium_user
DB_PASSWORD=schedium_password123
DB_NAME=schedium

# Configuración de la aplicación
SECRET_KEY=super-secret-key-change-this-in-production-32-chars-minimum
DEBUG=true
APP_ENV=development
```

## 📁 Estructura de Archivos

```
schedium-be/
├── docker-compose.yml          # Configuración de servicios
├── Dockerfile                  # Imagen de la API
├── requirements.txt            # Dependencias Python
├── app/                        # Código fuente de la API
├── scripts/                    # Scripts de utilidad
│   └── database/               # Scripts de base de datos
│       ├── 01-database-schema.sql
│       ├── 02-initial-data.sql
│       ├── 03-triggers.sql
│       └── 04-views.sql
├── tests/                      # Pruebas automatizadas
└── docs/                       # Documentación
```

## 🎯 Próximos Pasos

1. **Conectar Frontend**: El sistema está listo para recibir peticiones
2. **Configurar Nginx**: Para producción con SSL
3. **Agregar Monitoreo**: Prometheus/Grafana
4. **Configurar CI/CD**: Para despliegues automatizados
5. **Implementar Backup Automático**: Para datos críticos

---

¡El sistema Schedium está completamente funcional y listo para ser usado! 🎉