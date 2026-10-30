import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("mimir-importers")


def parse_agent_directive(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Parses a JSON Agent Directive file containing task rules,
    file cleanup strategies, or automated memory pruning instructions.
    """
    try:
        data = json.loads(file_bytes.decode('utf-8'))
        
        # Enforce required Agent Directive fields
        return {
            "name": data.get("name", filename.rsplit(".", 1)[0]),
            "role": data.get("role", "janitor"),
            "description": data.get("description", "Custom background maintenance agent."),
            "target_paths": data.get("target_paths", ["./"]),
            "rules": data.get("rules", []),
            "config": data.get("config", {
                "max_history_versions": 2,
                "preserve_base": True,
                "auto_merge": True
            }),
            "enabled": data.get("enabled", True)
        }
    except Exception as e:
        logger.error(f"Failed to parse Agent Directive from {filename}: {e}")
        raise ValueError(f"Invalid Agent Directive JSON: {e}")


def parse_lorebook(file_bytes: bytes) -> Dict[str, Any]:
    """
    Parses project lorebooks or technical context rules (JSON) 
    and converts them into keyword-triggerable memory chunks.
    """
    try:
        data = json.loads(file_bytes.decode('utf-8'))
        entries = data.get("entries", {})
        
        # Normalize dict-based or list-based entries
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
            "name": data.get("name", "Imported Project Lorebook"),
            "entries": parsed_entries
        }
    except Exception as e:
        logger.error(f"Failed to parse project lorebook: {e}")
        raise ValueError(f"Invalid Lorebook JSON format: {e}")
