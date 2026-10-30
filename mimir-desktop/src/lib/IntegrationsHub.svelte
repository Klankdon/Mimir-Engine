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
  
  // Model Draft List for the Modal
  let modalModels = $state<UpstreamModel[]>([
    { modelName: 'qwen2.5-coder:14b', friendlyName: 'Mimir-RAG-Chat', targetRole: 'chat' },
    { modelName: 'deepseek-coder', friendlyName: 'Qwen-Vibe-Coder', targetRole: 'vibe' }
  ]);

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
    modalModels = [
      { modelName: 'qwen2.5-coder:14b', friendlyName: 'Mimir-RAG-Chat', targetRole: 'chat' }
    ];
    showModal = true;
  }

  function closeModal() {
    showModal = false;
  }

  function addModelRow() {
    modalModels = [
      ...modalModels,
      { modelName: '', friendlyName: '', targetRole: 'agent' }
    ];
  }

  function removeModelRow(index: number) {
    modalModels = modalModels.filter((_, i) => i !== index);
  }

  async function saveUpstreamProvider() {
    if (!newName.trim() || !newBaseUrl.trim() || modalModels.length === 0) return;
    
    isSaving = true;

    const newProviderPayload = {
      name: newName,
      baseUrl: newBaseUrl,
      apiKey: newApiKey,
      enabled: true,
      models: modalModels.map(m => ({
        modelName: m.modelName,
        friendlyName: m.friendlyName || m.modelName,
        targetRole: m.targetRole
      }))
    };

    try {
      const response = await fetch('/api/providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProviderPayload)
      });
      
      if (response.ok) {
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
    <h3>🤖 Upstream LLM Providers & Custom Model Nodes</h3>
    <button class="action-btn" onclick={openModal}>➕ Add Upstream Host</button>
  </div>
  <p class="sub-text">
    Configure upstream hosts and assign custom ID/friendly names to individual models for Chat, Vibe workspace, and Agents.
  </p>

  <div class="provider-list">
    {#each upstreamProviders as provider (provider.id)}
      <div class="provider-item">
        <input type="checkbox" bind:checked={provider.enabled} title="Toggle Host" />
        <div class="provider-info">
          <div class="title-row">
            <strong>{provider.name}</strong>
            <code>{provider.baseUrl}</code>
          </div>
          
          <!-- Render Individual Custom Model Nodes Assigned to this Host -->
          <div class="model-nodes-grid">
            {#if provider.models && provider.models.length > 0}
              {#each provider.models as model}
                <div class="model-node-badge">
                  <span class="custom-id" title="Custom ID / Friendly Name">{model.friendlyName}</span>
                  <span class="raw-model">({model.modelName})</span>
                  <span class="role-pill {model.targetRole || 'chat'}">{model.targetRole || 'chat'}</span>
                </div>
              {/each}
            {/if}
          </div>
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
        <h4>Register Host & Custom Model Nodes</h4>
        <button class="close-btn" onclick={closeModal}>✕</button>
      </div>

      <div class="modal-body">
        <label>
          Provider Host Name
          <input type="text" placeholder="e.g. Local Ollama Rig, LM Studio" bind:value={newName} class="input-field" />
        </label>

        <label>
          Base API Endpoint URL
          <input type="text" placeholder="http://localhost:11434/v1" bind:value={newBaseUrl} class="input-field" />
        </label>

        <label>
          API Key (Optional)
          <input type="password" placeholder="sk-..." bind:value={newApiKey} class="input-field" />
        </label>

        <div class="models-section-header">
          <span>Assigned Model Nodes & Custom IDs</span>
          <button type="button" class="add-model-btn" onclick={addModelRow}>+ Add Model Node</button>
        </div>

        <div class="model-rows-container">
          {#each modalModels as model, index}
            <div class="model-row-card">
              <div class="model-row-inputs">
                <input type="text" placeholder="Custom ID (e.g. Mimir-RAG-Chat)" bind:value={model.friendlyName} class="input-field" />
                <input type="text" placeholder="Upstream ID (e.g. qwen2.5-coder)" bind:value={model.modelName} class="input-field" />
                <select bind:value={model.targetRole} class="input-field select-field">
                  <option value="chat">Chat (RAG)</option>
                  <option value="vibe">Vibe (Workspace)</option>
                  <option value="agent">Agent (Tasks)</option>
                </select>
              </div>
              {#if modalModels.length > 1}
                <button type="button" class="remove-row-btn" onclick={() => removeModelRow(index)}>✕</button>
              {/if}
            </div>
          {/each}
        </div>
      </div>

      <div class="modal-footer">
        <button class="cancel-btn" onclick={closeModal}>Cancel</button>
        <button class="submit-btn" onclick={saveUpstreamProvider} disabled={isSaving || !newName.trim() || modalModels.some(m => !m.modelName.trim())}>
          {isSaving ? 'Registering...' : 'Save Host & Nodes'}
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
    background: rgba(0, 0, 0, 0.75);
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
    max-width: 580px;
    padding: 1.5rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    max-height: 90vh;
    overflow-y: auto;
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
  
  .models-section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
    font-weight: bold;
    color: #38bdf8;
    margin-top: 0.50rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 0.75rem;
  }
  
  .add-model-btn {
    background: rgba(56, 189, 248, 0.15);
    border: 1px solid rgba(56, 189, 248, 0.3);
    color: #38bdf8;
    font-size: 0.75rem;
    padding: 3px 8px;
    border-radius: 4px;
    cursor: pointer;
  }
  .add-model-btn:hover { background: rgba(56, 189, 248, 0.25); }

  .model-rows-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 200px;
    overflow-y: auto;
  }

  .model-row-card {
    display: flex;
    gap: 8px;
    align-items: center;
    background: rgba(0, 0, 0, 0.25);
    padding: 8px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .model-row-inputs {
    display: grid;
    grid-template-columns: 1.2fr 1.2fr 1fr;
    gap: 6px;
    flex: 1;
  }

  .remove-row-btn {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.4);
    color: #f87171;
    border-radius: 4px;
    width: 28px;
    height: 28px;
    cursor: pointer;
    font-weight: bold;
  }

  .input-field {
    padding: 7px 10px;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    color: #fff;
    font-size: 0.82rem;
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

  .provider-list { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
  .provider-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
  }

  .provider-info { display: flex; flex-direction: column; flex: 1; gap: 8px; }
  .title-row { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
  .provider-info code { font-size: 0.75rem; color: rgba(255, 255, 255, 0.5); }

  .model-nodes-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .model-node-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 0.78rem;
  }

  .custom-id {
    color: #38bdf8;
    font-weight: bold;
  }

  .raw-model {
    color: rgba(255, 255, 255, 0.45);
    font-size: 0.72rem;
  }
  
  .role-pill {
    font-size: 0.58rem;
    font-weight: bold;
    padding: 2px 5px;
    border-radius: 3px;
    text-transform: uppercase;
  }
  .role-pill.chat { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
  .role-pill.vibe { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
  .role-pill.agent { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

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
