<script lang="ts">
  import { onMount } from 'svelte';

  interface UpstreamModel {
    id?: string;
    modelName: string;
    friendlyName: string;
    targetRole: 'chat' | 'vibe' | 'agent';
  }

  interface UpstreamProvider {
    id: string;
    name: string;
    baseUrl: string;
    apiKey: string;
    enabled: boolean;
    models?: UpstreamModel[];
  }

  let upstreamProviders = $state<UpstreamProvider[]>([]);
  let showModal = $state(false);

  // Form Fields
  let newName = $state('');
  let newBaseUrl = $state('http://localhost:11434/v1');
  let newApiKey = $state('');
  let newModelName = $state('llama3');
  let newFriendlyName = $state('Llama 3 Instruct');
  let newTargetRole = $state<'chat' | 'vibe' | 'agent'>('chat');
  let isSaving = $state(false);

  onMount(async () => {
    try {
      const response = await fetch('/api/providers');
      if (response.ok) {
        upstreamProviders = await response.json();
      }
    } catch (err) {
      console.error('Failed to load providers from backend:', err);
    }
  });

  function openModal() {
    newName = '';
    newBaseUrl = 'http://localhost:11434/v1';
    newApiKey = '';
    newModelName = 'qwen2.5-coder';
    newFriendlyName = 'Qwen 2.5 Coder';
    newTargetRole = 'chat';
    showModal = true;
  }

  function closeModal() {
    showModal = false;
  }

  async function saveUpstreamProvider() {
    if (!newName.trim() || !newBaseUrl.trim() || !newModelName.trim()) return;
    
    isSaving = true;

    const newProviderPayload = {
      name: newName,
      baseUrl: newBaseUrl,
      apiKey: newApiKey,
      enabled: true,
      models: [
        {
          modelName: newModelName,
          friendlyName: newFriendlyName || newModelName,
          targetRole: newTargetRole
        }
      ]
    };

    try {
      const response = await fetch('/api/providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProviderPayload)
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Reload provider list to catch newly assigned provider_id and model metadata
        const reloadRes = await fetch('/api/providers');
        if (reloadRes.ok) {
          upstreamProviders = await reloadRes.json();
        }
      }
    } catch (err) {
      console.error('Failed to persist provider to proxy backend:', err);
    } finally {
      isSaving = false;
      closeModal();
    }
  }

  async function removeProvider(id: string) {
    try {
      const response = await fetch(`/api/providers/${id}`, { method: 'DELETE' });
      if (response.ok) {
        upstreamProviders = upstreamProviders.filter(p => p.id !== id);
      } else {
        alert('Failed to delete provider from database.');
      }
    } catch (err) {
      console.error('Network error during deletion:', err);
    }
  }

  async function testConnection(id: string) {
    try {
      const response = await fetch(`/api/providers/${id}/test`);
      const data = await response.json();
      
      if (data.status === 'success') {
        alert(`✅ Success: ${data.message}`);
      } else {
        alert(`❌ Failed: ${data.message}`);
      }
    } catch (err) {
      alert(`❌ Network Error: Could not reach test endpoint.`);
      console.error(err);
    }
  }
</script>

