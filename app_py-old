import asyncio
import base64
import json
import os
import re
import time
import uuid
from datetime import datetime
from io import BytesIO
from typing import List, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from nicegui import app as nicegui_app, ui
from PIL import Image
from pydantic import BaseModel

# Import LLM client runner & provider profiles
from llm_client import PROVIDERS, stream_llm_response

# ==========================================
# 1. INITIALIZE FASTAPI & STATE
# ==========================================
app = FastAPI(title="Mimir Engine & Client", version="1.0.0")
st_router = APIRouter(prefix="/api/v1/st", tags=["SillyTavern Integration"])

# --- In-Memory Application State ---
session_state = {
    "character_name": "Eldrin the Alchemist",
    "character_avatar": "https://robohash.org/eldrin?bgset=bg1",
    "user_avatar": "https://robohash.org/user_me?bgset=bg2",
    "system_prompt": "You are Eldrin, a sharp-witted alchemist in a bustling metropolis.",
    "messages": [
        {
            "sender": "Eldrin",
            "text": "Ah, welcome to the workshop! Mind the steam valves. What brings you to my ledger today?",
            "is_user": False,
        }
    ],
    "last_memory_recall": [],
    "active_lorebook": [],
    "token_counter": 120,
    # --- LLM Configuration State ---
    "llm_config": {
        "provider": "Local (Ollama)",
        "api_key": "",
        "model": "llama3",
        "temperature": 0.7,
    },
}


# ==========================================
# 2. HELPER FUNCTIONS (PARSERS & TRIGGERS)
# ==========================================
def parse_character_card(file_bytes: bytes, filename: str) -> dict:
    """Parses PNG (tEXt chunk) or JSON Character Cards (V2 Spec)."""
    if filename.lower().endswith(".json"):
        return json.loads(file_bytes.decode("utf-8"))

    image = Image.open(BytesIO(file_bytes))
    metadata = image.info

    if "chara" in metadata:
        decoded_json = base64.b64decode(metadata["chara"]).decode("utf-8")
        return json.loads(decoded_json)

    if "character" in metadata:
        decoded_json = base64.b64decode(metadata["character"]).decode("utf-8")
        return json.loads(decoded_json)

    raise ValueError("No valid character card metadata found in PNG.")


def parse_lorebook(file_bytes: bytes) -> dict:
    """Parses SillyTavern / TavernAI World Info JSON files."""
    data = json.loads(file_bytes.decode("utf-8"))
    entries = data.get("entries", {})
    entries_list = (
        list(entries.values()) if isinstance(entries, dict) else entries
    )

    parsed_entries = []
    for entry in entries_list:
        parsed_entries.append(
            {
                "keys": entry.get("keys", []),
                "content": entry.get("content", ""),
                "enabled": entry.get("enabled", True),
                "insertion_order": entry.get("insertion_order", 100),
            }
        )

    return {
        "name": data.get("name", "Imported Lorebook"),
        "entries": parsed_entries,
    }


def check_lorebook_triggers(user_text: str) -> list[str]:
    """Scans active lorebook entries against user input keywords."""
    triggered_content = []
    text_lower = user_text.lower()

    for entry in session_state.get("active_lorebook", []):
        if not entry.get("enabled", True):
            continue

        keys = entry.get("keys", [])
        content = entry.get("content", "")

        if any(
            str(key).lower() in text_lower
            for key in keys
            if key and str(key).strip()
        ):
            if content:
                triggered_content.append(content)

    return triggered_content


# ==========================================
# 3. REST API ENDPOINTS
# ==========================================
@app.get("/api/v1/health")
def health_check():
    return {"status": "online", "engine": "Mimir", "db": "connected"}


@app.post("/api/v1/memory/ingest")
def ingest_chunk(payload: dict):
    return {"status": "success", "doc_id": "DOCID_1042"}


class STMessage(BaseModel):
    name: str
    is_user: bool
    send_date: int
    mes: str


class STContextRequest(BaseModel):
    character_id: str
    world_id: Optional[str] = "default"
    messages: List[STMessage]
    token_count: int


@st_router.post("/process-chat")
async def process_chat_stream(payload: STContextRequest):
    recalled_memories = [
        "User prefers skin-on-frame canoes using poplar.",
        "Character and User met in the industrial district.",
    ]
    augmented = list(payload.messages)
    if recalled_memories and len(augmented) > 0:
        memory_block = "\n".join([f"- {m}" for m in recalled_memories])
        system_note = STMessage(
            name="System",
            is_user=False,
            send_date=int(time.time()),
            mes=f"[Mimir Engine Recalled Memories]:\n{memory_block}",
        )
        augmented.insert(-1, system_note)

    return {
        "augmented_messages": augmented,
        "injected_memories": recalled_memories,
        "doc_id": f"DOCID_{int(time.time())}",
    }


