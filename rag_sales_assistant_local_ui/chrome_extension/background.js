importScripts('lib/config.js');

// ============================================================
// Sales Co-Pilot - Background Service Worker (THE BRAIN)
// Orchestrates: Tab Capture → Offscreen STT → Backend Query → Content Script Popup
// ============================================================

// --- State Management ---
let isCapturing = false;
let activeTabId = null;
let wsConnection = null;
let backendOnline = false;
let pingIntervalId = null;
let reconnectTimeoutId = null;
let lastTranscript = '';
let lastTranscriptTime = 0;

// --- Message Listener (Central Router) ---
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'start_capture':
      startCapture().then(sendResponse);
      return true; // Keep channel open for async response

    case 'stop_capture':
      stopCapture().then(sendResponse);
      return true;

    case 'get_status':
      sendResponse({
        isCapturing,
        backendOnline,
        activeTabId
      });
      break;

    case 'transcript_result':
      // Final transcript from offscreen document
      handleFinalTranscript(message.text, message.timestamp);
      break;

    case 'transcript_interim':
      // Interim transcript - forward to popup and content script for live display
      broadcastToPopup({
        type: 'transcript_update',
        data: { text: message.text }
      });
      if (activeTabId) {
        chrome.tabs.sendMessage(activeTabId, {
          type: 'transcript_update',
          data: { text: message.text, interim: true }
        }).catch(() => {});
      }
      break;

    case 'audio_chunk':
      // Audio chunk from offscreen MediaRecorder (for Whisper STT)
      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send(JSON.stringify({
          type: 'audio_chunk',
          audio_base64: message.audio_base64,
          format: message.format || '.webm'
        }));
      }
      break;

    case 'content_ready':
      console.log('[Sales Co-Pilot] Content script ready in tab:', sender.tab?.id);
      if (isCapturing && sender.tab?.id === activeTabId) {
        chrome.tabs.sendMessage(activeTabId, { type: 'capture_started' }).catch(() => {});
      }
      break;
  }
});

// --- Tab Audio Capture Flow ---
async function startCapture() {
  if (isCapturing) return { success: true, message: 'Already capturing' };

  try {
    // 1. Get the current active tab ID
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) throw new Error('No active tab found');
    if (tab.url && (tab.url.startsWith('chrome://') || tab.url.startsWith('edge://') || tab.url.startsWith('chrome-extension://') || tab.url.startsWith('about:'))) {
      throw new Error('Cannot run on browser internal pages. Please open a website (e.g. YouTube, Google Meet, Zoom, etc.)');
    }
    activeTabId = tab.id;

    // 2. Ensure content script is injected into the active tab
    try {
      await chrome.scripting.executeScript({
        target: { tabId: activeTabId },
        files: ['content/content.js']
      });
    } catch (e) {
      console.log('[Sales Co-Pilot] Content script injection note:', e);
    }

    // 3. Get stream ID using tabCapture API
    const streamId = await chrome.tabCapture.getMediaStreamId({ targetTabId: activeTabId });
    if (!streamId) throw new Error('Failed to get media stream ID');

    // 4. Create offscreen document for audio processing
    await ensureOffscreenDocument();

    // 5. Send stream ID to offscreen document to start STT
    chrome.runtime.sendMessage({
      type: 'start_stt',
      streamId: streamId
    });

    // 6. Connect WebSocket to FastAPI backend
    connectWebSocket();

    // 7. Start periodic health checks
    startHealthChecks();

    isCapturing = true;
    console.log('[Sales Co-Pilot] Capture started on tab:', activeTabId);

    // Notify content script in the active tab to display floating widget HUD
    chrome.tabs.sendMessage(activeTabId, {
      type: 'capture_started'
    }).catch(() => {});

    return { success: true };
  } catch (error) {
    console.error('[Sales Co-Pilot] Error starting capture:', error);
    await stopCapture(); // Cleanup on failure
    return { success: false, error: error.message };
  }
}

async function stopCapture() {
  isCapturing = false;

  // Close offscreen document
  try {
    if (await chrome.offscreen.hasDocument()) {
      chrome.runtime.sendMessage({ type: 'stop_stt' });
      await chrome.offscreen.closeDocument();
    }
  } catch (e) {
    console.error('[Sales Co-Pilot] Error closing offscreen:', e);
  }

  // Close WebSocket
  if (wsConnection) {
    wsConnection.close();
    wsConnection = null;
  }
  clearTimeout(reconnectTimeoutId);

  // Stop health checks
  if (pingIntervalId) {
    clearInterval(pingIntervalId);
    pingIntervalId = null;
  }

  // Notify content script to clear overlays
  if (activeTabId) {
    chrome.tabs.sendMessage(activeTabId, { type: 'capture_stopped' }).catch(() => {});
  }

  // Notify popup
  broadcastToPopup({ type: 'status_update', data: { isCapturing: false } });

  activeTabId = null;
  console.log('[Sales Co-Pilot] Capture stopped');
  return { success: true };
}

// --- Offscreen Document Management ---
async function ensureOffscreenDocument() {
  if (await chrome.offscreen.hasDocument()) return;

  await chrome.offscreen.createDocument({
    url: 'offscreen.html',
    reasons: ['USER_MEDIA'],
    justification: 'Capturing tab audio for real-time speech recognition'
  });
}

