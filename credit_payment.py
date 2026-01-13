import requests
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import json
import os
import re


NOTION_TOKEN = os.getenv("NOTION_TOKEN", "").strip()

# Extract only hexadecimal characters from database IDs (remove hyphens and other characters)
_cuentas_id_raw = os.getenv("DB_CUENTAS_ID", "").strip()
DB_CUENTAS_ID = re.sub(r'[^a-f0-9]', '', _cuentas_id_raw.lower())

_pre_id_raw = os.getenv("DB_PRESUPUESTO_ID", "").strip()
DB_PRESUPUESTO_ID = re.sub(r'[^a-f0-9]', '', _pre_id_raw.lower())

_template_id_raw = os.getenv("CUOTAS_TEMPLATE_ID", "").strip()
CUOTAS_TEMPLATE_ID = re.sub(r'[^a-f0-9]', '', _template_id_raw.lower())

_pago_deudas_raw = os.getenv("PAGO_DEUDAS_ID", "").strip()
PAGO_DEUDAS_ID = re.sub(r'[^a-f0-9]', '', _pago_deudas_raw.lower())

if not NOTION_TOKEN or not DB_CUENTAS_ID or not DB_PRESUPUESTO_ID:
    raise ValueError("Missing required environment variables: NOTION_TOKEN, DB_CUENTAS_ID, DB_PRESUPUESTO_ID")

# Debug: Show token info (without exposing full token)
import sys
token_preview = NOTION_TOKEN[:10] + "..." + NOTION_TOKEN[-5:] if NOTION_TOKEN else "NONE"
db_cuentas_display = DB_CUENTAS_ID[:8] + "..." + DB_CUENTAS_ID[-4:] if DB_CUENTAS_ID else "NONE"
db_pre_display = DB_PRESUPUESTO_ID[:8] + "..." + DB_PRESUPUESTO_ID[-4:] if DB_PRESUPUESTO_ID else "NONE"
print(f"[DEBUG] Using token: {token_preview}", file=sys.stderr)
print(f"[DEBUG] Token length: {len(NOTION_TOKEN)}", file=sys.stderr)
print(f"[DEBUG] DB_CUENTAS_ID: {db_cuentas_display} (length: {len(DB_CUENTAS_ID)})", file=sys.stderr)
print(f"[DEBUG] DB_PRESUPUESTO_ID: {db_pre_display} (length: {len(DB_PRESUPUESTO_ID)})", file=sys.stderr)
if CUOTAS_TEMPLATE_ID:
    print(f"[DEBUG] CUOTAS_TEMPLATE_ID: {CUOTAS_TEMPLATE_ID[:8]}...{CUOTAS_TEMPLATE_ID[-4:]}", file=sys.stderr)
else:
    print(f"[WARNING] CUOTAS_TEMPLATE_ID not set - will create pages WITHOUT template styling", file=sys.stderr)
if PAGO_DEUDAS_ID:
    print(f"[DEBUG] PAGO_DEUDAS_ID: {PAGO_DEUDAS_ID[:8]}...{PAGO_DEUDAS_ID[-4:]}", file=sys.stderr)
else:
    print(f"[WARNING] PAGO_DEUDAS_ID not set - will NOT set sub-category", file=sys.stderr)

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


def get_page_details(page_id):
    """Fetch full page details including relation data"""
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
    """Duplicate a template page and return the new page ID"""
    try:
        template_page = get_page_details(template_id)
        if not template_page:
            print(f"    Error: Could not fetch template page {template_id}")
            return None
        
        url = "https://api.notion.com/v1/pages"
        
        payload = {
            "parent": {
                "database_id": parent_db_id
            }
        }
        
        # Copy icon from template if it exists
        if template_page and "icon" in template_page and template_page["icon"]:
            payload["icon"] = template_page["icon"]
        else:
            # Default icon if template doesn't have one
            payload["icon"] = {
                "type": "emoji",
                "emoji": "💳"
            }
        
        # Copy cover from template if it exists
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


