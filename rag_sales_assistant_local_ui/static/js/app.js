/**
 * Voice RAG Sales Co-Pilot - Simple Controller
 * Features: Instant STT, Smart Strategy Popup, Auto-TTS Ear Cue, and Mini Zoom HUD.
 */

const state = {
  ws: null,
  isListening: false,
  continuousVad: false,
  autoPopup: true,
  autoTts: false,
  recognition: null,
  isSpacePressed: false,
  activePitch: '',
  meetingStream: null,
  mediaRecorder: null,
  isMeetingStreaming: false,
  audioSourceType: 'tab' // Default: Google Meet Tab Audio (Client Voice)
};

// DOM References
const el = {
  statusPill: document.getElementById('statusPill'),
  btnMasterMic: document.getElementById('btnMasterMic'),
  stageBadgeText: document.getElementById('stageBadgeText'),
  liveTranscriptDisplay: document.getElementById('liveTranscriptDisplay'),
  chkContinuousVad: document.getElementById('chkContinuousVad'),
  chkAutoPopup: document.getElementById('chkAutoPopup'),
  chkAutoTts: document.getElementById('chkAutoTts'),
  chkDesktopAudio: document.getElementById('chkDesktopAudio'),
  voiceBar: document.querySelector('.voice-hero-bar'),

  // Meeting Audio Modal
  meetingModal: document.getElementById('meetingModal'),
  btnCloseMeetingModal: document.getElementById('btnCloseMeetingModal'),
  txtMeetingUrl: document.getElementById('txtMeetingUrl'),
  btnLaunchMeetingTab: document.getElementById('btnLaunchMeetingTab'),
  meetingPresetChips: document.querySelectorAll('.meeting-preset-chip'),
  cardSourceTab: document.getElementById('cardSourceTab'),
  cardSourceMic: document.getElementById('cardSourceMic'),
  meetingStreamStatus: document.getElementById('meetingStreamStatus'),
  btnStartMeetingAudio: document.getElementById('btnStartMeetingAudio'),
  btnStopMeetingAudio: document.getElementById('btnStopMeetingAudio'),
  meetingStatusBadge: document.getElementById('meetingStatusBadge'),
  streamSubtext: document.getElementById('streamSubtext'),

  // Intent Analyzer
  txtClientIntentInput: document.getElementById('txtClientIntentInput'),
  btnAnalyzeIntent: document.getElementById('btnAnalyzeIntent'),
  presetChips: document.querySelectorAll('.preset-chip'),

  // Intent Strategy Modal
  intentStrategyModal: document.getElementById('intentStrategyModal'),
  modalIntentBadge: document.getElementById('modalIntentBadge'),
  modalIntentIcon: document.getElementById('modalIntentIcon'),
  modalIntentTitle: document.getElementById('modalIntentTitle'),
  modalConfidencePill: document.getElementById('modalConfidencePill'),
  modalClientText: document.getElementById('modalClientText'),
  modalClientMindset: document.getElementById('modalClientMindset'),
  modalHiddenConcern: document.getElementById('modalHiddenConcern'),
  modalPitchText: document.getElementById('modalPitchText'),
  modalDosList: document.getElementById('modalDosList'),
  modalDontsList: document.getElementById('modalDontsList'),
  modalKbInfo: document.getElementById('modalKbInfo'),
  modalKbRef: document.getElementById('modalKbRef'),
  btnCloseIntentModal: document.getElementById('btnCloseIntentModal'),
  btnModalListen: document.getElementById('btnModalListen'),
  btnModalCopy: document.getElementById('btnModalCopy'),
  btnModalCopyText: document.getElementById('btnModalCopyText'),

  // Strategy Card
  displayMatchedQuestion: document.getElementById('displayMatchedQuestion'),
  displayPitchResponse: document.getElementById('displayPitchResponse'),
  displayContextBody: document.getElementById('displayContextBody'),
  btnCopyPitch: document.getElementById('btnCopyPitch'),
  btnCopyText: document.getElementById('btnCopyText'),
  btnSpeakPitch: document.getElementById('btnSpeakPitch'),
  badgeMatchedQ: document.getElementById('badgeMatchedQ'),
  labelMatchedQ: document.getElementById('labelMatchedQ'),

  // Quick Tags
  pillBtns: document.querySelectorAll('.pill-btn'),

  // Smart Strategy Popup
  smartStrategyPopup: document.getElementById('smartStrategyPopup'),
  popupTitle: document.getElementById('popupTitle'),
  popupMatchedQ: document.getElementById('popupMatchedQ'),
  popupPitchText: document.getElementById('popupPitchText'),
  btnClosePopup: document.getElementById('btnClosePopup'),
  btnPopupCopy: document.getElementById('btnPopupCopy'),
  btnPopupListen: document.getElementById('btnPopupListen'),

  // Mini HUD
  btnToggleHud: document.getElementById('btnToggleHud'),
  miniHudWidget: document.getElementById('miniHudWidget'),
  miniHudHeader: document.getElementById('miniHudHeader'),
  hudDetectedQ: document.getElementById('hudDetectedQ'),
  hudPitch: document.getElementById('hudPitch'),
  btnCloseMiniHud: document.getElementById('btnCloseMiniHud'),
  btnMiniCopy: document.getElementById('btnMiniCopy'),
  btnMiniMic: document.getElementById('btnMiniMic'),
  miniHudOpacity: document.getElementById('miniHudOpacity'),

  // KB Modal
  btnOpenKB: document.getElementById('btnOpenKB'),
  kbModal: document.getElementById('kbModal'),
  btnCloseKBModal: document.getElementById('btnCloseKBModal'),
  kbSearchInput: document.getElementById('kbSearchInput'),
  kbCardsContainer: document.getElementById('kbCardsContainer'),

  // Theme Toggle
  btnThemeToggle: document.getElementById('btnThemeToggle'),
  themeIcon: document.getElementById('themeIcon'),
  themeText: document.getElementById('themeText'),

  toastBox: document.getElementById('toastBox')
};

// Toast notification
function showToast(text) {
  const toast = document.createElement('div');
  toast.className = 'simple-toast';
  toast.innerHTML = `<i class="fa-solid fa-circle-check text-cyan"></i> ${text}`;
  el.toastBox.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 250);
  }, 2200);
}

// Text-to-Speech (Speaks in Rep's earphone)
function speakText(text) {
  if (!text || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

// Safe Universal Clipboard Copy Helper
function copyToClipboard(text, successMsg = 'Copied to clipboard!') {
  if (!text) return;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(successMsg);
    }).catch(() => {
      fallbackCopyText(text, successMsg);
    });
  } else {
    fallbackCopyText(text, successMsg);
  }
}

function fallbackCopyText(text, successMsg) {
  try {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    showToast(successMsg);
  } catch (err) {
    showToast('Failed to copy text.');
  }
}

// WebSocket Setup with Exponential Backoff
let wsReconnectDelay = 2000;
let wsReconnectTimer = null;

function sendWebSocketAuth() {
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    if (currentUser) {
      state.ws.send(JSON.stringify({
        type: 'auth_identify',
        user: currentUser
      }));
    }
  }
}

function initWebSocket() {
  if (wsReconnectTimer) clearTimeout(wsReconnectTimer);
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  state.ws = new WebSocket(wsUrl);

  state.ws.onopen = () => {
    wsReconnectDelay = 2000;
    if (el.statusPill) el.statusPill.textContent = '🟢 Online';
    sendWebSocketAuth();
  };

  state.ws.onclose = () => {
    if (el.statusPill) el.statusPill.textContent = '🔴 Reconnecting...';
    wsReconnectTimer = setTimeout(() => {
      wsReconnectDelay = Math.min(wsReconnectDelay * 1.5, 30000);
      initWebSocket();
    }, wsReconnectDelay);
  };

  state.ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'stage_update') {
        if (msg.stage === 'searching') {
          el.stageBadgeText.textContent = 'Finding best sales strategy...';
        } else if (msg.stage === 'analyzing_intent') {
          el.stageBadgeText.textContent = 'Analyzing client intent & psychology...';
        } else if (msg.stage === 'transcribing') {
          el.stageBadgeText.textContent = 'Transcribing meeting speech (Whisper)...';
        }
      } else if (msg.type === 'transcription_complete') {
        if (msg.text) {
          el.liveTranscriptDisplay.textContent = `"${msg.text}"`;
          showToast(`Transcribed (${msg.stt_latency_ms || 0}ms): "${msg.text.length > 30 ? msg.text.slice(0, 30) + '...' : msg.text}"`);
        }
      } else if (msg.type === 'battlecard_response') {
        handleBattlecardResponse(msg.data);
      } else if (msg.type === 'intent_strategy_response') {
        handleIntentStrategyResponse(msg.data);
      }
    } catch (e) {
      console.error(e);
    }
  };
}

