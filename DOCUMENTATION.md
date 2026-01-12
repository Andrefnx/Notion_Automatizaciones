# Cuotas Generator - Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [How It Works](#how-it-works)
3. [Python Script Breakdown](#python-script-breakdown)
4. [GitHub Actions Workflow](#github-actions-workflow)
5. [Notion API Integration](#notion-api-integration)
6. [Configuration & Setup](#configuration--setup)
7. [Data Flow Diagram](#data-flow-diagram)
8. [Error Handling](#error-handling)

---

## Project Overview

**Cuotas Generator** is an automated system that creates monthly budget allocation pages in Notion when you mark a transaction as requiring installments (cuotas).

### What It Does
- Monitors your Notion "Movimientos" (Transactions) database
- Detects transactions marked with "Cuotas?" checkbox
- Automatically creates multiple budget entries in "Presupuesto Mensual" database
- Divides the total amount equally across the specified number of months
- Starts from next month and continues monthly
- Updates the source transaction to mark cuotas as generated

### Example
If you create a transaction for $1,200 with "Cuotas?" checked and "Cantidad cuotas" = 3:
- Creates 3 entries in Presupuesto database
- Each entry: $400, starting Feb 2026, then Mar, then Apr
- Links back to original transaction
- Automatically updates source transaction status

---

## How It Works

### High-Level Flow

```
1. Script runs (manually or every 5 minutes via GitHub Actions)
   ↓
2. Connects to Notion using API token
   ↓
3. Queries "Movimientos" database for all transactions
   ↓
4. For each transaction:
   - Check if "Cuotas?" is checked
   - Check if "Cuotas generadas" is NOT checked (not already processed)
   ↓
5. If conditions met:
   - Calculate per-month amount (total ÷ number of cuotas)
   - For each month:
     - Create new page in Presupuesto database
     - Set amount, date (next month + n months)
     - Link to original transaction
     - Set status to "Pendiente"
     - Set type to "Gasto Variable"
   ↓
6. Mark source transaction "Cuotas generadas" = True
   ↓
7. Log results and exit
```

---

## Python Script Breakdown

### File: `cuotas_generator.py`

#### Section 1: Imports & Configuration (Lines 1-40)

```python
import requests                          # HTTP library for Notion API calls
from datetime import datetime, timezone  # Date handling
from dateutil.relativedelta import relativedelta  # Add months easily
import json                              # Parse API responses
import os                                # Read environment variables
import re                                # Regex for cleaning IDs
import sys                               # Error logging
```

**Environment Variables:**
- `NOTION_TOKEN`: API token for Notion authentication
- `DB_MOVIMIENTOS_ID`: Database ID for transactions
- `DB_PRESUPUESTO_ID`: Database ID for budget

**ID Cleaning Logic:**
```python
DB_MOVIMIENTOS_ID = re.sub(r'[^a-f0-9]', '', _mov_id_raw.lower())
```
This removes ALL non-hexadecimal characters (hyphens, spaces, etc.) to handle GitHub's auto-formatting of UUIDs.

**Headers Configuration:**
```python
headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}
```
Every request to Notion API includes these headers:
- **Authorization**: Bearer token for authentication
- **Content-Type**: Tells Notion we're sending JSON
- **Notion-Version**: API version compatibility

---

#### Section 2: Helper Functions (Lines 42-110)

##### `get_page_link(page_id)` - Generates Notion URL

```python
def get_page_link(page_id):
    clean_id = page_id.replace("-", "")  # Remove hyphens from UUID
    return f"https://www.notion.so/{clean_id}"
```
**Purpose**: Creates clickable Notion links from page IDs
**Example**: `2e572fe5-2daf-80ad-a049...` → `https://www.notion.so/2e572fe52daf80ad...`

---

##### `get_page_details(page_id)` - Fetches Full Page Data

```python
def get_page_details(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if "object" in data and data["object"] == "error":
        print(f"Error fetching page {page_id}: {data.get('message')}")
        return None
    
    return data
```

**Why this exists**: 
- Notion database queries don't return complete relation data
- Need to fetch full page details separately to get Cargo (account) and Sub-Categorias (categories)
- Returns complete page object with all properties

**API Call**: `GET /v1/pages/{page_id}`

---

##### `duplicate_template_page(template_id, parent_db_id)` - Creates from Template

```python
def duplicate_template_page(template_id, parent_db_id):
    template_page = get_page_details(template_id)  # Get template styling
    
    payload = {
        "parent": {"database_id": parent_db_id},
        "icon": template_page["icon"],  # Copy template icon
        "cover": template_page["cover"]  # Copy template cover
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return result["id"]
```

**Purpose**: Create new pages with template styling (icon, cover, colors)

**Why not use `template_id` parameter**:
- Notion API doesn't support direct template application
- This approach duplicates the template page structure and styling
- Achieves the same visual result

**API Call**: `POST /v1/pages`

---

#### Section 3: Main Logic - Create Budget Pages (Lines 112-210)

##### `create_presupuesto_page(...)` - Creates Budget Entry

```python
def create_presupuesto_page(nombre_texto, monto, fecha, cargo_id, sub_cat_id, movimiento_page_id, nombre_original):
```

**Parameters:**
- `nombre_texto`: Cuota number (e.g., "1/3", "2/3")
- `monto`: Amount for this month
- `fecha`: Date for this entry
- `cargo_id`: Account/destination ID
- `sub_cat_id`: Category ID
- `movimiento_page_id`: Link to original transaction
- `nombre_original`: Original transaction name

**Step 1: Create/Duplicate Page**
```python
if CUOTAS_TEMPLATE_ID:
    new_page_id = duplicate_template_page(CUOTAS_TEMPLATE_ID, DB_PRESUPUESTO_ID)
```
Creates new page with template styling. Falls back to plain page if template fails.

**Step 2: Build Page Properties**
```python
properties = {
    "Nombre": {
        "title": [
            {
                "type": "mention",
                "mention": {"type": "page", "page": {"id": movimiento_page_id}}
            },
            {"type": "text", "text": {"content": f" {nombre_texto}"}}
        ]
    },
    "Monto": {"number": monto},
    "Fecha": {"date": {"start": fecha.strftime("%Y-%m-%d")}},
    "Estado de Pago": {"select": {"name": "Pendiente"}},
    "Tipo": {"select": {"name": "Gasto Variable"}}
}
```

**Title Format**: Creates mentions to original page
- Example: `@test2 1/2` (clickable link to original + cuota number)
- Uses Notion's mention annotation

**Properties Set**:
- **Nombre**: Page title with mention link
- **Monto**: Numerical amount
- **Fecha**: Start date for this cuota
- **Estado de Pago**: Payment status (Pendiente = Pending)
- **Tipo**: Expense type (Gasto Variable = Variable Expense)

**Step 3: Add Relations**
```python
if cargo_id:
    properties["Destino dinero"] = {"relation": [{"id": cargo_id}]}

if sub_cat_id:
    properties["Sub-Categorias"] = {"relation": [{"id": sub_cat_id}]}
```

Relations link this page to:
- **Destino dinero** (Destination account): Where money will come from
- **Sub-Categorias** (Subcategory): Expense classification

**Step 4: Update Page**
```python
response = requests.patch(update_url, json=update_payload, headers=headers)
```

Uses PATCH to update the newly created page with all properties.

**API Calls**:
- `POST /v1/pages` (create page)
- `PATCH /v1/pages/{page_id}` (update page)

---

##### `update_page_property(page_id, property_name, property_value)` - Mark as Complete

```python
def update_page_property(page_id, property_name, property_value):
    payload = {
        "properties": {
            property_name: {"checkbox": property_value}
        }
    }
    response = requests.patch(url, json=payload, headers=headers)
```

**Purpose**: Update "Cuotas generadas" checkbox to True after all cuotas created

**API Call**: `PATCH /v1/pages/{page_id}`

---

#### Section 4: Data Retrieval (Lines 212-250)

##### `get_pages()` - Query All Transactions

```python
def get_pages():
    url = f"https://api.notion.com/v1/databases/{DB_MOVIMIENTOS_ID}/query"
    payload = {"page_size": 100}
    response = requests.post(url, json=payload, headers=headers)
    
    with open("db_movimientos.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
```

**Purpose**: 
- Fetch all transactions from Movimientos database
- Save response to file for debugging

**API Call**: `POST /v1/databases/{database_id}/query`
- Returns up to 100 pages per request
- Page size can be increased for larger datasets

**Output**: List of all transaction pages

---

#### Section 5: Main Processing Loop (Lines 252-377)

##### Extract Data from Each Page

```python
for page in pages:
    page_id = page["id"]
    full_page = get_page_details(page_id)  # Get complete data
    props = full_page["properties"]
    
    # Extract each property
    nombre = props.get("Nombre", {}).get("title", [{}])
    nombre = nombre[0]["text"]["content"] if nombre and "text" in nombre[0] else ""
    
    monto = props.get("Monto", {}).get("number", "")
    
    fecha_str = props.get("Fecha", {}).get("date", {}).get("start", "")
    fecha = datetime.fromisoformat(fecha_str) if fecha_str else None
    
    cargo = props.get("Cargo", {}).get("relation", [])
    cargo_id = cargo[0]["id"] if cargo else None
    
    cuotas = props.get("Cuotas?", {}).get("checkbox", False)
    cantidad_cuotas = props.get("Cantidad cuotas", {}).get("number", "")
    cuotas_generadas = props.get("Cuotas generadas", {}).get("checkbox", False)
```

**Property Extraction Pattern**:
```
props.get("PropertyName", {}).get("type", default) → extracts nested values safely
```

**Types Handled**:
- `title`: Text title (usually in array)
- `number`: Numerical values
- `date`: Date objects (ISO format)
- `relation`: Links to other pages (array)
- `checkbox`: Boolean True/False

---

##### Process Cuotas (Lines 314-370)

```python
if cuotas and cantidad_cuotas and not cuotas_generadas and fecha and monto:
```

**Conditions to Process** (ALL must be true):
1. `cuotas` = "Cuotas?" checkbox is checked
2. `cantidad_cuotas` = Valid number value
3. `not cuotas_generadas` = Not already processed
4. `fecha` = Has a date
5. `monto` = Has an amount

If all true:

**Step 1: Calculate Per-Month Amount**
```python
cantidad_cuotas = int(cantidad_cuotas)
monto_cuota = monto / cantidad_cuotas
```
Example: $1200 ÷ 3 = $400 per month

**Step 2: Loop for Each Cuota**
```python
for num_cuota in range(1, cantidad_cuotas + 1):
    fecha_cuota = fecha + relativedelta(months=num_cuota)
    nombre_cuota = f"{num_cuota}/{cantidad_cuotas}"
```

**Date Calculation Logic**:
- `fecha + relativedelta(months=1)` = Next month, same day
- `fecha + relativedelta(months=2)` = 2 months from now
- `fecha + relativedelta(months=n)` = n months from now

**Example Timeline**:
```
Original transaction: Jan 12, 2026
Cuota 1 (n=1): Feb 12, 2026 (next month)
Cuota 2 (n=2): Mar 12, 2026
Cuota 3 (n=3): Apr 12, 2026
```

**Step 3: Create Each Page**
```python
new_page_id = create_presupuesto_page(
    nombre_texto=nombre_cuota,          # "1/3"
    monto=monto_cuota,                  # $400
    fecha=fecha_cuota,                  # Feb 12
    cargo_id=cargo_id,                  # Account link
    sub_cat_id=sub_categorias_id,       # Category link
    movimiento_page_id=page_id,         # Link to this transaction
    nombre_original=nombre              # "Original name"
)

if new_page_id:
    created_count += 1
    print(f"[OK] Created: {nombre} {nombre_cuota} | {fecha_cuota.strftime('%d-%m-%Y')} | ${monto_cuota:,.0f}")
```

**Step 4: Mark Complete (Only if All Succeed)**
```python
if created_count == cantidad_cuotas:
    update_page_property(page_id, "Cuotas generadas", True)
    print(f"[OK] Marked 'Cuotas generadas' as complete\n")
else:
    print(f"[WARN] Not all cuotas were created, 'Cuotas generadas' was not marked\n")
```

**Important**: Only marks as complete if ALL cuotas created successfully
- Prevents duplicate processing
- Ensures consistency

---

## GitHub Actions Workflow

### File: `.github/workflows/cuotas_generator.yml`

#### Trigger Configuration

```yaml
on:
  schedule:
    - cron: "*/5 * * * *"    # Every 5 minutes
  workflow_dispatch:          # Manual trigger
```

**Cron Expression Breakdown** `*/5 * * * *`:
- `*/5` = Every 5 minutes
- First `*` = Every hour
- Second `*` = Every day
- Third `*` = Every month
- Fourth `*` = Every weekday

**Result**: Runs automatically every 5 minutes, 24/7

---

#### Job Configuration

```yaml
jobs:
  run:
    runs-on: ubuntu-latest      # Run on Linux
    environment: Notion         # Use "Notion" environment for secrets
```

**`environment: Notion`**:
- References the GitHub environment where secrets are stored
- Secrets: NOTION_TOKEN, DB_MOVIMIENTOS_ID, DB_PRESUPUESTO_ID
- Prevents accidental exposure of credentials

---

#### Steps Breakdown

**Step 1: Checkout Code**
```yaml
- uses: actions/checkout@v4
```
Downloads the repository to the runner (GitHub's virtual machine)

**Step 2: Setup Python**
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
```
Installs Python 3.11 on the runner

**Step 3: Install Dependencies**
```yaml
- name: Install deps
  run: pip install -r requirements.txt
```
Installs packages from `requirements.txt`:
- `requests`: HTTP library
- `python-dateutil`: Date handling

**Step 4: Run Script with Secrets**
```yaml
- name: Run script
  env:
    NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
    DB_MOVIMIENTOS_ID: ${{ secrets.DB_MOVIMIENTOS_ID }}
    DB_PRESUPUESTO_ID: ${{ secrets.DB_PRESUPUESTO_ID }}
  run: python cuotas_generator.py
```

**`${{ secrets.VARIABLE }}`**:
- Securely passes secrets to the script
- Not visible in logs
- Read as environment variables by Python script

**Execution**:
1. Runner gets latest code
2. Installs dependencies
3. Sets environment variables from secrets
4. Runs `python cuotas_generator.py`
5. Script reads environment variables
6. Queries Notion, processes cuotas, exits

---

## Notion API Integration

### Authentication

```python
headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}
```

**Bearer Token**:
- Standard OAuth format
- Token format: `ntn_` + random characters
- Must be kept secret
- Each request includes: `Authorization: Bearer ntn_xxxxx`

### API Endpoints Used

#### 1. Query Database
```
POST /v1/databases/{database_id}/query
```
**Purpose**: Get all pages from a database
**Request**:
```json
{"page_size": 100}
```
**Response**: Array of page objects with properties

#### 2. Get Page Details
```
GET /v1/pages/{page_id}
```
**Purpose**: Fetch full page data including relations
**Response**: Complete page object with all properties, formatting, etc.

#### 3. Create Page
```
POST /v1/pages
```
**Purpose**: Create new page in database
**Request**:
```json
{
  "parent": {"database_id": "xxx"},
  "icon": {"type": "emoji", "emoji": "📋"},
  "properties": { /* page properties */ }
}
```
**Response**: Created page object with ID

#### 4. Update Page
```
PATCH /v1/pages/{page_id}
```
**Purpose**: Update page properties
**Request**:
```json
{
  "properties": {
    "PropertyName": {"type": value}
  }
}
```
**Response**: Updated page object

---

### Property Types in Notion API

| Type | Format | Example |
|------|--------|---------|
| Title | `{"title": [{"type": "text", "text": {"content": "..."}}]}` | Text title |
| Number | `{"number": 123}` | Numerical value |
| Date | `{"date": {"start": "2026-02-12"}}` | ISO format date |
| Select | `{"select": {"name": "Option"}}` | Single choice |
| Relation | `{"relation": [{"id": "xxx"}]}` | Link to other pages |
| Checkbox | `{"checkbox": true}` | True/False |
| Rich Text | `{"rich_text": [{"type": "text", "text": {"content": "..."}}]}` | Formatted text |

---

## Configuration & Setup

### Prerequisites
1. Notion workspace with at least Editor access
2. Two databases: "Movimientos" (transactions) and "Presupuesto Mensual" (budget)
3. A template page named "Cuotas" (optional, script works without it)
4. GitHub account with repository access

### Step 1: Create Notion Integration

1. Go to Notion Settings & members → Integrations → Develop your own
2. Create new integration
3. Grant permissions: Read, Update, Insert
4. Copy the token (starts with `ntn_`)

### Step 2: Share Databases with Integration

1. In each database (Movimientos, Presupuesto), click Share
2. Add your integration
3. Grant access to the database

### Step 3: Get Database IDs

1. Open Movimientos database
2. URL format: `notion.so/workspace/2e572fe52daf80ada049fac2ea4e0289`
3. ID is the last part: `2e572fe52daf80ada049fac2ea4e0289`
4. Repeat for Presupuesto database

### Step 4: Setup GitHub Secrets

1. Repository → Settings → Environments → Create "Notion" environment
2. Add secrets:
   - `NOTION_TOKEN`: Your integration token
   - `DB_MOVIMIENTOS_ID`: Movimientos database ID
   - `DB_PRESUPUESTO_ID`: Presupuesto database ID

### Step 5: Verify Property Names

Ensure your databases have these properties:

**Movimientos Database**:
- `Nombre` (Title) - Transaction name
- `Monto` (Number) - Amount
- `Fecha` (Date) - Transaction date
- `Cargo` (Relation) - Account/destination
- `Sub-Categorias` (Relation) - Category
- `Cuotas?` (Checkbox) - Mark for installments
- `Cantidad cuotas` (Number) - Number of months
- `Cuotas generadas` (Checkbox) - Already processed flag

**Presupuesto Database**:
- `Nombre` (Title) - Budget entry name
- `Monto` (Number) - Budget amount
- `Fecha` (Date) - Budget date
- `Destino dinero` (Relation) - Account link
- `Sub-Categorias` (Relation) - Category link
- `Estado de Pago` (Select) - Payment status
- `Tipo` (Select) - Expense type

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Actions (every 5 minutes or manual trigger)             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │  cuotas_generator.py starts      │
        │  - Load environment variables    │
        │  - Initialize Notion headers     │
        └──────────────┬───────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │  get_pages()                     │
        │  Query Movimientos database      │
        │  Returns all transactions        │
        └──────────────┬───────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  For each page:      │
            │  - Get full details  │
            │  - Extract props     │
            └──────────┬───────────┘
                       │
            ┌──────────┴────────────┐
            │                       │
            ▼                       ▼
    ┌──────────────────┐   ┌─────────────────┐
    │ Cuotas? = FALSE  │   │ Cuotas? = TRUE  │
    │ Skip             │   │ Check other...  │
    └──────────────────┘   └────────┬────────┘
                                    │
                        ┌───────────┴───────────┐
                        │                       │
                        ▼                       ▼
            ┌──────────────────────┐   ┌──────────────────┐
            │ Qty? & Generated?    │   │ All conditions   │
            │ Skip                 │   │ satisfied        │
            └──────────────────────┘   └────────┬─────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │ Calculate:            │
                                    │ - Per-month amount    │
                                    │ - Dates for each      │
                                    │ - Cuota numbers       │
                                    └───────────┬───────────┘
                                                │
                                    ┌───────────┴──────────┐
                                    │                      │
                                    ▼                      ▼
                        ┌──────────────────────┐   ┌──────────────────┐
                        │ For each cuota (1-N) │   │ Loop through:    │
                        │ create_presupuesto   │   │ 1/N, 2/N, 3/N... │
                        │ page()               │   │                  │
                        └──────────┬───────────┘   └──────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
        ┌──────────────────────┐     ┌──────────────────────┐
        │ Duplicate template   │     │ Update page with:    │
        │ or create basic page │     │ - Title (w/ mention) │
        │                      │     │ - Amount             │
        │                      │     │ - Date               │
        │                      │     │ - Relations          │
        │                      │     │ - Status             │
        └──────────────────────┘     └──────────────────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │ Count successes      │
                        │ Track creation       │
                        └──────────┬───────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
        ┌──────────────────────┐     ┌──────────────────────┐
        │ All created?         │     │ Some failed?         │
        │ YES ▼                │     │ NO ▼                │
        │ Update source page   │     │ Log warning          │
        │ "Cuotas generadas"=T │     │ Don't mark complete  │
        │ Log success          │     │ (Will retry next run)│
        └──────────────────────┘     └──────────────────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │ Script completes     │
                        │ Next run in 5 min    │
                        └──────────────────────┘
```

---

## Error Handling

### Types of Errors & Recovery

#### 1. Missing Environment Variables
```python
if not NOTION_TOKEN or not DB_MOVIMIENTOS_ID or not DB_PRESUPUESTO_ID:
    raise ValueError("Missing required environment variables...")
```
**What happens**: Script exits immediately with error message
**Why**: Can't function without credentials
**Fix**: Check GitHub secrets are configured

#### 2. Invalid API Token
```
Error: "API token is invalid"
```
**Cause**: Token expired, revoked, or incorrect
**Fix**: Generate new integration token in Notion, update GitHub secret

#### 3. Database Not Found
```
Error: "Could not find database with ID: xxx"
```
**Causes**: 
- Wrong database ID
- Integration doesn't have access
- Integration not shared with database
**Fix**: Re-share databases with integration in Notion

#### 4. Page Fetch Fails
```python
if "object" in data and data["object"] == "error":
    print(f"Error fetching page {page_id}: {data.get('message')}")
    return None
```
**Handled**: Skips that page, continues with others
**Why**: Some pages might have access issues, don't block entire process

#### 5. Property Update Fails
```python
if created_count == cantidad_cuotas:
    if update_page_property(page_id, "Cuotas generadas", True):
        print("Success")
    else:
        print("Failed to mark complete")
```
**Handled**: Logs error but doesn't stop script
**Impact**: Cuotas created but source not marked, will retry next run

#### 6. Partial Failure
```python
if created_count == cantidad_cuotas:
    # Mark complete only if ALL succeeded
else:
    print("Not all cuotas created, won't mark complete")
```
**Logic**: If 2 of 3 cuotas fail, doesn't mark as complete
**Why**: Ensures consistency, will retry next run

---

## Debugging Tips

### Enable Debug Output
The script prints:
```
[DEBUG] Using token: ntn_308683...nc2K0
[DEBUG] Token length: 50
[DEBUG] DB_MOVIMIENTOS_ID: 2e572f...4e28 (length: 32)
[DEBUG] DB_PRESUPUESTO_ID: 2e572f...7f68 (length: 32)
```

**Check**:
- Token length = 50 (exactly)
- Database IDs = 32 characters (exactly)
- If not, secrets are malformed

### Check GitHub Actions Logs
1. Repository → Actions → Latest workflow run
2. Click "Run script" step
3. View full output and errors

### Test Locally
```bash
export NOTION_TOKEN="ntn_xxx"
export DB_MOVIMIENTOS_ID="2e572fe52daf80ada049fac2ea4e0289"
export DB_PRESUPUESTO_ID="2e572fe52daf80858276f9c05a888791"
python cuotas_generator.py
```

### Manual Testing
1. Create test transaction in Movimientos
2. Set "Cuotas?" = checked
3. Set "Cantidad cuotas" = 2
4. Run: `Actions → Cuotas Generator → Run workflow → Run workflow`
5. Check Presupuesto for 2 new entries
6. Verify source transaction "Cuotas generadas" = checked

---

## Summary

**Cuotas Generator** automates the tedious process of creating monthly budget entries from installment transactions. By leveraging:

- **Notion API**: Direct database manipulation
- **Python**: Flexible scripting and date calculations
- **GitHub Actions**: Reliable, free automation
- **Cron scheduling**: Consistent 5-minute checks

The system ensures that every transaction marked for installments is automatically broken down into equal monthly payments, properly dated, and linked for easy tracking.

Once set up, it runs silently in the background, requiring no manual intervention.

