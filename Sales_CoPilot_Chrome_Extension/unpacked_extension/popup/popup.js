document.addEventListener('DOMContentLoaded', () => {
  const backendStatus = document.getElementById('backendStatus');
  const meetingUrlInput = document.getElementById('meetingUrlInput');
  const btnPasteUrl = document.getElementById('btnPasteUrl');
  const btnConnectMeeting = document.getElementById('btnConnectMeeting');
  const connectBtnText = document.getElementById('connectBtnText');
  const btnToggleCapture = document.getElementById('btnToggleCapture');
  const btnText = document.getElementById('btnText');
  const captureStatus = document.getElementById('captureStatus');
  const liveTranscript = document.getElementById('liveTranscript');
  const strategySection = document.getElementById('strategySection');
  const lastStrategy = document.getElementById('lastStrategy');
  const queryCountEl = document.getElementById('queryCount');
  const matchCountEl = document.getElementById('matchCount');
  const sessionTimeEl = document.getElementById('sessionTime');

  // Auth Elements
  const authLoggedInView = document.getElementById('authLoggedInView');
  const authLoggedOutView = document.getElementById('authLoggedOutView');
  const mainDashboardView = document.getElementById('mainDashboardView');
  const authErrorMsg = document.getElementById('authErrorMsg');
  const userDisplayName = document.getElementById('userDisplayName');
  const userRoleEmoji = document.getElementById('userRoleEmoji');
  const userRoleBadge = document.getElementById('userRoleBadge');
  const btnLogout = document.getElementById('btnLogout');
  const btnTabLogin = document.getElementById('btnTabLogin');
  const btnTabRegister = document.getElementById('btnTabRegister');
  const formMiniLogin = document.getElementById('formMiniLogin');
  const formMiniRegister = document.getElementById('formMiniRegister');

  // Knowledge Elements
  const lblActiveDocName = document.getElementById('lblActiveDocName');
  const lblActiveDocCards = document.getElementById('lblActiveDocCards');

  let isCapturing = false;
  let sessionTimer = null;
  let sessionSeconds = 0;
  let queryCount = 0;
  let matchCount = 0;
  let currentUser = null;
  let authToken = '';

  const BACKEND_URL = 'http://127.0.0.1:8000';

  // 1. Load User Session & Storage
  chrome.storage.local.get([
    'isCapturing',
    'sessionSeconds',
    'queryCount',
    'matchCount',
    'savedMeetingUrl',
    'sales_copilot_user',
    'sales_copilot_token'
  ], (result) => {
    isCapturing = result.isCapturing || false;
    sessionSeconds = result.sessionSeconds || 0;
    queryCount = result.queryCount || 0;
    matchCount = result.matchCount || 0;
    currentUser = result.sales_copilot_user || null;
    authToken = result.sales_copilot_token || '';

    syncAuthUI();

    if (result.savedMeetingUrl && meetingUrlInput) {
      meetingUrlInput.value = result.savedMeetingUrl;
    } else {
      chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
        if (tab && tab.url && (tab.url.includes('meet.google.com') || tab.url.includes('zoom.us') || tab.url.includes('teams.microsoft.com'))) {
          meetingUrlInput.value = tab.url;
        }
      });
    }

    updateCaptureUI();
    updateStatsUI();
    
    if (isCapturing) {
      startTimer();
    }
  });

  // --- Auth UI Sync ---
  function syncAuthUI() {
    if (currentUser) {
      if (authLoggedOutView) authLoggedOutView.style.display = 'none';
      if (mainDashboardView) mainDashboardView.style.display = 'block';
      if (authLoggedInView) authLoggedInView.style.display = 'flex';
      
      const isAdmin = currentUser.role === 'admin';
      if (userDisplayName) userDisplayName.textContent = currentUser.full_name || currentUser.email;
      if (userRoleEmoji) userRoleEmoji.textContent = isAdmin ? '👑' : '👤';
      if (userRoleBadge) {
        userRoleBadge.textContent = isAdmin ? 'Admin' : 'Rep';
        userRoleBadge.style.color = isAdmin ? '#f59e0b' : '#38bdf8';
      }
    } else {
      if (authLoggedOutView) authLoggedOutView.style.display = 'block';
      if (mainDashboardView) mainDashboardView.style.display = 'none';
      if (authLoggedInView) authLoggedInView.style.display = 'none';
    }
  }

  function showAuthError(msg) {
    if (authErrorMsg) {
      authErrorMsg.textContent = msg;
      authErrorMsg.style.display = 'block';
      setTimeout(() => {
        authErrorMsg.style.display = 'none';
      }, 5000);
    }
  }

  // Auth Tabs Toggle
  if (btnTabLogin && btnTabRegister) {
    btnTabLogin.addEventListener('click', () => {
      btnTabLogin.classList.add('active');
      btnTabRegister.classList.remove('active');
      formMiniLogin.style.display = 'block';
      formMiniRegister.style.display = 'none';
      if (authErrorMsg) authErrorMsg.style.display = 'none';
    });

    btnTabRegister.addEventListener('click', () => {
      btnTabRegister.classList.add('active');
      btnTabLogin.classList.remove('active');
      formMiniRegister.style.display = 'block';
      formMiniLogin.style.display = 'none';
      if (authErrorMsg) authErrorMsg.style.display = 'none';
    });
  }

  // Handle Mini Login Submit
  if (formMiniLogin) {
    formMiniLogin.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('txtPopupEmail').value.trim();
      const password = document.getElementById('txtPopupPassword').value;
      const btn = document.getElementById('btnPopupLogin');

      btn.disabled = true;
      btn.innerHTML = '<span>Authenticating...</span>';

      try {
        const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          currentUser = data.user;
          authToken = data.token;
          chrome.storage.local.set({
            sales_copilot_user: currentUser,
            sales_copilot_token: authToken
          });
          syncAuthUI();
          chrome.runtime.sendMessage({ type: 'user_authenticated', user: currentUser });
        } else {
          showAuthError(`❌ ${data.detail || 'Invalid email or password.'}`);
        }
      } catch (err) {
        showAuthError('❌ Cannot connect to backend server. Make sure it is running.');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Sign In to Co-Pilot</span> &rarr;';
      }
    });
  }

  // Handle Mini Register Submit
  if (formMiniRegister) {
    formMiniRegister.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fullName = document.getElementById('txtPopupRegName').value.trim();
      const email = document.getElementById('txtPopupRegEmail').value.trim();
      const password = document.getElementById('txtPopupRegPassword').value;
      const btn = document.getElementById('btnPopupRegister');

      btn.disabled = true;
      btn.innerHTML = '<span>Creating Account...</span>';

      try {
        const res = await fetch(`${BACKEND_URL}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ full_name: fullName, email, password })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          currentUser = data.user;
          authToken = data.token;
          chrome.storage.local.set({
            sales_copilot_user: currentUser,
            sales_copilot_token: authToken
          });
          syncAuthUI();
          chrome.runtime.sendMessage({ type: 'user_authenticated', user: currentUser });
        } else {
          showAuthError(`❌ ${data.detail || 'Registration failed.'}`);
        }
      } catch (err) {
        showAuthError('❌ Network error during registration.');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Create Sales Rep Account</span> &rarr;';
      }
    });
  }

  // Handle Logout
  if (btnLogout) {
    btnLogout.addEventListener('click', () => {
      currentUser = null;
      authToken = '';
      chrome.storage.local.remove(['sales_copilot_user', 'sales_copilot_token']);
      syncAuthUI();
      chrome.runtime.sendMessage({ type: 'user_logged_out' });
    });
  }

  // Paste from clipboard button
  if (btnPasteUrl) {
    btnPasteUrl.addEventListener('click', async () => {
      try {
        const text = await navigator.clipboard.readText();
        if (text) {
          meetingUrlInput.value = text.trim();
          chrome.storage.local.set({ savedMeetingUrl: text.trim() });
          captureStatus.textContent = 'Meeting link pasted! Ready to connect.';
        }
      } catch (e) {
        captureStatus.textContent = 'Please paste URL directly into input box.';
      }
    });
  }

  // Save URL on change
  meetingUrlInput.addEventListener('input', () => {
    chrome.storage.local.set({ savedMeetingUrl: meetingUrlInput.value.trim() });
  });

  // Check Backend Health & Active Strategy Status
  async function checkBackendHealth() {
    try {
      const response = await fetch(`${BACKEND_URL}/api/health`);
      if (response.ok) {
        backendStatus.textContent = '🟢 Online';
        backendStatus.className = 'status-badge online';
      } else {
        throw new Error('Backend offline');
      }

      // Fetch Knowledge Status
      const kbRes = await fetch(`${BACKEND_URL}/api/knowledge-status`);
      if (kbRes.ok) {
        const kbData = await kbRes.json();
        if (lblActiveDocName) lblActiveDocName.textContent = kbData.active_document || 'Playbook';
        if (lblActiveDocCards) lblActiveDocCards.textContent = `${kbData.total_cards || 0} Cards`;
      }
    } catch (error) {
      backendStatus.textContent = '🔴 Offline';
      backendStatus.className = 'status-badge offline';
    }
  }

  checkBackendHealth();
  setInterval(checkBackendHealth, 8000);

  // Ask background for current status
  chrome.runtime.sendMessage({ type: 'get_status' });

  // Format time
  function formatTime(seconds) {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }

  function startTimer() {
    if (sessionTimer) clearInterval(sessionTimer);
    sessionTimer = setInterval(() => {
      sessionSeconds++;
      sessionTimeEl.textContent = formatTime(sessionSeconds);
      chrome.storage.local.set({ sessionSeconds });
    }, 1000);
  }

  function stopTimer() {
    if (sessionTimer) {
      clearInterval(sessionTimer);
      sessionTimer = null;
    }
  }

  function updateCaptureUI() {
    if (isCapturing) {
      btnConnectMeeting.classList.add('active');
      btnToggleCapture.classList.add('active');
      connectBtnText.textContent = 'Disconnect Meeting';
      btnText.textContent = 'Stop Listening';
      captureStatus.textContent = '🟢 Active: Capturing audio & matching strategies...';
      startTimer();
    } else {
      btnConnectMeeting.classList.remove('active');
      btnToggleCapture.classList.remove('active');
      connectBtnText.textContent = 'Connect Meeting & Start Co-Pilot';
      btnText.textContent = 'Listen Active Tab';
      captureStatus.textContent = 'Ready to connect to meeting audio';
      stopTimer();
    }
    chrome.storage.local.set({ isCapturing });
  }
  
  function updateStatsUI() {
    queryCountEl.textContent = queryCount;
    matchCountEl.textContent = matchCount;
    sessionTimeEl.textContent = formatTime(sessionSeconds);
    chrome.storage.local.set({ queryCount, matchCount });
  }

  // Connect to Meeting Link button
  btnConnectMeeting.addEventListener('click', () => {
    if (!isCapturing) {
      const url = meetingUrlInput.value.trim();
      captureStatus.textContent = url ? 'Connecting to meeting link...' : 'Connecting to active meeting...';
      
      chrome.runtime.sendMessage({ 
        type: 'start_capture', 
        meetingUrl: url || null 
      }, (response) => {
        if (chrome.runtime.lastError || (response && !response.success)) {
          isCapturing = false;
          const err = chrome.runtime.lastError?.message || response?.error || 'Failed to connect';
          captureStatus.textContent = `❌ ${err}`;
          updateCaptureUI();
        } else {
          isCapturing = true;
          sessionSeconds = 0;
          updateCaptureUI();
        }
      });
    } else {
      chrome.runtime.sendMessage({ type: 'stop_capture' }, () => {
        isCapturing = false;
        updateCaptureUI();
      });
    }
  });

  // Listen to current active tab button
  btnToggleCapture.addEventListener('click', () => {
    if (!isCapturing) {
      captureStatus.textContent = 'Starting audio capture on active tab...';
      chrome.runtime.sendMessage({ type: 'start_capture', meetingUrl: null }, (response) => {
        if (chrome.runtime.lastError || (response && !response.success)) {
          isCapturing = false;
          const err = chrome.runtime.lastError?.message || response?.error || 'Failed to start';
          captureStatus.textContent = `❌ ${err}`;
          updateCaptureUI();
        } else {
          isCapturing = true;
          sessionSeconds = 0;
          updateCaptureUI();
        }
      });
    } else {
      chrome.runtime.sendMessage({ type: 'stop_capture' }, () => {
        isCapturing = false;
        updateCaptureUI();
      });
    }
  });

  // Listen for messages from background
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    switch (message.type) {
      case 'status_update':
        if (message.data.isCapturing !== undefined) {
          isCapturing = message.data.isCapturing;
          updateCaptureUI();
        }
        break;
      case 'transcript_update':
        liveTranscript.textContent = message.data.text;
        queryCount++;
        updateStatsUI();
        break;
      case 'strategy_found':
        strategySection.style.display = 'block';
        lastStrategy.textContent = message.data.pitch || 'Strategy matched!';
        matchCount++;
        updateStatsUI();
        break;
      case 'capture_error':
        isCapturing = false;
        updateCaptureUI();
        captureStatus.textContent = `Error: ${message.data.error}`;
        break;
    }
  });
});

