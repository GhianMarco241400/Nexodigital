# SalesIA API

Esqueleto del backend de SalesIA, un sistema interno de gestión de ventas.
Construido con FastAPI y SQLAlchemy 2.x, conectado a PostgreSQL en Supabase
(usado únicamente como base de datos).

## Requisitos

- Python 3.11 o superior (probado con 3.14).

## Instalación

Desde PowerShell, en la carpeta del proyecto:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Para desarrollo (pruebas):

```powershell
pip install -r requirements-dev.txt
```

## Configuración

Copia el archivo de ejemplo y coloca tus credenciales reales:

```powershell
Copy-Item .env.example .env
```

Edita `.env` y define:

- `DATABASE_URL`: cadena de conexión a PostgreSQL en Supabase con el driver
  `psycopg`, por ejemplo
  `postgresql+psycopg://postgres.PROYECTO:CONTRASEÑA@HOST.pooler.supabase.com:5432/postgres`.
- `CORS_ORIGINS`: lista de orígenes separados por comas. Por defecto
  `http://localhost:5173,http://localhost:8080`.
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (y opcionalmente
  `AWS_SESSION_TOKEN`): credenciales de solo lectura para la AWS Price List
  Query API. Nunca se versionan.
- `CATALOG_MODE`: modo del catálogo (`simulation` o `live`). El valor guardado
  en la tabla `app_settings` tiene prioridad sobre esta variable.
- `REVIEW_MODE`: motor de la revisión de pedidos con IA (`heuristic`, `llm` o
  `hybrid`). Ver la sección "Revisión de pedidos con IA".
- `REVIEW_PROVIDER`: proveedor por defecto (`gemini`, `groq`, `openrouter`,
  `ollama` u `openai`).
- `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY`:
  clave del proveedor elegido (solo se necesita la del activo). `OLLAMA_BASE_URL`
  no requiere clave. La clave nunca se expone al frontend.

El archivo `.env` no se versiona y nunca debe contener datos en el repositorio.

## Levantar el servidor

Con el entorno virtual activado:

```powershell
uvicorn app.main:app --reload
```

- Documentación interactiva: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Planes: http://localhost:8000/plans

## Infraestructura AWS

Los combos incluyen componentes de infraestructura AWS. El endpoint
`POST /aws/quote` cotiza un combo (`plan_code`) o una lista de servicios en una
región, sumando el costo mensual On-Demand en USD.

- `GET /aws/catalog`: metadatos (modo, aviso, fecha de referencia, divisas).
- `GET /aws/regions`: regiones disponibles con su factor de precio.
- `GET /aws/services`: servicios soportados.
- `POST /aws/quote`: `{ "plan_code": "negocio", "region_code": "us-east-1" }`.

En modo `live` las tarifas provienen de la AWS Price List API (solo lectura);
si un servicio no está soportado o AWS no responde, se usa la tarifa almacenada.

Para sincronizar las tarifas de referencia y activar el modo real:

```powershell
python -m scripts.sync_aws_prices           # dry-run (no escribe)
python -m scripts.sync_aws_prices --apply   # escribe aws_rates y activa live
```

El script solo ejecuta lecturas (`pricing:GetProducts`, `sts:GetCallerIdentity`)
y nunca crea ni modifica recursos AWS. Esas llamadas quedan registradas en
CloudTrail (eventSource `pricing.amazonaws.com`); revísalas en la consola de AWS
(Event history) si tu usuario IAM tiene `cloudtrail:LookupEvents`.

## Revisión de pedidos con IA

Cada pedido puede someterse a una revisión que calcula señales de riesgo
(precio vs. catálogo, margen de infraestructura, RUC, duplicados, datos del
cliente) y produce un veredicto (`risk`, `flags`, `summary`, `recommendation`,
`confidence`). El veredicto se guarda en `order_reviews` y el motor se elige con
`REVIEW_MODE`:

- `heuristic`: solo reglas deterministas (sin red, sin costo).
- `llm`: reglas + resumen redactado por el proveedor de IA.
- `hybrid`: igual que `llm` con degradación automática a `heuristic` si la API
  no responde.

Proveedores soportados (`REVIEW_PROVIDER`): `gemini` (Google, **tier gratis**),
`groq` (tier gratis), `openrouter` (modelos `:free`), `ollama` (local, sin clave)
y `openai` (de pago). Solo el proveedor activo necesita su clave en `.env`.

La IA **solo asesora**: nunca cambia el estado del pedido. Un vendedor o
administrador confirma (→ `confirmado`, que equivale a registrar la venta) o
rechaza con un motivo.

La configuración efectiva se guarda en `app_settings` (BD: `review_mode`,
`review_provider`, `review_model`) y **tiene prioridad** sobre el `.env`, por lo
que se cambia en caliente sin reiniciar (solo `administrador`, desde la UI de
SalesIA o vía API):

- `GET /settings/review`: estado (`mode`, `provider`, `model`, `has_api_key`).
- `PUT /settings/review`: `{ "mode"?, "provider"?, "model"? }`.
- `POST /settings/review/test`: prueba de conexión con el proveedor activo.

Para activar la IA por primera vez hay que pegar la clave del proveedor elegido
en `.env` (p. ej. `GEMINI_API_KEY` de https://aistudio.google.com/apikey) y
reiniciar una vez; después, encender/apagar no requiere reinicio.

- `POST /orders/{code}/review`: ejecuta la revisión (roles `administrador`,
  `vendedor`, `analista`).
- `POST /orders/{code}/confirm`: confirma la venta (roles `administrador`,
  `vendedor`).
- `POST /orders/{code}/reject`: rechaza con `{ "reason": "..." }`.

## Pruebas

```powershell
pytest
```

La prueba `tests/test_health.py` llama a `/health`. Si la base de datos no está
disponible, la prueba se marca como omitida (skip) en lugar de fallar.
