<script lang="ts">
  // Existing ingress state...
  let selectedProvider: 'cloudflare' | 'tailscale' | 'ngrok' | 'local' = $state('cloudflare');
  let cloudflareUrl = $state('https://your-tunnel.trycloudflare.com/v1');
  let tailscaleIp = $state('http://100.x.y.z:8000/v1');
  let ngrokUrl = $state('https://your-subdomain.ngrok-free.app/v1');
  let localUrl = $state('http://localhost:8000/v1');

  function copyText(text: string) {
    navigator.clipboard.writeText(text);
  }

  // --- Upstream Provider State ---
  interface UpstreamProvider {
    id: string;
    name: string;
    baseUrl: string;
    apiKey: string;
    enabled: boolean;
  }

  let upstreamProviders = $state<UpstreamProvider[]>([
    {
      id: '1',
      name: 'Local Ollama / vLLM',
      baseUrl: 'http://localhost:11434/v1',
      apiKey: '',
      enabled: true
    }
  ]);

  // Modal toggle state
  let showModal = $state(false);

  // Form input state inside modal
  let newName = $state('');
  let newBaseUrl = $state('http://localhost:11434/v1');
  let newApiKey = $state('');
  let isSaving = $state(false);

  function openModal() {
    newName = '';
    newBaseUrl = 'http://localhost:11434/v1';
    newApiKey = '';
    showModal = true;
  }

  function closeModal() {
    showModal = false;
  }

  async function saveUpstreamProvider() {
    if (!newName.trim() || !newBaseUrl.trim()) return;
    
    isSaving = true;

    const newProvider: UpstreamProvider = {
      id: crypto.randomUUID(),
      name: newName,
      baseUrl: newBaseUrl,
      apiKey: newApiKey,
      enabled: true
    };

    // 1. Update frontend state
    upstreamProviders.push(newProvider);

    // 2. Sync to Python backend proxy/DB
    try {
      await fetch('/api/providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProvider)
      });
    } catch (err) {
      console.error('Failed to persist provider to proxy backend:', err);
    } finally {
      isSaving = false;
      closeModal();
    }
  }

  function removeProvider(id: string) {
    upstreamProviders = upstreamProviders.filter(p => p.id !== id);
    // Optionally trigger DELETE /api/providers/:id here
  }
</script>

<!-- Card Header with Modal Trigger -->
<div class="card style-card">
  <div class="card-header">
    <h3>🤖 Upstream LLM Providers</h3>
    <button class="action-btn" onclick={openModal}>➕ Add Upstream Target</button>
  </div>
  <p class="sub-text">
    Configure downstream LLM hosts (Ollama, LM Studio, vLLM, OpenRouter, OpenAI) that Mimir forwards requests to.
  </p>

  <!-- Configured Providers List -->
  <div class="provider-list">
    {#each upstreamProviders as provider (provider.id)}
      <div class="provider-item">
        <input type="checkbox" bind:checked={provider.enabled} />
        <div class="provider-info">
          <strong>{provider.name}</strong>
          <code>{provider.baseUrl}</code>
        </div>
        <button class="delete-btn" onclick={() => removeProvider(provider.id)}>🗑️</button>
      </div>
    {/each}
  </div>
</div>

<!-- Modal Overlay -->
{#if showModal}
  <div class="modal-backdrop" onclick={closeModal} role="presentation">
    <div class="modal-content" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <div class="modal-header">
        <h4>Add Upstream LLM Provider</h4>
        <button class="close-btn" onclick={closeModal}>✕</button>
      </div>

      <div class="modal-body">
        <label>
          Friendly Name
          <input type="text" placeholder="e.g. Local Ollama, OpenRouter" bind:value={newName} class="input-field" />
        </label>

        <label>
          Base API Endpoint URL
          <input type="text" placeholder="http://localhost:11434/v1" bind:value={newBaseUrl} class="input-field" />
        </label>

        <label>
          API Key (Optional)
          <input type="password" placeholder="sk-..." bind:value={newApiKey} class="input-field" />
        </label>
      </div>

      <div class="modal-footer">
        <button class="cancel-btn" onclick={closeModal}>Cancel</button>
        <button class="submit-btn" onclick={saveUpstreamProvider} disabled={isSaving || !newName.trim()}>
          {isSaving ? 'Registering...' : 'Upload & Register Model'}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .style-card { margin-top: 1rem; }
  .card-header { display: flex; justify-content: space-between; align-items: center; }
  .action-btn {
    padding: 6px 12px;
    background: rgba(56, 189, 248, 0.2);
    border: 1px solid rgba(56, 189, 248, 0.4);
    color: #38bdf8;
    border-radius: 6px;
    cursor: pointer;
    font-weight: bold;
  }
  .action-btn:hover { background: rgba(56, 189, 248, 0.3); }

  /* Modal Styling */
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  .modal-content {
    background: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    width: 100%;
    max-width: 450px;
    padding: 1.5rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  }
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  .modal-header h4 { margin: 0; color: #fff; font-size: 1.1rem; }
  .close-btn { background: none; border: none; color: #94a3b8; font-size: 1.2rem; cursor: pointer; }
  
  .modal-body { display: flex; flex-direction: column; gap: 1rem; }
  .modal-body label { font-size: 0.8rem; color: #94a3b8; display: flex; flex-direction: column; gap: 0.3rem; }
  
  .input-field {
    padding: 8px 12px;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    color: #fff;
    font-size: 0.88rem;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 1.5rem;
  }
  .cancel-btn {
    padding: 8px 14px;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: #ccc;
    border-radius: 6px;
    cursor: pointer;
  }
  .submit-btn {
    padding: 8px 16px;
    background: #0284c7;
    border: none;
    color: #fff;
    border-radius: 6px;
    font-weight: bold;
    cursor: pointer;
  }
  .submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

  .provider-list { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
  .provider-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
  }
  .provider-info { display: flex; flex-direction: column; flex: 1; }
  .provider-info code { font-size: 0.75rem; color: rgba(255, 255, 255, 0.5); }
  .delete-btn { background: none; border: none; cursor: pointer; }
</style>
