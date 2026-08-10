<script lang="ts">
  let inputMessage = $state('');
  let messages = $state([
    { sender: 'Mimir', text: 'Mimir Engine client initialized. Send a message to test active memory retrieval.' }
  ]);

  function sendMessage() {
    if (!inputMessage.trim()) return;
    messages = [...messages, { sender: 'User', text: inputMessage }];
    inputMessage = '';
  }
</script>

<div class="chat-container">
  <div class="chat-history">
    {#each messages as msg}
      <div class="chat-bubble {msg.sender.toLowerCase()}">
        <span class="sender">{msg.sender}:</span>
        <p>{msg.text}</p>
      </div>
    {/each}
  </div>

  <div class="chat-input-bar">
    <input 
      type="text" 
      bind:value={inputMessage} 
      placeholder="Type a message..." 
      onkeydown={(e) => e.key === 'Enter' && sendMessage()}
    />
    <button onclick={sendMessage}>Send</button>
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
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 10px;
    font-size: 0.9rem;
    line-height: 1.4;
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

  button {
    padding: 10px 20px;
    border-radius: 6px;
    border: none;
    background: #38bdf8;
    color: #0b0f17;
    font-weight: bold;
    cursor: pointer;
  }
</style>