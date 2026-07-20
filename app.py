import asyncio
from datetime import datetime
from fastapi import FastAPI
from nicegui import app as nicegui_app, ui

# 1. Initialize FastAPI app
app = FastAPI(title="Mimir Engine API", version="1.0.0")

# --- Standard REST API Endpoints ---
@app.get("/api/v1/health")
def health_check():
    return {"status": "online", "engine": "Mimir", "db": "connected"}

@app.post("/api/v1/memory/ingest")
def ingest_chunk(payload: dict):
    # Endpoint hit by SillyTavern / Websniffer
    return {"status": "success", "doc_id": "DOCID_1042"}


# --- NiceGUI Dashboard ---
@ui.page("/")
def dashboard():
    ui.colors(primary="#6366f1", dark="#0f172a") # Dark Slate / Indigo theme
    
    # Header Banner
    with ui.header().classes("bg-slate-900 justify-between items-center px-6 py-3"):
        ui.label("🛡️ MIMIR ENGINE").classes("text-xl font-bold tracking-wider text-indigo-400")
        with ui.row().classes("items-center gap-4"):
            ui.badge("Postgres: Connected", color="emerald").classes("px-3 py-1")
            ui.label("Port: 59055").classes("text-slate-400 text-sm")

    # Main Grid Layout
    with ui.column().classes("w-full max-w-7xl mx-auto p-6 gap-6 bg-slate-950 min-h-screen text-slate-100"):
        
        # Row 1: System Status Cards (Multicraft Style)
        with ui.row().classes("w-full gap-4 border-b border-slate-800 pb-6"):
            
            # Card 1: Container Status
            with ui.card().classes("flex-1 bg-slate-900 border border-slate-800 p-4"):
                ui.label("CONTAINER STACK").classes("text-xs font-semibold text-slate-400")
                ui.label("Running").classes("text-2xl font-bold text-emerald-400 mt-1")
                ui.label("Up time: 4d 12h 30m").classes("text-xs text-slate-500 mt-2")

            # Card 2: Memory Ingestion Metrics
            with ui.card().classes("flex-1 bg-slate-900 border border-slate-800 p-4"):
                ui.label("INDEXED MEMORIES").classes("text-xs font-semibold text-slate-400")
                ui.label("1,248 DOCIDs").classes("text-2xl font-bold text-indigo-400 mt-1")
                ui.label("Total Chunks: 3,890").classes("text-xs text-slate-500 mt-2")

            # Card 3: Database Storage
            with ui.card().classes("flex-1 bg-slate-900 border border-slate-800 p-4"):
                ui.label("PGVECTOR STORAGE").classes("text-xs font-semibold text-slate-400")
                ui.label("42.8 MB").classes("text-2xl font-bold text-cyan-400 mt-1")
                ui.label("Table: memory_db").classes("text-xs text-slate-500 mt-2")

        # Row 2: Control Actions & Live Log Console
        with ui.row().classes("w-full gap-6"):
            
            # Left: Control Panel Actions
            with ui.column().classes("w-1/3 gap-4"):
                ui.label("Engine Controls").classes("text-lg font-semibold text-slate-200")
                
                ui.button("Restart Memory Worker", icon="refresh", on_click=lambda: log_view.push(f"[{datetime.now().strftime('%H:%M:%S')}] Worker restarted.")).classes("w-full bg-indigo-600 hover:bg-indigo-500")
                
                ui.button("Run Deduplication Sweep", icon="cleaning_services", on_click=lambda: log_view.push(f"[{datetime.now().strftime('%H:%M:%S')}] Deduplication sweep started...")).classes("w-full bg-slate-800 border border-slate-700 hover:bg-slate-700")
                
                ui.button("Purge Temporary Cache", icon="delete_sweep", on_click=lambda: log_view.push(f"[{datetime.now().strftime('%H:%M:%S')}] Cache cleared.")).classes("w-full bg-rose-950 border border-rose-800 text-rose-300 hover:bg-rose-900")

            # Right: Realtime Log Console
            with ui.column().classes("w-2/3 gap-2"):
                ui.label("Live Ingestion Stream").classes("text-lg font-semibold text-slate-200")
                
                # Terminal Log View
                log_view = ui.log(max_lines=100).classes("w-full h-64 bg-slate-900 border border-slate-800 font-mono text-xs text-emerald-400 p-4 rounded")
                log_view.push(f"[{datetime.now().strftime('%H:%M:%S')}] Mimir Engine initialized on port 59055.")
                log_view.push(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to Postgres (pgvector) container at 127.0.0.1:59057.")

# Mount NiceGUI directly onto the FastAPI instance
ui.run_with(
    app,
    title="Mimir Engine Dashboard",
    storage_secret="mimir_secret_key_123"
)