// Handle AI / RAG Strategy Response
function handleBattlecardResponse(data) {
  // 🛑 Guard: If random talk / no match found, do NOT show popup alert
  if (!data || !data.success || !data.pitch || data.pitch === 'No response found.' || !data.question_matched) {
    if (state.isListening && el.stageBadgeText) {
      el.stageBadgeText.textContent = '🟢 Live Listening Active... Speak naturally';
    }
    if (el.smartStrategyPopup) el.smartStrategyPopup.style.display = 'none';
    return;
  }

  const matchedQ = data.question_matched || 'Client Objection';
  const pitch = data.response || data.pitch || '';
  state.activePitch = pitch;

  if (el.stageBadgeText) el.stageBadgeText.textContent = `🎯 Strategy Matched: Q${data.q_number || 'Objection'}`;

  // 1. Update Main UI Card if present
  if (el.displayMatchedQuestion) el.displayMatchedQuestion.textContent = `Client: "${matchedQ}"`;
  if (el.displayPitchResponse) el.displayPitchResponse.textContent = pitch;
  if (el.displayContextBody) el.displayContextBody.textContent = data.context || 'End-to-end engineering excellence and risk mitigation.';
  if (data.q_number && el.labelMatchedQ) {
    el.labelMatchedQ.textContent = `MATCHED: Q${data.q_number} STRATEGY`;
  }

  // 2. Update Mini HUD
  if (el.hudDetectedQ) el.hudDetectedQ.textContent = `Client: "${matchedQ}"`;
  if (el.hudPitch) el.hudPitch.textContent = pitch;

  // 3. 🚨 Show Smart Strategy Popup ONLY if enabled AND matched
  if (state.autoPopup && pitch) {
    if (el.popupMatchedQ) el.popupMatchedQ.textContent = `"${matchedQ}"`;
    if (el.popupPitchText) el.popupPitchText.textContent = pitch;
    if (el.smartStrategyPopup) el.smartStrategyPopup.style.display = 'block';
  }

  // 4. 🎧 Auto Read Strategy Aloud (Audio Voice in Ear) if enabled
  if (state.autoTts && pitch) {
    speakText(pitch);
    showToast('Speaking strategy cue into earphone (TTS)');
  }
}

// 🎯 Handle Client Intent & Strategy Modal Display
function handleIntentStrategyResponse(data) {
  if (state.intentTimeout) {
    clearTimeout(state.intentTimeout);
    state.intentTimeout = null;
  }

  if (el.btnAnalyzeIntent) {
    el.btnAnalyzeIntent.classList.remove('loading');
    el.btnAnalyzeIntent.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> <span>Analyze Intent</span>';
  }

  // Guard: If response has no pitch or is not successful
  if (!data || !data.success || !data.recommended_pitch) {
    console.log('No strategy pitch in response:', data);
    if (el.intentStrategyModal) {
      el.intentStrategyModal.style.display = 'none';
    }
    showToast('No sales strategy detected.');
    return;
  }

  // ✅ Real objection / intent matched & strategy decided -> OPEN POPUP!
  const badgeColor = data.badge_color || 'amber';
  const iconClass = data.icon || 'fa-bullseye';
  const intentTitle = data.intent_title || 'Client Objection';
  const confidence = data.confidence_percent || 88;
  const clientText = data.input_text || (el.txtClientIntentInput ? el.txtClientIntentInput.value : '');
  const pitch = data.recommended_pitch || '';

  // 1. Update Modal Elements
  if (el.modalIntentBadge) {
    el.modalIntentBadge.className = `intent-tag-badge badge-${badgeColor}`;
  }
  if (el.modalIntentIcon) {
    el.modalIntentIcon.className = `fa-solid ${iconClass}`;
  }
  if (el.modalIntentTitle) {
    el.modalIntentTitle.textContent = intentTitle.toUpperCase();
  }
  if (el.modalConfidencePill) {
    el.modalConfidencePill.textContent = `🎯 ${confidence}% Match`;
  }
  if (el.modalClientText) {
    el.modalClientText.textContent = `"${clientText}"`;
  }
  if (el.modalClientMindset) {
    el.modalClientMindset.textContent = data.client_mindset || 'Evaluating value proposition and risk.';
  }
  if (el.modalHiddenConcern) {
    el.modalHiddenConcern.textContent = data.hidden_concern || 'Wants certainty and high execution standard.';
  }
  if (el.modalPitchText) {
    el.modalPitchText.textContent = pitch;
  }

  // Dos List
  if (el.modalDosList) {
    el.modalDosList.innerHTML = '';
    (data.dos || ['Anchor value on quality and risk management']).forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      el.modalDosList.appendChild(li);
    });
  }

  // Donts List
  if (el.modalDontsList) {
    el.modalDontsList.innerHTML = '';
    (data.donts || ['Do not give unconditional discounts']).forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      el.modalDontsList.appendChild(li);
    });
  }

  // Matched KB reference
  if (el.modalKbRef) {
    if (data.q_number) {
      el.modalKbRef.textContent = `Matched: Q${data.q_number} Battlecard Strategy (${data.matched_question || ''})`;
    } else {
      el.modalKbRef.textContent = 'Matched: Enterprise Sales Strategy & Playbook';
    }
  }

  // 🎯 2. Open Modal Popup on genuine strategy match!
  if (el.intentStrategyModal) {
    el.intentStrategyModal.style.display = 'flex';
  }

  // Visual pulse on live update
  const pitchCard = document.querySelector('.modal-pitch');
  if (pitchCard) {
    pitchCard.classList.remove('updated-flash');
    void pitchCard.offsetWidth; // trigger reflow
    pitchCard.classList.add('updated-flash');
  }

  // 3. Also sync to Main UI Card if present
  if (el.displayMatchedQuestion) el.displayMatchedQuestion.textContent = `Client: "${data.matched_question || clientText}"`;
  if (el.displayPitchResponse) el.displayPitchResponse.textContent = pitch;
  if (el.displayContextBody) el.displayContextBody.textContent = data.context || data.hidden_concern || '';
  if (data.q_number && el.labelMatchedQ) {
    el.labelMatchedQ.textContent = `MATCHED: Q${data.q_number} - ${intentTitle}`;
  }

  // 4. Also update HUD
  if (el.hudDetectedQ) el.hudDetectedQ.textContent = `Intent: ${intentTitle}`;
  if (el.hudPitch) el.hudPitch.textContent = pitch;

  // 5. Speak if Auto TTS is active
  if (state.autoTts) {
    speakText(pitch);
  }

  showToast(`🎯 Matched: ${intentTitle}`);
}

// 🎯 Analyze Client Intent (API + WebSocket) - Real-time continuous detection
async function analyzeClientIntent(text) {
  const queryText = (text || (el.txtClientIntentInput ? el.txtClientIntentInput.value : '')).trim();
  if (!queryText) {
    showToast('Please type or select client text to analyze');
    if (el.txtClientIntentInput) el.txtClientIntentInput.focus();
    return;
  }

  if (el.btnAnalyzeIntent) {
    el.btnAnalyzeIntent.classList.add('loading');
    el.btnAnalyzeIntent.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Analyzing...</span>';
  }

  if (el.stageBadgeText) {
    el.stageBadgeText.textContent = 'Decoding client intent & mindset...';
  }

  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    if (state.intentTimeout) clearTimeout(state.intentTimeout);
    state.intentTimeout = setTimeout(() => {
      if (el.btnAnalyzeIntent) {
        el.btnAnalyzeIntent.classList.remove('loading');
        el.btnAnalyzeIntent.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> <span>Analyze Intent</span>';
      }
      showToast('Analysis timed out. Please try again.');
    }, 10000);

    state.ws.send(JSON.stringify({ type: 'analyze_intent', text: queryText }));
  } else {
    try {
      const res = await fetch('/api/analyze-intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: queryText })
      });
      const data = await res.json();
      handleIntentStrategyResponse(data);
    } catch (err) {
      console.error(err);
      if (el.btnAnalyzeIntent) {
        el.btnAnalyzeIntent.classList.remove('loading');
        el.btnAnalyzeIntent.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> <span>Analyze Intent</span>';
      }
      showToast('Error analyzing intent. Please try again.');
    }
  }
}
window.analyzeClientIntent = analyzeClientIntent;

// Send query to backend (routes to both KB and Intent Decider)
function sendQuery(queryText) {
  if (!queryText.trim()) return;
  el.liveTranscriptDisplay.textContent = `"${queryText}"`;
  el.stageBadgeText.textContent = 'Analyzing client objection...';

  // Trigger rich intent analysis for live modal updates
  analyzeClientIntent(queryText);

  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({ type: 'query', text: queryText }));
  } else {
    fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: queryText })
    })
    .then(r => r.json())
    .then(handleBattlecardResponse)
    .catch(console.error);
  }
}

// ==========================================================================
// 🎙️ Browser Built-In Native Web Speech Engine (0ms Device-Level Recognition)
// ==========================================================================
let interimDebounceTimer = null;
let lastProcessedNativeText = '';

function setupSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.log('[SPEECH] Web Speech API not supported in this browser.');
    return;
  }

  state.recognition = new SpeechRecognition();
  state.recognition.continuous = true;
  state.recognition.interimResults = true;
  state.recognition.maxAlternatives = 1;
  state.recognition.lang = 'en-US';

  state.recognition.onresult = (event) => {
    let interim = '';
    let final = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        final += event.results[i][0].transcript;
      } else {
        interim += event.results[i][0].transcript;
      }
    }

    const currentText = (final || interim).trim();
    if (currentText) {
      if (el.liveTranscriptDisplay) {
        el.liveTranscriptDisplay.textContent = `"${currentText}"`;
      }
      if (el.stageBadgeText) {
        el.stageBadgeText.textContent = '🟢 Hearing speech in real-time (0ms Native Speech)...';
      }
    }

    // 1. Immediate trigger on Final utterance
    if (final.trim() && final.trim() !== lastProcessedNativeText) {
      lastProcessedNativeText = final.trim();
      if (interimDebounceTimer) clearTimeout(interimDebounceTimer);
      console.log(`[SPEECH] ⚡ 0ms Native Final: '${final.trim()}'`);
      sendQuery(final.trim());
      return;
    }

    // 2. Fast interim debounce: If user pauses for 380ms while speaking, trigger early matching!
    if (interim.trim().length >= 8 && interim.trim() !== lastProcessedNativeText) {
      if (interimDebounceTimer) clearTimeout(interimDebounceTimer);
      interimDebounceTimer = setTimeout(() => {
        const textToProcess = interim.trim();
        if (textToProcess && textToProcess !== lastProcessedNativeText) {
          lastProcessedNativeText = textToProcess;
          console.log(`[SPEECH] ⚡ 0ms Native Interim Pause Trigger: '${textToProcess}'`);
          sendQuery(textToProcess);
        }
      }, 380);
    }
  };

  state.recognition.onerror = (event) => {
    console.log('[SPEECH] SpeechRecognition status notice:', event.error);
    if (state.isListening && event.error !== 'not-allowed' && event.error !== 'aborted') {
      setTimeout(() => {
        if (state.isListening && state.recognition) {
          try { state.recognition.start(); } catch (e) {}
        }
      }, 100);
    }
  };

  state.recognition.onend = () => {
    if (state.isListening) {
      setTimeout(() => {
        if (state.isListening && state.recognition) {
          try { state.recognition.start(); } catch (e) {}
        }
      }, 50);
    }
  };
}