<div class="card style-card">
  <div class="card-header">
    <h3>🤖 Upstream LLM Providers & Multi-Role Router</h3>
    <button class="action-btn" onclick={openModal}>➕ Add Upstream Target</button>
  </div>
  <p class="sub-text">
    Configure upstream LLM hosts (Ollama, LM Studio, vLLM, OpenRouter, OpenAI) and assign target roles (Chat, Vibe, Agent).
  </p>

  <div class="provider-list">
    {#each upstreamProviders as provider (provider.id)}
      <div class="provider-item">
        <input type="checkbox" bind:checked={provider.enabled} />
        <div class="provider-info">
          <div class="title-row">
            <strong>{provider.name}</strong>
            {#if provider.models && provider.models.length > 0}
              {#each provider.models as model}
                <span class="role-badge {model.targetRole || 'chat'}">{model.targetRole || 'chat'}</span>
              {/each}
            {/if}
          </div>
          <code>{provider.baseUrl}</code>
        </div>
        <div class="action-buttons">
          <button class="test-btn" onclick={() => testConnection(provider.id)} title="Test Connection">🔌 Test</button>
          <button class="delete-btn" onclick={() => removeProvider(provider.id)} title="Delete Provider">🗑️</button>
        </div>
      </div>
    {/each}
  </div>
</div>

{#if showModal}
  <div class="modal-backdrop" onclick={closeModal} role="presentation">
    <div class="modal-content" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <div class="modal-header">
        <h4>Add Upstream LLM Target & Route Assignment</h4>
        <button class="close-btn" onclick={closeModal}>✕</button>
      </div>

      <div class="modal-body">
        <label>
          Provider Name
          <input type="text" placeholder="e.g. Local Ollama, LM Studio Coder" bind:value={newName} class="input-field" />
        </label>

        <label>
          Base API Endpoint URL
          <input type="text" placeholder="http://localhost:11434/v1" bind:value={newBaseUrl} class="input-field" />
        </label>

        <label>
          API Key (Optional)
          <input type="password" placeholder="sk-..." bind:value={newApiKey} class="input-field" />
        </label>

        <div class="grid-2-col">
          <label>
            Upstream Model ID
            <input type="text" placeholder="qwen2.5-coder:14b" bind:value={newModelName} class="input-field" />
          </label>

          <label>
            Assigned Target Role
            <select bind:value={newTargetRole} class="input-field select-field">
              <option value="chat">Chat (Primary Narrative)</option>
              <option value="vibe">Vibe (Code & Terminal)</option>
              <option value="agent">Agent (Background Tasks)</option>
            </select>
          </label>
        </div>
      </div>

      <div class="modal-footer">
        <button class="cancel-btn" onclick={closeModal}>Cancel</button>
        <button class="submit-btn" onclick={saveUpstreamProvider} disabled={isSaving || !newName.trim() || !newModelName.trim()}>
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
    max-width: 500px;
    padding: 1.5rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  }
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  .modal-header h4 { margin: 0; color: #fff; font-size: 1.05rem; }
  .close-btn { background: none; border: none; color: #94a3b8; font-size: 1.2rem; cursor: pointer; }
  
  .modal-body { display: flex; flex-direction: column; gap: 1rem; }
  .modal-body label { font-size: 0.8rem; color: #94a3b8; display: flex; flex-direction: column; gap: 0.3rem; }
  
  .grid-2-col { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

  .input-field {
    padding: 8px 12px;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    color: #fff;
    font-size: 0.88rem;
    outline: none;
  }
  .select-field { color: #38bdf8; font-weight: bold; }

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
    flex-wrap: wrap; /* Allows overflowing badges to wrap cleanly */
    gap: 12px;
    padding: 10px 12px;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    max-width: 100%;
    overflow: hidden;
  }

  .title-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    max-width: 100%;
  }
  
  .provider-info { display: flex; flex-direction: column; flex: 1; gap: 2px; }
  .title-row { display: flex; align-items: center; gap: 8px; }
  .provider-info code { font-size: 0.75rem; color: rgba(255, 255, 255, 0.5); }
  
  .role-badge {
    font-size: 0.62rem;
    font-weight: bold;
    padding: 2px 6px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .role-badge.chat { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
  .role-badge.vibe { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
  .role-badge.agent { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

  .action-buttons { display: flex; gap: 8px; align-items: center; }
  .delete-btn { background: none; border: none; cursor: pointer; font-size: 1.1rem; }
  
  .test-btn {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: #10b981;
    border-radius: 6px;
    padding: 4px 10px;
    cursor: pointer;
    font-size: 0.80rem;
    font-weight: bold;
  }
  .test-btn:hover { background: rgba(16, 185, 129, 0.3); }
</style>
