document.addEventListener('DOMContentLoaded', () => {
  console.log('Popup loaded - starting privacy check');
  
  // Privacy agreement elements
  const privacyOverlay = document.getElementById('privacyOverlay');
  const mainContent = document.getElementById('mainContent');
  const privacyAccept = document.getElementById('privacyAccept');
  const privacyDecline = document.getElementById('privacyDecline');
  
  // Main elements
  const toggleButton = document.getElementById('toggleButton');
  const status = document.getElementById('status');
  const currentDomain = document.getElementById('currentDomain');
  const authTokenInput = document.getElementById('authToken');
  const apiKeyInput = document.getElementById('apiKey');
  const saveConfigButton = document.getElementById('saveConfig');

  console.log('Found privacy elements:', !!privacyOverlay, !!mainContent, !!privacyAccept, !!privacyDecline);

  if (!toggleButton || !status || !currentDomain || !authTokenInput || !apiKeyInput || !saveConfigButton) {
    console.error('Could not find required elements');
    return;
  }

  // Check privacy agreement status first
  checkPrivacyAgreement();

  function checkPrivacyAgreement() {
    chrome.storage.local.get(['privacyAgreed'], (result) => {
      console.log('Privacy check result:', result);
      if (!result.privacyAgreed) {
        console.log('No privacy agreement found, showing modal');
        // Show privacy modal and disable main content
        privacyOverlay.style.display = 'flex';
        mainContent.classList.add('disabled');
      } else {
        // Privacy agreed, enable normal functionality
        privacyOverlay.style.display = 'none';
        mainContent.classList.remove('disabled');
        initializeExtension();
      }
    });
  }

  // Privacy agreement handlers
  privacyAccept.addEventListener('click', () => {
    chrome.storage.local.set({ 
      privacyAgreed: true,
      privacyAgreedDate: new Date().toISOString()
    }, () => {
      privacyOverlay.style.display = 'none';
      mainContent.classList.remove('disabled');
      initializeExtension();
      status.textContent = 'Privacy agreement accepted';
      setTimeout(() => {
        status.textContent = 'Ready';
      }, 2000);
    });
  });

  privacyDecline.addEventListener('click', () => {
    // Close popup if declined
    window.close();
  });

  function initializeExtension() {
    // Load saved configuration and initialize all functionality
    loadConfiguration();
    initializeToggleButton();
    initializeCredentials();
    initializeFeedback();
    initializeFAQ();
  }

  function loadConfiguration() {
    chrome.storage.local.get(['authToken', 'apiKey'], (result) => {
      if (result.authToken) {
        authTokenInput.value = result.authToken;
      }
      if (result.apiKey) {
        apiKeyInput.value = result.apiKey;
      }
    });

    // Auto-save auth token as user types
    authTokenInput.addEventListener('input', () => {
      const authToken = authTokenInput.value.trim();
      chrome.storage.local.set({ authToken });
    });

    // Auto-save API key as user types
    apiKeyInput.addEventListener('input', () => {
      const apiKey = apiKeyInput.value.trim();
      chrome.storage.local.set({ apiKey });
    });

    // Save configuration (now just for validation feedback)
    saveConfigButton.addEventListener('click', () => {
      const authToken = authTokenInput.value.trim();
      const apiKey = apiKeyInput.value.trim();
      
      if (!authToken) {
        status.textContent = 'Please enter your service auth token';
        return;
      }
      
      if (!apiKey) {
        status.textContent = 'Please enter your n8n API key';
        return;
      }
      
      status.textContent = 'Configuration saved';
      setTimeout(() => {
        status.textContent = 'Ready';
      }, 2000);
    });
  }

  function initializeToggleButton() {
    // Get current tab info first
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      if (tabs.length === 0) {
        status.textContent = 'Error: No active tab';
        return;
      }

      const currentTab = tabs[0];
      const url = new URL(currentTab.url);
      const domain = url.hostname;
      
      currentDomain.textContent = domain;

      // Get the current state for this domain
      chrome.storage.local.get(['domainStates'], (result) => {
        console.log('Storage result:', result);
        const domainStates = result.domainStates || {};
        const currentState = domainStates[domain] || false;
        
        updateButtonState(currentState);
      });
    });

    // Toggle button click handler
    toggleButton.addEventListener('click', () => {
      console.log('Toggle button clicked');
      chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        console.log('Active tabs:', tabs);
        if (tabs.length === 0) return;

        const currentTab = tabs[0];
        const url = new URL(currentTab.url);
        const domain = url.hostname;

        // Get current state
        chrome.storage.local.get(['domainStates'], (result) => {
          const domainStates = result.domainStates || {};
          const currentState = domainStates[domain] || false;
          const newState = !currentState;

          // Update state
          domainStates[domain] = newState;
          chrome.storage.local.set({ domainStates }, () => {
            console.log('Updated storage:', result);
            updateButtonState(newState);
          });

          // Inject or check content script
          if (newState) {
            console.log('Content script not found, injecting...');
            chrome.scripting.executeScript({
              target: { tabId: currentTab.id },
              files: ['config.js', 'content.js']
            }, () => {
              if (chrome.runtime.lastError) {
                console.error('Script injection failed:', chrome.runtime.lastError);
                status.textContent = 'Failed to inject content script';
                return;
              }
              
              // Send toggle message
              chrome.tabs.sendMessage(currentTab.id, { 
                action: 'toggleChatBox' 
              }, (response) => {
                if (chrome.runtime.lastError) {
                  console.error('Message sending failed:', chrome.runtime.lastError);
                } else {
                  console.log('Message sent successfully');
                  status.textContent = newState ? 'Chat box enabled' : 'Chat box disabled';
                }
              });
            });
          } else {
            // Send toggle message to hide
            chrome.tabs.sendMessage(currentTab.id, { 
              action: 'toggleChatBox' 
            }, (response) => {
              if (chrome.runtime.lastError) {
                console.error('Message sending failed:', chrome.runtime.lastError);
              } else {
                status.textContent = 'Chat box disabled';
              }
            });
          }
        });
      });
    });

    function updateButtonState(isEnabled) {
      setTimeout(() => {
        if (isEnabled) {
          toggleButton.textContent = 'Disable Chat Box';
        } else {
          toggleButton.textContent = 'Enable Chat Box';
        }
      }, 100);
    }
  }

  function initializeCredentials() {
    // Credentials functionality
    const credentialsToggle = document.getElementById('credentialsToggle');
    const credentialsView = document.getElementById('credentialsView');
    const credentialsList = document.getElementById('credentialsList');
    const exportCredentials = document.getElementById('exportCredentials');
    const clearCredentials = document.getElementById('clearCredentials');

    credentialsToggle.addEventListener('click', () => {
      const isVisible = credentialsView.style.display !== 'none';
      credentialsView.style.display = isVisible ? 'none' : 'block';
      
      if (!isVisible) {
        // Load and display credentials
        loadCredentials();
      }
    });

    exportCredentials.addEventListener('click', () => {
      chrome.runtime.sendMessage({ type: 'getCredentials' }, (response) => {
        const credentials = response.credentials;
        
        if (!credentials || !credentials.rawResponse) {
          status.textContent = 'No credentials to export';
          setTimeout(() => {
            status.textContent = 'Ready';
          }, 2000);
          return;
        }

        // Create the export data - this is the same format sent with chat requests
        const exportData = {
          rawResponse: credentials.rawResponse,
          timestamp: credentials.timestamp,
          domain: credentials.domain,
          credentialCount: credentials.credentialCount
        };

        // Create and download the JSON file
        const jsonString = JSON.stringify(exportData, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `n8n-credentials-${credentials.domain}-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        status.textContent = 'Credentials exported';
        setTimeout(() => {
          status.textContent = 'Ready';
        }, 2000);
      });
    });

    clearCredentials.addEventListener('click', () => {
      if (confirm('Are you sure you want to clear captured credentials?')) {
        chrome.runtime.sendMessage({ type: 'clearCredentials' }, (response) => {
          if (response.success) {
            credentialsList.innerHTML = '<div style="color: #666; text-align: center;">No credentials captured yet</div>';
            status.textContent = 'Credentials cleared';
            setTimeout(() => {
              status.textContent = 'Ready';
            }, 2000);
          }
        });
      }
    });

    function loadCredentials() {
      chrome.runtime.sendMessage({ type: 'getCredentials' }, (response) => {
        const credentials = response.credentials;
        displayCredentials(credentials);
      });
    }

    function displayCredentials(credentials) {
      if (!credentials) {
        credentialsList.innerHTML = '<div style="color: #666; text-align: center;">No credentials captured yet</div>';
        return;
      }

      const date = new Date(credentials.timestamp).toLocaleString();
      const credCount = credentials.credentialCount;
      const domain = credentials.domain;
      
      // Extract credential info for display (ID, name, type only)
      let credentialsHtml = '';
      try {
        if (credentials.rawResponse && credentials.rawResponse.data) {
          credentialsHtml = credentials.rawResponse.data.map(cred => 
            `<div style="margin-left: 10px; margin-bottom: 4px; padding: 4px; background: #fff; border-radius: 2px; border-left: 3px solid #4285f4;">
              <strong>${cred.name}</strong> (${cred.type})<br>
              <span style="color: #666;">ID: ${cred.id}</span>
            </div>`
          ).join('');
        }
      } catch (error) {
        credentialsHtml = '<div style="color: #999; font-style: italic;">Could not parse credentials</div>';
      }

      const html = `
        <div style="margin-bottom: 10px; padding: 8px; background: #fff; border-radius: 4px; border: 1px solid #ddd;">
          <div style="font-weight: bold; margin-bottom: 4px;">${domain}</div>
          <div style="font-size: 10px; color: #666; margin-bottom: 6px;">${date} - ${credCount} credentials</div>
          ${credentialsHtml}
        </div>
      `;

      credentialsList.innerHTML = html;
    }
  }

  function initializeFeedback() {
    // Feedback functionality
    const feedbackToggle = document.getElementById('feedbackToggle');
    const feedbackForm = document.getElementById('feedbackForm');
    const feedbackText = document.getElementById('feedbackText');
    const submitFeedback = document.getElementById('submitFeedback');
    
    feedbackToggle.addEventListener('click', () => {
      feedbackForm.style.display = feedbackForm.style.display === 'none' ? 'block' : 'none';
      if (feedbackForm.style.display === 'block') {
        feedbackText.focus();
      }
    });
    
    submitFeedback.addEventListener('click', async () => {
      const feedback = feedbackText.value.trim();
      
      if (!feedback) {
        status.textContent = 'Please enter feedback';
        return;
      }
      
      submitFeedback.disabled = true;
      submitFeedback.textContent = 'Sending...';
      
      try {
        const feedbackUrl = SERVICE_CONFIG.FEEDBACK_URL || `${SERVICE_CONFIG.SERVICE_URL}/feedback`;
        
        console.log('Sending feedback to:', feedbackUrl);
        console.log('Feedback data:', { feedback });
        
        const response = await fetch(feedbackUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ feedback })
        });
        
        console.log('Response status:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('Success response:', data);
          
          status.textContent = 'Feedback sent successfully!';
          feedbackText.value = '';
          feedbackForm.style.display = 'none';
          
          setTimeout(() => {
            status.textContent = 'Ready';
          }, 3000);
        } else {
          throw new Error(`HTTP ${response.status}`);
        }
      } catch (error) {
        console.error('Feedback submission error:', error);
        status.textContent = 'Failed to send feedback. Please try again.';
        
        setTimeout(() => {
          status.textContent = 'Ready';
        }, 3000);
      } finally {
        submitFeedback.disabled = false;
        submitFeedback.textContent = 'Submit Feedback';
      }
    });
  }

  function initializeFAQ() {
    // FAQ functionality
    const faqButton = document.getElementById('faqButton');
    
    faqButton.addEventListener('click', () => {
      chrome.tabs.create({ url: 'https://trylinker.io#faq' });
    });
  }
});