// --- Transcript Handling with Debouncing ---
function handleFinalTranscript(text, timestamp) {
  if (!text || text.trim().length < CONFIG.MIN_QUERY_LENGTH) return;

  const cleanText = text.trim();
  const now = Date.now();

  // Debounce: skip if identical text was sent very recently
  if (cleanText === lastTranscript && (now - lastTranscriptTime) < CONFIG.DEBOUNCE_MS) {
    return;
  }

  lastTranscript = cleanText;
  lastTranscriptTime = now;

  // Forward transcript to popup and content script for live display
  broadcastToPopup({
    type: 'transcript_update',
    data: { text: cleanText }
  });
  if (activeTabId) {
    chrome.tabs.sendMessage(activeTabId, {
      type: 'transcript_update',
      data: { text: cleanText, final: true }
    }).catch(() => {});
  }

  // Send to backend for RAG strategy lookup via WebSocket
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify({
      type: 'extension_query',  // Uses server-side debounced extension handler
      text: cleanText
    }));
  }
}

// --- WebSocket Connection to FastAPI Backend ---
function connectWebSocket(retryCount = 0) {
  if (wsConnection) {
    wsConnection.close();
  }

  try {
    wsConnection = new WebSocket(CONFIG.WS_URL);

    wsConnection.onopen = () => {
      console.log('[Sales Co-Pilot] WebSocket connected to backend');
      backendOnline = true;
      retryCount = 0;
      broadcastToPopup({ type: 'status_update', data: { backendOnline: true } });
    };

    wsConnection.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        // Handle transcription_complete from Whisper STT
        if (msg.type === 'transcription_complete') {
          broadcastToPopup({
            type: 'transcript_update',
            data: { text: msg.text }
          });
          if (activeTabId) {
            chrome.tabs.sendMessage(activeTabId, {
              type: 'transcript_update',
              data: { text: msg.text, latency_ms: msg.stt_latency_ms, final: true }
            }).catch(() => {});
          }
        }

        // Handle multi-strategy response from extension_query
        if (msg.type === 'extension_strategies' && activeTabId) {
          const strategies = msg.data?.strategies || [];
          if (strategies.length > 0) {
            // Send ONLY the top matching strategy to the floating widget
            const bestStrategy = strategies[0];
            chrome.tabs.sendMessage(activeTabId, {
              type: 'show_strategy',
              data: {
                question: bestStrategy.question_matched,
                pitch: bestStrategy.pitch,
                context: bestStrategy.context,
                confidence: bestStrategy.confidence_percent,
                q_number: bestStrategy.q_number,
                match_source: bestStrategy.match_source
              }
            }).catch(() => {});

            // Notify popup of match
            broadcastToPopup({
              type: 'strategy_found',
              data: {
                pitch: bestStrategy.pitch,
                count: strategies.length
              }
            });

            // Store in storage for popup access
            chrome.storage.local.set({ latestStrategies: strategies });
          }
        }

        // Also handle standard battlecard_response (fallback / compatibility)
        if (msg.type === 'battlecard_response' && activeTabId) {
          const data = msg.data;
          if (data && data.success) {
            chrome.tabs.sendMessage(activeTabId, {
              type: 'show_strategy',
              data: {
                question: data.question_matched,
                pitch: data.response || data.pitch,
                context: data.context,
                confidence: data.confidence_percent,
                q_number: data.q_number,
                match_source: data.match_source
              }
            }).catch(() => {});

            broadcastToPopup({
              type: 'strategy_found',
              data: { pitch: data.response || data.pitch }
            });
          }
        }

        // Handle system_status (initial connection)
        if (msg.type === 'system_status') {
          console.log('[Sales Co-Pilot] Backend system status:', msg.data);
        }

      } catch (e) {
        console.error('[Sales Co-Pilot] Error parsing WebSocket message:', e);
      }
    };

    wsConnection.onclose = () => {
      console.log('[Sales Co-Pilot] WebSocket closed');
      backendOnline = false;
      broadcastToPopup({ type: 'status_update', data: { backendOnline: false } });

      // Reconnect with exponential backoff if still capturing
      if (isCapturing) {
        const delay = Math.min(1000 * Math.pow(2, retryCount), 10000);
        console.log(`[Sales Co-Pilot] Reconnecting in ${delay}ms...`);
        reconnectTimeoutId = setTimeout(() => connectWebSocket(retryCount + 1), delay);
      }
    };

    wsConnection.onerror = (error) => {
      console.error('[Sales Co-Pilot] WebSocket error:', error);
    };
  } catch (error) {
    console.error('[Sales Co-Pilot] WebSocket connection error:', error);
  }
}

// --- Health Checks ---
function startHealthChecks() {
  if (pingIntervalId) clearInterval(pingIntervalId);

  pingIntervalId = setInterval(async () => {
    if (!isCapturing) return;
    try {
      const response = await fetch(`${CONFIG.BACKEND_URL}/api/ping`);
      backendOnline = response.ok;
    } catch (e) {
      backendOnline = false;
    }
  }, CONFIG.PING_INTERVAL);
}

// --- Helper: Broadcast to popup (popup may or may not be open) ---
function broadcastToPopup(message) {
  chrome.runtime.sendMessage(message).catch(() => {
    // Popup not open — that's fine, ignore
  });
}
