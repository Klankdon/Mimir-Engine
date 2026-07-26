import base64
from io import BytesIO
import json
import os
import zipfile
from PIL import Image

# Base storage directory matching app config
MIMIR_BASE_DIR = os.getenv("MIMIR_DATA_DIR", "./mimir_data")


def parse_character_card(file_bytes: bytes, filename: str) -> dict:
  """Parses PNG (tEXt chunk) or JSON Character Cards (V2 Spec) and saves a local copy."""
  parsed_data = {}

  if filename.lower().endswith(".json"):
    parsed_data = json.loads(file_bytes.decode("utf-8"))
  else:
    # If PNG, open with Pillow and search for character metadata chunks
    image = Image.open(BytesIO(file_bytes))
    metadata = image.info

    # V2 spec stores data in 'chara' base64 chunk
    if "chara" in metadata:
      decoded_json = base64.b64decode(metadata["chara"]).decode("utf-8")
      parsed_data = json.loads(decoded_json)
    # Legacy spec fallback
    elif "character" in metadata:
      decoded_json = base64.b64decode(metadata["character"]).decode("utf-8")
      parsed_data = json.loads(decoded_json)
    else:
      raise ValueError("No valid character card metadata found in PNG.")

  # Save persistent copy to /mimir_data/cards/
  cards_dir = os.path.join(MIMIR_BASE_DIR, "cards")
  os.makedirs(cards_dir, exist_ok=True)
  save_path = os.path.join(cards_dir, filename)
  with open(save_path, "wb") as f:
    f.write(file_bytes)

  return parsed_data


def parse_lorebook(file_bytes: bytes, filename: str = "lorebook.json") -> dict:
  """Parses SillyTavern / TavernAI World Info JSON files and saves a local copy."""
  data = json.loads(file_bytes.decode("utf-8"))

  # Save persistent copy to /mimir_data/lorebooks/
  lore_dir = os.path.join(MIMIR_BASE_DIR, "lorebooks")
  os.makedirs(lore_dir, exist_ok=True)
  save_path = os.path.join(lore_dir, filename)
  with open(save_path, "wb") as f:
    f.write(file_bytes)

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
      "entries": parsed_entries,
  }


# ==========================================
# NEW: SKIN ZIP PACKAGE & TEXT CHUNKER HELPERS
# ==========================================


def parse_skin_package(file_bytes: bytes, filename: str) -> dict:
  """Unpacks a .mimirskin or .zip theme package into /mimir_data/skins/ and returns its manifest."""
  skin_name = os.path.splitext(filename)[0]
  skins_dir = os.path.join(MIMIR_BASE_DIR, "skins", skin_name)
  os.makedirs(skins_dir, exist_ok=True)

  with zipfile.ZipFile(BytesIO(file_bytes), "r") as zip_ref:
    zip_ref.extractall(skins_dir)

  # Read skin manifest if provided
  manifest_path = os.path.join(skins_dir, "manifest.json")
  if os.path.exists(manifest_path):
    with open(manifest_path, "r", encoding="utf-8") as f:
      return json.load(f)

  return {
      "skin_name": skin_name,
      "version": "1.0",
      "status": "extracted",
      "path": skins_dir,
  }


def chunk_text_for_memory(
    raw_text: str, max_chunk_words: int = 150, overlap_words: int = 25
) -> list[str]:
  """Splits large lore descriptions or chat histories into ~300 token slices for pgvector ingestion."""
  words = raw_text.split()
  if not words:
    return []

  chunks = []
  start = 0
  while start < len(words):
    end = start + max_chunk_words
    chunk_words = words[start:end]
    chunks.append(" ".join(chunk_words))
    start += max_chunk_words - overlap_words

  return chunks
