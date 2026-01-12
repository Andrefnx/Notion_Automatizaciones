import requests
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import json
import os
import re


NOTION_TOKEN = os.getenv("NOTION_TOKEN", "").strip()

# Extract only hexadecimal characters from database IDs
_cuentas_id_raw = os.getenv("DB_CUENTAS_ID", "").strip()
DB_CUENTAS_ID = re.sub(r'[^a-f0-9]', '', _cuentas_id_raw.lower())

_pre_id_raw = os.getenv("DB_PRESUPUESTO_ID", "").strip()
DB_PRESUPUESTO_ID = re.sub(r'[^a-f0-9]', '', _pre_id_raw.lower())

# Template page ID for "Pago" (optional, similar to cuotas)
PAGO_TEMPLATE_ID = ""  # Set this if you have a template page

if not NOTION_TOKEN or not DB_CUENTAS_ID or not DB_PRESUPUESTO_ID:
    raise ValueError("Missing required environment variables: NOTION_TOKEN, DB_CUENTAS_ID, DB_PRESUPUESTO_ID")

# Debug: Show token info
import sys
token_preview = NOTION_TOKEN[:10] + "..." + NOTION_TOKEN[-5:] if NOTION_TOKEN else "NONE"
db_cuentas_display = DB_CUENTAS_ID[:8] + "..." + DB_CUENTAS_ID[-4:] if DB_CUENTAS_ID else "NONE"
db_pre_display = DB_PRESUPUESTO_ID[:8] + "..." + DB_PRESUPUESTO_ID[-4:] if DB_PRESUPUESTO_ID else "NONE"
print(f"[DEBUG] Using token: {token_preview}", file=sys.stderr)
print(f"[DEBUG] Token length: {len(NOTION_TOKEN)}", file=sys.stderr)
print(f"[DEBUG] DB_CUENTAS_ID: {db_cuentas_display} (length: {len(DB_CUENTAS_ID)})", file=sys.stderr)
print(f"[DEBUG] DB_PRESUPUESTO_ID: {db_pre_display} (length: {len(DB_PRESUPUESTO_ID)})", file=sys.stderr)

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2024-08-15"
}


def get_page_details(page_id):
    """Fetch full page details"""
    try:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if "object" in data and data["object"] == "error":
            print(f"Error fetching page {page_id}: {data.get('message')}")
            return None
        
        return data
    except Exception as e:
        print(f"Error fetching page {page_id}: {e}")
        return None


def duplicate_template_page(template_id, parent_db_id):
    """Duplicate a template page and return its ID"""
    try:
        template_page = get_page_details(template_id)
        
        url = "https://api.notion.com/v1/pages"
        
        payload = {
            "parent": {
                "database_id": parent_db_id
            }
        }
        
        if template_page and "icon" in template_page and template_page["icon"]:
            payload["icon"] = template_page["icon"]
        else:
            payload["icon"] = {
                "type": "emoji",
                "emoji": "💳"
            }
        
        if template_page and "cover" in template_page and template_page["cover"]:
            payload["cover"] = template_page["cover"]
        
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        
        if response.status_code == 200:
            new_page_id = result["id"]
            return new_page_id
        else:
            print(f"    Error duplicating template (HTTP {response.status_code}): {result.get('message')}")
            return None
            
    except Exception as e:
        print(f"Error duplicating template: {e}")
        return None


