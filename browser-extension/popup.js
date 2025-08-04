document.addEventListener('DOMContentLoaded', () => {
  console.log('Popup loaded');
  const toggleButton = document.getElementById('toggleButton');
  const status = document.getElementById('status');
  const currentDomain = document.getElementById('currentDomain');

  if (!toggleButton || !status || !currentDomain) {
    console.error('Could not find required elements');
    return;
  }

  // Get current tab info first
  chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
    if (tabs.length === 0) {
      status.textContent = 'Error: No active tab';
      return;
    }

    const tab = tabs[0];
    let domain;
    
    try {
      domain = new URL(tab.url).hostname;
      currentDomain.textContent = domain;
    } catch (error) {
      domain = 'unknown';
      currentDomain.textContent = 'Invalid URL';
    }

    // Check if we're on a restricted page
    if (tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://') || 
        tab.url.startsWith('about:') || tab.url.startsWith('moz-extension://')) {
      status.textContent = 'Not available on this page';
      toggleButton.disabled = true;
      return;
    }

    // Get domain-specific state
    chrome.storage.local.get(['domainStates'], (result) => {
      console.log('Storage result:', result);
      const domainStates = result.domainStates || {};
      const isEnabled = domainStates[domain] || false;
      
      if (isEnabled) {
        status.textContent = 'Chat box is enabled';
        toggleButton.textContent = 'Disable Chat Box';
      } else {
        status.textContent = 'Chat box is disabled';
        toggleButton.textContent = 'Enable Chat Box';
      }
    });
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
      let domain;
      
      try {
        domain = new URL(tab.url).hostname;
      } catch (error) {
        status.textContent = 'Error: Invalid URL';
        return;
      }
      
      // Check if we're on a restricted page
      if (tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://') || 
          tab.url.startsWith('about:') || tab.url.startsWith('moz-extension://')) {
        status.textContent = 'Not available on this page';
        return;
      }

      // First try to send message
      chrome.tabs.sendMessage(tab.id, {action: 'toggleChatBox', domain: domain}, (response) => {
        if (chrome.runtime.lastError) {
          console.log('Content script not found, injecting...');
          // Content script not running, inject it
          chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['config.js', 'content.js']
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
                chrome.tabs.sendMessage(tab.id, {action: 'toggleChatBox', domain: domain}, (response) => {
                  if (chrome.runtime.lastError) {
                    console.error('Message sending error after injection:', chrome.runtime.lastError);
                    status.textContent = 'Error: ' + chrome.runtime.lastError.message;
                    return;
                  }
                  updateButtonState(domain);
                });
              }, 100);
            });
          });
        } else {
          console.log('Message sent successfully');
          updateButtonState(domain);
        }
      });
    });
  });

  function updateButtonState(domain) {
    setTimeout(() => {
      chrome.storage.local.get(['domainStates'], (result) => {
        console.log('Updated storage:', result);
        const domainStates = result.domainStates || {};
        const isEnabled = domainStates[domain] || false;
        
        if (isEnabled) {
          status.textContent = 'Chat box is enabled';
          toggleButton.textContent = 'Disable Chat Box';
        } else {
          status.textContent = 'Chat box is disabled';
          toggleButton.textContent = 'Enable Chat Box';
        }
      });
    }, 100);
  }
});