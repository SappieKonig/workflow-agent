document.addEventListener('DOMContentLoaded', () => {
  console.log('Popup loaded');
  const toggleButton = document.getElementById('toggleButton');
  const status = document.getElementById('status');

  if (!toggleButton || !status) {
    console.error('Could not find required elements');
    return;
  }

  chrome.storage.local.get(['chatBoxVisible'], (result) => {
    console.log('Storage result:', result);
    if (result.chatBoxVisible) {
      status.textContent = 'Chat box is visible';
      toggleButton.textContent = 'Hide Chat Box';
    } else {
      status.textContent = 'Chat box is hidden';
      toggleButton.textContent = 'Show Chat Box';
    }
  });

  toggleButton.addEventListener('click', () => {
    console.log('Toggle button clicked');
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      console.log('Active tabs:', tabs);
      if (tabs.length === 0) {
        console.error('No active tabs found');
        status.textContent = 'Error: No active tab';
        return;
      }

      const tab = tabs[0];
      
      // Check if we're on a restricted page
      if (tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://') || 
          tab.url.startsWith('about:') || tab.url.startsWith('moz-extension://')) {
        status.textContent = 'Not available on this page';
        return;
      }

      // First try to send message
      chrome.tabs.sendMessage(tab.id, {action: 'toggleChatBox'}, (response) => {
        if (chrome.runtime.lastError) {
          console.log('Content script not found, injecting...');
          // Content script not running, inject it
          chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content.js']
          }, () => {
            if (chrome.runtime.lastError) {
              console.error('Injection error:', chrome.runtime.lastError);
              status.textContent = 'Error: Cannot inject on this page';
              return;
            }
            
            // Also inject CSS
            chrome.scripting.insertCSS({
              target: { tabId: tab.id },
              files: ['chat-styles.css']
            }, () => {
              // Wait a bit for script to load then send message
              setTimeout(() => {
                chrome.tabs.sendMessage(tab.id, {action: 'toggleChatBox'}, (response) => {
                  if (chrome.runtime.lastError) {
                    console.error('Message sending error after injection:', chrome.runtime.lastError);
                    status.textContent = 'Error: ' + chrome.runtime.lastError.message;
                    return;
                  }
                  updateButtonState();
                });
              }, 100);
            });
          });
        } else {
          console.log('Message sent successfully');
          updateButtonState();
        }
      });
    });
  });

  function updateButtonState() {
    setTimeout(() => {
      chrome.storage.local.get(['chatBoxVisible'], (result) => {
        console.log('Updated storage:', result);
        if (result.chatBoxVisible) {
          status.textContent = 'Chat box is visible';
          toggleButton.textContent = 'Hide Chat Box';
        } else {
          status.textContent = 'Chat box is hidden';
          toggleButton.textContent = 'Show Chat Box';
        }
      });
    }, 100);
  }
});