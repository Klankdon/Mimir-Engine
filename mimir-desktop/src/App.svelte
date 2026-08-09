<script lang="ts">

  import ChatPage from './lib/ChatPage.svelte';
  import GeeksDashboard from './lib/GeeksDashboard.svelte';
  import IntegrationsHub from './lib/IntegrationsHub.svelte';

  // Svelte 5 reactive state for active page route
  let activePage = $state<'chat' | 'dashboard' | 'integrations'>('chat');
</script>

<header class="app-header">
  <div class="brand">
    <span class="logo">⚡</span>
    <h1>MIMIR <span class="engine">ENGINE</span></h1>
  </div>

  <nav class="nav-links">
    <button 
      class="nav-btn" 
      class:active={activePage === 'chat'} 
      on:click={() => activePage = 'chat'}
    >
      💬 Chat Client
    </button>
    
    <button 
      class="nav-btn" 
      class:active={activePage === 'dashboard'} 
      on:click={() => activePage = 'dashboard'}
    >
      🛠️ Geeks Dashboard
    </button>
    
    <button 
      class="nav-btn" 
      class:active={activePage === 'integrations'} 
      on:click={() => activePage = 'integrations'}
    >
      🔌 Integrations Hub
    </button>
  </nav>
</header>

<main class="viewport-container">
  {#if activePage === 'chat'}
    <ChatPage />
  {:else if activePage === 'dashboard'}
    <GeeksDashboard />
  {:else if activePage === 'integrations'}
    <IntegrationsHub />
  {/if}
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background: #0b0f17;
    color: #f1f5f9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    overflow-x: hidden;
  }

  .app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    height: 52px;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  h1 {
    font-size: 1.1rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: 1.5px;
    color: #fff;
  }

  .engine {
    color: #38bdf8;
    font-weight: 400;
  }

  .nav-links {
    display: flex;
    gap: 8px;
  }

  .nav-btn {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.7);
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .nav-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
  }

  .nav-btn.active {
    background: rgba(56, 189, 248, 0.15);
    border-color: rgba(56, 189, 248, 0.4);
    color: #38bdf8;
  }

  .viewport-container {
    height: calc(100vh - 52px);
    width: 100vw;
    box-sizing: border-box;
    padding: 12px;
  }
</style>

