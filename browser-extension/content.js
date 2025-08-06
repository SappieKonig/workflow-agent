console.log('Content script loaded');
let chatBoxContainer = null;
let isVisible = false;
let currentDomain = null;

// Get current domain
try {
  currentDomain = window.location.hostname;
} catch (error) {
  currentDomain = 'unknown';
}

function createChatBox() {
  if (chatBoxContainer) return;

  chatBoxContainer = document.createElement('div');
  chatBoxContainer.id = 'right-side-chatbox';
  chatBoxContainer.innerHTML = `
    <div class="chat-header">
      <span class="chat-title">Chat Assistant</span>
      <button class="chat-clear" id="chat-clear-btn">Clear</button>
      <button class="chat-close" id="chat-close-btn">×</button>
    </div>
    <div class="chat-messages" id="chat-messages">
      <div class="message assistant-message">
        <div class="message-content">Hello! How can I help you today?</div>
      </div>
    </div>
    <div class="chat-input-container">
      <textarea id="chat-input" placeholder="Type your message..." rows="1"></textarea>
      <button id="chat-send-btn">Send</button>
    </div>
  `;

  document.body.appendChild(chatBoxContainer);

  setupEventListeners();
  loadChatHistory();
}

function setupEventListeners() {
  const sendButton = document.getElementById('chat-send-btn');
  const chatInput = document.getElementById('chat-input');
  const closeButton = document.getElementById('chat-close-btn');
  const clearButton = document.getElementById('chat-clear-btn');

  sendButton.addEventListener('click', sendMessage);
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize textarea
  chatInput.addEventListener('input', autoResizeTextarea);
  
  closeButton.addEventListener('click', hideChatBox);
  clearButton.addEventListener('click', clearChatHistory);
}

function autoResizeTextarea() {
  const chatInput = document.getElementById('chat-input');
  if (!chatInput) return;
  
  // Reset height to auto to get the correct scrollHeight
  chatInput.style.height = 'auto';
  
  // Calculate the number of lines based on scrollHeight
  const lineHeight = parseInt(window.getComputedStyle(chatInput).lineHeight);
  const lines = Math.ceil(chatInput.scrollHeight / lineHeight);
  
  // Set maximum of 5 lines
  const maxLines = 5;
  const finalLines = Math.min(lines, maxLines);
  
  // Set the height
  chatInput.style.height = (finalLines * lineHeight) + 'px';
  chatInput.rows = finalLines;
}

async function sendMessage() {
  const chatInput = document.getElementById('chat-input');
  const message = chatInput.value.trim();
  
  if (!message) return;

  addMessage(message, 'user');
  chatInput.value = '';
  
  // Add loading message
  const loadingMessage = addLoadingMessage();
  
  saveChatHistory();
  
  // Get configuration and session from storage
  chrome.storage.local.get(['authToken', 'apiKey', 'sessionIds'], async (result) => {
    if (!result.authToken) {
      removeLoadingMessage(loadingMessage);
      addMessage('Error: Service auth token not configured. Please configure it in the extension popup.', 'assistant');
      return;
    }
    
    if (!result.apiKey) {
      removeLoadingMessage(loadingMessage);
      addMessage('Error: n8n API key not configured. Please configure it in the extension popup.', 'assistant');
      return;
    }
    
    // Deduce API URL from current page URL
    let apiUrl = '';
    try {
      const currentUrl = new URL(window.location.href);
      // Extract the base URL (protocol + hostname)
      apiUrl = `${currentUrl.protocol}//${currentUrl.hostname}/`;
    } catch (error) {
      removeLoadingMessage(loadingMessage);
      addMessage('Error: Could not determine API URL from current page.', 'assistant');
      return;
    }
    
    // Get session ID for this domain if it exists
    const sessionIds = result.sessionIds || {};
    const sessionId = sessionIds[currentDomain] || null;
    
    // Check if streaming is supported and use SSE
    const useStreaming = true; // You can make this configurable
    
    if (useStreaming) {
      // Use SSE for streaming response
      const streamUrl = CONFIG.SERVICE_URL.replace('/chat', '/chat/stream');
      
      // Create form data for POST request with EventSource
      const params = new URLSearchParams({
        message: message,
        auth_token: result.authToken,
        api_key: result.apiKey,
        api_url: apiUrl,
        ...(sessionId && { session_id: sessionId })
      });
      
      // Use fetch with SSE since EventSource doesn't support POST with body
      const response = await fetch(streamUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          auth_token: result.authToken,
          api_key: result.apiKey,
          api_url: apiUrl,
          session_id: sessionId
        })
      });
      
      if (!response.ok) {
        removeLoadingMessage(loadingMessage);
        const error = await response.text();
        addMessage(`Error: ${error}`, 'assistant');
        return;
      }
      
      // Track session ID from result
      let sessionIdReceived = null;
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            
            // Try to parse as JSON first (for result/error messages)
            try {
              const data = JSON.parse(dataStr);
              
              if (data.type === 'result') {
                // Final result - remove loading and show final message
                removeLoadingMessage(loadingMessage);
                addMessage(data.text, 'assistant');
                sessionIdReceived = data.session_id;
              } else if (data.type === 'error') {
                removeLoadingMessage(loadingMessage);
                addMessage(`Error: ${data.message}`, 'assistant');
                return;
              }
            } catch (e) {
              // Not JSON, must be a message ID
              if (dataStr && loadingMessage) {
                // Update the loading text with the message ID
                const loadingText = loadingMessage.querySelector('.loading-text');
                if (loadingText) {
                  loadingText.textContent = dataStr;
                }
              }
            }
          }
        }
      }
      
      // Store session ID if received
      if (sessionIdReceived) {
        chrome.storage.local.get(['sessionIds'], (storageResult) => {
          const sessionIds = storageResult.sessionIds || {};
          sessionIds[currentDomain] = sessionIdReceived;
          chrome.storage.local.set({ sessionIds: sessionIds });
        });
      }
      
      // Add notification about reload and then reload the page
      setTimeout(() => {
        addMessage('Reloading page to show workflow...', 'assistant');
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      }, 1000);
      
    } else {
      // Fallback to regular fetch
      try {
        const response = await fetch(CONFIG.SERVICE_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            message: message,
            auth_token: result.authToken,
            api_key: result.apiKey,
            api_url: apiUrl,
            session_id: sessionId
          })
        });
        
        // Remove loading message
        removeLoadingMessage(loadingMessage);
        
        if (response.ok) {
          const data = await response.json();
          addMessage(data.response, 'assistant');
          
          // Store session ID if present
          if (data.session_id) {
            chrome.storage.local.get(['sessionIds'], (storageResult) => {
              const sessionIds = storageResult.sessionIds || {};
              sessionIds[currentDomain] = data.session_id;
              chrome.storage.local.set({ sessionIds: sessionIds });
            });
          }
          
          // Add notification about reload and then reload the page
          setTimeout(() => {
            addMessage('Reloading page to show workflow...', 'assistant');
            setTimeout(() => {
              window.location.reload();
            }, 2000);
          }, 1000);
        } else {
          addMessage('Error: Failed to get response from Claude service', 'assistant');
        }
      } catch (error) {
        // Remove loading message on error
        removeLoadingMessage(loadingMessage);
        addMessage('Error: Could not connect to Claude service. Make sure the service is running.', 'assistant');
      }
    }
    
    saveChatHistory();
  });
}

