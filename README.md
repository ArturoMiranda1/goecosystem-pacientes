# GoEcosystem — Seguimiento de pacientes

Aplicación web para gestionar pacientes pendientes de atención médica.

Permite iniciar sesión, consultar indicadores operativos, buscar pacientes,
filtrar por estado y prioridad, y crear, editar o eliminar registros.

Desarrollada como parte de una prueba técnica. Todos los datos suministrados
son sintéticos; no se utilizan datos reales de pacientes.

## Tecnologías

- Python y FastAPI: API REST.
- Pydantic: validación de datos.
- SQLAlchemy: acceso y modelado de base de datos.
- SQLite: persistencia local.
- PyJWT: generación y validación de tokens JWT.
- pwdlib con Argon2: hashes de contraseñas.
- openpyxl: lectura del archivo Excel.
- HTML, CSS y JavaScript: interfaz web sin proceso de compilación.

## Requisitos

- Python 3.10 o superior.
- Git.
- Navegador web actualizado.
- Acceso a internet para instalar las dependencias.

La aplicación se desarrolló y probó manualmente en macOS con Python 3.14.

No requiere instalar un servidor de base de datos: SQLite utiliza un archivo local.

## Instalación

Los siguientes comandos están orientados a macOS y Linux.

### 1. Clonar el repositorio

```bash
git clone https://github.com/ArturoMiranda1/goecosystem-pacientes.git
cd goecosystem-pacientes
```

### 2. Crear y activar el entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copiar el archivo de ejemplo:

```bash
cp .env.example .env
```

Generar una clave aleatoria:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Editar `.env` e introducir el valor generado:

```dotenv
JWT_SECRET_KEY=CLAVE_ALEATORIA_GENERADA
```

La aplicación requiere una clave de al menos 32 caracteres.

El archivo `.env` está excluido de Git. No se deben publicar claves reales.
Cambiar la clave invalida los tokens emitidos anteriormente.

### 5. Crear la base de datos

```bash
python -m app.init_db
```

Se genera el archivo:

```text
data/patients.db
```

El comando crea las tablas que falten. No modifica la estructura de tablas
existentes ni constituye un sistema de migraciones.

### 6. Cargar los datos sintéticos

El archivo suministrado debe encontrarse en:

```text
data/Datos_Sinteticos_Prueba_2026.xlsx
```

Ejecutar:

```bash
python -m app.seed
```

En una base vacía, la carga incorpora:

- 10 EPS.
- 2 usuarios de demostración.
- 1.000 pacientes.

La importación utiliza las hojas `Catalogos`, `Usuarios_Login` y `Pacientes`.

Las contraseñas demo se convierten a hashes Argon2 antes de almacenarse.

La carga se ejecuta en una transacción: si falla un registro, se revierten
las inserciones de esa ejecución.

Puede repetirse sin duplicar registros. Omite EPS por código, usuarios por
nombre de usuario y pacientes por documento cuando ya existen.

Los registros existentes no se actualizan al repetir la importación.
El identificador interno del paciente lo genera SQLite; no se conserva
necesariamente el `paciente_id` del Excel.

## Ejecución

Desde la raíz del proyecto y con el entorno virtual activo:

```bash
python -m uvicorn app.main:app --reload
```

Direcciones locales:

- Aplicación web: http://127.0.0.1:8000
- Documentación interactiva: http://127.0.0.1:8000/docs
- Especificación OpenAPI: http://127.0.0.1:8000/openapi.json
- Estado del servicio: http://127.0.0.1:8000/health

Para detener el servidor, presionar `Ctrl + C`.

`--reload` se utiliza para desarrollo local.

## Credenciales de demostración

| Usuario | Contraseña | Rol |
|---|---|---|
| admin.demo | Demo2026* | ADMIN |
| operador.demo | Demo2026* | OPERADOR |

Estas credenciales son públicas y exclusivas de demostración.

Ambos usuarios deben estar activos. En esta versión, los dos roles tienen
los mismos permisos sobre el módulo de pacientes.

## Cobertura de historias de usuario

| Historia de usuario | Funcionalidad implementada |
|---|---|
| Iniciar sesión para acceder al módulo | Login con credenciales, JWT y protección de endpoints |
| Consultar y buscar pacientes | Listado paginado, búsqueda por nombre o documento y filtros |
| Registrar y actualizar pacientes | Formulario de creación y edición con validaciones |
| Cambiar estado y prioridad | Edición de ambos campos desde el formulario del paciente |
| Consultar indicadores del servicio | Dashboard global con totales por estado y prioridad alta |

El cambio de estado y prioridad se realiza desde la acción «Editar».
Después de guardar, se actualizan el listado y los indicadores.


## Funcionalidades

### Inicio de sesión

- Validación contra usuarios almacenados en SQLite.
- Verificación de contraseñas mediante hashes Argon2.
- Emisión de tokens JWT con vencimiento de 60 minutos.
- Validación de firma, vencimiento y estado activo del usuario.
- Cierre de sesión desde la interfaz.

### Dashboard

Muestra indicadores globales:

