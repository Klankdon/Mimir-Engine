<script>
  // Agents Dashboard Placeholder
  let agents = $state([]);
  let loading = $state(false);
</script>

<div class="p-6 text-slate-100">
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-bold">Autonomous Agents</h1>
      <p class="text-sm text-slate-400">Manage background memory janitors, vibe-coding assistants, and custom rules.</p>
    </div>
    <button class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg font-medium text-sm transition-colors">
      + Create Agent
    </button>
  </div>

  <!-- Active Agents Grid Placeholder -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <div class="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
      <div class="flex items-center justify-between mb-2">
        <span class="font-semibold text-indigo-400">Database Janitor</span>
        <span class="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Idle</span>
      </div>
      <p class="text-xs text-slate-400 mb-4">Prunes low-relevance embeddings and deduplicates pgvector memory.</p>
      <div class="text-xs text-slate-500">Assigned Role: <code class="text-slate-300">agent</code></div>
    </div>
  </div>
</div>
