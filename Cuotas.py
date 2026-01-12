import requests
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import json


NOTION_TOKEN = "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"

DB_MOVIMIENTOS_ID = "2e572fe52daf80ada049fac2ea4e0289"

DB_PRESUPUESTO_ID = "2e572fe52daf80858276f9c05a888791"

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


def get_page_link(page_id):
    """Generate a Notion page link from a page ID"""
    # Remove hyphens from the ID to create the link format
    clean_id = page_id.replace("-", "")
    return f"https://www.notion.so/{clean_id}"


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


def create_presupuesto_page(nombre_texto, monto, fecha, cargo_id, sub_cat_id, movimiento_page_id, nombre_original):
    """Create a new page in Presupuesto Mensual database"""
    try:
        url = "https://api.notion.com/v1/pages"
        
        # Build the properties for the new page
        # Nombre includes a mention to the movimiento page and the cuota number
        properties = {
            "Nombre": {
                "title": [
                    {
                        "type": "mention",
                        "mention": {
                            "type": "page",
                            "page": {
                                "id": movimiento_page_id
                            }
                        }
                    },
                    {
                        "type": "text",
                        "text": {
                            "content": f" {nombre_texto}"
                        }
                    }
                ]
            },
            "Monto": {
                "number": monto
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
            }
        }
        
        # Add Destino dinero (from Cargo in Movimientos) if present
        if cargo_id:
            properties["Destino dinero"] = {
                "relation": [
                    {"id": cargo_id}
                ]
            }
        
        # Add Sub-Categorias if present
        if sub_cat_id:
            properties["Sub-Categorias"] = {
                "relation": [
                    {"id": sub_cat_id}
                ]
            }
        
        payload = {
            "parent": {
                "database_id": DB_PRESUPUESTO_ID
            },
            "properties": properties
        }
        
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        
        if response.status_code == 200:
            return result["id"]
        else:
            error_msg = result.get('message', 'Unknown error')
            print(f"    Error creating page (HTTP {response.status_code}): {error_msg}")
            print(f"    Response: {result}")
            return None
            
    except Exception as e:
        print(f"Error creating presupuesto page: {e}")
        return None


def update_page_property(page_id, property_name, property_value):
    """Update a single property in a page"""
    try:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        
        payload = {
            "properties": {
                property_name: {
                    "checkbox": property_value
                }
            }
        }
        
        response = requests.patch(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"Error updating page {page_id}: {response.json().get('message')}")
            return False
        return True
        
    except Exception as e:
        print(f"Error updating page: {e}")
        return False


def get_pages():
    url = f"https://api.notion.com/v1/databases/{DB_MOVIMIENTOS_ID}/query"
    
    payload = {"page_size": 100}
    response = requests.post(url, json=payload, headers=headers)
    
    data = response.json()
    
    import json
    with open("db_movimientos.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
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

# Debug: Save first page's full details
if pages:
    import json
    first_page_id = pages[0]["id"]
    first_page_full = get_page_details(first_page_id)
    if first_page_full:
        with open("first_page_details.json", "w", encoding="utf-8") as f:
            json.dump(first_page_full, f, ensure_ascii=False, indent=4)
        
        # Check if relations are empty
        cargo = first_page_full["properties"].get("Cargo", {}).get("relation", [])
        sub_cats = first_page_full["properties"].get("Sub-Categorias", {}).get("relation", [])
        
        # Save full properties to debug
        with open("cargo_debug.json", "w", encoding="utf-8") as f:
            json.dump({
                "Cargo": first_page_full["properties"].get("Cargo"),
                "Sub-Categorias": first_page_full["properties"].get("Sub-Categorias")
            }, f, ensure_ascii=False, indent=4)
        
        if not cargo and not sub_cats:
            print("WARNING: No relations found in Notion API response.")
            print("Please verify that the Cargo and Sub-Categorias relations are properly SAVED in Notion.")
            print("Make sure to click outside the field or press Enter after selecting a relation.\n")

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

    monto = props.get("Monto", {}).get("number", "")

    tipo = props.get("Tipo", {}).get("select", {}).get("name", "")

    fecha_str = props.get("Fecha", {}).get("date", {}).get("start", "")
    fecha = datetime.fromisoformat(fecha_str) if fecha_str else None

    cargo = props.get("Cargo", {}).get("relation", [])
    cargo_id = cargo[0]["id"] if cargo else None

    sub_categorias = props.get("Sub-Categorias", {}).get("relation", [])
    sub_categorias_id = sub_categorias[0]["id"] if sub_categorias else None

    descripcion = props.get("Descripción", {}).get("rich_text", [{}])
    descripcion = descripcion[0]["text"]["content"] if descripcion and "text" in descripcion[0] else ""

    cuotas = props.get("Cuotas?", {}).get("checkbox", False)

    cantidad_cuotas = props.get("Cantidad cuotas", {}).get("number", "")

    cuotas_generadas = props.get("Cuotas generadas", {}).get("checkbox", False)

    print(
        f"{page_id} | Nombre: {nombre} | Monto: {monto} | Tipo: {tipo} | Fecha: {fecha} | "
        f"Cuotas?: {cuotas} | Cantidad cuotas: {cantidad_cuotas} | Cuotas generadas: {cuotas_generadas}"
    )
    
    # Process cuotas if needed
    # Only process if: cuotas is checked AND cuotas_generadas is NOT checked
    if cuotas and cantidad_cuotas and not cuotas_generadas and fecha and monto:
        cantidad_cuotas = int(cantidad_cuotas)
        monto_cuota = monto / cantidad_cuotas
        
        print(f"\n  Creating {cantidad_cuotas} cuotas for: {nombre}")
        created_count = 0
        
        for num_cuota in range(1, cantidad_cuotas + 1):
            # Calculate the date for this cuota (start next month, then same day each month)
            fecha_cuota = fecha + relativedelta(months=num_cuota)
            
            # Create the name for this cuota (just the number, page link will be in Nombre relation)
            nombre_cuota = f"{num_cuota}/{cantidad_cuotas}"
            
            print(f"    Creating cuota {nombre_cuota}...")
            
            # Create the page in Presupuesto
            new_page_id = create_presupuesto_page(
                nombre_texto=nombre_cuota,
                monto=monto_cuota,
                fecha=fecha_cuota,
                cargo_id=cargo_id,
                sub_cat_id=sub_categorias_id,
                movimiento_page_id=page_id,
                nombre_original=nombre
            )
            
            if new_page_id:
                created_count += 1
                print(f"    ✓ Created: {nombre} {nombre_cuota} | {fecha_cuota.strftime('%d-%m-%Y')} | ${monto_cuota:,.0f}")
            else:
                print(f"    ✗ Failed to create: {nombre} {nombre_cuota}")
        
        print(f"  Created {created_count}/{cantidad_cuotas} cuotas")
        
        # Mark Cuotas generadas as True only if all cuotas were created
        if created_count == cantidad_cuotas:
            if update_page_property(page_id, "Cuotas generadas", True):
                print(f"  ✓ Marked 'Cuotas generadas' as complete\n")
            else:
                print(f"  ✗ Failed to mark 'Cuotas generadas'\n")
        else:
            print(f"  ⚠ Not all cuotas were created, 'Cuotas generadas' was not marked\n")