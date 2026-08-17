

<h1 align="center">Notion Automatizaciones</h1>
<p align="center"><b>Plantilla visual de gestión financiera mensual + automatización real con Python y Notion API.</b></p>
<p align="center">
  <a href="https://andrefnx.github.io/Notion_Automatizaciones/"><b>Ver demo</b></a> ·
  <a href="./DOCUMENTATION.md">Documentación</a>
</p>

> La versión pública se presenta como una **plantilla de Notion navegable**. Todos los movimientos, montos, nombres y fechas de la demostración son ficticios. No contiene tokens, IDs de bases/data sources ni información financiera personal.

## Qué automatiza

El proyecto convierte tareas repetitivas de una plantilla financiera de Notion en procesos reproducibles. Al comenzar un período puede preparar la página del mes, registrar el sueldo, replicar gastos programados y generar las cuotas correspondientes a compras anteriores, conservando su organización por categorías.

La demostración visual reproduce el flujo de una plantilla real de Notion: barra lateral, portada, página mensual, vistas de base de datos, grupos por mes, propiedades y etiquetas. El botón **Ejecutar demostración** simula la automatización completamente en el navegador y sin credenciales.

### Flujo representado

- crea/prepara un nuevo período mensual;
- registra ingresos programados como el sueldo;
- replica gastos recurrentes del mes;
- genera cuotas futuras de compras;
- conserva categorías y relaciones;
- muestra estado, ejecución y errores simulados;
- evita exponer cualquier dato real del proyecto original.

## Arquitectura

```text
main.py                     Entrada segura: demo por defecto
notion_automation/
  config.py                 Validación de variables de entorno
  client.py                 Cliente HTTP, paginación, reintentos y errores
  demo.py                   Ejecución local sin credenciales
demo/
  data.json                 Dataset 100% ficticio
  src/                      Plantilla visual React estilo Notion
docs/
  notion-template-cover.svg Portada pública del proyecto
tests/                      Pruebas con respuestas simuladas
.github/workflows/          Validación, Pages y scripts manuales
credit_payment.py           Automatización existente de pagos programados
cuotas_generator.py         Automatización existente de cuotas
```

El cliente reutilizable usa `Notion-Version: 2025-09-03` y consulta registros mediante `POST /v1/data_sources/{data_source_id}/query`. Incluye paginación con `has_more`/`next_cursor`, timeout, manejo de JSON inválido, errores HTTP y reintentos ante `429` y errores transitorios `5xx`.

## Instalación local

Requiere Python 3.11+.

```bash
python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py --demo
```

El modo demo funciona sin token y sin conexión a Notion.

## Demo navegable

```bash
cd demo
npm install
npm run dev
```

Para comprobar el build:

```bash
npm run build
```

La interfaz está diseñada intencionalmente para sentirse como una **plantilla de Notion** y no como un dashboard SaaS independiente. Los montos se muestran ficticios o visualmente censurados.

## Variables de entorno

Copia `.env.example` a `.env` solamente si vas a conectar tu propia integración privada.

```text
NOTION_TOKEN=
NOTION_MOVIMIENTOS_DATA_SOURCE_ID=
NOTION_CUENTAS_DATA_SOURCE_ID=
NOTION_PRESUPUESTO_DATA_SOURCE_ID=
DRY_RUN=true
```

`.env` está ignorado por Git. Mantén `DRY_RUN=true` mientras validas la configuración.

## Conexión real con Notion

La capa nueva está preparada para la API `2025-09-03`. Comparte tu integración únicamente con los data sources necesarios, configura las variables privadas y valida sin escribir:

```bash
python main.py --real
```

Con `DRY_RUN=true`, el comando valida configuración sin ejecutar escrituras. Los módulos históricos permanecen separados para no romper su comportamiento existente y deben revisarse antes de usarlos contra una base real.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Las pruebas no llaman a Notion: simulan paginación, rate limiting y respuestas JSON inválidas.

## GitHub Actions y Pages

`Manual validation` se ejecuta exclusivamente mediante `workflow_dispatch` y comprueba tests, demo Python y build React. Los workflows históricos también quedaron manuales para evitar modificaciones automáticas sobre una base real.

Para configurar secretos: **Settings → Secrets and variables → Actions → New repository secret**. Nunca copies tokens o IDs en código, README, issues o logs.

`Deploy demo to Pages` compila `demo/` y publica `demo/dist`. En **Settings → Pages**, selecciona **GitHub Actions** como fuente y ejecuta manualmente el workflow de despliegue.

## Seguridad de la versión pública

- Demo con datos ficticios y montos censurados.
- Sin credenciales ni IDs reales.
- Sin exports privados de Notion versionados.
- Demo por defecto; conexión real opt-in.
- Ningún workflow de escritura se ejecuta por cron.
- Existe una branch de respaldo previa a la conversión pública.