app.include_router(st_router)


# ==========================================
# 4. PAGE 1: MIMIR DASHBOARD ('/')
# ==========================================
@ui.page("/")
def dashboard():
    ui.colors(primary="#6366f1", dark="#0f172a")

    with ui.header().classes(
        "bg-slate-900 justify-between items-center px-6 py-3 border-b border-slate-800"
    ):
        ui.label("🛡️ MIMIR ENGINE").classes(
            "text-xl font-bold tracking-wider text-indigo-400"
        )
        with ui.row().classes("items-center gap-4"):
            ui.button(
                "Launch Chat Client 💬",
                on_click=lambda: ui.navigate.to("/chat"),
            ).classes("bg-indigo-600 hover:bg-indigo-500 text-xs")
            ui.badge("Postgres: Connected", color="emerald").classes("px-3 py-1")
            ui.label("Port: 59056").classes("text-slate-400 text-sm")

    with ui.column().classes(
        "w-full max-w-7xl mx-auto p-6 gap-6 bg-slate-950 min-h-screen text-slate-100"
    ):
        with ui.row().classes("w-full gap-4 border-b border-slate-800 pb-6"):
            with ui.card().classes(
                "flex-1 bg-slate-900 border border-slate-800 p-4"
            ):
                ui.label("CONTAINER STACK").classes(
                    "text-xs font-semibold text-slate-400"
                )
                ui.label("Running").classes(
                    "text-2xl font-bold text-emerald-400 mt-1"
                )
                ui.label("Up time: Active").classes(
                    "text-xs text-slate-500 mt-2"
                )

            with ui.card().classes(
                "flex-1 bg-slate-900 border border-slate-800 p-4"
            ):
                ui.label("INDEXED MEMORIES").classes(
                    "text-xs font-semibold text-slate-400"
                )
                ui.label("1,248 DOCIDs").classes(
                    "text-2xl font-bold text-indigo-400 mt-1"
                )
                ui.label("Total Chunks: 3,890").classes(
                    "text-xs text-slate-500 mt-2"
                )

            with ui.card().classes(
                "flex-1 bg-slate-900 border border-slate-800 p-4"
            ):
                ui.label("PGVECTOR STORAGE").classes(
                    "text-xs font-semibold text-slate-400"
                )
                ui.label("42.8 MB").classes(
                    "text-2xl font-bold text-cyan-400 mt-1"
                )
                ui.label("Table: memory_db").classes(
                    "text-xs text-slate-500 mt-2"
                )

        with ui.row().classes("w-full gap-6"):
            with ui.column().classes("w-1/3 gap-4"):
                ui.label("Engine Controls").classes(
                    "text-lg font-semibold text-slate-200"
                )
                ui.button(
                    "Restart Memory Worker",
                    icon="refresh",
                    on_click=lambda: log_view.push(
                        f"[{datetime.now().strftime('%H:%M:%S')}] Worker restarted."
                    ),
                ).classes("w-full bg-indigo-600 hover:bg-indigo-500")
                ui.button(
                    "Run Deduplication Sweep",
                    icon="cleaning_services",
                    on_click=lambda: log_view.push(
                        f"[{datetime.now().strftime('%H:%M:%S')}] Deduplication sweep started..."
                    ),
                ).classes(
                    "w-full bg-slate-800 border border-slate-700 hover:bg-slate-700"
                )
                ui.button(
                    "Purge Temporary Cache",
                    icon="delete_sweep",
                    on_click=lambda: log_view.push(
                        f"[{datetime.now().strftime('%H:%M:%S')}] Cache cleared."
                    ),
                ).classes(
                    "w-full bg-rose-950 border border-rose-800 text-rose-300 hover:bg-rose-900"
                )

            with ui.column().classes("w-2/3 gap-2"):
                ui.label("Live Ingestion Stream").classes(
                    "text-lg font-semibold text-slate-200"
                )
                log_view = ui.log(max_lines=100).classes(
                    "w-full h-64 bg-slate-900 border border-slate-800 font-mono text-xs text-emerald-400 p-4 rounded"
                )
                log_view.push(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Mimir Engine initialized on port 59056."
                )
                log_view.push(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Connected to Postgres (pgvector) container at 127.0.0.1:59057."
                )


