document.addEventListener('DOMContentLoaded', () => {
  const backendStatus = document.getElementById('backendStatus');
  const btnToggleCapture = document.getElementById('btnToggleCapture');
  const btnText = document.getElementById('btnText');
  const captureStatus = document.getElementById('captureStatus');
  const liveTranscript = document.getElementById('liveTranscript');
  const strategySection = document.getElementById('strategySection');
  const lastStrategy = document.getElementById('lastStrategy');
  const queryCountEl = document.getElementById('queryCount');
  const matchCountEl = document.getElementById('matchCount');
  const sessionTimeEl = document.getElementById('sessionTime');

  let isCapturing = false;
  let sessionTimer = null;
  let sessionSeconds = 0;
  let queryCount = 0;
  let matchCount = 0;

  // Load state from storage
  chrome.storage.local.get(['isCapturing', 'sessionSeconds', 'queryCount', 'matchCount'], (result) => {
    isCapturing = result.isCapturing || false;
    sessionSeconds = result.sessionSeconds || 0;
    queryCount = result.queryCount || 0;
    matchCount = result.matchCount || 0;
    
    updateCaptureUI();
    updateStatsUI();
    
    if (isCapturing) {
      startTimer();
    }
  });

  // Check Backend Health
  async function checkBackendHealth() {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/health');
      if (response.ok) {
        backendStatus.textContent = '🟢 Online';
        backendStatus.className = 'status-badge online';
      } else {
        throw new Error('Backend not healthy');
      }
    } catch (error) {
      backendStatus.textContent = '🔴 Offline';
      backendStatus.className = 'status-badge offline';
    }
  }

  checkBackendHealth();
  setInterval(checkBackendHealth, 10000);

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
      btnToggleCapture.classList.add('active');
      btnText.textContent = 'Stop Listening';
      captureStatus.textContent = 'Recording meeting audio...';
      startTimer();
    } else {
      btnToggleCapture.classList.remove('active');
      btnText.textContent = 'Start Listening';
      captureStatus.textContent = 'Ready to capture meeting audio';
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

  btnToggleCapture.addEventListener('click', () => {
    if (!isCapturing) {
      captureStatus.textContent = 'Starting audio capture...';
      chrome.runtime.sendMessage({ type: 'start_capture' }, (response) => {
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