- Pacientes registrados.
- Pacientes pendientes.
- Pacientes en atención.
- Pacientes atendidos.
- Pacientes con prioridad alta.

Los indicadores incluyen todos los registros y no dependen de los filtros
del listado.

La prioridad alta se cuenta en cualquier estado, incluidos los pacientes
atendidos.

### Gestión de pacientes

- Creación, consulta, edición y eliminación.
- Búsqueda por nombre o documento.
- Filtros combinables por estado y prioridad.
- Paginación de 20 registros en la interfaz.
- Selección de EPS desde el catálogo almacenado.
- Mensajes de éxito y error.
- Confirmación antes de eliminar.
- Actualización de indicadores después de las operaciones.

### Validaciones

- Nombre obligatorio con longitud entre 2 y 150 caracteres.
- Documento obligatorio y único.
- Documento almacenado como texto para preservar ceros iniciales.
- Fecha de nacimiento no futura.
- Género, tipo de documento, prioridad y estado controlados.
- Teléfono con validación básica de caracteres y entre 7 y 15 dígitos.
- EPS existente.
- Correo opcional con validación básica de formato.
- Rechazo de campos inesperados en las solicitudes.

Las validaciones de entrada se aplican mediante Pydantic en la API.
La base de datos refuerza unicidad, relaciones y valores controlados.
El importador incorpora validaciones propias y restricciones de la base;
no utiliza todos los esquemas de validación de la API.

## API REST

Los endpoints de pacientes, dashboard y catálogos requieren:

```http
Authorization: Bearer TOKEN
```

| Método | Ruta | Descripción | Requiere token |
|---|---|---|---|
| POST | /auth/login | Iniciar sesión | No |
| GET | /auth/me | Consultar el usuario autenticado | Sí |
| GET | /patients | Listar y filtrar pacientes | Sí |
| GET | /patients/{patient_id} | Consultar un paciente | Sí |
| POST | /patients | Crear un paciente | Sí |
| PUT | /patients/{patient_id} | Actualizar un paciente | Sí |
| DELETE | /patients/{patient_id} | Eliminar un paciente | Sí |
| GET | /dashboard | Consultar indicadores | Sí |
| GET | /catalogs/eps | Consultar catálogo de EPS | Sí |
| GET | /health | Consultar estado básico del servicio | No |

### Autenticación desde Swagger

1. Ejecutar `POST /auth/login` con:

```json
{
  "username": "admin.demo",
  "password": "Demo2026*"
}
```

2. Copiar el valor de `access_token`.
3. Pulsar `Authorize`.
4. Pegar únicamente el token, sin añadir `Bearer`.
5. Ejecutar los endpoints protegidos.

### Parámetros del listado

Ejemplo:

```text
GET /patients?search=Mateo&status=Pendiente&priority=Alta&page=1&page_size=20
```

| Parámetro | Descripción |
|---|---|
| search | Coincidencia parcial en nombre o documento |
| status | Pendiente, En atención o Atendido |
| priority | Alta, Media o Baja |
| page | Número de página, mínimo 1 |
| page_size | Registros por página, entre 1 y 100 |

El listado se ordena por identificador descendente.

Su respuesta contiene `items`, `total`, `page` y `page_size`.

### Ejemplo de creación o actualización

```json
{
  "document_type": "CC",
  "document": "NUEVA DEMO-PRUEBA-001",
  "full_name": "Paciente de prueba Extra",
  "birth_date": "1995-05-27",
  "gender": "Masculino",
  "phone": "3001234564",
  "email": "pacienteejemplo@example.test",
  "city": "Pereira",
  "eps_code": "EPS001",
  "priority": "Alta",
  "status": "Pendiente"
}
```

`PUT` recibe la representación completa de los campos editables del paciente.
Los campos opcionales omitidos quedan en `null`, y los valores predeterminados
de prioridad y estado se aplican cuando no se envían.

`id`, `created_at` y `updated_at` son administrados por el servidor.

### Respuestas principales

| Código | Significado |
|---|---|
| 200 | Consulta o actualización correcta |
| 201 | Paciente creado |
| 204 | Paciente eliminado; respuesta sin contenido |
| 401 | Credenciales incorrectas o token ausente, inválido o expirado |
| 404 | Paciente no encontrado |
| 409 | Documento duplicado o conflicto de integridad |
| 422 | Datos o parámetros inválidos |

## Modelo de datos

### users

| Campo | Propósito |
|---|---|
| id | Clave primaria |
| username | Nombre de usuario único |
| full_name | Nombre visible |
| password_hash | Hash de contraseña |
| role | ADMIN u OPERADOR |
| active | Habilitación del acceso |

### eps

| Campo | Propósito |
|---|---|
| code | Clave primaria del catálogo |
| name | Nombre único de la EPS |

### patients