# ==========================================
# 5. PAGE 2: NATIVE CHAT CLIENT ('/chat')
# ==========================================
@ui.page("/chat")
def chat_client():
    ui.colors(primary="#6366f1", dark="#0f172a")

    # --- MODAL 1: Asset Upload Dialog ---
    def open_import_dialog():
        with ui.dialog() as dialog, ui.card().classes(
            "bg-slate-900 border border-slate-800 p-6 w-96 text-slate-100"
        ):
            ui.label("IMPORT ASSETS").classes(
                "text-sm font-bold text-indigo-400 mb-2"
            )

            ui.label("Character Card (.png / .json)").classes(
                "text-xs text-slate-400 mt-2"
            )

            async def handle_card_upload(e):
                try:
                    filename = getattr(e, "name", None) or getattr(getattr(e, "file", None), "name", "card.json")
                    if hasattr(e, "content"):
                        content = e.content.read()
                    elif hasattr(e, "file"):
                        if hasattr(e.file, "content"):
                            content = e.file.content.read()
                        elif hasattr(e.file, "read"):
                            content = await e.file.read() if asyncio.iscoroutinefunction(e.file.read) else e.file.read()
                        else:
                            content = getattr(e.file, "_data", b"")
                    else:
                        content = b""

                    data = parse_character_card(content, filename)
                    card_data = data.get("data", data)
                    
                    char_name = card_data.get("name", "Unknown Character")
                    session_state["character_name"] = char_name
                    
                    desc = card_data.get("description", "")
                    personality = card_data.get("personality", "")
                    scenario = card_data.get("scenario", "")
                    session_state["system_prompt"] = f"{desc}\n\n{personality}\n\n{scenario}".strip()

                    first_mes = card_data.get("first_mes", f"Hello! I am {char_name}.")
                    session_state["messages"] = [
                        {
                            "sender": char_name,
                            "text": first_mes,
                            "is_user": False,
                        }
                    ]

                    ui.notify(f"Loaded character: {session_state['character_name']}", type="positive")
                    dialog.close()
                    render_chat_messages.refresh()
                except Exception as err:
                    ui.notify(f"Card error: {str(err)}", type="negative")

            ui.upload(on_upload=handle_card_upload, auto_upload=True).classes(
                "w-full"
            ).props('accept=".png, .json"')

            ui.label("Lorebook / World Info (.json)").classes(
                "text-xs text-slate-400 mt-4"
            )

            async def handle_lorebook_upload(e):
                try:
                    if hasattr(e, "content"):
                        content = e.content.read()
                    elif hasattr(e, "file"):
                        if hasattr(e.file, "content"):
                            content = e.file.content.read()
                        elif hasattr(e.file, "read"):
                            content = await e.file.read() if asyncio.iscoroutinefunction(e.file.read) else e.file.read()
                        else:
                            content = getattr(e.file, "_data", b"")
                    else:
                        content = b""

                    lore_data = parse_lorebook(content)
                    session_state["active_lorebook"] = lore_data["entries"]

                    ui.notify(f"Loaded {len(lore_data['entries'])} lorebook entries!", type="positive")
                    dialog.close()
                    render_inspector.refresh()
                except Exception as err:
                    ui.notify(f"Lorebook error: {str(err)}", type="negative")

            ui.upload(
                on_upload=handle_lorebook_upload, auto_upload=True
            ).classes("w-full").props('accept=".json"')
            ui.button("Close", on_click=dialog.close).classes(
                "mt-4 w-full bg-slate-800"
            )

        dialog.open()

    # --- MODAL 2: LLM Settings Dialog ---
    def open_llm_settings():
        with ui.dialog() as dialog, ui.card().classes(
            "bg-slate-900 border border-slate-800 p-6 w-96 text-slate-100"
        ):
            ui.label("LLM BACKEND SETTINGS").classes(
                "text-sm font-bold text-indigo-400 mb-2"
            )

            provider_dropdown = ui.select(
                options=list(PROVIDERS.keys()),
                value=session_state["llm_config"]["provider"],
            ).classes("w-full").props("outlined dark")

            model_input = ui.input(
                "Model Identifier",
                value=session_state["llm_config"]["model"],
            ).classes("w-full mt-2").props("outlined dark")

            key_input = ui.input(
                "API Key (for Cloud / OpenRouter)",
                value=session_state["llm_config"]["api_key"],
                password=True,
            ).classes("w-full mt-2").props("outlined dark")

            def save_and_close():
                session_state["llm_config"]["provider"] = provider_dropdown.value
                session_state["llm_config"]["model"] = model_input.value
                session_state["llm_config"]["api_key"] = key_input.value
                ui.notify("LLM configuration saved!", type="positive")
                dialog.close()

            ui.button("Save Configuration", on_click=save_and_close).classes(
                "mt-4 w-full bg-indigo-600"
            )

        dialog.open()

    # --- User Chat Event Handler ---
    async def handle_user_send(user_input_field):
        user_text = user_input_field.value.strip()
        if not user_text:
            return

        user_input_field.value = ""
        session_state["messages"].append(
            {"sender": "You", "text": user_text, "is_user": True}
        )
        session_state["token_counter"] += len(user_text.split()) * 2

        lore_matches = check_lorebook_triggers(user_text)

        recalled_facts = [
            {
                "doc_id": "DOCID_1084",
                "similarity": 0.89,
                "fact": "User prefers skin-on-frame canoes using poplar.",
            },
        ]
        session_state["last_memory_recall"] = recalled_facts

        render_chat_messages.refresh()
        render_inspector.refresh()

        assistant_msg = {
            "sender": session_state["character_name"],
            "text": "",
            "is_user": False,
        }
        session_state["messages"].append(assistant_msg)

        prompt_payload = [
            {"role": "system", "content": session_state["system_prompt"]}
        ]
        if lore_matches:
            prompt_payload.append(
                {"role": "system", "content": "LOREBOOK:\n" + "\n".join(lore_matches)}
            )

        for msg in session_state["messages"][-6:]:
            if msg["text"]:
                role = "user" if msg["is_user"] else "assistant"
                prompt_payload.append({"role": role, "content": msg["text"]})

        cfg = session_state["llm_config"]

        try:
            async for token in stream_llm_response(
                provider_name=cfg["provider"],
                api_key=cfg["api_key"],
                model_name=cfg["model"],
                messages=prompt_payload,
            ):
                assistant_msg["text"] += token
                render_chat_messages.refresh()
                await ui.run_javascript(
                    "window.scrollTo(0, document.body.scrollHeight)"
                )
        except Exception as err:
            assistant_msg["text"] = f"[LLM Error: {str(err)}]"
            render_chat_messages.refresh()

    # --- TOP HEADER BAR ---
    with ui.header().classes(
        "bg-slate-900 justify-between items-center px-6 py-3 border-b border-slate-800"
    ):
        ui.label("🛡️ MIMIR CHAT CLIENT").classes(
            "text-xl font-bold tracking-wider text-indigo-400"
        )
        with ui.row().classes("gap-2"):
            ui.button("LLM Settings ⚙️", on_click=open_llm_settings).classes(
                "bg-slate-800 hover:bg-slate-700 text-xs"
            )
            ui.button("Import Assets 📥", on_click=open_import_dialog).classes(
                "bg-indigo-600 hover:bg-indigo-500 text-xs"
            )
            ui.button(
                "‹ Back to Dashboard", on_click=lambda: ui.navigate.to("/")
            ).classes("bg-slate-800 hover:bg-slate-700 text-xs")

    # --- HUD METRICS BAR ---
    with ui.row().classes(
        "w-full bg-slate-900 border-b border-slate-800 px-6 py-2 items-center justify-between font-mono text-xs text-slate-300"
    ):
        with ui.row().classes("items-center gap-3 w-1/3"):
            ui.label("TOKEN SLICE:").classes("font-bold text-slate-400")
            ui.linear_progress(
                value=session_state["token_counter"] / 300,
                show_value=False,
            ).classes("flex-grow h-3 rounded bg-slate-950 text-indigo-500")
            ui.label(
                f"{session_state['token_counter']}/300"
            ).classes("text-indigo-400 font-bold")

        with ui.row().classes("items-center gap-2"):
            ui.icon("memory", color="emerald").classes("text-base")
            ui.label("LLM:").classes("text-slate-400 font-bold")
            ui.label(
                f"{session_state['llm_config']['provider']} ({session_state['llm_config']['model']})"
            ).classes("text-emerald-400")

        with ui.row().classes("items-center gap-2"):
            ui.icon("menu_book", color="indigo").classes("text-base")
            ui.label("LOREBOOK:").classes("text-slate-400 font-bold")
            ui.label(
                f"{len(session_state['active_lorebook'])} Entries"
            ).classes("text-indigo-400")

    # --- MAIN WORKSPACE ---
    with ui.row().classes(
        "w-full h-[calc(100vh-110px)] no-wrap gap-0 bg-slate-950 text-slate-100"
    ):
        # Left Column: Chat Feed
        with ui.column().classes("w-2/3 h-full p-6 justify-between flex-grow"):
            with ui.column().classes("w-full flex-grow overflow-y-auto gap-4 pr-2"):

                @ui.refreshable
                def render_chat_messages():
                    for msg in session_state["messages"]:
                        ui.chat_message(
                            text=msg["text"],
                            name=msg["sender"],
                            sent=msg["is_user"],
                            avatar=(
                                session_state["user_avatar"]
                                if msg["is_user"]
                                else session_state["character_avatar"]
                            ),
                        ).classes("w-full max-w-3xl")

                render_chat_messages()

            with ui.row().classes("w-full items-center gap-2 pt-4 border-t border-slate-800"):
                msg_input = (
                    ui.input(placeholder="Type your turn...")
                    .classes("flex-grow bg-slate-900 rounded-lg px-4")
                    .props("outlined dark")
                )
                msg_input.on("keydown.enter", lambda: handle_user_send(msg_input))
                ui.button(
                    icon="send", on_click=lambda: handle_user_send(msg_input)
                ).classes("bg-indigo-600 h-12 w-12")

        # Right Column: Accordion Control Drawer
        with ui.column().classes("w-1/3 h-full bg-slate-900 border-l border-slate-800 p-4 gap-3 overflow-y-auto"):
            ui.label("CONTROL PANEL & MEMORIES").classes("text-xs font-bold tracking-wider text-indigo-400 px-2 py-1")

            with ui.expansion("🎭 Character & Persona", icon="person").classes("w-full bg-slate-950 border border-slate-800 rounded text-slate-200"):
                with ui.column().classes("p-3 gap-3 w-full"):
                    ui.label("Active Character").classes("text-xs text-slate-400 font-bold")
                    ui.input("Character Name", value=session_state["character_name"]).classes("w-full").props("outlined dark dense")
                    
                    ui.label("Active User Persona").classes("text-xs text-slate-400 font-bold mt-2")
                    persona_select = ui.select(
                        options=["Default User", "Engineer Persona", "Investigator Persona"],
                        value="Default User"
                    ).classes("w-full").props("outlined dark dense")
                    
                    ui.button("Load Character Card (.png/.json)", on_click=open_import_dialog).classes("w-full bg-indigo-600 text-xs mt-2")

            with ui.expansion("📖 Lorebook & World Info", icon="auto_stories").classes("w-full bg-slate-950 border border-slate-800 rounded text-slate-200"):
                with ui.column().classes("p-3 gap-2 w-full"):
                    with ui.row().classes("justify-between w-full items-center"):
                        ui.label("Active Entries:").classes("text-xs text-slate-400")
                        ui.badge(f"{len(session_state['active_lorebook'])} Loaded", color="indigo").classes("text-xs")
                    
                    ui.button("Import / Swap Lorebook JSON", on_click=open_import_dialog).classes("w-full bg-slate-800 hover:bg-slate-700 text-xs mt-2")
                    
                    if session_state["active_lorebook"]:
                        ui.button("Detach Lorebook", on_click=lambda: (session_state.update({"active_lorebook": []}), render_inspector.refresh())).classes("w-full bg-rose-950 border border-rose-800 text-rose-300 text-xs")

            with ui.expansion("⚡ Memory Hover-Thrusters (pgvector)", icon="analytics", value=True).classes("w-full bg-slate-950 border border-slate-800 rounded text-slate-200"):
                with ui.column().classes("p-3 gap-2 w-full"):
                    ui.label("Recalled Chunks for Last Turn").classes("text-xs text-slate-400")
                    
                    @ui.refreshable
                    def render_inspector():
                        if not session_state["last_memory_recall"]:
                            ui.label("No active vector recalls.").classes("text-xs text-slate-600 italic py-2")
                            return

                        for item in session_state["last_memory_recall"]:
                            with ui.card().classes("w-full bg-slate-900 border border-slate-800 p-3 gap-1"):
                                with ui.row().classes("justify-between w-full"):
                                    ui.badge(item["doc_id"], color="indigo").classes("text-xs")
                                    ui.label(f"Sim: {item['similarity']}").classes("text-xs text-emerald-400 font-mono")
                                ui.label(item["fact"]).classes("text-xs text-slate-300 mt-1")

                    render_inspector()


# ==========================================
# 6. MOUNT NICEGUI TO FASTAPI
# ==========================================
ui.run_with(
    app, title="Mimir Engine & Client", storage_secret="mimir_secret_key_123"
)
