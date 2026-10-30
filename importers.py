import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("mimir-importers")

def scan_directives_directory(directives_dir: str = "directives") -> List[Dict[str, Any]]:
    """
    Scans the given directory for JSON agent directives, 
    parses them, and returns a list of valid directive objects.
    """
    directives = []
    if not os.path.exists(directives_dir):
        os.makedirs(directives_dir, exist_ok=True)
        return directives

    for filename in os.listdir(directives_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(directives_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_bytes = f.read().encode("utf-8")
                    directive = parse_agent_directive(file_bytes, filename)
                    directives.append(directive)
            except Exception as e:
                logger.error(f"Error parsing directive file {filename}: {e}")
                
    return directives

def parse_agent_directive(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Parses a JSON Agent Directive file containing task rules and constraints."""
    data = json.loads(file_bytes.decode('utf-8'))
    return {
        "id": data.get("id", filename.rsplit(".", 1)[0]),
        "name": data.get("name", filename.rsplit(".", 1)[0]),
        "role": data.get("role", "janitor"),
        "description": data.get("description", "Custom background maintenance agent."),
        "target_paths": data.get("target_paths", ["./"]),
        "rules": data.get("rules", []),
        "config": data.get("config", {
            "max_history_versions": 2,
            "preserve_base": True,
            "dry_run": false
        }),
        "enabled": data.get("enabled", True)
    }
