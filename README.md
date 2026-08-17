<h1 align="center">Notion Automatizaciones</h1>
<p align="center"><b>Gestión financiera en Notion + automatizaciones Python + demo pública interactiva.</b></p>
<p align="center"><a href="https://andrefnx.github.io/Notion_Automatizaciones/"><b>▶ Abrir demo interactiva</b></a> · <a href="./DOCUMENTATION.md">Documentación</a></p>

> La demo pública es una **simulación visual segura de una plantilla de Notion**. Funciona completamente en el navegador con datos ficticios y no tiene acceso al workspace, tokens, IDs, cuentas ni información financiera real.

## Qué demuestra el proyecto

El repositorio automatiza tareas repetitivas de una plantilla financiera: preparación de períodos, pagos programados y generación de cuotas. La interfaz React permite enseñar ese comportamiento sin exponer una integración privada.

En la demo puedes navegar entre **Inicio, Movimientos, Presupuesto mensual, Gastos programados, Categorías y Cuentas**, abrir registros como páginas laterales, crear movimientos, filtrar vistas y ver los totales recalcularse inmediatamente.

Las compras en cuotas se distribuyen automáticamente entre meses. Por ejemplo, un gasto de `$600.000` en 6 cuotas genera `1/6`, `2/6` … `6/6` en seis períodos consecutivos y cada cuota afecta únicamente el presupuesto del mes correspondiente.

## Dos capas separadas

### Automatización real

```text
Python + requests
        ↓
    Notion API
        ↓
Bases de datos / períodos / movimientos
```

Los scripts Python leen configuración privada desde variables de entorno y realizan operaciones contra la API de Notion. `credit_payment.py` prepara pagos asociados a cuentas y `cuotas_generator.py` genera registros mensuales de cuotas. La capa reutilizable en `notion_automation/` incorpora cliente HTTP, paginación, reintentos y manejo de errores.

### Demo pública

```text
   React Demo
        ↓
  Datos ficticios
        ↓
Simulación pública
```

La demo **no llama a Notion**. Usa estado React y `localStorage` para conservar durante la sesión los movimientos y cambios realizados en el navegador. La opción **Restablecer demo** vuelve a cargar el dataset ficticio original.

## Funcionalidades de la demo

- navegación real mediante sidebar estilo Notion;
- dashboard con ingresos, gastos, disponible y cuotas pendientes;
- base de datos de movimientos con vistas Todos / Ingresos / Gastos / Cuotas;
- filas clickeables que se abren como páginas laterales;
- creación y edición de movimientos;
- tipos Ingreso, Gasto y Ahorro;
- compra en cuotas con monto total, cantidad y fecha de primera cuota;
- navegación mensual con flechas y cálculo dinámico por período;
- gastos programados editables y creación de nuevas reglas ficticias;
- categorías navegables;
- cuentas ficticias con saldos derivados de movimientos;
- simulación visual de automatización mensual;
- persistencia local con `localStorage`;
- diseño responsive con menú móvil.

## Automatización mensual simulada

El botón **Ejecutar demostración** muestra el flujo:

```text
Creando período...
Registrando ingreso programado...
Replicando gastos...
Generando cuotas...
Actualizando estados...
Completado.
```

Al terminar, la interfaz prepara el siguiente período, crea un sueldo ficticio y replica los gastos programados activos. Las cuotas ya creadas continúan apareciendo en el mes que les corresponde.

## Arquitectura

```text
main.py                     Entrada segura de la capa Python
notion_automation/
  config.py                 Variables de entorno y validación
  client.py                 Cliente HTTP para Notion API
  demo.py                   Ejecución local segura
credit_payment.py           Automatización histórica de pagos
cuotas_generator.py         Automatización histórica de cuotas

demo/
  data.json                 Dataset 100% ficticio
  src/main.jsx              Workspace React interactivo
  src/style.css             Apariencia estilo Notion
  vite.config.js            Base path de GitHub Pages

.github/workflows/pages.yml Build y despliegue de la demo
```

## Ejecutar localmente

### Python

```bash
python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
python main.py --demo
```

### React

```bash
cd demo
npm install
npm run dev
```

Build de producción:

```bash
npm run build
```

## GitHub Pages

La demo se publica en:

**https://andrefnx.github.io/Notion_Automatizaciones/**

`demo/vite.config.js` usa el base path `/Notion_Automatizaciones/`. El workflow de Pages se ejecuta automáticamente con cambios de la demo en `main` y también puede iniciarse manualmente con `workflow_dispatch`. El build y el deploy están separados y se sube un único artifact de Pages.

## Seguridad

- datos públicos exclusivamente ficticios;
- sin conexión de la demo React a Notion;
- sin tokens ni IDs privados en la interfaz;
- `.env` ignorado por Git;
- conexión real opt-in mediante variables de entorno;
- workflows históricos de escritura separados de la demo pública;
- branch de respaldo previa a esta reconstrucción: `backup/pre-interactive-demo-2026-08-17`.
