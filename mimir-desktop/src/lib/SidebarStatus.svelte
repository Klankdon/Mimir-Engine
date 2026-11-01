<script lang="ts">
  interface Props {
    docId?: string;
    dbHealth?: string;
    pgvectorStatus?: string;
    tokensUsed?: number;
    maxTokens?: number;
    ramUsage?: number;
  }

  let { 
    docId = 'doc_8f91a2b', 
    dbHealth = 'Healthy', 
    pgvectorStatus = 'Active', 
    tokensUsed = 195, 
    maxTokens = 300, 
    ramUsage = 58 
  }: Props = $props();
</script>

<div class="sidebar-status-container">
  <div class="panel-header">
    <span class="dot green"></span>
    <h3>System Telemetry</h3>
  </div>
  <div class="panel-content">
    <div class="metric-group">
      <span class="label">Active Doc ID</span>
      <span class="value code">{docId}</span>
    </div>
    <div class="metric-group">
      <span class="label">Database Health</span>
      <span class="value text-green">{dbHealth}</span>
    </div>
    <div class="metric-group">
      <span class="label">pgvector Engine</span>
      <span class="value text-cyan">{pgvectorStatus}</span>
    </div>
    <div class="metric-group">
      <span class="label">Context Tokens</span>
      <span class="value">{tokensUsed} / {maxTokens}</span>
    </div>
    <div class="metric-group">
      <span class="label">RAM Usage</span>
      <div class="progress-bar-container">
        <div class="progress-bar" style="width: {ramUsage}%"></div>
      </div>
      <span class="sub-val">{ramUsage}% Allocated</span>
    </div>
  </div>
</div>

<style>
  .sidebar-status-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    font-family: "JetBrains Mono", monospace;
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
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  .dot.green { background: #10b981; }
  .panel-content {
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex: 1;
  }
  .metric-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .label {
    font-size: 0.68rem;
    color: rgba(255, 255, 255, 0.4);
    text-transform: uppercase;
  }
  .value {
    font-size: 0.78rem;
    color: #cbd5e1;
  }
  .code {
    font-family: inherit;
    color: #a855f7;
  }
  .text-green { color: #10b981; font-weight: bold; }
  .text-cyan { color: #38bdf8; font-weight: bold; }
  .progress-bar-container {
    width: 100%;
    height: 6px;
    background: rgba(0, 0, 0, 0.4);
    border-radius: 3px;
    overflow: hidden;
    margin-top: 2px;
  }
  .progress-bar {
    height: 100%;
    background: #38bdf8;
    border-radius: 3px;
  }
  .sub-val {
    font-size: 0.65rem;
    color: rgba(255, 255, 255, 0.5);
    margin-top: 2px;
  }
</style>
