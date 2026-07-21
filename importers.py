import base64
import json
from io import BytesIO
from PIL import Image

def parse_character_card(file_bytes: bytes, filename: str) -> dict:
    """Parses PNG (tEXt chunk) or JSON Character Cards (V2 Spec)."""
    if filename.lower().endswith('.json'):
        return json.loads(file_bytes.decode('utf-8'))

    # If PNG, open with Pillow and search for character metadata chunks
    image = Image.open(BytesIO(file_bytes))
    metadata = image.info

    # V2 spec stores data in 'chara' base64 chunk
    if 'chara' in metadata:
        decoded_json = base64.b64decode(metadata['chara']).decode('utf-8')
        return json.loads(decoded_json)
    
    # Legacy spec fallback
    if 'character' in metadata:
        decoded_json = base64.b64decode(metadata['character']).decode('utf-8')
        return json.loads(decoded_json)

    raise ValueError("No valid character card metadata found in PNG.")


def parse_lorebook(file_bytes: bytes) -> dict:
    """Parses SillyTavern / TavernAI World Info JSON files."""
    data = json.loads(file_bytes.decode('utf-8'))
    
    # Standardize dictionary structure whether it uses 'entries' array or dict
    entries = data.get("entries", {})
    if isinstance(entries, dict):
        entries_list = list(entries.values())
    else:
        entries_list = entries

    parsed_entries = []
    for entry in entries_list:
        parsed_entries.append({
            "keys": entry.get("keys", []),
            "content": entry.get("content", ""),
            "enabled": entry.get("enabled", True),
            "insertion_order": entry.get("insertion_order", 100),
        })

    return {
        "name": data.get("name", "Imported Lorebook"),
        "entries": parsed_entries
    }
