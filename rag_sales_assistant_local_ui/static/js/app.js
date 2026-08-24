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

// WebSocket Setup
function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  state.ws = new WebSocket(wsUrl);

  state.ws.onopen = () => {
    el.statusPill.textContent = '🟢 Online';
  };

  state.ws.onclose = () => {
    el.statusPill.textContent = '🔴 Reconnecting...';
    setTimeout(initWebSocket, 2000);
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

  el.stageBadgeText.textContent = 'Decoding client intent & mindset...';

  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
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

// Speech Recognition (Continuous Real-Time Listening)
function setupSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  state.recognition = new SpeechRecognition();
  state.recognition.continuous = true;
  state.recognition.interimResults = true;
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

    const text = (final || interim).trim();
    if (text) {
      el.liveTranscriptDisplay.textContent = `"${text}"`;
    }

    if (final.trim()) {
      sendQuery(final.trim());
    }
  };

  state.recognition.onerror = (event) => {
    console.log('SpeechRecognition event notice:', event.error);
    if (state.isListening && event.error !== 'not-allowed') {
      setTimeout(() => {
        if (state.isListening) {
          try { state.recognition.start(); } catch (e) {}
        }
      }, 100);
    }
  };

  state.recognition.onend = () => {
    if (state.isListening) {
      setTimeout(() => {
        if (state.isListening) {
          try { state.recognition.start(); } catch (e) {}
        }
      }, 50);
    }
  };
}