def create_payment_page(nombre_texto, monto, fecha, cuentas_page_id):
    """Create a new page in Presupuesto Mensual database for monthly payment"""
    try:
        url = "https://api.notion.com/v1/pages"
        
        # Duplicate template if available
        new_page_id = None
        if PAGO_TEMPLATE_ID:
            new_page_id = duplicate_template_page(PAGO_TEMPLATE_ID, DB_PRESUPUESTO_ID)
            if not new_page_id:
                print(f"    Warning: Could not duplicate template, creating page from scratch")
        
        # If no template, create basic page
        if not new_page_id:
            payload = {
                "parent": {
                    "database_id": DB_PRESUPUESTO_ID
                },
                "properties": {
                    "Nombre": {
                        "title": [{"type": "text", "text": {"content": nombre_texto}}]
                    }
                }
            }
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            if response.status_code == 200:
                new_page_id = result["id"]
            else:
                return None
        
        # Update page with payment data
        properties = {
            "Nombre": {
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Pago "
                        }
                    },
                    {
                        "type": "mention",
                        "mention": {
                            "type": "page",
                            "page": {
                                "id": cuentas_page_id
                            }
                        }
                    }
                ]
            },
            "Fecha": {
                "date": {
                    "start": fecha.strftime("%Y-%m-%d")
                }
            },
            "Estado de Pago": {
                "select": {
                    "name": "Pendiente"
                }
            },
            "Tipo": {
                "select": {
                    "name": "Gasto Fijo"
                }
            },
            "Destino pago": {
                "relation": [
                    {"id": cuentas_page_id}
                ]
            },
            "Sub-Categorias": {
                "relation": [
                    {"id": "PAGO_DEUDAS_ID_PLACEHOLDER"}  # Replace with actual sub-category ID
                ]
            }
        }
        
        # Update the page
        update_url = f"https://api.notion.com/v1/pages/{new_page_id}"
        update_payload = {
            "properties": properties
        }
        
        response = requests.patch(update_url, json=update_payload, headers=headers)
        
        if response.status_code == 200:
            return new_page_id
        else:
            result = response.json()
            error_msg = result.get('message', 'Unknown error')
            print(f"    Error updating page (HTTP {response.status_code}): {error_msg}")
            return None
            
    except Exception as e:
        print(f"Error creating payment page: {e}")
        return None


def get_pages():
    """Query all accounts from Cuentas database"""
    url = f"https://api.notion.com/v1/databases/{DB_CUENTAS_ID}/query"
    
    payload = {"page_size": 100}
    response = requests.post(url, json=payload, headers=headers)
    
    data = response.json()
    
    if "object" in data and data["object"] == "error":
        print(f"Notion API Error: {data.get('message', 'Unknown error')}")
        return []
    
    if "results" not in data:
        print(f"Unexpected response format. Keys: {data.keys()}")
        return []
        
    results = data["results"]
    return results


pages = get_pages()

for page in pages:
    page_id = page["id"]
    
    # Fetch full page details
    full_page = get_page_details(page_id)
    if full_page:
        props = full_page["properties"]
    else:
        props = page["properties"]
    
    page_id = full_page["id"] if full_page else page["id"]

    # Extract properties
    nombre = props.get("Nombre", {}).get("title", [{}])
    nombre = nombre[0]["text"]["content"] if nombre and "text" in nombre[0] else ""

    # Monto is optional - not all Cuentas have this field
    monto = props.get("Monto", {}).get("number", None)

    fecha_corte = props.get("Fecha de corte", {}).get("number", "")

    print(
        f"{page_id} | Nombre: {nombre} | Monto: {monto} | Fecha de corte: {fecha_corte}"
    )
    
    # Process if fecha_corte has a value (Monto is optional)
    if fecha_corte:
        fecha_corte = int(fecha_corte)
        
        # Get current date to create payment for current month
        today = datetime.now()
        
        # Create date with the cutoff day in current month
        try:
            fecha_pago = today.replace(day=fecha_corte)
        except ValueError:
            # Handle invalid day (e.g., Feb 31)
            # Use last day of month instead
            if today.month == 12:
                last_day = (today.replace(year=today.year + 1, month=1, day=1) - relativedelta(days=1)).day
            else:
                last_day = (today.replace(month=today.month + 1, day=1) - relativedelta(days=1)).day
            fecha_pago = today.replace(day=last_day)
        
        print(f"  Creating payment for: {nombre} on {fecha_pago.strftime('%d-%m-%Y')}")
        
        # Create the payment page
        new_page_id = create_payment_page(
            nombre_texto="",  # Will be added as title with mention
            monto=monto,
            fecha=fecha_pago,
            cuentas_page_id=page_id
        )
        
        if new_page_id:
            print(f"  [OK] Created payment: {nombre} | {fecha_pago.strftime('%d-%m-%Y')}")
        else:
            print(f"  [FAIL] Failed to create payment for: {nombre}")