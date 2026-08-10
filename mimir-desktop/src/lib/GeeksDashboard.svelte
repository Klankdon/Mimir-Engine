<script lang="ts">
  import SidebarStatus from './SidebarStatus.svelte';

  // State management for SubSurface Dev Mode
  let devModeUnlocked = $state(false);
  let showWarningModal = $state(false);
  let activeTab = $state<'telemetry' | 'postgres'>('telemetry');

  // Sample telemetry data stream
  let telemetryLogs = $state([
    { id: 1042, time: '14:22:01', type: 'INGRESS', msg: 'Prompt received from proxy port 8000' },
    { id: 1042, time: '14:22:01', type: 'VECTOR', msg: 'pgvector distance search: 3 matches found (threshold < 0.25)' },
    { id: 1042, time: '14:22:02', type: 'INJECT', msg: 'Injected memory_id #1042 into prompt payload' },
    { id: 1042, time: '14:22:02', type: 'EGRESS', msg: 'Payload forwarded to local LLM backend' }
  ]);

  // Handle Dev Mode Toggle
  function handleDevToggle() {
    if (!devModeUnlocked) {
      showWarningModal = true;
    } else {
      devModeUnlocked = false;
    }
  }

  function confirmDevAccess() {
    devModeUnlocked = true;
    showWarningModal = false;
  }

  function cancelDevAccess() {
    devModeUnlocked = false;
    showWarningModal = false;
  }
</script>

