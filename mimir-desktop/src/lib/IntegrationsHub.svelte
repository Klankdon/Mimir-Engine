<script lang="ts">
  // Provider selection: 'cloudflare' | 'tailscale' | 'ngrok' | 'local'
  let selectedProvider: 'cloudflare' | 'tailscale' | 'ngrok' | 'local' = $state('cloudflare');
  
  let cloudflareUrl = $state('https://your-tunnel.trycloudflare.com/v1');
  let tailscaleIp = $state('http://100.x.y.z:8000/v1');
  let ngrokUrl = $state('https://your-subdomain.ngrok-free.app/v1');
  let localUrl = $state('http://localhost:8000/v1');

  function copyText(text: string) {
    navigator.clipboard.writeText(text);
  }
</script>

<div class="card">
  <div class="card-header">
    <h3>🔒 Network Ingress & Proxy Provider</h3>
    <span class="badge active">{selectedProvider.toUpperCase()} ACTIVE</span>
  </div>
  
  <p class="sub-text">
    Select the remote connection tool or external proxy middleware you prefer to route traffic into Mimir Engine.
  </p>

  <!-- Provider Dropdown Selector -->
  <div class="selector-group">
    <label for="provider-select" class="select-label">Choose Ingress Protocol / Provider:</label>
    <select id="provider-select" bind:value={selectedProvider} class="provider-dropdown">
      <option value="cloudflare">Cloudflare Tunnel (Zero-Config HTTPS)</option>
      <option value="tailscale">Tailscale Mesh Network (Private Encrypted)</option>
      <option value="ngrok">ngrok Tunnel (Public Port Forwarding)</option>
      <option value="aisniffer">AI-Sniffer Logger (External Proxy Service)</option>
      <option value="local">Local Direct Binding (localhost / LAN)</option>
    </select>
  </div>

  <!-- Dynamic Instructions & Endpoint Box based on selection -->
  <div class="provider-details">
    {#if selectedProvider === 'cloudflare'}
      <div class="route-header">
        <span class="tag cloudflare">Cloudflare</span>
        <span>Free TryCloudflare or Custom Tunnel Endpoint</span>
      </div>
      <div class="url-box">
        <code class="endpoint-code">{cloudflareUrl}</code>
        <button class="copy-btn" onclick={() => copyText(cloudflareUrl)}>📋 Copy</button>
      </div>
      <p class="provider-hint">Point third-party frontends (SillyTavern/Agnai) to your Cloudflare HTTPS URL.</p>

    {:else if selectedProvider === 'tailscale'}
      <div class="route-header">
        <span class="tag tailscale">Tailscale</span>
        <span>Internal Mesh Network IP Binding</span>
      </div>
      <div class="url-box">
        <code class="endpoint-code">{tailscaleIp}</code>
        <button class="copy-btn" onclick={() => copyText(tailscaleIp)}>📋 Copy</button>
      </div>
      <p class="provider-hint">Use your Tailscale 100.x.y.z node address for private cross-device routing.</p>

    {:else if selectedProvider === 'ngrok'}
      <div class="route-header">
        <span class="tag ngrok">ngrok</span>
        <span>Public Forwarding Interceptor Endpoint</span>
      </div>
      <div class="url-box">
        <code class="endpoint-code">{ngrokUrl}</code>
        <button class="copy-btn" onclick={() => copyText(ngrokUrl)}>📋 Copy</button>
      </div>
      <p class="provider-hint">Copy your active ngrok public tunnel URL into your frontend configuration.</p>

    {:else if selectedProvider === 'aisniffer'}
      <div class="route-header">
        <span class="tag sniffer">AI-Sniffer</span>
        <span>External AI-Sniffer Logger Proxy Endpoint</span>
      </div>
      <div class="url-box">
        <code class="endpoint-code">{snifferPort}</code>
        <button class="copy-btn" onclick={() => copyText(snifferPort)}>📋 Copy</button>
      </div>
      <p class="provider-hint">Routes traffic through your standalone AI-Sniffer instance before hitting Mimir.</p>

    {:else if selectedProvider === 'local'}
      <div class="route-header">
        <span class="tag local">Local</span>
        <span>Direct Localhost API Endpoint</span>
      </div>
      <div class="url-box">
        <code class="endpoint-code">{localUrl}</code>
        <button class="copy-btn" onclick={() => copyText(localUrl)}>📋 Copy</button>
      </div>
      <p class="provider-hint">Standard local connection for frontends running on the same machine.</p>
    {/if}
  </div>
</div>

<style>
  .card-header { display: flex; justify-content: space-between; align-items: center; }
  .badge.active { 
    font-size: 0.65rem; 
    background: rgba(56, 189, 248, 0.15); 
    color: #38bdf8; 
    padding: 3px 8px; 
    border-radius: 4px; 
    border: 1px solid rgba(56, 189, 248, 0.3); 
    font-weight: bold;
  }

  .selector-group { margin: 14px 0; display: flex; flex-direction: column; gap: 6px; }
  .select-label { font-size: 0.82rem; color: rgba(255, 255, 255, 0.7); }

  .provider-dropdown {
    width: 100%;
    padding: 10px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #fff;
    font-size: 0.88rem;
    cursor: pointer;
  }

  .provider-dropdown option { background: #0f172a; color: #fff; }

  .provider-details { margin-top: 14px; }
  .route-header { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: rgba(255, 255, 255, 0.8); margin-bottom: 6px; }

  .tag { font-size: 0.65rem; font-weight: bold; text-transform: uppercase; padding: 2px 6px; border-radius: 4px; }
  .tag.cloudflare { background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.4); }
  .tag.tailscale { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }
  .tag.ngrok { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
  .tag.local { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }

  .url-box { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
  .endpoint-code { 
    flex: 1; 
    padding: 8px 12px; 
    background: rgba(0, 0, 0, 0.4); 
    border-radius: 6px; 
    color: #34d399; 
    font-family: monospace; 
    font-size: 0.85rem; 
  }

  .copy-btn { 
    padding: 8px 14px; 
    background: rgba(255, 255, 255, 0.1); 
    border: 1px solid rgba(255, 255, 255, 0.2); 
    color: #fff; 
    border-radius: 6px; 
    cursor: pointer; 
  }
  .copy-btn:hover { background: rgba(255, 255, 255, 0.2); }

  .provider-hint { font-size: 0.75rem; color: rgba(255, 255, 255, 0.4); margin: 4px 0 0 0; }
</style>