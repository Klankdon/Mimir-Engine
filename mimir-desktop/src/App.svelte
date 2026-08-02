<script lang="ts">
  import { onMount } from 'svelte';

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
    name: string;
    description: string;
    personality: string;
    scenario: string;
    firstMsg: string;
    avatar: string;
  }

  interface VectorResult {
    doc_id: string;
    similarity: number;
    fact: string;
  }

  interface ThemePreset {
    id: string;
    name: string;
    bg: string;
    surface: string;
    border: string;
    primary: string;
    accent: string;
    text: string;
    bgImage?: string;
    bgOverlayOpacity?: number;
    isCrt?: boolean;
  }

  // ==========================================
  // 2. APPLICATION RUNTIME STATE
  // ==========================================
  const API_BASE = ''; // Proxied by Vite to FastAPI backend

  let activeTab = $state<'chat' | 'vectors'>('chat');
  let activeModal = $state<
    'none' | 'character' | 'char_lore' | 'worldbook' | 'persona' | 'persona_lore' | 'theme' | 'llm_config' | 'st_hook'
  >('none');

  let promptInput = $state('');
  let isStreaming = $state(false);
  let isSearching = $state(false);

  // Default Active Character State
  let activeCharacter = $state<CharacterCard>({
    name: 'Eldrin the Alchemist',
    description: 'A sharp-witted alchemist operating out of a hidden cellar laboratory.',
    personality: 'Analytical, pragmatic, sarcastic yet helpful.',
    scenario: 'The user has entered Eldrin laboratory seeking specialized transmutations.',
    firstMsg: 'Ah, welcome to the workshop! Mind the steam valves. What brings you to my ledger today?',
    avatar: 'https://robohash.org/eldrin?bgset=bg1'
  });

  let chatHistory = $state<Message[]>([
    {
      id: '1',
      sender: 'Eldrin the Alchemist',
      isUser: false,
      text: 'Ah, welcome to the workshop! Mind the steam valves. What brings you to my ledger today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);

  let vectorResults = $state<VectorResult[]>([]);
  let charLoreEntriesCount = $state(0);
  let worldbookEntriesCount = $state(0);

  // LLM Engine Config State
  let llmConfig = $state({
    provider: 'Local (Ollama)',
    model: 'llama3',
    apiKey: '',
    temperature: 0.7
  });

  const providerOptions = [
    'Local (Ollama)',
    'OpenAI',
    'Anthropic',
    'OpenRouter',
    'Custom / Local OpenAI-Compatible'
  ];

  // Theme & Skinning Engine State
  const themePresets: Record<string, ThemePreset> = {
    cyberpunk: {
      id: 'cyberpunk',
      name: 'Cyberpunk Slate',
      bg: '#020617',
      surface: '#0f172a',
      border: '#1e293b',
      primary: '#6366f1',
      accent: '#38bdf8',
      text: '#f8fafc'
    },
    amber_crt: {
      id: 'amber_crt',
      name: 'Retro Amber CRT',
      bg: '#0c0a09',
      surface: '#1c1917',
      border: '#292524',
      primary: '#f59e0b',
      accent: '#fbbf24',
      text: '#fef3c7',
      isCrt: true
    },
    monochrome_matrix: {
      id: 'monochrome_matrix',
      name: 'Phosphor Green Terminal',
      bg: '#050505',
      surface: '#0d130e',
      border: '#18261a',
      primary: '#22c55e',
      accent: '#4ade80',
      text: '#dcfce7'
    },
    synthwave_vamp: {
      id: 'synthwave_vamp',
      name: 'Synthwave Crimson',
      bg: '#09050d',
      surface: '#140a1d',
      border: '#261238',
      primary: '#e11d48',
      accent: '#f43f5e',
      text: '#ffe4e6'
    }
  };

  let activeTheme = $state<ThemePreset>(themePresets.cyberpunk);

  let customTheme = $state<ThemePreset>({
    id: 'custom_user',
    name: 'Custom User Theme',
    bg: '#05070f',
    surface: '#0f172a',
    border: '#1e293b',
    primary: '#6366f1',
    accent: '#38bdf8',
    text: '#f8fafc',
    bgImage: '',
    bgOverlayOpacity: 0.5
  });

  // ==========================================
  // 3. ACTION HANDLERS & API CALLS
  // ==========================================
  function applyTheme(themeKey: string) {
    if (themePresets[themeKey]) {
      activeTheme = themePresets[themeKey];
    }
  }

  function applyCustomTheme() {
    activeTheme = { ...customTheme };
    activeModal = 'none';
  }

  async function saveLLMConfig() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/llm/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: llmConfig.provider,
          model: llmConfig.model,
          api_key: llmConfig.apiKey,
          temperature: llmConfig.temperature
        })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      activeModal = 'none';
    } catch (err) {
      alert(`LLM Config save failed: ${err}`);
    }
  }

  async function handleFileUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('asset_type', activeModal);

    try {
      const res = await fetch(`${API_BASE}/api/v1/assets/upload`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (res.ok) {
        // --- CHARACTER INGESTION HANDLER ---
        if (activeModal === 'character') {
          const charData = data.character || data.card || data;
          activeCharacter = {
            name: charData.name || charData.data?.name || file.name.replace(/\.[^/.]+$/, ''),
            description: charData.description || charData.data?.description || '',
            personality: charData.personality || charData.data?.personality || '',
            scenario: charData.scenario || charData.data?.scenario || '',
            firstMsg: charData.first_mes || charData.data?.first_mes || charData.firstMsg || 'Greetings.',
            avatar: charData.avatar || `https://robohash.org/${encodeURIComponent(file.name)}?bgset=bg1`
          };

          // Reset chat history stream with the imported character greeting
          chatHistory = [
            {
              id: Date.now().toString(),
              sender: activeCharacter.name,
              isUser: false,
              text: activeCharacter.firstMsg,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
          ];
        }

        if (activeModal === 'char_lore') charLoreEntriesCount += (data.entries_count || 12);
        if (activeModal === 'worldbook') worldbookEntriesCount += (data.entries_count || 24);

        activeModal = 'none';
      } else {
        alert(`Upload error: ${data.error || 'Failed to upload asset'}`);
      }
    } catch (err) {
      alert(`Asset Ingestion Error: ${err}`);
    }
  }

  async function sendChatMessage() {
    if (!promptInput.trim() || isStreaming) return;

    const userText = promptInput.trim();
    promptInput = '';

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'User',
      isUser: true,
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    chatHistory = [...chatHistory, userMessage];

    const botMessageId = (Date.now() + 1).toString();
    const botMessage: Message = {
      id: botMessageId,
      sender: activeCharacter.name,
      isUser: false,
      text: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    chatHistory = [...chatHistory, botMessage];
    isStreaming = true;

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: userText,
          provider: llmConfig.provider,
          model: llmConfig.model
        })
      });

      if (!res.body) throw new Error('ReadableStream not supported.');
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const token = decoder.decode(value, { stream: true });
        chatHistory = chatHistory.map((msg) =>
          msg.id === botMessageId ? { ...msg, text: msg.text + token } : msg
        );
      }
    } catch (err) {
      chatHistory = chatHistory.map((msg) =>
        msg.id === botMessageId ? { ...msg, text: `[Stream Error: ${err}]` } : msg
      );
    } finally {
      isStreaming = false;
    }
  }

  async function searchVectors() {
    isSearching = true;
    try {
      const res = await fetch(`${API_BASE}/api/vectors/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'canoe poplar workshop steam', limit: 5 })
      });
      const data = await res.json();
      vectorResults = data.results || [];
    } catch (err) {
      console.error('Vector Search Error:', err);
    } finally {
      isSearching = false;
    }
  }
</script>

<!-- ==========================================
     4. HTML TEMPLATE & RESPONSIVE LAYOUT
     ========================================== -->
<div 
  class="flex h-screen w-screen font-sans overflow-hidden transition-colors duration-300 relative bg-cover bg-center bg-no-repeat select-none"
  style="
    background-color: {activeTheme.bg};
    background-image: {activeTheme.bgImage ? `url('${activeTheme.bgImage}')` : 'none'};
    color: {activeTheme.text};
    --color-surface: {activeTheme.surface};
    --color-border: {activeTheme.border};
    --color-primary: {activeTheme.primary};
    --color-accent: {activeTheme.accent};
  "
>
  <!-- Wallpaper Dimming Overlay -->
  {#if activeTheme.bgImage}
    <div 
      class="pointer-events-none fixed inset-0 z-0 bg-slate-950 transition-opacity duration-300"
      style="opacity: {activeTheme.bgOverlayOpacity ?? 0.5};"
    ></div>
  {/if}

  <!-- CRT Scanline Effect -->
  {#if activeTheme.isCrt}
    <div class="pointer-events-none fixed inset-0 z-50 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%)] bg-[length:100%_4px] opacity-40"></div>
  {/if}

  <!-- LEFT SIDEBAR: CONTEXT & LOADED ASSETS -->
  <aside 
    class="w-64 border-r flex flex-col justify-between p-4 z-10 transition-colors duration-300 shrink-0"
    style="background-color: var(--color-surface); border-color: var(--color-border);"
  >
    <div class="space-y-6">
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full animate-pulse" style="background-color: var(--color-primary);"></div>
        <span class="font-bold tracking-wider text-sm">MIMIR//ENGINE</span>
      </div>

      <!-- Navigation Tabs -->
      <nav class="space-y-1">
        <button 
          onclick={() => activeTab = 'chat'}
          class="w-full text-left px-3 py-2 rounded text-xs font-medium transition-all flex items-center justify-between"
          style={activeTab === 'chat' ? 'background-color: var(--color-primary); color: white;' : 'opacity: 0.7;'}
        >
          <span>💬 Live Console</span>
        </button>
        <button 
          onclick={() => { activeTab = 'vectors'; searchVectors(); }}
          class="w-full text-left px-3 py-2 rounded text-xs font-medium transition-all flex items-center justify-between"
          style={activeTab === 'vectors' ? 'background-color: var(--color-primary); color: white;' : 'opacity: 0.7;'}
        >
          <span>⚡ Vector Recalls (DB)</span>
        </button>
      </nav>

      <!-- Context Asset Status -->
      <div class="space-y-3">
        <span class="text-[10px] font-bold uppercase tracking-wider opacity-50 block">Loaded Context</span>

        <!-- Active Character -->
        <div class="p-2.5 rounded border text-xs space-y-1" style="border-color: var(--color-border);">
          <div class="font-bold truncate">{activeCharacter.name}</div>
          <p class="text-[11px] opacity-60 line-clamp-2">{activeCharacter.description || 'No description loaded.'}</p>
        </div>

        <!-- Lorebook Buttons -->
        <button 
          onclick={() => activeModal = 'char_lore'}
          class="w-full p-2 rounded border text-xs flex items-center justify-between hover:opacity-80 transition-opacity"
          style="border-color: var(--color-border);"
        >
          <span>📖 Char Lore</span>
          <span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-black/30">{charLoreEntriesCount} entries</span>
        </button>

        <button 
          onclick={() => activeModal = 'worldbook'}
          class="w-full p-2 rounded border text-xs flex items-center justify-between hover:opacity-80 transition-opacity"
          style="border-color: var(--color-border);"
        >
          <span>🌍 Worldbook</span>
          <span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-black/30">{worldbookEntriesCount} entries</span>
        </button>
      </div>
    </div>

    <!-- JARVIS / RAINMETER REACTOR RING & METRICS -->
    <div class="pt-4 border-t border-white/10 space-y-3">
      
      <!-- JARVIS Rotating Arc Reactor Widget -->
      <div class="flex items-center gap-3 bg-black/30 p-2.5 rounded border border-cyan-500/20">
        <div class="relative w-10 h-10 flex items-center justify-center shrink-0">
          <div class="absolute inset-0 rounded-full border-2 border-dashed border-cyan-400 animate-[spin_8s_linear_infinite] opacity-70"></div>
          <div class="absolute inset-1 rounded-full border border-indigo-500 border-t-transparent animate-[spin_3s_linear_infinite_reverse]"></div>
          <div class="w-3 h-3 rounded-full bg-cyan-400 animate-ping opacity-75"></div>
          <div class="w-2.5 h-2.5 rounded-full bg-cyan-300 shadow-[0_0_10px_#22d3ee] absolute"></div>
        </div>

        <div class="space-y-0.5 font-mono text-[10px]">
          <div class="text-cyan-300 font-bold tracking-wider">JARVIS//NODE</div>
          <div class="text-emerald-400 text-[9px]">pgVector Stream Active</div>
        </div>
      </div>

      <!-- Real-Time Token Slice Stacked Bar -->
      <div class="space-y-1 text-[10px] font-mono">
        <div class="flex justify-between opacity-70">
          <span>Context Allocation</span>
          <span>1,420 / 8,192</span>
        </div>
        
        <div class="w-full h-2 bg-black/40 rounded overflow-hidden flex border border-white/10 p-0.5">
          <div class="h-full bg-indigo-500 rounded-l" style="width: 15%" title="System Prompt"></div>
          <div class="h-full bg-sky-400" style="width: 25%" title="Char Lore / Worldbook"></div>
          <div class="h-full bg-emerald-400" style="width: 10%" title="pgVector Recalls"></div>
          <div class="h-full bg-cyan-300" style="width: 20%" title="Chat Buffer"></div>
          <div class="h-full bg-transparent" style="width: 30%"></div>
        </div>

        <div class="flex justify-between text-[8px] opacity-50 pt-0.5">
          <span class="text-indigo-400">■ System</span>
          <span class="text-sky-300">■ Lore</span>
          <span class="text-emerald-400">■ Vector</span>
          <span class="text-cyan-300">■ Chat</span>
        </div>
      </div>

    </div>
  </aside>

  <!-- MAIN WORKSPACE CONTAINER -->
  <main class="flex-1 flex flex-col overflow-hidden z-10 transition-colors duration-300">
    
    <!-- TOP TOOLBAR & INGESTION BUTTONS -->
    <header 
      class="h-14 border-b flex items-center justify-between px-6 shrink-0"
      style="background-color: var(--color-surface); border-color: var(--color-border);"
    >
      <div class="text-xs font-mono font-bold tracking-wider opacity-80 uppercase">
        Active Session // {activeTab}
      </div>

      <!-- Action Toolbar Buttons -->
      <div class="flex items-center gap-2">
        <button 
          onclick={() => activeModal = 'character'}
          class="px-3 py-1.5 rounded text-xs font-medium border transition-all hover:opacity-80"
          style="border-color: var(--color-border); background-color: rgba(255,255,255,0.05);"
        >
          📥 Card
        </button>

        <button 
          onclick={() => activeModal = 'char_lore'}
          class="px-3 py-1.5 rounded text-xs font-medium border transition-all hover:opacity-80"
          style="border-color: var(--color-border); background-color: rgba(255,255,255,0.05);"
        >
          📖 Lorebook
        </button>
        
        <button 
          onclick={() => activeModal = 'llm_config'}
          class="px-3 py-1.5 rounded text-xs font-medium border transition-all hover:opacity-80"
          style="border-color: var(--color-border); background-color: rgba(255,255,255,0.05);"
        >
          ⚙️ LLM
        </button>
        
        <button 
          onclick={() => activeModal = 'st_hook'}
          class="px-2.5 py-1.5 rounded text-xs font-medium border transition-all hover:opacity-80 text-cyan-300 border-cyan-500/30"
          style="background-color: rgba(6, 182, 212, 0.1);"
        >
          🔌 Aether Hook
        </button>

        <button 
          onclick={() => activeModal = 'theme'}
          class="px-2.5 py-1.5 rounded text-xs font-medium border transition-all hover:opacity-80"
          style="border-color: var(--color-border); background-color: rgba(255,255,255,0.05);"
        >
          🎨 Theme
        </button>
      </div>

      <div class="text-[11px] font-mono opacity-60 flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
        <span>FastAPI Docker Connected</span>
      </div>
    </header>

    <!-- VIEW TAB 1: LIVE CHAT STREAM -->
    {#if activeTab === 'chat'}
      <div class="flex-1 flex flex-col justify-between overflow-hidden p-6 gap-4">
        
        <!-- Chat History Stream -->
        <div class="flex-1 overflow-y-auto space-y-4 pr-2">
          {#each chatHistory as msg}
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

        <!-- Chat Prompt Input Bar -->
        <form 
          onsubmit={(e) => { e.preventDefault(); sendChatMessage(); }}
          class="flex items-center gap-2 border p-2 rounded-lg shrink-0 shadow-xl"
          style="background-color: var(--color-surface); border-color: var(--color-border);"
        >
          <input 
            type="text"
            bind:value={promptInput}
            placeholder="Send prompt or roleplay turn..."
            disabled={isStreaming}
            class="flex-1 bg-transparent border-none px-3 py-2 text-xs focus:outline-none"
          />
          <button 
            type="submit"
            disabled={isStreaming || !promptInput.trim()}
            class="px-5 py-2 rounded text-xs font-medium transition-all disabled:opacity-40"
            style="background-color: var(--color-primary); color: white;"
          >
            {isStreaming ? 'Streaming...' : 'Send'}
          </button>
        </form>

      </div>
    {/if}

    <!-- VIEW TAB 2: VECTOR RECALL INSPECTOR -->
    {#if activeTab === 'vectors'}
      <div class="flex-1 overflow-y-auto p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-bold tracking-wider uppercase">pgVector Memories Index</h2>
          <button 
            onclick={searchVectors}
            class="px-3 py-1.5 rounded text-xs border hover:opacity-80"
            style="border-color: var(--color-border);"
          >
            {isSearching ? 'Searching...' : 'Refresh Vector Recall'}
          </button>
        </div>

        <div class="grid grid-cols-1 gap-3">
          {#each vectorResults as vec}
            <div class="p-4 rounded border text-xs space-y-2" style="background-color: var(--color-surface); border-color: var(--color-border);">
              <div class="flex items-center justify-between font-mono text-[10px]">
                <span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">{vec.doc_id}</span>
                <span class="text-emerald-400 font-bold">Similarity: {vec.similarity}</span>
              </div>
              <p class="opacity-80">{vec.fact}</p>
            </div>
          {:else}
            <div class="p-8 text-center text-xs opacity-40 italic">
              No vector similarity matches recalled. Click 'Refresh Vector Recall' to query pgVector.
            </div>
          {/each}
        </div>
      </div>
    {/if}

  </main>
</div>

<!-- ==========================================
     5. FLOATING MODALS (HIGHEST Z-INDEX)
     ========================================== -->

<!-- 1. THEME & SKINNING MODAL -->
{#if activeModal === 'theme'}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-6 max-w-md w-full space-y-4 shadow-2xl text-slate-100">
      
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 class="text-sm font-bold text-indigo-400 uppercase tracking-wider">🎨 Theme & Skinning Engine</h3>
        <button onclick={() => activeModal = 'none'} class="text-slate-500 hover:text-slate-300">✕</button>
      </div>

      <p class="text-xs text-slate-400">Select an interface palette to reskin the HUD, borders, and accent highlights:</p>

      <div class="grid grid-cols-1 gap-2 text-xs max-h-40 overflow-y-auto pr-1">
        {#each Object.entries(themePresets) as [key, preset]}
          <button 
            onclick={() => applyTheme(key)}
            class="flex items-center justify-between p-2.5 rounded border transition-all text-left {activeTheme.id === key ? 'border-indigo-500 bg-indigo-950/40 ring-1 ring-indigo-500' : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'}"
          >
            <div class="flex items-center gap-3">
              <div class="flex gap-1">
                <span class="w-3 h-3 rounded-full" style="background-color: {preset.bg}"></span>
                <span class="w-3 h-3 rounded-full" style="background-color: {preset.primary}"></span>
                <span class="w-3 h-3 rounded-full" style="background-color: {preset.accent}"></span>
              </div>
              <span class="font-medium text-slate-200">{preset.name}</span>
            </div>
            
            {#if activeTheme.id === key}
              <span class="text-indigo-400 text-xs font-mono">● Active</span>
            {/if}
          </button>
        {/each}
      </div>

      <!-- Custom Theme & Wallpaper Injector -->
      <div class="border-t border-slate-800 pt-3 space-y-3">
        <h4 class="text-xs font-bold text-indigo-400 uppercase tracking-wider">🛠️ Custom Theme & Wallpaper</h4>
        
        <div class="space-y-2 text-xs">
          <div>
            <label class="text-slate-400 block mb-1">Background Image URL / Path</label>
            <input 
              type="text" 
              bind:value={customTheme.bgImage} 
              placeholder="https://... or /wallpapers/cyberpunk.png" 
              class="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-indigo-500 font-mono text-[11px]"
            />
          </div>

          {#if customTheme.bgImage}
            <div>
              <label class="text-slate-400 block mb-1">Wallpaper Dimming Opacity: {customTheme.bgOverlayOpacity}</label>
              <input 
                type="range" 
                min="0.1" 
                max="0.9" 
                step="0.05" 
                bind:value={customTheme.bgOverlayOpacity} 
                class="w-full accent-indigo-500"
              />
            </div>
          {/if}

          <div class="grid grid-cols-2 gap-2 pt-1">
            <div>
              <label class="text-slate-400 block mb-1">Primary Accent</label>
              <input type="color" bind:value={customTheme.primary} class="w-full h-8 bg-slate-950 border border-slate-800 rounded cursor-pointer p-0.5" />
            </div>
            <div>
              <label class="text-slate-400 block mb-1">Highlight Accent</label>
              <input type="color" bind:value={customTheme.accent} class="w-full h-8 bg-slate-950 border border-slate-800 rounded cursor-pointer p-0.5" />
            </div>
          </div>
        </div>

        <button 
          onclick={applyCustomTheme}
          class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-1.5 rounded text-xs transition-colors"
        >
          Inject Custom Theme
        </button>
      </div>

      <div class="flex justify-end pt-2 border-t border-slate-800">
        <button onclick={() => activeModal = 'none'} class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-1.5 rounded text-xs font-medium">
          Apply & Close
        </button>
      </div>

    </div>
  </div>
{/if}

<!-- 2. LLM CONFIGURATION MODAL -->
{#if activeModal === 'llm_config'}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-6 max-w-md w-full space-y-4 shadow-2xl text-slate-100">
      
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 class="text-sm font-bold text-indigo-400 uppercase tracking-wider">⚙️ LLM Backend Settings</h3>
        <button onclick={() => activeModal = 'none'} class="text-slate-500 hover:text-slate-300">✕</button>
      </div>

      <div class="space-y-3 text-xs">
        <div>
          <label class="text-slate-400 block mb-1">Provider Engine</label>
          <select 
            bind:value={llmConfig.provider}
            class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {#each providerOptions as provider}
              <option value={provider}>{provider}</option>
            {/each}
          </select>
        </div>

        <div>
          <label class="text-slate-400 block mb-1">Model Identifier / Path</label>
          <input 
            type="text" 
            bind:value={llmConfig.model} 
            placeholder="e.g. llama3, gpt-4o, claude-3-5-sonnet" 
            class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div>
          <label class="text-slate-400 block mb-1">API Key / Token</label>
          <input 
            type="password" 
            bind:value={llmConfig.apiKey} 
            placeholder="sk-..." 
            class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        <div>
          <label class="text-slate-400 block mb-1">Temperature: {llmConfig.temperature}</label>
          <input 
            type="range" 
            min="0.0" 
            max="1.5" 
            step="0.05" 
            bind:value={llmConfig.temperature} 
            class="w-full accent-indigo-500"
          />
        </div>
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
        <button onclick={() => activeModal = 'none'} class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-1.5 rounded text-xs">
          Cancel
        </button>
        <button onclick={saveLLMConfig} class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1.5 rounded text-xs font-medium">
          Save & Apply
        </button>
      </div>

    </div>
  </div>
{/if}

<!-- 3. ASSET FILE UPLOAD MODAL -->
{#if activeModal === 'character' || activeModal === 'char_lore' || activeModal === 'worldbook' || activeModal === 'persona' || activeModal === 'persona_lore'}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-6 max-w-md w-full space-y-4 shadow-2xl text-slate-100">
      
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 class="text-sm font-bold text-indigo-400 uppercase tracking-wider">
          📥 Import {activeModal.replace('_', ' ')}
        </h3>
        <button onclick={() => activeModal = 'none'} class="text-slate-500 hover:text-slate-300">✕</button>
      </div>

      <p class="text-xs text-slate-400">
        Upload a file to persist it directly to server disk (<span class="font-mono text-indigo-300">~/.mimir_data/</span>):
      </p>

      <input 
        type="file" 
        accept={activeModal === 'character' ? '.png,.json' : '.json'}
        onchange={handleFileUpload}
        class="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer bg-slate-950 border border-slate-800 rounded p-1"
      />

      <div class="flex justify-end pt-2 border-t border-slate-800">
        <button onclick={() => activeModal = 'none'} class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-1.5 rounded text-xs font-medium">
          Close
        </button>
      </div>

    </div>
  </div>
{/if}

<!-- 4. SILLYTAVERN / AGNAISTIC AETHER HOOK MODAL -->
{#if activeModal === 'st_hook'}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
    <div class="bg-slate-900 border border-cyan-500/30 rounded-lg p-6 max-w-lg w-full space-y-4 shadow-[0_0_30px_rgba(6,182,212,0.15)] text-slate-100">
      
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
          <h3 class="text-sm font-bold text-cyan-400 uppercase tracking-wider">🔌 SillyTavern / Agnai Connector Hook</h3>
        </div>
        <button onclick={() => activeModal = 'none'} class="text-slate-500 hover:text-slate-300">✕</button>
      </div>

      <p class="text-xs text-slate-300 leading-relaxed">
        Plug Mimir Engine directly into SillyTavern or Agnaistic as an automated middleware proxy. Mimir will intercept turns, perform real-time pgVector similarity searches, and inject memory context on the fly:
      </p>

      <div class="bg-slate-950 p-3 rounded border border-slate-800 space-y-2 text-xs font-mono">
        <div>
          <span class="text-slate-500 block text-[10px]">API ENDPOINT URL (OpenAI-Compatible):</span>
          <code class="text-cyan-300 select-all block bg-slate-900 p-1.5 rounded mt-0.5">http://localhost:8000/v1</code>
        </div>
        <div>
          <span class="text-slate-500 block text-[10px]">DIRECT RECALL HOOK:</span>
          <code class="text-emerald-300 select-all block bg-slate-900 p-1.5 rounded mt-0.5">http://localhost:8000/api/v1/vectors/search</code>
        </div>
      </div>

      <div class="space-y-2 text-xs">
        <label class="text-slate-400 block">Vector Context Injection Strategy</label>
        <select class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500">
          <option>Inject as System Extension Depth 2 (Recommended)</option>
          <option>Append to Character Personality / World Info</option>
          <option>Prepend to User Turn Payload</option>
        </select>
      </div>

      <div class="flex justify-end pt-2 border-t border-slate-800">
        <button onclick={() => activeModal = 'none'} class="bg-cyan-600 hover:bg-cyan-500 text-white px-5 py-1.5 rounded text-xs font-medium transition-colors">
          Done & Close
        </button>
      </div>

    </div>
  </div>
{/if}