// ==========================================================================
// 🎙️ High-Fidelity Audio Stream Processor (Sub-Second VAD 16kHz PCM Streamer)
// ==========================================================================

// High-fidelity anti-aliased resampler (48kHz/44.1kHz -> 16kHz)
function floatTo16BitPCM(input, inputSampleRate, outputSampleRate = 16000) {
  if (inputSampleRate === outputSampleRate) {
    const output = new Int16Array(input.length);
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]));
      output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return output;
  }

  const ratio = inputSampleRate / outputSampleRate;
  const newLength = Math.round(input.length / ratio);
  const output = new Int16Array(newLength);

  // 3-point anti-aliasing low-pass filter
  for (let i = 0; i < newLength; i++) {
    const centerIdx = i * ratio;
    const idx0 = Math.max(0, Math.floor(centerIdx - 1));
    const idx1 = Math.min(input.length - 1, Math.floor(centerIdx));
    const idx2 = Math.min(input.length - 1, Math.ceil(centerIdx + 1));
    
    // Weighted Gaussian-like average to eliminate high-frequency aliasing
    const filteredSample = (input[idx0] * 0.25) + (input[idx1] * 0.5) + (input[idx2] * 0.25);
    const s = Math.max(-1, Math.min(1, filteredSample));
    output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  return output;
}

async function startAudioProcessorStream(primaryStream, secondaryStream = null) {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) {
      console.error('[AUDIO] No AudioContext support');
      return;
    }

    // Close previous context cleanly
    if (state.audioCtx) {
      try { state.audioCtx.close(); } catch (e) {}
      state.audioCtx = null;
    }
    if (state.mediaRecorder && state.mediaRecorder.state !== 'inactive') {
      try { state.mediaRecorder.stop(); } catch (e) {}
      state.mediaRecorder = null;
    }

    const audioCtx = new AudioContextClass({ sampleRate: 48000 });
    if (audioCtx.state === 'suspended') {
      await audioCtx.resume();
    }
    console.log(`[AUDIO] AudioContext created. State: ${audioCtx.state}, SampleRate: ${audioCtx.sampleRate}`);

    const sampleRate = audioCtx.sampleRate;
    const processor = audioCtx.createScriptProcessor(4096, 1, 1);

    const gainNode = audioCtx.createGain();
    gainNode.gain.value = 0.001;

    // 1. Primary Audio Stream (Google Meet Tab or Mic)
    const primaryAudioTracks = primaryStream.getAudioTracks();
    if (primaryAudioTracks.length === 0) {
      console.error('[AUDIO] No audio tracks in primary stream!');
      return;
    }
    const cleanPrimaryStream = new MediaStream(primaryAudioTracks);
    const source1 = audioCtx.createMediaStreamSource(cleanPrimaryStream);
    source1.connect(processor);

    // 2. Secondary Stream (Microphone if available)
    let source2 = null;
    if (secondaryStream && secondaryStream.getAudioTracks().length > 0) {
      try {
        const secTracks = secondaryStream.getAudioTracks();
        const cleanSecondaryStream = new MediaStream(secTracks);
        source2 = audioCtx.createMediaStreamSource(cleanSecondaryStream);
        source2.connect(processor);
      } catch (e) {}
    }

    let pcm16Chunks = [];
    let samplesAccumulated = 0;
    const targetSampleRate = 16000;
    
    // Sub-Second VAD Parameters:
    // Trigger on natural 200ms silence after speech OR 0.8s max speech window (Eliminates 2.0s delay!)
    const minSpeechSamples = Math.round(targetSampleRate * 0.4);   // 400ms min
    const maxSpeechSamples = Math.round(targetSampleRate * 1.2);   // 1.2s max chunk
    const silenceTriggerSamples = Math.round(targetSampleRate * 0.22); // 220ms pause
    let speechActive = false;
    let silenceCounter = 0;
    let chunksSentCount = 0;

    processor.onaudioprocess = (e) => {
      if (!state.isListening && !state.isMeetingStreaming) return;

      const inputBuffer = e.inputBuffer.getChannelData(0);
      const resampled = floatTo16BitPCM(inputBuffer, sampleRate, targetSampleRate);
      
      // Calculate RMS energy for this 4096-frame slice
      let sumSq = 0;
      for (let i = 0; i < resampled.length; i++) {
        sumSq += (resampled[i] / 32768) ** 2;
      }
      const sliceRms = Math.sqrt(sumSq / resampled.length);

      const isSpeechNow = sliceRms >= 0.0025;

      if (isSpeechNow) {
        speechActive = true;
        silenceCounter = 0;
        pcm16Chunks.push(resampled);
        samplesAccumulated += resampled.length;
      } else {
        if (speechActive) {
          pcm16Chunks.push(resampled);
          samplesAccumulated += resampled.length;
          silenceCounter += resampled.length;
        }
      }

      // Natural Phrase Pause Trigger or Max Buffer Trigger
      const naturalPauseDetected = speechActive && (silenceCounter >= silenceTriggerSamples) && (samplesAccumulated >= minSpeechSamples);
      const maxWindowReached = samplesAccumulated >= maxSpeechSamples;

      if ((naturalPauseDetected || maxWindowReached) && pcm16Chunks.length > 0) {
        const fullLength = pcm16Chunks.reduce((acc, c) => acc + c.length, 0);
        const fullPcm = new Int16Array(fullLength);
        let offset = 0;
        for (const chunk of pcm16Chunks) {
          fullPcm.set(chunk, offset);
          offset += chunk.length;
        }

        // Reset state for next phrase
        pcm16Chunks = [];
        samplesAccumulated = 0;
        speechActive = false;
        silenceCounter = 0;

        if (state.ws && state.ws.readyState === WebSocket.OPEN && fullLength >= minSpeechSamples) {
          const uint8 = new Uint8Array(fullPcm.buffer);
          let binary = '';
          const len = uint8.byteLength;
          for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(uint8[i]);
          }
          const base64Pcm = btoa(binary);

          state.ws.send(JSON.stringify({
            type: 'audio_chunk',
            audio_base64: base64Pcm,
            format: 'raw_pcm'
          }));
          chunksSentCount++;
          console.log(`[AUDIO] ⚡ Sub-second VAD PCM phrase #${chunksSentCount} sent (${(fullLength / 16000).toFixed(2)}s)`);
        }
      }
    };

    processor.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    console.log('[AUDIO] ScriptProcessor audio graph connected with Sub-Second VAD');

    state.audioCtx = audioCtx;
    state.audioProcessor = processor;
    state.audioSource = source1;
    state.audioSource2 = source2;

    console.log('[AUDIO] ✅ Low-latency audio pipeline fully active');
  } catch (err) {
    console.error('[AUDIO] ❌ AudioContext streaming setup error:', err);
  }
}

function openMeetingModal() {
  if (el.meetingModal) {
    el.meetingModal.style.display = 'flex';
  }
}

function closeMeetingModal() {
  if (el.meetingModal) {
    el.meetingModal.style.display = 'none';
  }
}

async function startMeetingAudioStream() {
  try {
    let tabStream = null;
    const isTab = state.audioSourceType === 'tab';

    if (isTab) {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
        showToast('Screen/Tab audio not supported in this browser. Using microphone.');
        tabStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } else {
        showToast('Select your Google Meet tab and check "Also share tab audio"');
        tabStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: {
            echoCancellation: false,
            noiseSuppression: false,
            autoGainControl: false
          }
        });
      }
    } else {
      tabStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    }

    if (!tabStream || tabStream.getAudioTracks().length === 0) {
      showToast('⚠️ No audio track found! Make sure you checked "Also share tab audio" in Chrome.');
      return;
    }

    // Stop physical mic recognition if running so rep voice is NEVER transcribed
    if (state.recognition) {
      try { state.recognition.stop(); } catch (e) {}
    }

    state.meetingStream = tabStream;
    state.meetingMicStream = null;
    state.isMeetingStreaming = true;
    state.isListening = true;

    // Listen for user stopping share
    tabStream.getAudioTracks()[0].addEventListener('ended', () => {
      stopMeetingAudioStream();
      showToast('Meeting audio stream ended');
    });

    // Start 16kHz PCM Audio Streamer for CLIENT TAB AUDIO ONLY
    await startAudioProcessorStream(tabStream, null);

    // UI Updates
    closeMeetingModal();
    if (el.meetingStreamStatus) el.meetingStreamStatus.style.display = 'flex';
    if (el.btnStartMeetingAudio) el.btnStartMeetingAudio.style.display = 'none';
    if (el.btnStopMeetingAudio) el.btnStopMeetingAudio.style.display = 'flex';
    if (el.meetingStatusBadge) {
      el.meetingStatusBadge.className = 'confidence-pill';
      el.meetingStatusBadge.style.color = '#10b981';
      el.meetingStatusBadge.textContent = '🟢 Client-Only Audio Active';
    }

    el.btnMasterMic.classList.add('listening');
    el.voiceBar.classList.add('listening');
    el.stageBadgeText.textContent = '🟢 Listening to Client Voice (Google Meet Tab Only)...';
    showToast('Client Audio Stream Connected! Listening ONLY to client voice.');

  } catch (err) {
    console.error('Error accessing meeting audio:', err);
    showToast(`Could not start audio stream: ${err.message || 'Permission denied'}`);
    stopMeetingAudioStream();
  }
}

