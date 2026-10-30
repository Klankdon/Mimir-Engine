<script>
	// Svelte 5 state runes
	let agents = $state([
		{
			id: '1',
			name: 'Database Janitor',
			role: 'janitor',
			status: 'idle',
			description: 'Prunes low-relevance embeddings and deduplicates pgvector memory chunks in PostgreSQL.',
			lastRun: '12 mins ago',
			config: { threshold: 0.35, maxTokens: 300 }
		},
		{
			id: '2',
			name: 'Context Slicer',
			role: 'middleware',
			status: 'active',
			description: 'Monitors real-time prompt payloads and enforces strict top-k context window bounds.',
			lastRun: 'Just now',
			config: { topK: 5, targetLatencyMs: 4 }
		},
		{
			id: '3',
			name: 'Vibe-Coding Assistant',
			role: 'assistant',
			status: 'paused',
			description: 'Scans workspace diffs to auto-generate REST API schemas and documentation.',
			lastRun: '2 hours ago',
			config: { model: 'local-ollama' }
		}
	]);

	let showModal = $state(false);
	let newAgentName = $state('');
	let newAgentRole = $state('janitor');
	let newAgentDesc = $state('');

	function toggleAgentStatus(id) {
		agents = agents.map((agent) => {
			if (agent.id === id) {
				const nextStatus = agent.status === 'active' ? 'paused' : 'active';
				return { ...agent, status: nextStatus };
			}
			return agent;
		});
	}

	function handleCreateAgent(e) {
		e.preventDefault();
		if (!newAgentName.trim()) return;

		const newAgent = {
			id: Date.now().toString(),
			name: newAgentName,
			role: newAgentRole,
			status: 'idle',
			description: newAgentDesc || 'Custom background task runner.',
			lastRun: 'Never',
			config: {}
		};

		agents = [...agents, newAgent];
		newAgentName = '';
		newAgentDesc = '';
		showModal = false;
	}
</script>

<div class="p-6 text-slate-100 max-w-7xl mx-auto">
	<!-- Header -->
	<div class="flex items-center justify-between mb-8">
		<div>
			<h1 class="text-2xl font-bold tracking-tight">Autonomous Agents</h1>
			<p class="text-sm text-slate-400 mt-1">
				Configure background memory janitors, automated vector pruning, and context handlers.
			</p>
		</div>
		<button
			onclick={() => (showModal = true)}
			class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg font-medium text-sm transition-colors flex items-center gap-2 shadow-lg shadow-indigo-600/20"
		>
			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			Create Agent
		</button>
	</div>

	<!-- Agents Grid -->
	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
		{#each agents as agent (agent.id)}
			<div class="p-5 rounded-xl bg-slate-800/60 border border-slate-700/60 flex flex-col justify-between hover:border-slate-600 transition-all shadow-md">
				<div>
					<div class="flex items-center justify-between mb-3">
						<span class="font-semibold text-indigo-300 text-base">{agent.name}</span>
						<span
							class="text-xs px-2.5 py-0.5 rounded-full font-medium border capitalize
							{agent.status === 'active' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : ''}
							{agent.status === 'idle' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' : ''}
							{agent.status === 'paused' ? 'bg-slate-500/10 text-slate-400 border-slate-500/30' : ''}"
						>
							{agent.status}
						</span>
					</div>
					<p class="text-xs text-slate-300 leading-relaxed mb-4">{agent.description}</p>
				</div>

				<div class="pt-4 border-t border-slate-700/40 flex items-center justify-between text-xs text-slate-400">
					<div>
						<span>Role: </span>
						<code class="text-indigo-400 bg-slate-900/60 px-1.5 py-0.5 rounded border border-slate-700/50">{agent.role}</code>
					</div>
					<button
						onclick={() => toggleAgentStatus(agent.id)}
						class="px-2.5 py-1 rounded bg-slate-700/50 hover:bg-slate-700 text-slate-200 transition-colors font-medium"
					>
						{agent.status === 'active' ? 'Pause' : 'Activate'}
					</button>
				</div>
			</div>
		{/each}
	</div>

	<!-- Create Agent Modal -->
	{#if showModal}
		<div class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
			<div class="bg-slate-900 border border-slate-700/80 rounded-xl p-6 w-full max-w-md shadow-2xl">
				<h2 class="text-lg font-bold text-slate-100 mb-4">Deploy New Agent</h2>
				<form onsubmit={handleCreateAgent} class="space-y-4">
					<div>
						<label for="agent-name" class="block text-xs font-medium text-slate-300 mb-1">Agent Name</label>
						<input
							id="agent-name"
							type="text"
							bind:value={newAgentName}
							placeholder="e.g., pgvector Deduplicator"
							class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
							required
						/>
					</div>

					<div>
						<label for="agent-role" class="block text-xs font-medium text-slate-300 mb-1">Role / Function</label>
						<select
							id="agent-role"
							bind:value={newAgentRole}
							class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
						>
							<option value="janitor">Janitor (Cleanup/Deduplication)</option>
							<option value="middleware">Middleware (Real-time Interceptor)</option>
							<option value="assistant">Assistant (Vibe-Coding / Docs)</option>
						</select>
					</div>

					<div>
						<label for="agent-desc" class="block text-xs font-medium text-slate-300 mb-1">Description</label>
						<textarea
							id="agent-desc"
							bind:value={newAgentDesc}
							rows="3"
							placeholder="Describe what this background worker handles..."
							class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
						></textarea>
					</div>

					<div class="flex justify-end gap-3 pt-2">
						<button
							type="button"
							onclick={() => (showModal = false)}
							class="px-4 py-2 bg-
