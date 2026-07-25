# 🗺️ Mimir-Engine Architectural Roadmap

Welcome to the long-term vision for **Mimir-Engine**. Our goal is to transform local LLM narrative sessions from heavy, context-bloated prompt setups into a modular, stage-driven, multi-user narrative ecosystem.

---

## 📌 Phase 1: Core Engine & Relational World State (Active)
- [x] **pgvector Memory Slicing:** Tight ~120–300 token memory retrieval buffers to prevent context degradation.
- [ ] **`WORLDS` Table Integration:** Establishing PostgreSQL relational schema (`worlds`, `world_scenes`, `world_characters`) to link sessions cleanly.
- [ ] **User Persona Root Anchor:** Anchoring story state to the human chatter's identity, inventory, and choices rather than static lorebooks.

---

## 🎭 Phase 2: Automated Stage Slicing & Living Worlds
- [ ] **7k Lorebook Slicer:** Automated ingestion worker that breaks heavy external worldbooks (Chub, SillyTavern, JSON/PNG) into ~500-token modular "Stage Cards."
- [ ] **Keyword & Vector Scene Swapping:** Dynamic scene switching based on chatter input or manual UI selection.
- [ ] **Dynamic World Mutations:** Optional toggle (`Save World Events`) allowing key narrative events to update active stage state in real-time.

---

## 🖥️ Phase 3: Out-of-Band Developer Console (`~`)
- [ ] **In-Universe System Oracles:** Selectable administrative personas (e.g., **CLU** for high-tech grid analysis, **Ogma** for Celtic Ogham archivist lore) residing at `char_id: 0`.
- [ ] **Isolated Debug Buffer:** Developer console execution mode that freezes story state and provides live JSON telemetry (Postgres health, vector density, token slicing stats).
- [ ] **Interactive DB Gatekeeper:** In-character confirmation prompts before unmasking direct links to local management tools (PgAdmin, NocoDB, Metabase).

---

## 🎨 Phase 4: UI Customization & DIY Theme Engine
- [ ] **Theme Variable Architecture:** Full CSS variable and layout slot separation.
- [ ] **DIY Skinning Import:** One-click `.zip` package uploader (`theme.json`, `layout.json`, custom icons/backgrounds) with downloadable example templates.

---

## 🌐 Phase 5: Multi-User Lobbies & Multiplayer Bridge
- [ ] **Multi-Persona World Lobbies:** Shared `world_id` sessions mapping multiple distinct User Persona Anchors to the same active stage and vector pool.
- [ ] **Discord / External Bridge:** Lightweight bot proxy to route multi-user channel roleplay through Mimir's backend logic.
- [ ] **Live Stage & Asset Trading:** Peer-to-peer sharing of 500-token scene modules and visual skins directly inside shared sessions.

---

💡 *Want to contribute? Pick an open issue or start a thread in **GitHub Discussions**!*