function stopMeetingAudioStream() {
  state.isMeetingStreaming = false;
  state.isListening = false;

  if (state.mediaRecorder && state.mediaRecorder.state !== 'inactive') {
    try { state.mediaRecorder.stop(); } catch (e) {}
  }
  state.mediaRecorder = null;

  if (state.audioProcessor) {
    try { state.audioProcessor.disconnect(); } catch (e) {}
    state.audioProcessor = null;
  }
  if (state.audioSource) {
    try { state.audioSource.disconnect(); } catch (e) {}
    state.audioSource = null;
  }
  if (state.audioSource2) {
    try { state.audioSource2.disconnect(); } catch (e) {}
    state.audioSource2 = null;
  }
  if (state.audioCtx) {
    try { state.audioCtx.close(); } catch (e) {}
    state.audioCtx = null;
  }

  if (state.meetingStream) {
    state.meetingStream.getTracks().forEach(t => t.stop());
    state.meetingStream = null;
  }
  if (state.meetingMicStream) {
    state.meetingMicStream.getTracks().forEach(t => t.stop());
    state.meetingMicStream = null;
  }

  if (state.recognition) {
    try { state.recognition.stop(); } catch (e) {}
  }

  // Reset UI
  if (el.meetingStreamStatus) el.meetingStreamStatus.style.display = 'none';
  if (el.btnStartMeetingAudio) el.btnStartMeetingAudio.style.display = 'flex';
  if (el.btnStopMeetingAudio) el.btnStopMeetingAudio.style.display = 'none';
  if (el.meetingStatusBadge) {
    el.meetingStatusBadge.className = 'confidence-pill';
    el.meetingStatusBadge.style.color = '';
    el.meetingStatusBadge.textContent = '⚡ Ready to Connect';
  }

  el.btnMasterMic.classList.remove('listening');
  el.voiceBar.classList.remove('listening');
  el.stageBadgeText.textContent = 'Hold Spacebar or Click Mic to Listen';
}

async function startListening() {
  if (state.isListening) return;
  state.isListening = true;
  el.btnMasterMic.classList.add('listening');
  el.voiceBar.classList.add('listening');
  el.stageBadgeText.textContent = '🟢 Listening Live... Speak naturally';

  // 1. Browser Web Speech Recognition
  if (state.recognition) {
    try { state.recognition.start(); } catch (e) {}
  }

  // 2. Microphone Stream via AudioProcessor
  try {
    if (!state.meetingStream) {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      state.meetingStream = stream;
      await startAudioProcessorStream(stream);
    }
  } catch (err) {
    console.log('Microphone stream notice:', err);
  }
}

function stopListening() {
  if (!state.isListening) return;
  state.isListening = false;
  el.btnMasterMic.classList.remove('listening');
  el.voiceBar.classList.remove('listening');
  el.stageBadgeText.textContent = 'Hold Spacebar or Click Mic to Listen';

  if (state.recognition) {
    try { state.recognition.stop(); } catch (e) {}
  }

  if (state.mediaRecorder && state.mediaRecorder.state !== 'inactive') {
    try { state.mediaRecorder.stop(); } catch (e) {}
  }
  state.mediaRecorder = null;

  if (state.meetingStream && !state.isMeetingStreaming) {
    state.meetingStream.getTracks().forEach(t => t.stop());
    state.meetingStream = null;
  }

  const spokenText = el.liveTranscriptDisplay.textContent.replace(/^"|"$/g, '').trim();
  if (spokenText && !spokenText.startsWith('Listening for client') && !spokenText.startsWith('Client ki baat')) {
    sendQuery(spokenText);
  }
}

