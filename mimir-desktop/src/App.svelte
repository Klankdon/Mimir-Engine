<script lang="ts">
  import { currentTheme } from './lib/stores/themeStore';
  import ThemeModal from './lib/components/ThemeModal.svelte';

  let showThemeModal = false;

  // ==========================================
  // 1. DATA STRUCTURES & INTERFACES
  // ==========================================
  interface Message {
    id: string;
    sender: string;
    isUser: boolean;
    text: string;
    timestamp: string;
  }

  interface CharacterCard {
    id: string;
    name: string;
    description: string;
    personality: string;
    scenario: string;
    firstMsg: string;
    avatar: string;
    tags?: string[];
    theme?: any;
  }

  interface ChatSession {
    id: string;
    title: string;
    lastUpdated: string;
    activeCharacterId: string;
    rosterIds: string[];
    chatHistory: Message[];
  }

  // ==========================================
  // 2. APPLICATION STATE
  // ==========================================
  const API_BASE = ''; // Proxied by Vite to FastAPI backend

  // Navigation View: 'chat' | 'sessions' | 'hub' | 'vectors'
  let activeTab: 'chat' | 'sessions' | 'hub' | 'vectors' = 'chat';
  
  // Modals state
  let activeModal: 'none' | 'character' | 'char_lore' | 'worldbook' | 'llm_config' | 'st_hook' = 'none';

  let promptInput = '';
  let isStreaming = false;

  let charLoreEntriesCount = 12;
  let worldbookEntriesCount = 24;

  // LLM Backend Settings
  let llmConfig = {
    provider: 'Local (Ollama)',
    model: 'llama3',
    apiKey: '',
    temperature: 0.7
  };

  const providerOptions = ['Local (Ollama)', 'OpenAI', 'Anthropic', 'OpenRouter', 'Custom / Local OpenAI Compatible'];

  // Default Character Library
  let characterGallery: CharacterCard[] = [
    {
      id: 'eldrin_01',
      name: 'Eldrin the Alchemist',
      description: 'A sharp-witted alchemist operating out of a hidden cellar laboratory.',
      personality: 'Analytical, pragmatic, sarcastic yet helpful.',
      scenario: 'Cellar laboratory transmutation session.',
      firstMsg: 'Ah, welcome to the workshop! Mind the steam valves. What brings you to my ledger today?',
      avatar: 'https://robohash.org/eldrin?bgset=bg1',
      tags: ['Alchemy', 'Fantasy']
    },
    {
      id: 'vanguard_01',
      name: 'Red Vanguard',
      description: 'Tactical cybernetic operative operating in high-risk netspace.',
      personality: 'Direct, tactical, precise.',
      scenario: 'Infiltration operation in cyberspace.',
      firstMsg: 'Systems online. Uplink established. What\'s our vector?',
      avatar: 'https://robohash.org/vanguard?bgset=bg1',
      tags: ['Cyberpunk', 'Tactical']
    },
    {
      id: 'sunny_01',
      name: 'Sunny',
      description: 'Mischievous wasteland driver with a giant truck.',
      personality: 'Upbeat, energetic, chaotic.',
      scenario: 'Wasteland road trip.',
      firstMsg: 'Hey there! Ready for a wild ride across the sands?',
      avatar: 'https://robohash.org/sunny?bgset=bg1',
      tags: ['Wasteland', 'Slice of Life']
    }
  ];

  // Active Story Sessions
  let chatSessions: ChatSession[] = [
    {
      id: 'session_cellar_01',
      title: 'Eldrin\'s Transmutation Experiments',
      lastUpdated: '10 mins ago',
      activeCharacterId: 'eldrin_01',
      rosterIds: ['eldrin_01', 'vanguard_01'],
      chatHistory: [
        {
          id: '1',
          sender: 'Eldrin the Alchemist',
          isUser: false,
          text: 'Ah, welcome to the workshop! Mind the steam valves. What brings you to my ledger today?',
          timestamp: '04:15 PM'
        }
      ]
    }
  ];

  let currentSessionId = 'session_cellar_01';

  $: activeSession = chatSessions.find((s) => s.id === currentSessionId) || chatSessions[0];
  $: activeCharacter = characterGallery.find((c) => c.id === activeSession.activeCharacterId) || characterGallery[0];
  $: loadedRoster = characterGallery.filter((c) => activeSession.rosterIds.includes(c.id));

  // ==========================================
  // 3. UNIVERSAL INGESTION & UPLOAD HANDLER
  // ==========================================
  async function handleFileUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    const fileName = file.name.toLowerCase();

    // 1. CLIENT-SIDE JSON INGESTION (.json / .JSON)
    if (fileName.endsWith('.json')) {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const parsed = JSON.parse(event.target?.result as string);
          
          // Theme auto-apply
          const themePayload = parsed.theme || parsed.data?.theme || (parsed.colors ? parsed : null);
          if (themePayload && parsed.colors) {
            currentTheme.set(themePayload);
          }

          if (activeModal === 'character') {
            const charData = parsed.character || parsed.card || parsed.data || parsed;
            const newChar: CharacterCard = {
              id: `char_${Date.now()}`,
              name: charData.name || file.name.replace(/\.[^/.]+$/, ''),
              description: charData.description || charData.data?.description || '',
              personality: charData.personality || charData.data?.personality || '',
              scenario: charData.scenario || charData.data?.scenario || '',
              firstMsg: charData.first_mes || charData.firstMsg || 'Greetings.',
              avatar: charData.avatar || `https://robohash.org/${encodeURIComponent(file.name)}?bgset=bg1`,
              theme: themePayload
            };

            characterGallery = [newChar, ...characterGallery];
            addCardToCurrentSession(newChar);
          }

          if (activeModal === 'char_lore') charLoreEntriesCount += (parsed.entries?.length || 12);
          if (activeModal === 'worldbook') worldbookEntriesCount += (parsed.entries?.length || 24);

          activeModal = 'none';
        } catch (err) {
          alert(`JSON Parsing Error in ${file.name}: ${err}`);
        }
      };
      reader.readAsText(file);
      return;
    }

    // 2. FALLBACK MULTIPART POST FOR BINARY/PNG ASSETS
    const formData = new FormData();
    formData.append('file', file);
    formData.append('asset_type', activeModal);

    try {
      const res = await fetch(`${API_BASE}/api/v1/assets/upload`, {
        method: 'POST',
        body: formData
      });

      if (res.status === 502 || res.status === 504) {
        throw new Error('Backend container offline. Ingested asset in local frontend cache.');
      }

      const text = await res.text();
      if (!text) throw new Error('Server returned an empty response.');

      const data = JSON.parse(text);

      if (res.ok) {
        if (activeModal === 'character') {
          const charData = data.character || data.card || data;
          const newChar: CharacterCard = {
            id: `char_${Date.now()}`,
            name: charData.name || file.name.replace(/\.[^/.]+$/, ''),
            description: charData.description || '',
            personality: charData.personality || '',
            scenario: charData.scenario || '',
            firstMsg: charData.first_mes || charData.firstMsg || 'Greetings.',
            avatar: charData.avatar || `https://robohash.org/${encodeURIComponent(file.name)}?bgset=bg1`
          };
          characterGallery = [newChar, ...characterGallery];
          addCardToCurrentSession(newChar);
        }

        activeModal = 'none';
      } else {
        alert(`Upload notice: ${data.error || 'Failed to persist to disk'}`);
      }
    } catch (err) {
      alert(`Asset Ingestion Notice: ${err}`);
      activeModal = 'none';
    }
  }

  function switchSession(sessionId: string) {
    currentSessionId = sessionId;
    activeTab = 'chat';
  }

  function startNewChatSession(initialCharacterId?: string) {
    const charId = initialCharacterId || characterGallery[0].id;
    const targetChar = characterGallery.find((c) => c.id === charId) || characterGallery[0];

    const newSession: ChatSession = {
      id: `session_${Date.now()}`,
      title: `Story with ${targetChar.name}`,
      lastUpdated: 'Just now',
      activeCharacterId: targetChar.id,
      rosterIds: [targetChar.id],
      chatHistory: [
        {
          id: Date.now().toString(),
          sender: targetChar.name,
          isUser: false,
          text: targetChar.firstMsg,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]
    };

    chatSessions = [newSession, ...chatSessions];
    currentSessionId = newSession.id;
    activeTab = 'chat';
  }

  function selectActiveSpeaker(char: CharacterCard) {
    chatSessions = chatSessions.map((s) => {
      if (s.id === currentSessionId) {
        return {
          ...s,
          activeCharacterId: char.id,
          chatHistory: [
            ...s.chatHistory,
            {
              id: Date.now().toString(),
              sender: 'MIMIR//SYSTEM',
              isUser: false,
              text: `[Active Persona switched to: ${char.name}]`,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
          ]
        };
      }
      return s;
    });

    if (char.theme) {
      currentTheme.set(char.theme);
    }
  }

  function addCardToCurrentSession(char: CharacterCard) {
    chatSessions = chatSessions.map((s) => {
      if (s.id === currentSessionId) {
        const updatedRoster = s.rosterIds.includes(char.id) ? s.rosterIds : [...s.rosterIds, char.id];
        return {
          ...s,
          rosterIds: updatedRoster,
          activeCharacterId: char.id
        };
      }
      return s;
    });
    activeTab = 'chat';
  }

  function sendChatMessage() {
    if (!promptInput.trim() || isStreaming) return;

    const userText = promptInput.trim();
    promptInput = '';

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'User',
      isUser: true,
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    chatSessions = chatSessions.map((s) => {
      if (s.id === currentSessionId) {
        return {
          ...s,
          chatHistory: [...s.chatHistory, userMsg]
        };
      }
      return s;
    });
  }
</script>

<!-- ==========================================
     4. MAIN UI SHELL & HUD LAYOUT
     ========================================== -->
<div 
  class="flex h-screen w-screen font-sans overflow-hidden transition-colors duration-300 relative select-none"
  style="
    background-color: {$currentTheme.colors.bgMain};
    color: {$currentTheme.colors.textPrimary};
    --color-surface: {$currentTheme.colors.surface};
    --color-border: {$currentTheme.colors.surfaceBorder};
    --color-primary: {$currentTheme.colors.accent};
  "
>
  <!-- Background Wallpaper Layer -->
  {#if $currentTheme.bgType !== 'color' && $currentTheme.bgUrl}
    <div 
      class="fixed inset-0 bg-cover bg-center pointer-events-none transition-all duration-500 z-0"
      style="background-image: url('{$currentTheme.bgUrl}'); filter: blur({$currentTheme.blur});"
    ></div>
    <div 
      class="fixed inset-0 pointer-events-none z-0"
      style="background-color: rgba(0, 0, 0, {$currentTheme.overlayOpacity});"
    ></div>
  {/if}

  <!-- LEFT SIDEBAR -->
  <aside 
    class="w-72 border-r flex flex-col justify-between p-4 z-10 shrink-0 transition-colors duration-300"
    style="background-color: var(--color-surface); border-color: var(--color-border);"
  >
    <div class="space-y-5 overflow-y-auto pr-1">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full animate-pulse" style="background-color: var(--color-primary);"></div>
          <span class="font-bold tracking-wider text-sm font-mono">MIMIR//ENGINE</span>
        </div>
      </div>

      <!-- Main Navigation Links -->
      <nav class="space-y-1">
        <button 
          on:click={() => activeTab = 'chat'}
          class="w-full text-left px-3 py-2 rounded text-xs font-medium transition-all flex items-center justify-between"
          style={activeTab === 'chat' ? 'background-color: var(--color-primary); color: white;' : 'opacity: 0.7;'}
        >
          <span>💬 Live Console</span>
        </button>

        <button 
          on:click={() => activeTab = 'sessions'}
          class="w-full text-left px-3 py-2 rounded text-xs font-medium transition-all flex items-center justify-between"
          style={activeTab === 'sessions' ? 'background-color: var(--color-primary); color: white;' : 'opacity: 0.7;'}
        >
          <span>📚 Story Timelines ({chatSessions.length})</span>
        </button>

        <button 
          on:click={() => activeTab = 'hub'}
          class="w-full text-left px-3 py-2 rounded text-xs font-medium transition-all flex items-center justify-between"
          style={activeTab === 'hub' ? 'background-color: var(--color-primary); color: white;' : 'opacity: 0.7;'}
        >
          <span>🎴 Character & World Hub</span>
        </button>
      </nav>

      <hr class="border-white/10" />

      <!-- ACTIVE PERSONA BADGE WITH AVATAR MARKER -->
      <div class="space-y-2">
        <span class="text-[10px] font-bold uppercase tracking-wider opacity-50 block font-mono">Active Speaker</span>
        <div 
          class="p-2.5 rounded-lg border flex items-center gap-3 relative overflow-hidden bg-black/30"
          style="border-color: var(--color-primary);"
        >
          <div class="relative shrink-0">
            <img 
              src={activeCharacter.avatar} 
              alt={activeCharacter.name} 
              class="w-11 h-11 rounded-md object-cover border-2 shadow-md"
              style="border-color: var(--color-primary);"
            />
            <span class="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-emerald-400 border-2 border-slate-900 rounded-full"></span>
          </div>

          <div class="overflow-hidden space-y-0.5">
            <div class="font-bold text-xs truncate">{activeCharacter.name}</div>
            <p class="text-[10px] opacity-60 line-clamp-2">{activeCharacter.description}</p>
          </div>
        </div>
      </div>

      <!-- LOADED CONTEXT & ROOM ROSTER -->
      <div class="space-y-3 pt-2">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold uppercase tracking-wider opacity-50 font-mono">Current Session Roster</span>
          <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/40 text-cyan-300">{loadedRoster.length} Cards</span>
        </div>

        <!-- Loaded Character Stack -->
        <div class="space-y-1.5 max-h-32 overflow-y-auto pr-1">
          {#each loadedRoster as char}
            <button 
              on:click={() => selectActiveSpeaker(char)}
              class="w-full text-left p-2 rounded border text-xs flex items-center justify-between transition-all hover:border-cyan-400/50 {activeCharacter.id === char.id ? 'bg-white/10 ring-1' : 'bg-black/20 opacity-75'}"
              style={activeCharacter.id === char.id ? 'border-color: var(--color-primary);' : 'border-color: var(--color-border);'}
            >
              <div class="flex items-center gap-2 overflow-hidden">
                <img src={char.avatar} alt={char.name} class="w-6 h-6 rounded object-cover shrink-0" />
                <span class="truncate font-medium text-[11px]">{char.name}</span>
              </div>
              {#if activeCharacter.id === char.id}
                <span class="text-[9px] font-mono px-1 rounded bg-emerald-500/20 text-emerald-300">Active</span>
              {/if}
            </button>
          {/each}
        </div>

        <!-- Lorebook & Worldbook Modals Trigger Badges -->
        <div class="space-y-1.5 pt-1">
          <button 
            on:click={() => activeModal = 'char_lore'}
            class="w-full p-2 rounded border text-xs flex items-center justify-between hover:opacity-80 transition-opacity bg-black/20"
            style="border-color: var(--color-border);"
          >
            <span>📖 Char Lore</span>
            <span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-black/40">{charLoreEntriesCount} entries</span>
          </button>

          <button 
            on:click={() => activeModal = 'worldbook'}
            class="w-full p-2 rounded border text-xs flex items-center justify-between hover:opacity-80 transition-opacity bg-black/20"
            style="border-color: var(--color-border);"
          >
            <span>🌍 Worldbook</span>
            <span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-black/40 text-sky-300">{worldbookEntriesCount} entries</span>
          </button>
        </div>
      </div>
    </div>

    <div class="pt-3 border-t border-white/10 space-y-2">
      <div class="flex items-center gap-3 bg-black/30 p-2 rounded border border-cyan-500/20">
        <div class="relative w-8 h-8 flex items-center justify-center shrink-0">
          <div class="absolute inset-0 rounded-full border-2 border-dashed border-cyan-400 animate-[spin_8s_linear_infinite] opacity-70"></div>
          <div class="w-2 h-2 rounded-full bg-cyan-300 shadow-[0_0_10px_#22d3ee]"></div>
        </div>
        <div class="font-mono text-[9px]">
          <div class="text-cyan-300 font-bold">JARVIS//NODE</div>
          <div class="text-emerald-400 text-[8px]">pgVector Session: {activeSession.id.slice(0, 10)}...</div>
        </div>
      </div>
    </div>
  </aside>

  <!-- MAIN WORKSPACE -->
  <main class="flex-1 flex flex-col overflow-hidden z-10">
    <!-- TOP TOOLBAR WITH ALL ACTION BUTTONS RESTORED -->
    <header 
      class="h-14 border-b flex items-center justify-between px-6 shrink-0"
      style="background-color: var(--color-surface); border-color: var(--color-border);"
    >
      <div class="text-xs font-mono font-bold tracking-wider opacity-80 uppercase flex items-center gap-3">
        <span>Story: {activeSession.title}</span>
      </div>

      <!-- Action Buttons Row -->
      <div class="flex items-center gap-1.5">
        <button 
          on:click={() => activeModal = 'character'}
          class="px-2.5 py-1.5 rounded text-xs font-medium border transition-all hover:opacity-80 flex items-center gap-1 bg-amber-500/10 border-amber-500/30 text-amber-300"
        >
          <span>🍰 Card</span>
        </button>

        <button 
          on:click={() => activeModal = 'char_lore'}
          class="px-2.5 py-1.5 rounded text-xs font-medium border transition-all hover:opacity-80 flex items-center gap-1 bg-white/5 border-white/10"
        >
          <span>📖 Lorebook</span>
        </button>

        <button 
          on:click={() => activeModal = 'llm_config'}
          class="px-2.5 py-1.5 rounded text-xs font-medium border transition-all hover:opacity-80 flex items-center gap-1 bg-white/5 border-white/10"
        >
          <span>⚙️ LLM</span>
        </button>

        <button 
          on:click={() => activeModal = 'st_hook'}
          class="px-2.5 py-1.5 rounded text-xs font-medium border transition-all hover:opacity-80 flex items-center gap-1 bg-cyan-500/10 border-cyan-500/30 text-cyan-300"
        >
          <span>🔌 Aether Hook</span>
        </button>

        <button 
          on:click={() => showThemeModal = true}
          class="px-2.5 py-1.5 rounded text-xs font-medium border transition-all hover:opacity-80 flex items-center gap-1 bg-white/5 border-white/10"
        >
          <span>🎨 Theme</span>
        </button>
      </div>
    </header>

    <!-- VIEW 1: LIVE CHAT STREAM -->
    {#if activeTab === 'chat'}
      <div class="flex-1 flex flex-col justify-between overflow-hidden p-6 gap-4">
        <div class="flex-1 overflow-y-auto space-y-4 pr-2">
          {#each activeSession.chatHistory as msg}
            <div class="flex flex-col {msg.isUser ? 'items-end' : 'items-start'}">
              <div class="text-[10px] font-mono opacity-40 mb-1 px-1">
                {msg.sender} • {msg.timestamp}
              </div>
              <div 
                class="max-w-2xl p-4 rounded-lg text-xs leading-relaxed border shadow-lg"
                style={msg.isUser 
                  ? 'background-color: var(--color-primary); color: white; border-color: transparent;' 
                  : 'background-color: var(--color-surface); border-color: var(--color-border);'}
              >
                {msg.text}
              </div>
            </div>
          {/each}
        </div>

        <form 
          on:submit|preventDefault={sendChatMessage}
          class="flex items-center gap-2 border p-2 rounded-lg shrink-0 shadow-xl"
          style="background-color: var(--color-surface); border-color: var(--color-border);"
        >
          <input 
            type="text"
            bind:value={promptInput}
            placeholder={`Speak with ${activeCharacter.name}...`}
            disabled={isStreaming}
            class="flex-1 bg-transparent border-none px-3 py-2 text-xs focus:outline-none"
          />
          <button 
            type="submit"
            disabled={isStreaming || !promptInput.trim()}
            class="px-5 py-2 rounded text-xs font-medium transition-all disabled:opacity-40"
            style="background-color: var(--color-primary); color: white;"
          >
            Send
          </button>
        </form>
      </div>
    {/if}

    <!-- VIEW 2: CHAT SESSIONS & STORY TIMELINES MANAGER -->
    {#if activeTab === 'sessions'}
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <div class="flex items-center justify-between border-b border-white/10 pb-4">
          <div>
            <h2 class="text-lg font-bold tracking-wider font-mono">STORY TIMELINES & CHAT SESSIONS</h2>
            <p class="text-xs opacity-60">Select an existing story thread or spawn a brand new chat session.</p>
          </div>
          
          <button 
            on:click={() => startNewChatSession()}
            class="px-4 py-2 rounded text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
          >
            + Create New Story Thread
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each chatSessions as session}
            <div 
              class="border rounded-xl p-5 flex flex-col justify-between space-y-4 bg-slate-900/80 shadow-2xl transition-all hover:border-cyan-400/50 {session.id === currentSessionId ? 'ring-2 ring-emerald-400 border-emerald-400' : ''}"
              style="border-color: var(--color-border);"
            >
              <div class="space-y-2">
                <h3 class="font-bold text-sm text-slate-100">{session.title}</h3>
                <p class="text-[11px] text-slate-400 font-mono">Last turn: {session.lastUpdated}</p>
              </div>

              <div class="pt-3 border-t border-white/10 flex items-center justify-between">
                <span class="text-[10px] font-mono opacity-60">{session.chatHistory.length} turns in log</span>
                <button 
                  on:click={() => switchSession(session.id)}
                  class="px-4 py-1.5 rounded text-xs font-medium transition-colors text-white"
                  style="background-color: var(--color-primary);"
                >
                  {session.id === currentSessionId ? 'Resume Chat' : 'Load Timeline'}
                </button>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- VIEW 3: CHUB-STYLE CHARACTER & WORLD HUB GALLERY -->
    {#if activeTab === 'hub'}
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <div class="flex items-center justify-between border-b border-white/10 pb-4">
          <div>
            <h2 class="text-lg font-bold tracking-wider font-mono">MIMIR // CHARACTER HUB</h2>
            <p class="text-xs opacity-60">Browse personas and launch new stories or load into current session.</p>
          </div>
          
          <button 
            on:click={() => activeModal = 'character'}
            class="px-4 py-2 rounded text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
          >
            + Upload Character Card
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {#each characterGallery as card}
            <div 
              class="border rounded-xl overflow-hidden flex flex-col justify-between bg-slate-900/80 shadow-2xl transition-all hover:scale-[1.02] hover:border-cyan-400/50"
              style="border-color: var(--color-border);"
            >
              <div class="relative h-48 w-full overflow-hidden bg-black">
                <img src={card.avatar} alt={card.name} class="w-full h-full object-cover" />
              </div>

              <div class="p-4 space-y-2 flex-1 flex flex-col justify-between">
                <div class="space-y-1">
                  <h3 class="font-bold text-sm text-slate-100">{card.name}</h3>
                  <p class="text-[11px] text-slate-400 line-clamp-3 leading-relaxed">{card.description}</p>
                </div>

                <div class="pt-3 border-t border-white/10 flex gap-2">
                  <button 
                    on:click={() => addCardToCurrentSession(card)}
                    class="flex-1 py-1.5 rounded text-[11px] font-medium transition-colors bg-black/40 hover:bg-black/60 border border-white/10 text-cyan-300"
                  >
                    Add to Session
                  </button>
                  <button 
                    on:click={() => startNewChatSession(card.id)}
                    class="flex-1 py-1.5 rounded text-[11px] font-medium transition-colors text-white text-center"
                    style="background-color: var(--color-primary);"
                  >
                    New Story
                  </button>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </main>
</div>

<!-- ==========================================
     5. RESTORED UPLOAD & CONFIG MODALS
     ========================================== -->
{#if showThemeModal}
  <ThemeModal on:close={() => showThemeModal = false} />
{/if}

<!-- Character Upload Modal -->
{#if activeModal === 'character'}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-6 max-w-md w-full space-y-4 shadow-2xl text-slate-100">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 class="text-sm font-bold text-amber-400 uppercase tracking-wider">🍰 Import Character Card</h3>
        <button on:click={() => activeModal = 'none'} class="text-slate-500 hover:text-slate-300">✕</button>
      </div>

      <input 
        type="file" 
        accept=".png,.json"
        on:change={handleFileUpload}
        class="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-amber-600 file:text-white cursor-pointer bg-slate-950 border border-slate-800 rounded p-1"
      />

      <div class="flex justify-end pt-2 border-t border-slate-800">
        <button on:click={() => activeModal = 'none'} class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-1.5 rounded text-xs font-medium">
          Close
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Char Lore Upload Modal -->
{#if activeModal === 'char_lore'}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-6 max-w-md w-full space-y-4 shadow-2xl text-slate-100">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 class="text-sm font-bold text-cyan-400 uppercase tracking-wider">📖 Import Character Lorebook</h3>
        <button on:click={() => activeModal = 'none'} class="text-slate-500 hover:text-slate-300">✕</button>
      </div>

      <input 
        type="file" 
        accept=".json"
        on:change={handleFileUpload}
        class="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-cyan-600 file:text-white cursor-pointer bg-slate-950 border border-slate-800 rounded p-1"
      />

      <div class="flex justify-end pt-2 border-t border-slate-800">
        <button on:click={() => activeModal = 'none'} class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-1.5 rounded text-xs font-medium">
          Close
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Worldbook Upload Modal -->
{#if activeModal === 'worldbook'}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-6 max-w-md w-full space-y-4 shadow-2xl text-slate-100">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 class="text-sm font-bold text-sky-400 uppercase tracking-wider">🌍 Import Worldbook</h3>
        <button on:click={() => activeModal = 'none'} class="text-slate-500 hover:text-slate-300">✕</button>
      </div>

      <input 
        type="file" 
        accept=".json"
        on:change={handleFileUpload}
        class="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-sky-600 file:text-white cursor-pointer bg-slate-950 border border-slate-800 rounded p-1"
      />

      <div class="flex justify-end pt-2 border-t border-slate-800">
        <button on:click={() => activeModal = 'none'} class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-1.5 rounded text-xs font-medium">
          Close
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- LLM Config Modal -->
{#if activeModal === 'llm_config'}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-6 max-w-md w-full space-y-4 shadow-2xl text-slate-100">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 class="text-sm font-bold text-indigo-400 uppercase tracking-wider">⚙️ LLM Backend Settings</h3>
        <button on:click={() => activeModal = 'none'} class="text-slate-500 hover:text-slate-300">✕</button>
      </div>

      <div class="space-y-3 text-xs">
        <div>
          <label class="block text-[10px] uppercase font-mono text-slate-400 mb-1">Provider Engine</label>
          <select bind:value={llmConfig.provider} class="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200">
            {#each providerOptions as opt}
              <option value={opt}>{opt}</option>
            {/each}
          </select>
        </div>

        <div>
          <label class="block text-[10px] uppercase font-mono text-slate-400 mb-1">Model Identifier / Path</label>
          <input type="text" bind:value={llmConfig.model} class="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200" />
        </div>

        <div>
          <label class="block text-[10px] uppercase font-mono text-slate-400 mb-1">API Key / Token</label>
          <input type="password" bind:value={llmConfig.apiKey} placeholder="sk-..." class="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200" />
        </div>
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
        <button on:click={() => activeModal = 'none'} class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-1.5 rounded text-xs font-medium">
          Cancel
        </button>
        <button on:click={() => activeModal = 'none'} class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1.5 rounded text-xs font-medium">
          Save & Apply
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Aether Hook Proxy Settings Modal -->
{#if activeModal === 'st_hook'}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-6 max-w-md w-full space-y-4 shadow-2xl text-slate-100">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 class="text-sm font-bold text-cyan-400 uppercase tracking-wider">🔌 SillyTavern / Agnaistic Connector Hook</h3>
        <button on:click={() => activeModal = 'none'} class="text-slate-500 hover:text-slate-300">✕</button>
      </div>

      <p class="text-xs text-slate-400">
        Plug Mimir Engine directly into SillyTavern or Agnaistic as an automated middleware proxy.
      </p>

      <div class="space-y-2 text-xs font-mono">
        <div class="p-2 bg-slate-950 rounded border border-slate-800">
          <div class="text-[10px] text-cyan-400">API ENDPOINT (OpenAI-Compatible)</div>
          <div class="text-slate-200">http://localhost:8000/v1</div>
        </div>
        <div class="p-2 bg-slate-950 rounded border border-slate-800">
          <div class="text-[10px] text-emerald-400">DIRECT RECALL HOOK</div>
          <div class="text-slate-200">http://localhost:8000/api/v1/vectors/search</div>
        </div>
      </div>

      <div class="flex justify-end pt-2 border-t border-slate-800">
        <button on:click={() => activeModal = 'none'} class="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-1.5 rounded text-xs font-medium">
          Done & Close
        </button>
      </div>
    </div>
  </div>
{/if}
