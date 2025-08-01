console.log('Content script loaded');
let chatBoxContainer = null;
let isVisible = false;

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
  
  try {
    const response = await fetch('http://127.0.0.1:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        message: message,
        url: window.location.href
      })
    });
    
    // Remove loading message
    removeLoadingMessage(loadingMessage);
    
    if (response.ok) {
      const data = await response.json();
      addMessage(data.response, 'assistant');
      
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
  
  saveChatHistory();
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
  chrome.storage.local.set({ chatBoxVisible: true });
}

function hideChatBox() {
  if (chatBoxContainer) {
    chatBoxContainer.style.display = 'none';
  }
  isVisible = false;
  chrome.storage.local.set({ chatBoxVisible: false });
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
  chrome.storage.local.set({ chatHistory: [] });
}

chrome.storage.local.get(['chatBoxVisible'], (result) => {
  if (result.chatBoxVisible) {
    showChatBox();
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Message received:', request);
  if (request.action === 'toggleChatBox') {
    console.log('Toggling chat box, current visibility:', isVisible);
    if (isVisible) {
      hideChatBox();
    } else {
      showChatBox();
    }
    sendResponse({success: true, visible: isVisible});
  }
  return true;
});