// Event Bindings
function setupEvents() {
  // Push to talk: Spacebar (Desktop)
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !state.isSpacePressed && document.activeElement.tagName !== 'INPUT') {
      e.preventDefault();
      state.isSpacePressed = true;
      startListening();
    }
  });

  window.addEventListener('keyup', (e) => {
    if (e.code === 'Space' && state.isSpacePressed) {
      e.preventDefault();
      state.isSpacePressed = false;
      if (!state.continuousVad) {
        stopListening();
      }
    }
  });

  // Mic Click -> Direct Connect Google Meet Tab (Client Voice)
  if (el.btnMasterMic) {
    el.btnMasterMic.addEventListener('click', (e) => {
      e.preventDefault();
      if (state.isMeetingStreaming || state.isListening) {
        stopMeetingAudioStream();
        stopListening();
        showToast('Client Audio Stream Stopped');
      } else {
        openMeetingModal();
      }
    });

    // Mobile Push-to-Talk (Touch & Hold Support)
    el.btnMasterMic.addEventListener('touchstart', (e) => {
      if (!state.isMeetingStreaming && !state.isListening) {
        openMeetingModal();
      }
    }, { passive: true });
  }

  if (el.btnMiniMic) {
    el.btnMiniMic.addEventListener('click', () => {
      if (state.isMeetingStreaming || state.isListening) {
        stopMeetingAudioStream();
        stopListening();
      } else {
        openMeetingModal();
      }
    });
  }

  // Meeting Modal Event Handlers
  if (el.btnCloseMeetingModal) {
    el.btnCloseMeetingModal.addEventListener('click', () => {
      closeMeetingModal();
    });
  }

  if (el.meetingModal) {
    el.meetingModal.addEventListener('click', (e) => {
      if (e.target === el.meetingModal) {
        closeMeetingModal();
      }
    });
  }

  // Audio Source selection
  if (el.cardSourceTab) {
    el.cardSourceTab.addEventListener('click', () => {
      state.audioSourceType = 'tab';
      el.cardSourceTab.classList.add('active');
      if (el.cardSourceMic) el.cardSourceMic.classList.remove('active');
      const radioTab = el.cardSourceTab.querySelector('.source-radio');
      if (radioTab) radioTab.innerHTML = '<i class="fa-solid fa-circle-dot text-cyan"></i>';
      const radioMic = el.cardSourceMic ? el.cardSourceMic.querySelector('.source-radio') : null;
      if (radioMic) radioMic.innerHTML = '<i class="fa-regular fa-circle"></i>';
    });
  }

  if (el.cardSourceMic) {
    el.cardSourceMic.addEventListener('click', () => {
      state.audioSourceType = 'mic';
      el.cardSourceMic.classList.add('active');
      if (el.cardSourceTab) el.cardSourceTab.classList.remove('active');
      const radioMic = el.cardSourceMic.querySelector('.source-radio');
      if (radioMic) radioMic.innerHTML = '<i class="fa-solid fa-circle-dot text-cyan"></i>';
      const radioTab = el.cardSourceTab ? el.cardSourceTab.querySelector('.source-radio') : null;
      if (radioTab) radioTab.innerHTML = '<i class="fa-regular fa-circle"></i>';
    });
  }

  // Meeting Preset Chips
  if (el.meetingPresetChips) {
    el.meetingPresetChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const prefix = chip.getAttribute('data-prefix');
        if (el.txtMeetingUrl) {
          el.txtMeetingUrl.value = prefix;
          el.txtMeetingUrl.focus();
        }
      });
    });
  }

  // Launch Meeting Tab button
  if (el.btnLaunchMeetingTab) {
    el.btnLaunchMeetingTab.addEventListener('click', () => {
      const url = el.txtMeetingUrl ? el.txtMeetingUrl.value.trim() : '';
      if (url) {
        window.open(url, '_blank');
        showToast('Meeting tab opened. Click "Connect Audio" below to start listening.');
      } else {
        showToast('Please enter a valid meeting URL first');
        if (el.txtMeetingUrl) el.txtMeetingUrl.focus();
      }
    });
  }

  // Start Meeting Audio Stream
  if (el.btnStartMeetingAudio) {
    el.btnStartMeetingAudio.addEventListener('click', () => {
      const url = el.txtMeetingUrl ? el.txtMeetingUrl.value.trim() : '';
      if (url && !state.isMeetingStreaming) {
        showToast('Connecting audio stream for meeting...');
      }
      startMeetingAudioStream();
    });
  }

  // Stop Meeting Audio Stream
  if (el.btnStopMeetingAudio) {
    el.btnStopMeetingAudio.addEventListener('click', () => {
      stopMeetingAudioStream();
      showToast('Meeting audio disconnected');
    });
  }

  // Continuous Hands-Free VAD Toggle
  if (el.chkContinuousVad) {
    el.chkContinuousVad.addEventListener('change', (e) => {
      state.continuousVad = e.target.checked;
      if (state.continuousVad) {
        startListening();
        showToast('Continuous Hands-Free VAD On');
      } else {
        stopListening();
        showToast('Push-to-Talk (Spacebar) Mode');
      }
    });
  }

  // Auto-Popup Toggle
  if (el.chkAutoPopup) {
    el.chkAutoPopup.addEventListener('change', (e) => {
      state.autoPopup = e.target.checked;
      showToast(state.autoPopup ? 'Auto Strategy Popup Enabled' : 'Auto Strategy Popup Disabled');
    });
  }

  // Top Nav Tabs
  const tabLive = document.getElementById('tabLiveAssist');
  if (tabLive) tabLive.addEventListener('click', () => switchMainView('live'));
  const tabChunks = document.getElementById('tabChunkManager');
  if (tabChunks) tabChunks.addEventListener('click', () => switchMainView('chunks'));
  const tabAdmin = document.getElementById('tabAdminDashboard');
  if (tabAdmin) tabAdmin.addEventListener('click', () => switchMainView('admin'));

  // Auto-TTS Toggle
  if (el.chkAutoTts) {
    el.chkAutoTts.addEventListener('change', (e) => {
      state.autoTts = e.target.checked;
      showToast(state.autoTts ? 'Auto Voice Cue in Ear Enabled 🎧' : 'Auto Voice Cue Disabled');
    });
  }

  // Autonomous Zoom / System Audio Toggle (WASAPI)
  if (el.chkDesktopAudio) {
    el.chkDesktopAudio.addEventListener('change', async (e) => {
      try {
        const res = await fetch('/api/desktop-listener/toggle', { method: 'POST' });
        const data = await res.json();
        showToast(data.message || 'Desktop Audio Listener updated');
      } catch (err) {
        showToast('Error toggling Desktop Audio Listener');
      }
    });
  }

  // Copy Buttons using Universal Safe Helper
  if (el.btnCopyPitch) {
    el.btnCopyPitch.addEventListener('click', () => {
      const text = el.displayPitchResponse ? el.displayPitchResponse.textContent.trim() : '';
      copyToClipboard(text, 'Pitch copied to clipboard');
      if (el.btnCopyText) el.btnCopyText.textContent = 'Copied!';
      setTimeout(() => {
        if (el.btnCopyText) el.btnCopyText.textContent = 'Copy Pitch';
      }, 1800);
    });
  }

  if (el.btnPopupCopy) {
    el.btnPopupCopy.addEventListener('click', () => {
      const text = el.popupPitchText ? el.popupPitchText.textContent.trim() : '';
      copyToClipboard(text, 'Popup strategy copied!');
    });
  }

  if (el.btnMiniCopy) {
    el.btnMiniCopy.addEventListener('click', () => {
      const text = el.hudPitch ? el.hudPitch.textContent.trim() : '';
      copyToClipboard(text, 'HUD strategy copied!');
    });
  }

  // Listen / TTS Buttons
  if (el.btnSpeakPitch) {
    el.btnSpeakPitch.addEventListener('click', () => {
      if (el.displayPitchResponse) speakText(el.displayPitchResponse.textContent.trim());
      showToast('Playing voice cue');
    });
  }

  if (el.btnPopupListen) {
    el.btnPopupListen.addEventListener('click', () => {
      if (el.popupPitchText) speakText(el.popupPitchText.textContent.trim());
    });
  }

  // Close Popup
  if (el.btnClosePopup) {
    el.btnClosePopup.addEventListener('click', () => {
      if (el.smartStrategyPopup) el.smartStrategyPopup.style.display = 'none';
    });
  }

  // Quick Questions
  if (el.pillBtns) {
    el.pillBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        sendQuery(btn.getAttribute('data-q'));
      });
    });
  }

  // Mini HUD Toggle & Opacity
  if (el.btnToggleHud) {
    el.btnToggleHud.addEventListener('click', () => {
      const isShown = el.miniHudWidget && el.miniHudWidget.style.display === 'block';
      if (el.miniHudWidget) el.miniHudWidget.style.display = isShown ? 'none' : 'block';
      showToast(isShown ? 'Zoom HUD closed' : 'Zoom HUD opened');
    });
  }

  if (el.btnCloseMiniHud) {
    el.btnCloseMiniHud.addEventListener('click', () => {
      if (el.miniHudWidget) el.miniHudWidget.style.display = 'none';
    });
  }

  if (el.miniHudOpacity) {
    el.miniHudOpacity.addEventListener('input', (e) => {
      if (el.miniHudWidget) el.miniHudWidget.style.opacity = e.target.value / 100;
    });
  }

  // Knowledge Base Modal
  if (el.btnOpenKB) {
    el.btnOpenKB.addEventListener('click', () => {
      if (el.kbModal) el.kbModal.style.display = 'flex';
      loadKnowledgeBase();
    });
  }

  if (el.btnCloseKBModal) {
    el.btnCloseKBModal.addEventListener('click', () => {
      if (el.kbModal) el.kbModal.style.display = 'none';
    });
  }

  if (el.kbSearchInput) {
    el.kbSearchInput.addEventListener('input', (e) => {
      loadKnowledgeBase(e.target.value);
    });
  }

  // ==========================================================================
  // 🎯 Intent Analyzer & Strategy Modal Events
  // ==========================================================================
  if (el.btnAnalyzeIntent) {
    el.btnAnalyzeIntent.addEventListener('click', () => {
      analyzeClientIntent();
    });
  }

  if (el.txtClientIntentInput) {
    el.txtClientIntentInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        analyzeClientIntent();
      }
    });
  }

  // Preset Chips
  if (el.presetChips) {
    el.presetChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const intentText = chip.getAttribute('data-intent');
        if (el.txtClientIntentInput) {
          el.txtClientIntentInput.value = intentText;
        }
        analyzeClientIntent(intentText);
      });
    });
  }

  // Backdrop click to close Intent Modal
  if (el.intentStrategyModal) {
    el.intentStrategyModal.addEventListener('click', (e) => {
      if (e.target === el.intentStrategyModal) {
        if (typeof closeIntentModal === 'function') {
          closeIntentModal();
        } else {
          el.intentStrategyModal.style.display = 'none';
        }
      }
    });
  }

  // Copy from Intent Modal
  if (el.btnModalCopy) {
    el.btnModalCopy.addEventListener('click', () => {
      const pitch = el.modalPitchText ? el.modalPitchText.textContent.trim() : '';
      copyToClipboard(pitch, 'Strategy pitch copied to clipboard!');
      if (el.btnModalCopyText) el.btnModalCopyText.textContent = 'Copied!';
      setTimeout(() => {
        if (el.btnModalCopyText) el.btnModalCopyText.textContent = 'Copy Strategy Pitch';
      }, 1800);
    });
  }

  // Listen / TTS in Intent Modal
  if (el.btnModalListen) {
    el.btnModalListen.addEventListener('click', () => {
      const pitch = el.modalPitchText.textContent.trim();
      speakText(pitch);
      showToast('Playing strategy cue in ear (TTS)');
    });
  }

  // Theme Toggle Button
  if (el.btnThemeToggle) {
    el.btnThemeToggle.addEventListener('click', () => {
      toggleTheme();
    });
  }
}

// 🌓 Theme Controller (Dark / Light Mode)
function initTheme() {
  const savedTheme = localStorage.getItem('sales_copilot_theme') || 'dark';
  applyTheme(savedTheme);
}

function toggleTheme() {
  const currentTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  applyTheme(newTheme);
  localStorage.setItem('sales_copilot_theme', newTheme);
  showToast(newTheme === 'light' ? '☀️ Light Mode Enabled' : '🌙 Dark Mode Enabled');
}

function applyTheme(theme) {
  if (theme === 'light') {
    document.body.classList.add('light-theme');
    document.body.setAttribute('data-theme', 'light');
    if (el.themeIcon) el.themeIcon.className = 'fa-solid fa-sun text-amber';
    if (el.themeText) el.themeText.textContent = 'Light';
  } else {
    document.body.classList.remove('light-theme');
    document.body.setAttribute('data-theme', 'dark');
    if (el.themeIcon) el.themeIcon.className = 'fa-solid fa-moon';
    if (el.themeText) el.themeText.textContent = 'Dark';
  }
}

// Load KB Cards
async function loadKnowledgeBase(query = '') {
  try {
    const url = query ? `/api/battlecards?q=${encodeURIComponent(query)}` : '/api/battlecards';
    const res = await fetch(url);
    const data = await res.json();

    el.kbCardsContainer.innerHTML = '';
    (data.battlecards || []).forEach(card => {
      const cardDiv = document.createElement('div');
      cardDiv.className = 'kb-card-simple';
      cardDiv.innerHTML = `
        <div class="kb-q-title">Q${card.q_number}. ${card.question}</div>
        <div class="kb-p-body">${card.pitch}</div>
      `;
      cardDiv.addEventListener('click', () => {
        handleBattlecardResponse({
          q_number: card.q_number,
          question_matched: card.question,
          pitch: card.pitch,
          response: card.pitch,
          context: card.context
        });
        el.kbModal.style.display = 'none';
        showToast(`Loaded Q${card.q_number}`);
      });
      el.kbCardsContainer.appendChild(cardDiv);
    });
  } catch (err) {
    console.error(err);
  }
}