// ==========================================================================
// 🎙️ High-Fidelity Audio Stream Processor (16kHz PCM Streamer for Google Meet & Mic)
// ==========================================================================

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
  for (let i = 0; i < newLength; i++) {
    const index = i * ratio;
    const indexFloor = Math.floor(index);
    const indexCeil = Math.min(input.length - 1, Math.ceil(index));
    const t = index - indexFloor;
    const sample = (1 - t) * input[indexFloor] + t * input[indexCeil];
    const s = Math.max(-1, Math.min(1, sample));
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
    // CRITICAL: AudioContext MUST be resumed after user gesture
    if (audioCtx.state === 'suspended') {
      await audioCtx.resume();
    }
    console.log(`[AUDIO] AudioContext created. State: ${audioCtx.state}, SampleRate: ${audioCtx.sampleRate}`);

    const sampleRate = audioCtx.sampleRate;
    const processor = audioCtx.createScriptProcessor(4096, 1, 1);

    // CRITICAL FIX: gain=0.001 instead of 0.0
    // Chrome throttles/kills ScriptProcessor.onaudioprocess when it detects the
    // entire output path produces zero samples. gain=0.001 is inaudible but keeps
    // the audio graph alive and onaudioprocess firing.
    const gainNode = audioCtx.createGain();
    gainNode.gain.value = 0.001;

    // 1. Primary Audio Stream (Google Meet Tab or Mic)
    const primaryAudioTracks = primaryStream.getAudioTracks();
    console.log(`[AUDIO] Primary stream tracks: ${primaryAudioTracks.length}, enabled: ${primaryAudioTracks.map(t => t.enabled)}, readyState: ${primaryAudioTracks.map(t => t.readyState)}`);
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
        console.log(`[AUDIO] Secondary stream tracks: ${secTracks.length}`);
        const cleanSecondaryStream = new MediaStream(secTracks);
        source2 = audioCtx.createMediaStreamSource(cleanSecondaryStream);
        source2.connect(processor);
      } catch (e) {
        console.log('[AUDIO] Secondary audio source attach skipped:', e);
      }
    }

    let pcm16Chunks = [];
    let samplesAccumulated = 0;
    const targetSampleRate = 16000;
    const samplesNeeded = targetSampleRate * 2.0; // 2.0s clean window
    const overlapSamples = Math.round(targetSampleRate * 0.4); // 400ms overlap buffer
    let processCallCount = 0;
    let chunksSentCount = 0;

    processor.onaudioprocess = (e) => {
      if (!state.isListening && !state.isMeetingStreaming) return;

      processCallCount++;
      const inputBuffer = e.inputBuffer.getChannelData(0);
      const resampled = floatTo16BitPCM(inputBuffer, sampleRate, targetSampleRate);
      pcm16Chunks.push(resampled);
      samplesAccumulated += resampled.length;

      if (samplesAccumulated >= samplesNeeded) {
        const fullLength = pcm16Chunks.reduce((acc, c) => acc + c.length, 0);
        const fullPcm = new Int16Array(fullLength);
        let offset = 0;
        for (const chunk of pcm16Chunks) {
          fullPcm.set(chunk, offset);
          offset += chunk.length;
        }

        // Keep last 400ms for continuous phonetic overlap
        if (fullLength > overlapSamples) {
          const overlapPcm = fullPcm.slice(fullLength - overlapSamples);
          pcm16Chunks = [overlapPcm];
          samplesAccumulated = overlapPcm.length;
        } else {
          pcm16Chunks = [];
          samplesAccumulated = 0;
        }

        // Compute RMS energy
        let sumSquares = 0;
        for (let i = 0; i < fullPcm.length; i++) {
          sumSquares += (fullPcm[i] / 32768) ** 2;
        }
        const rms = Math.sqrt(sumSquares / fullPcm.length);

        // Only skip complete digital zero silence (RMS < 0.0008)
        if (rms >= 0.0008 && state.ws && state.ws.readyState === WebSocket.OPEN) {
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
          console.log(`[AUDIO] ⚡ PCM chunk #${chunksSentCount} sent | RMS: ${rms.toFixed(5)}`);
        }
      }
    };

    // Connect: source → processor → gainNode(0.001) → destination
    processor.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    console.log('[AUDIO] ScriptProcessor audio graph connected');

    state.audioCtx = audioCtx;
    state.audioProcessor = processor;
    state.audioSource = source1;
    state.audioSource2 = source2;

    console.log('[AUDIO] ✅ Audio pipeline fully initialized and streaming');
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

  el.btnMiniMic.addEventListener('click', () => {
    if (state.isMeetingStreaming || state.isListening) {
      stopMeetingAudioStream();
      stopListening();
    } else {
      openMeetingModal();
    }
  });

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
      el.cardSourceMic.classList.remove('active');
      el.cardSourceTab.querySelector('.source-radio').innerHTML = '<i class="fa-solid fa-circle-dot text-cyan"></i>';
      el.cardSourceMic.querySelector('.source-radio').innerHTML = '<i class="fa-regular fa-circle"></i>';
    });
  }

  if (el.cardSourceMic) {
    el.cardSourceMic.addEventListener('click', () => {
      state.audioSourceType = 'mic';
      el.cardSourceMic.classList.add('active');
      el.cardSourceTab.classList.remove('active');
      el.cardSourceMic.querySelector('.source-radio').innerHTML = '<i class="fa-solid fa-circle-dot text-cyan"></i>';
      el.cardSourceTab.querySelector('.source-radio').innerHTML = '<i class="fa-regular fa-circle"></i>';
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
        // If URL provided and not yet opened, give helpful notice
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

  // Auto-Popup Toggle
  el.chkAutoPopup.addEventListener('change', (e) => {
    state.autoPopup = e.target.checked;
    showToast(state.autoPopup ? 'Auto Strategy Popup Enabled' : 'Auto Strategy Popup Disabled');
  });

  // Auto-TTS Toggle
  el.chkAutoTts.addEventListener('change', (e) => {
    state.autoTts = e.target.checked;
    showToast(state.autoTts ? 'Auto Voice Cue in Ear Enabled 🎧' : 'Auto Voice Cue Disabled');
  });

  // Copy Buttons
  if (el.btnCopyPitch) {
    el.btnCopyPitch.addEventListener('click', () => {
      const text = el.displayPitchResponse ? el.displayPitchResponse.textContent.trim() : '';
      navigator.clipboard.writeText(text);
      if (el.btnCopyText) el.btnCopyText.textContent = 'Copied!';
      showToast('Pitch copied to clipboard');
      setTimeout(() => {
        if (el.btnCopyText) el.btnCopyText.textContent = 'Copy Pitch';
      }, 1800);
    });
  }

  if (el.btnPopupCopy) {
    el.btnPopupCopy.addEventListener('click', () => {
      const text = el.popupPitchText.textContent.trim();
      navigator.clipboard.writeText(text);
      showToast('Popup strategy copied!');
    });
  }

  if (el.btnMiniCopy) {
    el.btnMiniCopy.addEventListener('click', () => {
      const text = el.hudPitch.textContent.trim();
      navigator.clipboard.writeText(text);
      showToast('HUD strategy copied!');
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
      speakText(el.popupPitchText.textContent.trim());
    });
  }

  // Close Popup
  if (el.btnClosePopup) {
    el.btnClosePopup.addEventListener('click', () => {
      el.smartStrategyPopup.style.display = 'none';
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
  el.btnToggleHud.addEventListener('click', () => {
    const isShown = el.miniHudWidget.style.display === 'block';
    el.miniHudWidget.style.display = isShown ? 'none' : 'block';
    showToast(isShown ? 'Zoom HUD closed' : 'Zoom HUD opened');
  });

  el.btnCloseMiniHud.addEventListener('click', () => {
    el.miniHudWidget.style.display = 'none';
  });

  el.miniHudOpacity.addEventListener('input', (e) => {
    el.miniHudWidget.style.opacity = e.target.value / 100;
  });

  // Knowledge Base Modal
  el.btnOpenKB.addEventListener('click', () => {
    el.kbModal.style.display = 'flex';
    loadKnowledgeBase();
  });

  el.btnCloseKBModal.addEventListener('click', () => {
    el.kbModal.style.display = 'none';
  });

  el.kbSearchInput.addEventListener('input', (e) => {
    loadKnowledgeBase(e.target.value);
  });

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

  // Close Intent Modal
  if (el.btnCloseIntentModal) {
    el.btnCloseIntentModal.addEventListener('click', () => {
      if (el.intentStrategyModal) el.intentStrategyModal.style.display = 'none';
    });
  }

  // Backdrop click to close Intent Modal
  if (el.intentStrategyModal) {
    el.intentStrategyModal.addEventListener('click', (e) => {
      if (e.target === el.intentStrategyModal) {
        el.intentStrategyModal.style.display = 'none';
      }
    });
  }

  // Copy from Intent Modal
  if (el.btnModalCopy) {
    el.btnModalCopy.addEventListener('click', () => {
      const pitch = el.modalPitchText.textContent.trim();
      navigator.clipboard.writeText(pitch);
      if (el.btnModalCopyText) el.btnModalCopyText.textContent = 'Copied!';
      showToast('Strategy pitch copied to clipboard!');
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
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = '#38bdf8';
      dropZone.style.background = 'rgba(56, 189, 248, 0.1)';
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.style.borderColor = 'rgba(56, 189, 248, 0.4)';
      dropZone.style.background = 'rgba(15, 23, 42, 0.3)';
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = 'rgba(56, 189, 248, 0.4)';
      dropZone.style.background = 'rgba(15, 23, 42, 0.3)';
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelect(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelect(e.target.files[0]);
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

// Init on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initWebSocket();
  setupSpeechRecognition();
  setupEvents();
  setupPlaybookUpload();
  refreshPlaybookStatus();
});


