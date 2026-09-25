<script lang="ts">
  import { tick } from 'svelte';

  interface ChatMessage {
    sender: 'Mimir' | 'User';
    text: string;
  }

  let inputMessage = $state('');
  let isGenerating = $state(false);
  let chatHistoryContainer: HTMLDivElement;

  let messages = $state<ChatMessage[]>([
    { sender: 'Mimir', text: 'Mimir Engine client initialized. Send a message to test active memory retrieval and stream passthrough.' }
  ]);

  let codeOutput = $state('// Vibe code output preview will stream or render here...');
  let scratchpadNotes = $state('// Architectural Scratchpad & Rationale:\n// Document the "why" behind specific code choices here (e.g., why asyncpg pooling was selected over standard psycopg2 for concurrency, or how vector cosine distance optimization works).');

  async function scrollToBottom() {
    await tick();
    if (chatHistoryContainer) {
      chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;
    }
  }

  async function sendMessage() {
    if (!inputMessage.trim() || isGenerating) return;

    const userText = inputMessage.trim();
    inputMessage = '';
    
    messages = [...messages, { sender: 'User', text: userText }];
    await scrollToBottom();

    messages = [...messages, { sender: 'Mimir', text: '' }];
    const targetMessageIndex = messages.length - 1;
    isGenerating = true;

    try {
      const payload = {
        model: 'mimir-proxy',
        stream: true,
        messages: messages
          .filter(m => m.text)
          .map(m => ({
            role: m.sender === 'User' ? 'user' : 'assistant',
            content: m.text
          }))
      };

      const res = await fetch('/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok || !res.body) {
        messages[targetMessageIndex].text = '⚠️ Error: Failed to connect to proxy downstream.';
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith(':')) continue;
          if (trimmed === 'data: [DONE]') break;

          if (trimmed.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(trimmed.slice(6));
              const token = parsed.choices?.[0]?.delta?.content || parsed.choices?.[0]?.text || '';
              
              if (token) {
                messages[targetMessageIndex].text += token;
                await scrollToBottom();
              }
            } catch (err) {}
          }
        }
      }
    } catch (err) {
      console.error('Failed to execute stream completion:', err);
      messages[targetMessageIndex].text = '⚠️ Connection error. Check upstream backend status in Integrations Hub.';
    } finally {
      isGenerating = false;
      await scrollToBottom();
    }
  }
</script>

<div class="workspace-grid">
  <!-- Left Side: Chat Interface -->
  <div class="chat-container">
    <div class="panel-header">💬 Chat Workspace</div>
    <div class="chat-history" bind:this={chatHistoryContainer}>
      {#each messages as msg}
        <div class="chat-bubble {msg.sender.toLowerCase()}">
          <span class="sender">{msg.sender}:</span>
          <p>{msg.text || (isGenerating && msg === messages[messages.length - 1] ? '▋' : '')}</p>
        </div>
      {/each}
    </div>

    <div class="chat-input-bar">
      <input 
        type="text" 
        bind:value={inputMessage} 
        placeholder={isGenerating ? "Mimir is processing..." : "Type a message..."} 
        disabled={isGenerating}
        onkeydown={(e) => e.key === 'Enter' && sendMessage()}
      />
      <button onclick={sendMessage} disabled={isGenerating || !inputMessage.trim()}>
        {isGenerating ? 'Streaming...' : 'Send'}
      </button>
    </div>
  </div>

  <!-- Right Side: Stacked Vibe Dashboard -->
  <div class="dashboard-stack">
    <!-- Top Pane: Vibe Code Output / Terminal -->
    <div class="stack-pane">
      <div class="panel-header">⚡ Vibe Code & Terminal Output</div>
      <div class="pane-content code-pane">
        <pre><code>{codeOutput}</code></pre>
      </div>
    </div>

    <!-- Bottom Pane: Architectural Scratchpad & Educational Rationale -->
    <div class="stack-pane">
      <div class="panel-header">💡 Architectural Scratchpad & Educational Rationale</div>
      <div class="pane-content notes-pane">
        <textarea 
          bind:value={scratchpadNotes} 
          placeholder="Capture the 'why' behind implementation choices, trade-offs, and conceptual notes..."
        ></textarea>
      </div>
    </div>
  </div>
</div>

<style>
  .workspace-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    height: 100%;
    box-sizing: border-box;
  }

  .panel-header {
    background: rgba(15, 23, 42, 0.9);
    padding: 10px 16px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: #38bdf8;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .chat-container {
    display: flex;
    flex-direction: column;
    background: rgba(15, 23, 42, 0.4);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    overflow: hidden;
    height: 100%;
  }

  .chat-history {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .chat-bubble {
    max-width: 80%;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 0.88rem;
    line-height: 1.4;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .chat-bubble.mimir {
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.2);
    align-self: flex-start;
  }

  .chat-bubble.user {
    background: rgba(168, 85, 247, 0.15);
    border: 1px solid rgba(168, 85, 247, 0.3);
    align-self: flex-end;
  }

  .sender {
    font-weight: bold;
    font-size: 0.72rem;
    color: rgba(255, 255, 255, 0.5);
    display: block;
    margin-bottom: 4px;
  }

  p { margin: 0; }

  .chat-input-bar {
    display: flex;
    padding: 12px;
    background: rgba(0, 0, 0, 0.3);
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    gap: 8px;
  }

  input {
    flex: 1;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(15, 23, 42, 0.8);
    color: #fff;
    font-size: 0.88rem;
  }

  input:disabled { opacity: 0.5; }

  button {
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    background: #38bdf8;
    color: #0b0f17;
    font-weight: bold;
    cursor: pointer;
    font-size: 0.88rem;
  }

  button:disabled { opacity: 0.5; cursor: not-allowed; }

  .dashboard-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
    height: 100%;
  }

  .stack-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: rgba(15, 23, 42, 0.4);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    overflow: hidden;
  }

  .pane-content {
    flex: 1;
    padding: 12px;
    overflow-y: auto;
    font-family: monospace;
    font-size: 0.84rem;
  }

  .code-pane pre {
    margin: 0;
    color: #e2e8f0;
    white-space: pre-wrap;
  }

  .notes-pane textarea {
    width: 100%;
    height: 100%;
    background: transparent;
    border: none;
    color: #cbd5e1;
    font-family: inherit;
    font-size: 0.86rem;
    resize: none;
    box-sizing: border-box;
    outline: none;
  }
</style>
