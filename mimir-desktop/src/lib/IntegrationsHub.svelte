<script lang="ts">
  import { onMount } from 'svelte';

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

  let upstreamProviders = $state<UpstreamProvider[]>([]);
  let showModal = $state(false);

  // Form input state inside modal
  let newName = $state('');
  let newBaseUrl = $state('http://localhost:11434/v1');
  let newApiKey = $state('');
  let isSaving = $state(false);

  // 1. Fetch saved providers from PostgreSQL when the page loads
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

    // Sync to Python backend proxy/DB first
    try {
      const response = await fetch('/api/providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProvider)
      });
      
      if (response.ok) {
        const data = await response.json();
        newProvider.id = data.id; // Use the real UUID from PostgreSQL
        upstreamProviders.push(newProvider); // Update UI
      }
    } catch (err) {
      console.error('Failed to persist provider to proxy backend:', err);
    } finally {
      isSaving = false;
      closeModal();
    }
  }

  // 2. Actually delete the provider from PostgreSQL
  async function removeProvider(id: string) {
    try {
      const response = await fetch(`/api/providers/${id}`, { method: 'DELETE' });
      if (response.ok) {
        // Remove from UI only if the backend successfully deleted it
        upstreamProviders = upstreamProviders.filter(p => p.id !== id);
      } else {
        alert('Failed to delete provider from the database.');
      }
    } catch (err) {
      console.error('Network error during deletion:', err);
    }
  }

  // --- Test Connection Function ---
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
      alert(`❌ Network Error: Could not reach the test endpoint.`);
      console.error(err);
    }
  }
</script>