// Custom Playbook Upload & Embeddings Management
function setupPlaybookUpload() {
  const btnOpen = document.getElementById('btnOpenUploadModal');
  const btnClose = document.getElementById('btnCloseUploadModal');
  const modal = document.getElementById('modalUploadPlaybook');
  const dropZone = document.getElementById('playbookDropZone');
  const fileInput = document.getElementById('playbookFileInput');
  const selectedName = document.getElementById('selectedFileName');
  const btnSubmit = document.getElementById('btnSubmitPlaybook');
  const btnReset = document.getElementById('btnResetPlaybook');
  const resultBox = document.getElementById('playbookUploadResult');
  const resultMsg = document.getElementById('playbookUploadMsg');
  let selectedFile = null;

  const btnMainOpen = document.getElementById('btnMainUploadDoc');
  if (btnMainOpen && modal) {
    btnMainOpen.addEventListener('click', () => {
      modal.style.display = 'flex';
      refreshPlaybookStatus();
    });
  }

  if (btnOpen && modal) {
    btnOpen.addEventListener('click', () => {
      modal.style.display = 'flex';
      refreshPlaybookStatus();
    });
  }

  if (btnClose && modal) {
    btnClose.addEventListener('click', () => {
      modal.style.display = 'none';
    });
  }

  // Close on backdrop click
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
      }
    });
  }

  if (dropZone && fileInput) {
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = '#38bdf8';
      dropZone.style.background = 'rgba(56, 189, 248, 0.15)';
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.style.borderColor = 'rgba(56, 189, 248, 0.4)';
      dropZone.style.background = 'rgba(15, 23, 42, 0.5)';
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = 'rgba(56, 189, 248, 0.4)';
      dropZone.style.background = 'rgba(15, 23, 42, 0.5)';
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        if (typeof onPlaybookFileSelected === 'function') {
          onPlaybookFileSelected({ files: e.dataTransfer.files });
        } else {
          handleFileSelect(e.dataTransfer.files[0]);
        }
      }
    });
  }

  function handleFileSelect(file) {
    selectedFile = file;
    if (selectedName) {
      selectedName.style.display = 'block';
      selectedName.textContent = `📄 Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    }
    if (btnSubmit) {
      btnSubmit.removeAttribute('disabled');
      btnSubmit.style.opacity = '1';
    }
  }

  if (btnSubmit) {
    btnSubmit.addEventListener('click', async () => {
      if (!selectedFile) return;
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Parsing & Embedding...';
      if (resultBox) resultBox.style.display = 'none';

      try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        const res = await fetch('/api/upload-document', {
          method: 'POST',
          body: formData
        });

        const data = await res.json();
        if (res.ok && data.success) {
          showToast(`✅ ${data.total_chunks} Custom Strategy Chunks Activated!`);
          if (resultBox && resultMsg) {
            resultBox.style.display = 'block';
            resultBox.style.background = 'rgba(16, 185, 129, 0.15)';
            resultBox.style.color = '#10b981';
            resultMsg.innerHTML = `🎉 Successfully loaded <strong>${data.filename}</strong> with <strong>${data.total_chunks} strategy chunks</strong>! All custom embeddings are now live across Chrome Extension and Web UI.`;
          }
          refreshPlaybookStatus();
          loadKnowledgeBase();
        } else {
          throw new Error(data.detail || 'Upload failed');
        }
      } catch (err) {
        showToast(`❌ Error: ${err.message}`);
        if (resultBox && resultMsg) {
          resultBox.style.display = 'block';
          resultBox.style.background = 'rgba(239, 68, 68, 0.15)';
          resultBox.style.color = '#ef4444';
          resultMsg.textContent = `Error: ${err.message}`;
        }
      } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<i class="fa-solid fa-bolt"></i> Chunk & Generate Embeddings';
      }
    });
  }

  if (btnReset) {
    btnReset.addEventListener('click', async () => {
      if (!confirm('Are you sure you want to reset to the default 70 sales battlecards?')) return;
      btnReset.disabled = true;
      try {
        const res = await fetch('/api/reset-knowledge', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
          showToast('🔄 Restored default 70 battlecards!');
          refreshPlaybookStatus();
          loadKnowledgeBase();
          if (resultBox && resultMsg) {
            resultBox.style.display = 'block';
            resultBox.style.background = 'rgba(56, 189, 248, 0.15)';
            resultBox.style.color = '#38bdf8';
            resultMsg.textContent = 'Restored default zoom.pdf with 70 sales battlecards.';
          }
        }
      } catch (e) {
        showToast('Error resetting knowledge base');
      } finally {
        btnReset.disabled = false;
      }
    });
  }
}

async function refreshPlaybookStatus() {
  try {
    const res = await fetch('/api/knowledge-status');
    const data = await res.json();
    const lblName = document.getElementById('lblActiveDocName');
    const lblMeta = document.getElementById('lblActiveDocMeta');
    const badge = document.getElementById('badgeActiveStatus');
    const mainName = document.getElementById('mainActiveDocName');
    const mainMeta = document.getElementById('mainActiveDocMeta');

    if (lblName) lblName.textContent = data.active_document || 'Default 70 Battlecards';
    if (lblMeta) lblMeta.textContent = `${data.total_chunks} Strategy Chunks Loaded ${data.uploaded_at ? `(Uploaded: ${data.uploaded_at})` : ''}`;
    if (mainName) mainName.textContent = data.active_document || 'Default 70 Battlecards';
    if (mainMeta) mainMeta.textContent = `${data.total_chunks} Strategy Chunks Loaded — Real-Time Voice Matching Active`;

    if (badge) {
      if (data.is_custom) {
        badge.textContent = 'Custom Playbook Active';
        badge.style.background = 'rgba(6, 182, 212, 0.2)';
        badge.style.color = '#38bdf8';
      } else {
        badge.textContent = 'Default 70 Battlecards';
        badge.style.background = 'rgba(16, 185, 129, 0.2)';
        badge.style.color = '#10b981';
      }
    }
  } catch (e) {}
}

// =========================================================================
// 🔐 MULTI-TENANT RBAC, CHUNK MANAGER & ADMIN CONTROLLER
// =========================================================================

let currentUser = null;
let authToken = localStorage.getItem('sales_copilot_token') || '';
let userChunksData = [];

// Helper for authenticated fetch
async function authFetch(url, options = {}) {
  options.headers = options.headers || {};
  if (authToken) {
    options.headers['Authorization'] = `Bearer ${authToken}`;
  }
  return fetch(url, options);
}

// 1. Initialize Authentication & Session
async function initAuth() {
  const savedUser = localStorage.getItem('sales_copilot_user');
  if (savedUser && authToken) {
    try {
      currentUser = JSON.parse(savedUser);
      syncAuthUI();
      // Verify token with backend
      const res = await authFetch('/api/auth/me');
      if (res.ok) {
        currentUser = await res.json();
        localStorage.setItem('sales_copilot_user', JSON.stringify(currentUser));
        syncAuthUI();
        return;
      }
    } catch (e) {
      console.warn('Session verification error:', e);
    }
  }

  // Default clean state: Standard Sales Rep (Prompt Login/Register on open)
  currentUser = null;
  authToken = '';
  syncAuthUI();

  // Auto-prompt Account Login & Registration on page open
  setTimeout(() => {
    openAuthModal();
  }, 400);
}

function syncAuthUI() {
  const badge = document.getElementById('userAuthBadge');
  const roleIcon = document.getElementById('userRoleIcon');
  const nameLabel = document.getElementById('userDisplayName');
  const roleTag = document.getElementById('userRoleTag');
  const adminTab = document.getElementById('tabAdminDashboard');
  const logoutBtn = document.getElementById('btnLogout');

  if (!currentUser) {
    if (nameLabel) nameLabel.textContent = 'Sales Rep Mode';
    if (roleTag) {
      roleTag.textContent = 'Sales Rep';
      roleTag.className = 'user-role-tag user';
      roleTag.style.display = 'none';
    }
    if (roleIcon) {
      roleIcon.className = 'fa-solid fa-user-tie text-cyan';
    }
    if (logoutBtn) logoutBtn.style.display = 'none';
    if (adminTab) adminTab.style.display = 'none';
    loadUserChunks();
    return;
  }

  const isAdmin = currentUser.role === 'admin';

  if (nameLabel) nameLabel.textContent = isAdmin ? currentUser.email : (currentUser.full_name || currentUser.email);
  if (roleTag) {
    roleTag.textContent = isAdmin ? 'Admin' : 'Sales Rep';
    roleTag.className = `user-role-tag ${isAdmin ? 'admin' : 'user'}`;
    roleTag.style.display = 'inline-block';
  }
  if (roleIcon) {
    roleIcon.className = isAdmin ? 'fa-solid fa-crown text-amber' : 'fa-solid fa-user text-cyan';
  }
  if (logoutBtn) {
    logoutBtn.style.display = 'inline-block';
  }

  // Strictly enforce Admin Tab visibility: ONLY visible if authenticated role === 'admin'
  if (adminTab) {
    adminTab.style.display = isAdmin ? 'inline-flex' : 'none';
  }

  // If currently on admin view but user is not admin, redirect to live view
  const viewAdmin = document.getElementById('viewAdminDashboard');
  if (viewAdmin && viewAdmin.style.display !== 'none' && !isAdmin) {
    switchMainView('live');
  }

  // Load user chunks count badge
  loadUserChunks();
}

function openAuthModal() {
  const modal = document.getElementById('authModal');
  if (modal) modal.style.display = 'flex';
}

function closeAuthModal() {
  const modal = document.getElementById('authModal');
  if (modal) modal.style.display = 'none';
}

function switchAuthTab(tab) {
  const btnLogin = document.getElementById('btnTabLogin');
  const btnReg = document.getElementById('btnTabRegister');
  const formLogin = document.getElementById('formLogin');
  const formReg = document.getElementById('formRegister');

  if (tab === 'login') {
    btnLogin.classList.add('active');
    btnReg.classList.remove('active');
    formLogin.style.display = 'block';
    formReg.style.display = 'none';
  } else {
    btnReg.classList.add('active');
    btnLogin.classList.remove('active');
    formReg.style.display = 'block';
    formLogin.style.display = 'none';
  }
}

function fillAdminCredentials() {
  document.getElementById('txtLoginEmail').value = 'okashaxortlogix@gmail.com';
  document.getElementById('txtLoginPassword').value = 'adminokasha';
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  const email = document.getElementById('txtLoginEmail').value.trim();
  const password = document.getElementById('txtLoginPassword').value;
  const btn = document.getElementById('btnLoginSubmit');

  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Authenticating...';

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (res.ok && data.success) {
      authToken = data.token;
      currentUser = data.user;
      localStorage.setItem('sales_copilot_token', authToken);
      localStorage.setItem('sales_copilot_user', JSON.stringify(currentUser));
      syncAuthUI();
      sendWebSocketAuth();
      closeAuthModal();
      showToast(`👋 Welcome back, ${currentUser.full_name} (${currentUser.role})!`);
      if (currentUser.role === 'admin') {
        loadAdminDashboardData();
      }
    } else {
      showToast(data.detail || 'Login failed.');
    }
  } catch (err) {
    showToast('Network error during login: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>Sign In to Co-Pilot</span> <i class="fa-solid fa-arrow-right"></i>';
  }
}

async function handleRegisterSubmit(e) {
  e.preventDefault();
  const fullName = document.getElementById('txtRegFullName').value.trim();
  const email = document.getElementById('txtRegEmail').value.trim();
  const password = document.getElementById('txtRegPassword').value;
  const btn = document.getElementById('btnRegSubmit');

  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating Account...';

  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name: fullName })
    });
    const data = await res.json();

    if (res.ok && data.success) {
      authToken = data.token;
      currentUser = data.user;
      localStorage.setItem('sales_copilot_token', authToken);
      localStorage.setItem('sales_copilot_user', JSON.stringify(currentUser));
      syncAuthUI();
      sendWebSocketAuth();
      closeAuthModal();
      showToast(`🎉 Sales rep account registered! Welcome, ${fullName}.`);
      switchMainView('chunks');
    } else {
      showToast(data.detail || 'Registration failed.');
    }
  } catch (err) {
    showToast('Network error: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>Create Sales Rep Account</span> <i class="fa-solid fa-user-check"></i>';
  }
}

function logoutUser(e) {
  if (e) e.stopPropagation();
  localStorage.removeItem('sales_copilot_token');
  localStorage.removeItem('sales_copilot_user');
  authToken = '';
  currentUser = null;
  syncAuthUI();
  switchMainView('live');
  showToast('Logged out. Switched to standard Sales Rep mode.');
}

// 2. View Switcher (Live Co-Pilot, Custom Chunks, Admin Dashboard)
function switchMainView(viewName) {
  const viewLive = document.getElementById('viewLiveAssist');
  const viewChunks = document.getElementById('viewChunkManager');
  const viewAdmin = document.getElementById('viewAdminDashboard');

  const tabLive = document.getElementById('tabLiveAssist');
  const tabChunks = document.getElementById('tabChunkManager');
  const tabAdmin = document.getElementById('tabAdminDashboard');

  // Hide all
  if (viewLive) viewLive.style.display = 'none';
  if (viewChunks) viewChunks.style.display = 'none';
  if (viewAdmin) viewAdmin.style.display = 'none';

  if (tabLive) tabLive.classList.remove('active');
  if (tabChunks) tabChunks.classList.remove('active');
  if (tabAdmin) tabAdmin.classList.remove('active');

  if (viewName === 'chunks') {
    if (viewChunks) viewChunks.style.display = 'block';
    if (tabChunks) tabChunks.classList.add('active');
    loadUserChunks();
  } else if (viewName === 'admin') {
    if (viewAdmin) viewAdmin.style.display = 'block';
    if (tabAdmin) tabAdmin.classList.add('active');
    loadAdminDashboardData();
  } else {
    if (viewLive) viewLive.style.display = 'block';
    if (tabLive) tabLive.classList.add('active');
  }
}

// 3. User Document Upload & Custom Chunk Manager
async function handleUserFileUpload(e) {
  const file = e.target.files && e.target.files[0];
  if (!file) return;

  const progressBox = document.getElementById('userUploadProgressBox');
  const statusText = document.getElementById('userUploadStatusText');

  if (progressBox) progressBox.style.display = 'block';
  if (statusText) statusText.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading & parsing strategy chunks into Vector DB...';

  try {
    const formData = new FormData();
    formData.append('file', file);

    let res, data;
    if (authToken) {
      res = await authFetch('/api/user/documents/upload', {
        method: 'POST',
        body: formData
      });
      data = await res.json();
      if (res.ok && data.success) {
        showToast(`☁️ Backed up to Google Drive & generated ${data.chunks_count} strategy chunks!`);
      }
    } else {
      res = await fetch('/api/upload-document', {
        method: 'POST',
        body: formData
      });
      data = await res.json();
      if (res.ok && data.success) {
        showToast(`✅ Generated & indexed ${data.total_chunks} custom strategy chunks!`);
      }
    }

    if (res.ok && data.success) {
      refreshPlaybookStatus();
      loadUserChunks();
    } else {
      showToast(data.detail || 'Upload failed.');
    }
  } catch (err) {
    showToast('Upload error: ' + err.message);
  } finally {
    if (progressBox) progressBox.style.display = 'none';
    e.target.value = '';
  }
}

async function loadUserChunks() {
  try {
    let chunks = [];
    if (authToken) {
      const res = await authFetch('/api/user/chunks');
      if (res.ok) {
        const data = await res.json();
        chunks = data.chunks || [];
      }
    }
    // If no user custom chunks yet, load from active battlecards (/api/battlecards)
    if (chunks.length === 0) {
      const resBc = await fetch('/api/battlecards');
      if (resBc.ok) {
        const dataBc = await resBc.json();
        chunks = (dataBc.battlecards || []).map((b, idx) => ({
          id: b.id || b.q_number || (idx + 1),
          title: b.question || `Battlecard #${b.q_number || idx + 1}`,
          strategy_pitch: b.pitch || b.response || '',
          context: b.context || '',
          is_base: true
        }));
      }
    }
    userChunksData = chunks;
    const countBadge = document.getElementById('userChunksCount');
    const metaLbl = document.getElementById('lblChunksMeta');
    if (countBadge) countBadge.textContent = userChunksData.length;
    if (metaLbl) metaLbl.textContent = `Showing ${userChunksData.length} strategy chunks`;
    renderUserChunksGrid(userChunksData);
  } catch (e) {
    console.error('Error loading chunks:', e);
  }
}