| Campo | Propósito |
|---|---|
| id | Clave primaria generada por SQLite |
| document_type | CC, TI, CE o PA |
| document | Documento único |
| full_name | Nombre completo |
| birth_date | Fecha de nacimiento |
| gender | Género del catálogo |
| phone | Teléfono |
| email | Correo opcional |
| city | Ciudad opcional |
| eps_code | Clave foránea a eps.code |
| priority | Alta, Media o Baja |
| status | Pendiente, En atención o Atendido |
| created_at | Fecha de creación |
| updated_at | Fecha de actualización |

Una EPS puede estar asociada con muchos pacientes. Cada paciente debe tener
una EPS válida.

No se repite `eps_nombre` en la tabla de pacientes: se obtiene mediante la
relación con el catálogo.

La unicidad del documento es global, independientemente del tipo de documento,
siguiendo la regla de documento único de esta prueba.

Las claves foráneas de SQLite se habilitan en cada conexión.
Se impide eliminar una EPS que tenga pacientes asociados.

## Estructura del proyecto

```text
app/
    __init__.py
    main.py
    database.py
    models.py
    schemas.py
    security.py
    auth.py
    patients.py
    dashboard.py
    catalogs.py
    init_db.py
    seed.py
    static/
        index.html
        styles.css
        app.js
data/
    Datos_Sinteticos_Prueba_2026.xlsx
tests/
.env.example
.gitignore
requirements.txt
README.md
```

`data/patients.db`, `.env` y el entorno virtual se generan localmente y no se
incluyen en el repositorio.

## Decisiones técnicas

- **FastAPI:** permite implementar la API con validaciones y documentación
  OpenAPI integradas.
- **SQLite:** reduce los requisitos de instalación para una aplicación local
  de demostración.
- **SQLAlchemy:** organiza las entidades, consultas y transacciones.
- **Pydantic:** separa la validación de solicitudes de la persistencia.
- **Frontend sin framework:** permite desarrollar una interfaz funcional sin
  agregar un proceso de compilación.
- **Mismo origen:** FastAPI sirve la interfaz y la API, simplificando su ejecución.
- **JWT con HS256:** autenticación sencilla con algoritmo de verificación
  explícito y clave configurable.
- **Argon2:** las contraseñas se almacenan como hashes.
- **Catálogo de EPS separado:** evita duplicación y mantiene integridad referencial.
- **Paginación:** limita la cantidad de pacientes devueltos por solicitud.
- **Eliminación física:** simplifica el alcance solicitado; requiere confirmación
  en la interfaz.
- **Carga reproducible:** la base se puede reconstruir con el inicializador y
  el Excel suministrado.

## Validación realizada

Se realizaron pruebas manuales desde Swagger y la interfaz web:

- Login válido e inválido.
- Acceso protegido con y sin token.
- Consulta del usuario autenticado.
- Importación repetida sin duplicación.
- Creación, consulta, edición y eliminación de pacientes.
- Rechazo de documentos duplicados.
- Rechazo de EPS inexistentes.
- Rechazo de fechas de nacimiento futuras.
- Validación de límites de paginación.
- Búsquedas y filtros.
- Confirmación y cancelación de eliminación.
- Actualización de indicadores tras modificar los datos.
- Consulta del catálogo de EPS.
- Cierre de sesión.

La validación descrita es manual. Aunque se incluyen herramientas para pruebas
en las dependencias, esta versión todavía no incorpora una suite automatizada.

## Limitaciones conocidas

- Aplicación de demostración local; no está preparada como despliegue productivo.
- SQLite tiene limitaciones para escenarios de alta concurrencia de escrituras.
- Los roles se almacenan, pero no tienen permisos diferenciados.
- No existe registro de usuarios, recuperación de contraseñas ni renovación
  automática de tokens.
- El cierre de sesión elimina el token del navegador, pero no lo revoca en el
  servidor. Un token copiado puede seguir siendo válido hasta su vencimiento,
  mientras el usuario siga activo.
- El token se guarda en `sessionStorage`, accesible al JavaScript de la página.
  Para producción se debe revisar la estrategia de sesión y protección contra XSS.
- No se implementan limitación de intentos de login, auditoría ni historial de cambios.
- La eliminación de pacientes es permanente.
- La búsqueda no normaliza acentos. La comparación sin distinguir mayúsculas de
  SQLite funciona principalmente con caracteres ASCII.
- La validación de teléfono y correo es básica; no verifica que existan.
- No hay control de edición concurrente: la última actualización guardada prevalece.
- No se utilizan migraciones versionadas. `init_db` crea tablas faltantes, pero
  no actualiza estructuras existentes.
- Las dependencias no están fijadas a versiones exactas.
- No se ha verificado compatibilidad en otros sistemas operativos o versiones
  de Python distintas al entorno de desarrollo.
- `/health` informa que el servicio responde; no comprueba la conexión a la base.
- Los indicadores representan registros de pacientes, no un historial de episodios
  o citas médicas.

## Uso de herramientas de inteligencia artificial

Se utilizó ChatGPT como apoyo para estructurar la solución, generar propuestas
de código, identificar errores y preparar documentación.

El código se incorporó y revisó durante el desarrollo, y su comportamiento
se comprobó mediante pruebas manuales. Las decisiones técnicas y la validación
de la entrega son responsabilidad del candidato.