function addMessage(text, sender) {
  const messagesContainer = document.getElementById('chat-messages');
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}-message`;
  
  messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
  
  messagesContainer.appendChild(messageDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addLoadingMessage() {
  const messagesContainer = document.getElementById('chat-messages');
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'message assistant-message loading-message';
  
  loadingDiv.innerHTML = `
    <div class="message-content">
      <div class="loading-spinner"></div>
      <div class="loading-text">Answering your request might take a while...</div>
    </div>
  `;
  
  messagesContainer.appendChild(loadingDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  
  return loadingDiv;
}

function removeLoadingMessage(loadingElement) {
  if (loadingElement && loadingElement.parentNode) {
    loadingElement.parentNode.removeChild(loadingElement);
  }
}

function showChatBox() {
  if (!chatBoxContainer) {
    createChatBox();
  }
  chatBoxContainer.style.display = 'flex';
  isVisible = true;
  updateDomainState(true);
}

function hideChatBox() {
  if (chatBoxContainer) {
    chatBoxContainer.style.display = 'none';
  }
  isVisible = false;
  updateDomainState(false);
}

function updateDomainState(enabled) {
  chrome.storage.local.get(['domainStates'], (result) => {
    const domainStates = result.domainStates || {};
    domainStates[currentDomain] = enabled;
    chrome.storage.local.set({ domainStates: domainStates });
  });
}

function saveChatHistory() {
  const messages = [];
  const messageElements = document.querySelectorAll('#chat-messages .message');
  
  messageElements.forEach(msg => {
    const isAssistant = msg.classList.contains('assistant-message');
    const content = msg.querySelector('.message-content').textContent;
    messages.push({
      text: content,
      sender: isAssistant ? 'assistant' : 'user'
    });
  });
  
  chrome.storage.local.set({ chatHistory: messages });
}

function loadChatHistory() {
  chrome.storage.local.get(['chatHistory'], (result) => {
    if (result.chatHistory && result.chatHistory.length > 0) {
      const messagesContainer = document.getElementById('chat-messages');
      messagesContainer.innerHTML = '';
      
      result.chatHistory.forEach(msg => {
        addMessage(msg.text, msg.sender);
      });
    }
  });
}

function clearChatHistory() {
  const messagesContainer = document.getElementById('chat-messages');
  messagesContainer.innerHTML = `
    <div class="message assistant-message">
      <div class="message-content">Hello! How can I help you today?</div>
    </div>
  `;
  
  // Clear chat history and session ID for this domain
  chrome.storage.local.set({ chatHistory: [] });
  
  chrome.storage.local.get(['sessionIds'], (result) => {
    const sessionIds = result.sessionIds || {};
    delete sessionIds[currentDomain];
    chrome.storage.local.set({ sessionIds: sessionIds });
  });
}

chrome.storage.local.get(['domainStates'], (result) => {
  const domainStates = result.domainStates || {};
  const isEnabled = domainStates[currentDomain] || false;
  if (isEnabled) {
    showChatBox();
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Message received:', request);
  if (request.action === 'toggleChatBox') {
    console.log('Toggling chat box, current visibility:', isVisible);
    
    // Update domain if provided in message
    if (request.domain && request.domain !== currentDomain) {
      currentDomain = request.domain;
    }
    
    if (isVisible) {
      hideChatBox();
    } else {
      showChatBox();
    }
    sendResponse({success: true, visible: isVisible, domain: currentDomain});
  }
  return true;
});