function renderUserChunksGrid(chunks) {
  const grid = document.getElementById('userChunksGrid');
  if (!grid) return;

  if (!chunks || chunks.length === 0) {
    grid.innerHTML = `
      <div class="chunks-empty-state" style="grid-column: 1/-1; text-align: center; padding: 40px; color: #94a3b8;">
        <i class="fa-solid fa-layer-group" style="font-size: 32px; color: #38bdf8; margin-bottom: 12px;"></i>
        <p style="font-size: 13.5px;">No custom strategy chunks found. Upload a document (.PDF, .DOCX, .TXT) above to generate your isolated battlecards!</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = '';
  chunks.forEach((c, idx) => {
    const card = document.createElement('div');
    card.className = 'chunk-card';
    card.id = `user-chunk-${c.id}`;
    card.innerHTML = `
      <div class="chunk-card-header">
        <div>
          <span class="chunk-index-badge">CHUNK #${idx + 1}</span>
          <div class="chunk-title">${escapeHtml(c.title || 'Strategy Objection')}</div>
        </div>
        <span style="font-size: 10px; color: #10b981; background: rgba(16, 185, 129, 0.15); padding: 2px 6px; border-radius: 4px;">Active</span>
      </div>

      <div class="chunk-pitch-body">
        <strong>Pitch:</strong> "${escapeHtml(c.strategy_pitch || '')}"
        ${c.context ? `<div style="color: #94a3b8; font-size: 11px; margin-top: 6px;"><em>Rationale: ${escapeHtml(c.context)}</em></div>` : ''}
      </div>

      <div class="chunk-card-actions">
        <button class="btn-clean" style="font-size: 11px; color: #ef4444;" onclick="deleteUserChunk(${c.id})" title="Delete Chunk">
          <i class="fa-solid fa-trash"></i> Delete
        </button>
        <button class="btn-clean primary-glow" style="font-size: 11px;" onclick="openEditChunkModal(${c.id})" title="Edit Strategy Pitch">
          <i class="fa-solid fa-pen-to-square"></i> Edit Strategy
        </button>
      </div>
    `;
    grid.appendChild(card);
  });
}

function filterUserChunks() {
  const query = (document.getElementById('txtSearchChunks').value || '').toLowerCase().trim();
  if (!query) {
    renderUserChunksGrid(userChunksData);
    return;
  }
  const filtered = userChunksData.filter(c => 
    (c.title || '').toLowerCase().includes(query) ||
    (c.strategy_pitch || '').toLowerCase().includes(query) ||
    (c.context || '').toLowerCase().includes(query)
  );
  renderUserChunksGrid(filtered);
}

function openEditChunkModal(chunkId) {
  const chunk = userChunksData.find(c => c.id === chunkId);
  if (!chunk) return;

  document.getElementById('editChunkId').value = chunk.id;
  document.getElementById('editChunkTitle').value = chunk.title || '';
  document.getElementById('editChunkPitch').value = chunk.strategy_pitch || '';
  document.getElementById('editChunkContext').value = chunk.context || '';

  const modal = document.getElementById('editChunkModal');
  if (modal) modal.style.display = 'flex';
}

function closeEditChunkModal() {
  const modal = document.getElementById('editChunkModal');
  if (modal) modal.style.display = 'none';
}

async function saveEditedChunk() {
  const chunkId = document.getElementById('editChunkId').value;
  const title = document.getElementById('editChunkTitle').value.trim();
  const pitch = document.getElementById('editChunkPitch').value.trim();
  const context = document.getElementById('editChunkContext').value.trim();

  if (!title || !pitch) {
    showToast('Question title and Strategy Pitch are required.');
    return;
  }

  try {
    const res = await authFetch(`/api/user/chunks/${chunkId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        strategy_pitch: pitch,
        context,
        is_active: 1
      })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast('✅ Strategy pitch updated and re-indexed!');
      closeEditChunkModal();
      loadUserChunks();
    } else {
      showToast(data.detail || 'Error updating chunk.');
    }
  } catch (err) {
    showToast('Save error: ' + err.message);
  }
}

