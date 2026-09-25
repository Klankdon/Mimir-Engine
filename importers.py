import base64
import json
from io import BytesIO
from PIL import Image

def parse_character_card(file_bytes: bytes, filename: str) -> dict:
    if filename.lower().endswith('.json'):
        return json.loads(file_bytes.decode('utf-8'))

    image = Image.open(BytesIO(file_bytes))
    metadata = image.info

    if 'chara' in metadata:
        return json.loads(base64.b64decode(metadata['chara']).decode('utf-8'))
    
    if 'character' in metadata:
        return json.loads(base64.b64decode(metadata['character']).decode('utf-8'))

    raise ValueError("Invalid metadata")


def parse_lorebook(file_bytes: bytes) -> dict:
    data = json.loads(file_bytes.decode('utf-8'))
    entries = data.get("entries", {})
    
    if isinstance(entries, dict):
        entries_list = list(entries.values())
    else:
        entries_list = entries

    parsed = []
    for entry in entries_list:
        parsed.append({
            "keys": entry.get("keys", []),
            "content": entry.get("content", ""),
            "enabled": entry.get("enabled", True),
            "insertion_order": entry.get("insertion_order", 100),
        })

    return {
        "name": data.get("name", "Imported"),
        "entries": parsed
    }
