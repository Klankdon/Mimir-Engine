<script lang="ts">
  import ChatPage from './lib/ChatPage.svelte';
  import GeeksDashboard from './lib/GeeksDashboard.svelte';
  import IntegrationsHub from './lib/IntegrationsHub.svelte';

  // Svelte 5 Runes State
  let activePage = $state<'chat' | 'dashboard' | 'integrations'>('chat');
</script>

<header class="app-header">
  <div class="brand">
    <span class="logo">⚡</span>
    <h1>MIMIR <span class="engine">ENGINE</span></h1>
  </div>

  <nav class="nav-links">
    <!-- Notice onclick instead of on:click for Svelte 5 -->
    <button 
      class="nav-btn" 
      class:active={activePage === 'chat'} 
      onclick={() => activePage = 'chat'}
    >
      💬 Chat Client
    </button>
    
    <button 
      class="nav-btn" 
      class:active={activePage === 'dashboard'} 
      onclick={() => activePage = 'dashboard'}
    >
      🛠️ Geeks Dashboard
    </button>
    
    <button 
      class="nav-btn" 
      class:active={activePage === 'integrations'} 
      onclick={() => activePage = 'integrations'}
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