<div class="dashboard-grid">
  <!-- Panel 1: Left Control & Status Sidebar -->
  <div class="grid-panel sidebar-panel">
    <SidebarStatus 
      docId="doc_8f91a2b"
      dbHealth="Healthy"
      pgvectorStatus="Active"
      tokensUsed={195}
      maxTokens={300}
      ramUsage={58}
    />
  </div>

  <!-- Panel 2: Center Top - Active Chat Window -->
  <div class="grid-panel chat-panel">
    <div class="panel-header">
      <span class="dot green"></span>
      <h3>Active Chat Stream</h3>
    </div>
    <div class="panel-content flex-center">
      <p class="placeholder-text">Active Chat Window Connected & Intercepting</p>
    </div>
  </div>

  <!-- Panel 3: Right Top - pgvector Keyword Inspector -->
  <div class="grid-panel keywords-panel">
    <div class="panel-header">
      <span class="dot cyan"></span>
      <h3>pgvector Keywords & Memory Links</h3>
    </div>
    <div class="panel-content">
      <div class="keyword-tags">
        <span class="tag">#location: workshop</span>
        <span class="tag">#entity: user</span>
        <span class="tag">#memory_id: 1042</span>
      </div>
      <div class="memory-card">
        <span class="mem-id">memory_id: 1042</span>
        <p class="mem-text">"User discussed constructing skin-on-frame canoe using local timber."</p>
      </div>
    </div>
  </div>

  <!-- Panel 4: Center Bottom - Database Monitor / Visual Query Tool -->
  <div class="grid-panel db-panel">
    <div class="panel-header">
      <span class="dot purple"></span>
      <h3>PostgreSQL / Table Monitor</h3>
    </div>
    <div class="panel-content flex-center">
      <p class="placeholder-text">Embedded Table / NocoDB Grid View</p>
    </div>
  </div>

  <!-- Panel 5: Right Bottom - SubSurface Console & Dev Tools -->
  <div class="grid-panel subsurface-panel">
    <div class="subsurface-header">
      <div class="title-group">
        <span class="sub-logo">⚡</span>
        <h3>SubSurface</h3>
        <span class="badge">Raw Data</span>
      </div>

      <div class="sub-controls">
        {#if devModeUnlocked}
          <div class="tab-group">
            <button class="tab-btn" class:active={activeTab === 'telemetry'} on:click={() => activeTab = 'telemetry'}>Telemetry</button>
            <button class="tab-btn" class:active={activeTab === 'postgres'} on:click={() => activeTab = 'postgres'}>SQL Tool</button>
          </div>
        {/if}

        <label class="toggle-switch">
          <input type="checkbox" checked={devModeUnlocked} on:change={handleDevToggle} />
          <span class="slider"></span>
          <span class="toggle-label">Dev Mode</span>
        </label>
      </div>
    </div>

    <div class="panel-content console-bg">
      {#if devModeUnlocked}
        {#if activeTab === 'telemetry'}
          <div class="log-stream">
            {#each telemetryLogs as log}
              <div class="log-line">
                <span class="log-time">[{log.time}]</span>
                <span class="log-type {log.type.toLowerCase()}">{log.type}</span>
                <span class="log-msg">{log.msg}</span>
              </div>
            {/each}
          </div>
        {:else}
          <div class="sql-editor">
            <textarea placeholder="SELECT * FROM mimir_memories WHERE memory_id = 1042;"></textarea>
            <button class="run-btn">Execute Query</button>
          </div>
        {/if}
      {:else}
        <div class="locked-state">
          <span class="lock-icon">🔒</span>
          <p>SubSurface Developer Mode is Locked</p>
          <p class="sub-lock">Enable Dev Mode to access unfiltered raw execution streams and the PostgreSQL manager.</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Developer Warning Modal -->
{#if showWarningModal}
  <div class="modal-backdrop">
    <div class="glass-modal">
      <div class="modal-header">
        <span class="warning-icon">⚠️</span>
        <h4>SubSurface Warning</h4>
      </div>
      <p>
        Tampering with settings or executing raw commands in the <strong>SubSurface</strong> screen can break <strong>Mimir Engine</strong> unless you know what you are doing.
      </p>
      <p class="sub-text">Are you sure you want to continue?</p>
      
      <div class="modal-actions">
        <button class="btn btn-confirm" on:click={confirmDevAccess}>Yes</button>
        <button class="btn btn-cancel" on:click={cancelDevAccess}>No</button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* 5-Panel CSS Grid Layout */
  .dashboard-grid {
    display: grid;
    grid-template-columns: 270px 1fr 340px;
    grid-template-rows: 1fr 1fr;
    gap: 12px;
    height: 100%;
    width: 100%;
    box-sizing: border-box;
  }

  .sidebar-panel { grid-column: 1; grid-row: 1 / 3; }
  .chat-panel { grid-column: 2; grid-row: 1; }
  .keywords-panel { grid-column: 3; grid-row: 1; }
  .db-panel { grid-column: 2; grid-row: 2; }
  .subsurface-panel { grid-column: 3; grid-row: 2; }

  /* Generic Panel Container */
  .grid-panel {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .panel-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    background: rgba(0, 0, 0, 0.2);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  .panel-header h3 {
    margin: 0;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: rgba(255, 255, 255, 0.7);
  }

  .dot { width: 8px; height: 8px; border-radius: 50%; }
  .dot.green { background: #10b981; }
  .dot.cyan { background: #38bdf8; }
  .dot.purple { background: #a855f7; }

  .panel-content {
    flex: 1;
    padding: 14px;
    overflow-y: auto;
  }

  .flex-center {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .placeholder-text {
    color: rgba(255, 255, 255, 0.3);
    font-size: 0.85rem;
    font-family: monospace;
  }

  /* SubSurface Header & Controls */
  .subsurface-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: rgba(0, 0, 0, 0.3);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .title-group { display: flex; align-items: center; gap: 6px; }
  .title-group h3 { margin: 0; font-size: 0.85rem; color: #38bdf8; }
  .badge { font-size: 0.6rem; background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 2px 6px; border-radius: 4px; }

  .sub-controls { display: flex; align-items: center; gap: 10px; }
  .toggle-switch { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 0.75rem; color: rgba(255, 255, 255, 0.7); }

  .console-bg { background: rgba(5, 8, 15, 0.8); font-family: "JetBrains Mono", monospace; }

  /* Log Stream */
  .log-line { font-size: 0.75rem; margin-bottom: 6px; line-height: 1.4; }
  .log-time { color: rgba(255, 255, 255, 0.4); }
  .log-type { font-weight: bold; margin: 0 4px; }
  .log-type.ingress { color: #38bdf8; }
  .log-type.vector { color: #a855f7; }
  .log-type.inject { color: #f59e0b; }
  .log-type.egress { color: #10b981; }
  .log-msg { color: rgba(255, 255, 255, 0.85); }

  /* Locked State */
  .locked-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; }
  .lock-icon { font-size: 1.8rem; margin-bottom: 8px; }
  .locked-state p { margin: 0; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7); }
  .sub-lock { font-size: 0.75rem !important; color: rgba(255, 255, 255, 0.4) !important; margin-top: 4px !important; }

  /* Modal Styling */
  .modal-backdrop { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 999; }
  .glass-modal { background: rgba(20, 24, 33, 0.9); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 12px; padding: 20px; width: 360px; color: #fff; }
  .modal-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; color: #f87171; }
  .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
  .btn { padding: 6px 14px; border-radius: 6px; border: none; cursor: pointer; font-weight: 600; font-size: 0.8rem; }
  .btn-confirm { background: #ef4444; color: white; }
  .btn-cancel { background: rgba(255, 255, 255, 0.1); color: white; }
</style>