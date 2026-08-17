# Notion Automatizaciones

Automatización financiera construida con **Python + requests + Notion API**. El proyecto nació para evitar trabajo manual repetitivo en una base de movimientos: preparar cada período mensual, registrar ingresos programados, replicar gastos recurrentes y generar vencimientos de compras en cuotas.

> La demo pública usa exclusivamente datos ficticios. No contiene tokens, IDs de bases/data sources ni información financiera personal.

## Qué problema resuelve

Un control financiero en Notion puede requerir crear todos los meses las mismas filas y páginas: sueldo, arriendo, suscripciones, pagos programados y cuotas. Esta automatización convierte esas reglas repetitivas en procesos reproducibles y deja la información lista para revisar en Notion.

Ejemplos del flujo original:

- creación y preparación del período mensual;
- ingresos programados como sueldo;
- gastos recurrentes y pagos de cuentas;
- generación de cuotas mensuales a partir de una compra;
- conservación de relaciones con cuenta/categoría;
- marcado del registro de origen cuando las cuotas ya fueron generadas.

## Arquitectura

```text
main.py                     Entrada segura: demo por defecto
notion_automation/
  config.py                 Validación de variables de entorno
  client.py                 Cliente HTTP, paginación, reintentos y errores
  demo.py                   Ejecución local sin credenciales
demo/
  data.json                 Dataset 100% ficticio
  src/                      Interfaz React
tests/                      Pruebas con respuestas simuladas
.github/workflows/          Validación, Pages y scripts legacy manuales
credit_payment.py           Automatización existente de pagos programados
cuotas_generator.py         Automatización existente de cuotas
```

El cliente reutilizable usa `Notion-Version: 2025-09-03` y consulta registros con `POST /v1/data_sources/{data_source_id}/query`. Incluye paginación mediante `has_more`/`next_cursor`, timeout, manejo de JSON inválido, errores HTTP y reintentos para `429` y errores transitorios `5xx`.

## Instalación local

Requiere Python 3.11+.

```bash
python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

El punto de entrada documentado ahora sí existe. La ejecución predeterminada es segura y abre el modo demo:

```bash
python main.py
# equivalente
python main.py --demo
```

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores solamente para trabajar con tu propia integración privada.

```text
NOTION_TOKEN=
NOTION_MOVIMIENTOS_DATA_SOURCE_ID=
NOTION_CUENTAS_DATA_SOURCE_ID=
NOTION_PRESUPUESTO_DATA_SOURCE_ID=
DRY_RUN=true
```

`.env` está ignorado por Git. Mantén `DRY_RUN=true` mientras validas la configuración.

## Modo demo

No requiere token ni conexión a Notion:

```bash
python main.py --demo
```

La interfaz navegable usa el mismo dataset ficticio y permite simular una ejecución:

```bash
cd demo
npm install
npm run dev
```

Para comprobar el build:

```bash
npm run build
```

La demo muestra automatizaciones, cantidad de registros procesados, estado, fecha de ejecución, movimientos ficticios y un error `429` simulado para explicar la estrategia de reintento.

## Conexión real con Notion

La capa nueva está preparada para la API `2025-09-03`. Primero comparte la integración con los data sources necesarios y obtiene sus IDs desde Notion. Después configura las variables privadas y valida sin escribir:

```bash
python main.py --real
```

Con `DRY_RUN=true`, el comando únicamente valida configuración. `main.py` no habilita escrituras reales automáticamente. Los módulos históricos permanecen separados para no romper el comportamiento existente y deben revisarse antes de ejecutarlos contra una base real.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Las pruebas no llaman a Notion: simulan paginación, rate limiting y respuestas JSON inválidas.

## GitHub Actions

`Manual validation` se ejecuta exclusivamente con `workflow_dispatch` y comprueba tests, demo Python y build React. Los workflows históricos también quedaron en ejecución manual para evitar modificaciones automáticas sobre una base real.

Para configurar secretos: abre **Settings → Secrets and variables → Actions → New repository secret** y crea únicamente los secretos requeridos por el workflow que hayas revisado. Nunca copies tokens o IDs en el código, README, issues o logs.

`Deploy demo to Pages` compila `demo/` y publica `demo/dist` mediante GitHub Pages. Se inicia manualmente desde **Actions**. En **Settings → Pages**, usa **GitHub Actions** como fuente de publicación.

## Capturas del proyecto real

Las capturas del proyecto original pueden incorporarse al portfolio únicamente después de ocultar montos, nombres de cuentas, identificadores y cualquier dato personal. Para la demostración pública, la interfaz React es la fuente principal porque todos sus registros son ficticios.

## Demo pública

Una vez habilitado GitHub Pages y ejecutado el workflow de despliegue, la demo quedará disponible en el sitio de Pages del repositorio.

## Seguridad

- Sin credenciales en la demo.
- Sin IDs reales en `.env.example`.
- Sin exports privados de Notion versionados en la rama pública.
- Demo por defecto y conexión real opt-in.
- Ningún workflow de escritura se ejecuta por cron.