async function deleteUserChunk(chunkId) {
  if (!confirm('Are you sure you want to delete this custom strategy chunk?')) return;
  try {
    const res = await authFetch(`/api/user/chunks/${chunkId}`, {
      method: 'DELETE'
    });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast('Chunk deleted.');
      loadUserChunks();
    } else {
      showToast(data.detail || 'Error deleting chunk.');
    }
  } catch (err) {
    showToast('Delete error: ' + err.message);
  }
}

// 4. Simplified Executive Admin Dashboard Loader
async function loadAdminDashboardData() {
  if (!currentUser || currentUser.role !== 'admin') return;

  try {
    // 1. Fetch Live Sessions for quick presence mapping
    const resSessions = await authFetch('/api/admin/active-sessions');
    let liveSessionsMap = {};
    let totalLiveCount = 0;

    if (resSessions.ok) {
      const sessData = await resSessions.json();
      const sessions = sessData.sessions || [];
      totalLiveCount = sessions.length;

      sessions.forEach(s => {
        if (s.user_id) {
          liveSessionsMap[s.user_id] = s;
        } else if (s.email) {
          liveSessionsMap[s.email] = s;
        }
      });
    }

    // 2. Fetch Overview KPI Counts
    const resOverview = await authFetch('/api/admin/overview');
    if (resOverview.ok) {
      const ov = await resOverview.json();
      const liveCountEl = document.getElementById('adminLiveUsers');
      if (liveCountEl) liveCountEl.textContent = totalLiveCount;

      const badgeCountEl = document.getElementById('lblLiveSessionsCount');
      if (badgeCountEl) badgeCountEl.textContent = `${totalLiveCount} Live Online`;

      const usersEl = document.getElementById('adminTotalUsers');
      if (usersEl) usersEl.textContent = ov.total_users || 0;

      const docsEl = document.getElementById('adminTotalDocs');
      if (docsEl) docsEl.textContent = ov.total_documents || 0;
    }

    // 3. Render Card 1: Sales Team Members & Unified Live Status
    const resUsers = await authFetch('/api/admin/users');
    if (resUsers.ok) {
      const userData = await resUsers.json();
      const users = userData.users || [];
      const tbodyUsers = document.getElementById('adminUsersTableBody');

      if (tbodyUsers) {
        if (users.length === 0) {
          tbodyUsers.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px; color:#94a3b8;">No registered team members found.</td></tr>';
        } else {
          tbodyUsers.innerHTML = users.map(u => {
            const isProtectedAdmin = u.role === 'admin' || u.email === 'okashaxortlogix@gmail.com';
            const activeSession = liveSessionsMap[u.id] || liveSessionsMap[u.email];
            
            let statusPill = '<span style="color:#64748b; font-size:12px; font-weight:500;">⚪ Offline</span>';
            if (activeSession) {
              if (activeSession.is_meeting_active) {
                statusPill = `<span style="color:#38bdf8; font-size:12px; font-weight:700; background:rgba(56,189,248,0.12); border:1px solid rgba(56,189,248,0.3); padding:4px 10px; border-radius:14px; display:inline-flex; align-items:center; gap:6px;">
                  <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#38bdf8;box-shadow:0 0 8px #38bdf8;animation:pulse 1s infinite;"></span>🎙️ In Live Call
                </span>`;
              } else {
                statusPill = `<span style="color:#10b981; font-size:12px; font-weight:700; background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); padding:4px 10px; border-radius:14px; display:inline-flex; align-items:center; gap:6px;">
                  <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#10b981;box-shadow:0 0 8px #10b981;animation:pulse 1.5s infinite;"></span>🟢 Online Now
                </span>`;
              }
            } else if (u.is_online) {
              statusPill = `<span style="color:#10b981; font-size:12px; font-weight:700; background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); padding:4px 10px; border-radius:14px; display:inline-flex; align-items:center; gap:6px;">
                <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#10b981;box-shadow:0 0 8px #10b981;animation:pulse 1.5s infinite;"></span>🟢 Online Now
              </span>`;
            }

            const actionBtn = isProtectedAdmin
              ? '<span style="color:#64748b; font-size:11.5px; font-weight:600;"><i class="fa-solid fa-lock"></i> Protected</span>'
              : `<button type="button" class="btn-clean" onclick="deleteUserByAdmin(${u.id}, '${escapeHtml(u.full_name || u.email)}')" style="padding:4px 10px; font-size:11px; border-radius:6px; color:#f87171; border:1px solid rgba(239,68,68,0.35); background:rgba(239,68,68,0.12); cursor:pointer; font-weight:600;" onmouseover="this.style.background='rgba(239,68,68,0.25)'" onmouseout="this.style.background='rgba(239,68,68,0.12)'" title="Permanently Delete Sales Rep"><i class="fa-solid fa-trash-can"></i> Delete</button>`;

            return `
              <tr>
                <td style="padding:14px 18px;">
                  <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:32px; height:32px; border-radius:50%; background:rgba(56,189,248,0.15); color:#38bdf8; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; border:1px solid rgba(56,189,248,0.3);">
                      ${(u.full_name || u.email || 'U')[0].toUpperCase()}
                    </div>
                    <div>
                      <div style="font-weight:700; color:#f8fafc; font-size:13px;">${escapeHtml(u.full_name || 'Sales Rep')}</div>
                      <div style="color:#94a3b8; font-size:11px;">${escapeHtml(u.email || '')}</div>
                    </div>
                  </div>
                </td>
                <td style="padding:14px 18px;">
                  <span class="user-role-tag ${u.role === 'admin' ? 'admin' : 'user'}">
                    ${u.role === 'admin' ? '👑 Admin' : '👤 Sales Rep'}
                  </span>
                </td>
                <td style="padding:14px 18px;">${statusPill}</td>
                <td style="padding:14px 18px; color:#94a3b8; font-size:12px;">${(u.created_at || '').substring(0, 10)}</td>
                <td style="padding:14px 18px; text-align:right;">${actionBtn}</td>
              </tr>
            `;
          }).join('');
        }
      }
    }

    // 4. Render Card 2: Documents & Google Drive Links
    const resDocs = await authFetch('/api/admin/documents');
    if (resDocs.ok) {
      const docData = await resDocs.json();
      const docs = docData.documents || [];
      const tbody = document.getElementById('adminDocumentsTableBody');

      if (tbody) {
        if (docs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px; color:#94a3b8;">No client strategy documents uploaded yet.</td></tr>';
        } else {
          tbody.innerHTML = docs.map(d => `
            <tr>
              <td style="padding:14px 18px;">
                <div style="display:flex; align-items:center; gap:8px;">
                  <span style="font-size:16px;">📄</span>
                  <div>
                    <div style="font-weight:700; color:#f8fafc; font-size:13px;">${escapeHtml(d.filename || '')}</div>
                    <div style="color:#94a3b8; font-size:11px;">${(d.file_size / 1024).toFixed(1)} KB</div>
                  </div>
                </div>
              </td>
              <td style="padding:14px 18px;">
                <div style="font-weight:600; color:#cbd5e1; font-size:12.5px;">${escapeHtml(d.user_full_name || 'Sales Rep')}</div>
                <div style="color:#94a3b8; font-size:11px;">${escapeHtml(d.user_email || '')}</div>
              </td>
              <td style="padding:14px 18px;">
                <span style="color:#38bdf8; font-weight:700; font-size:12px; background:rgba(56,189,248,0.1); border:1px solid rgba(56,189,248,0.25); padding:3px 8px; border-radius:10px;">
                  ${d.chunks_count || 0} chunks
                </span>
              </td>
              <td style="padding:14px 18px; color:#94a3b8; font-size:12px;">${(d.uploaded_at || '').substring(0, 16).replace('T', ' ')}</td>
              <td style="padding:14px 18px; text-align:right;">
                <a href="${d.drive_web_view_link || '#'}" target="_blank" class="drive-link-btn" title="Open file in Google Drive" style="display:inline-flex; align-items:center; gap:6px; background:rgba(245,158,11,0.15); color:#fbbf24; border:1px solid rgba(245,158,11,0.35); text-decoration:none; padding:5px 12px; border-radius:6px; font-weight:600; font-size:11.5px;">
                  <i class="fa-brands fa-google-drive"></i> Open in Drive
                </a>
              </td>
            </tr>
          `).join('');
        }
      }
    }
  } catch (err) {
    console.error('Admin dashboard fetch error:', err);
  }
}

async function deleteUserByAdmin(userId, userName) {
  if (!confirm(`⚠️ Are you sure you want to permanently delete user "${userName}"?\n\nThis will also remove their custom documents and strategies.`)) {
    return;
  }
  try {
    const res = await authFetch(`/api/admin/users/${userId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`🗑️ User "${userName}" deleted successfully.`);
      loadAdminDashboardData();
    } else {
      showToast(data.detail || 'Failed to delete user.');
    }
  } catch (err) {
    showToast('Network error while deleting user: ' + err.message);
  }
}

function escapeHtml(text) {
  return (text || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Init on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initAuth();
  initTheme();
  initWebSocket();
  setupSpeechRecognition();
  setupEvents();
  setupPlaybookUpload();
  refreshPlaybookStatus();
});