def update_page_property(page_id, property_name, property_value):
    """Update a single property on a page"""
    try:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        
        payload = {
            "properties": {
                property_name: property_value
            }
        }
        
        response = requests.patch(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            result = response.json()
            error_msg = result.get('message', 'Unknown error')
            print(f"    Error updating property {property_name} (HTTP {response.status_code}): {error_msg}")
            return False
        
        return True
    except Exception as e:
        print(f"Error updating property: {e}")
        return False


def create_payment_page(cuentas_page_id, fecha):
    """Create a new page in Presupuesto Mensual database from template, then update properties"""
    try:
        # First, duplicate the template page
        new_page_id = None
        if CUOTAS_TEMPLATE_ID:
            new_page_id = duplicate_template_page(CUOTAS_TEMPLATE_ID, DB_PRESUPUESTO_ID)
            if not new_page_id:
                print(f"    Warning: Could not duplicate template, creating page from scratch")
        
        # If no template or duplication failed, create a basic page
        if not new_page_id:
            url = "https://api.notion.com/v1/pages"
            payload = {
                "parent": {
                    "database_id": DB_PRESUPUESTO_ID
                },
                "properties": {
                    "Nombre": {
                        "title": [{"type": "text", "text": {"content": "Pago"}}]
                    }
                }
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                return None
            new_page_id = response.json()["id"]
        
        # Now update the properties
        success = True
        
        # Update title with mention
        title_payload = {
            "title": [
                {"type": "text", "text": {"content": "Pago "}},
                {
                    "type": "mention",
                    "mention": {
                        "type": "page",
                        "page": {"id": cuentas_page_id}
                    }
                }
            ]
        }
        success = update_page_property(new_page_id, "Nombre", title_payload) and success
        
        # Update date
        fecha_payload = {
            "date": {"start": fecha.strftime("%Y-%m-%d")}
        }
        success = update_page_property(new_page_id, "Fecha", fecha_payload) and success
        
        # Update payment status
        estado_payload = {
            "select": {"name": "Pendiente"}
        }
        success = update_page_property(new_page_id, "Estado de Pago", estado_payload) and success
        
        # Update type
        tipo_payload = {
            "select": {"name": "Gasto Fijo"}
        }
        success = update_page_property(new_page_id, "Tipo", tipo_payload) and success
        
        # Update destination money (relation)
        destino_payload = {
            "relation": [{"id": cuentas_page_id}]
        }
        success = update_page_property(new_page_id, "Destino dinero", destino_payload) and success
        
        # Update sub-category (relation to Pago Deudas)
        if PAGO_DEUDAS_ID:
            sub_cat_payload = {
                "relation": [{"id": PAGO_DEUDAS_ID}]
            }
            success = update_page_property(new_page_id, "Sub-Categorias", sub_cat_payload) and success
        
        if success:
            return new_page_id
        else:
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
    
    # Check if the response contains an error
    if "object" in data and data["object"] == "error":
        print(f"Notion API Error: {data.get('message', 'Unknown error')}")
        print(f"Full response: {json.dumps(data, indent=2)}")
        return []
    
    if "results" not in data:
        print(f"Unexpected response format. Keys: {data.keys()}")
        print(f"Full response: {json.dumps(data, indent=2)}")
        return []
        
    results = data["results"]
    return results

pages = get_pages()

for page in pages:
    page_id = page["id"]
    
    # Fetch full page details to get complete relation data
    full_page = get_page_details(page_id)
    if full_page:
        props = full_page["properties"]
    else:
        props = page["properties"]
    
    page_id = full_page["id"] if full_page else page["id"]

    nombre = props.get("Nombre", {}).get("title", [{}])
    nombre = nombre[0]["text"]["content"] if nombre and "text" in nombre[0] else ""

    fecha_corte = props.get("Fecha de corte", {}).get("number", "")

    print(
        f"{page_id} | Nombre: {nombre} | Fecha de corte: {fecha_corte}"
    )
    
    # Process if fecha_corte has a value
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
            cuentas_page_id=page_id,
            fecha=fecha_pago
        )
        
        if new_page_id:
            print(f"  [OK] Created payment: {nombre} | {fecha_pago.strftime('%d-%m-%Y')}\n")
        else:
            print(f"  [FAIL] Failed to create payment for: {nombre}\n")