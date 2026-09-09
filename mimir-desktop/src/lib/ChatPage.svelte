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
    
    // 1. Append User Message
    messages = [...messages, { sender: 'User', text: userText }];
    await scrollToBottom();

    // 2. Prepare Mimir placeholder response
    messages = [...messages, { sender: 'Mimir', text: '' }];
    const targetMessageIndex = messages.length - 1;
    isGenerating = true;

    try {
      // Build standard OpenAI format payload
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

      // 3. Process Server-Sent Events (SSE) Stream
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
            } catch (err) {
              // Ignore non-JSON ping/keep-alive frames
            }
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

<div class="chat-container">
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

<style>
  .chat-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: rgba(15, 23, 42, 0.4);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    overflow: hidden;
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
    max-width: 75%;
    padding: 12px 16px;
    border-radius: 10px;
    font-size: 0.9rem;
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

  .sender { font-weight: bold; font-size: 0.75rem; color: rgba(255, 255, 255, 0.5); display: block; margin-bottom: 4px; }
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
    padding: 10px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(15, 23, 42, 0.8);
    color: #fff;
  }

  input:disabled { opacity: 0.5; }

  button {
    padding: 10px 20px;
    border-radius: 6px;
    border: none;
    background: #38bdf8;
    color: #0b0f17;
    font-weight: bold;
    cursor: pointer;
  }

  button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
