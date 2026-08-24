// ============================================================
// Sales Co-Pilot - Offscreen Document Audio Engine
// 1. Audio Passthrough: Unmutes tab audio to user's speakers/headphones
// 2. High-Reliability MediaRecorder: Streams standalone WebM audio slices to Groq Whisper
// ============================================================

let audioContext = null;
let mediaStream = null;
let mediaRecorder = null;
let analyserNode = null;
let recordCycleTimeout = null;
let isCapturing = false;
let speechDetectedInCurrentChunk = false;
let vadCheckInterval = null;

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'start_stt') {
    startAudioProcessing(message.streamId);
  } else if (message.type === 'stop_stt') {
    stopAudioProcessing();
  }
});

async function startAudioProcessing(streamId) {
  try {
    console.log('[Sales Co-Pilot] Starting audio capture for stream:', streamId);
    
    // 1. Capture Tab MediaStream
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        mandatory: {
          chromeMediaSource: 'tab',
          chromeMediaSourceId: streamId
        }
      },
      video: false
    });

    // 2. Setup AudioContext for speaker passthrough and VAD Analyser
    try {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const sourceNode = audioContext.createMediaStreamSource(mediaStream);
      
      // Passthrough to user headphones/speakers
      sourceNode.connect(audioContext.destination);

      // VAD Analyser to measure speech volume
      analyserNode = audioContext.createAnalyser();
      analyserNode.fftSize = 256;
      sourceNode.connect(analyserNode);

      if (audioContext.state === 'suspended') {
        await audioContext.resume();
      }
    } catch (e) {
      console.warn('[Sales Co-Pilot] Passthrough/Analyser warning:', e);
    }

    isCapturing = true;

    // Start VAD volume monitor
    startVADMonitoring();

    // 3. Start high-precision continuous MediaRecorder cycle
    startRecordingCycle();
    console.log('[Sales Co-Pilot] VAD-Enabled Audio streaming started.');

  } catch (error) {
    console.error('[Sales Co-Pilot] Error in startAudioProcessing:', error);
    chrome.runtime.sendMessage({
      type: 'capture_error',
      data: { error: error.message }
    }).catch(() => {});
  }
}

function startVADMonitoring() {
  if (vadCheckInterval) clearInterval(vadCheckInterval);
  const dataArray = new Uint8Array(128);

  vadCheckInterval = setInterval(() => {
    if (!isCapturing || !analyserNode) return;
    analyserNode.getByteFrequencyData(dataArray);

    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i];
    }
    const avg = sum / dataArray.length;

    // If audio level is above background threshold, mark as active speech
    if (avg > 5.0) {
      speechDetectedInCurrentChunk = true;
    }
  }, 100);
}

function startRecordingCycle() {
  if (!isCapturing || !mediaStream) return;

  speechDetectedInCurrentChunk = false;
  const audioChunks = [];

  try {
    mediaRecorder = new MediaRecorder(mediaStream, { mimeType: 'audio/webm;codecs=opus' });
  } catch (e) {
    try {
      mediaRecorder = new MediaRecorder(mediaStream);
    } catch (err) {
      console.error('[Sales Co-Pilot] Failed to create MediaRecorder:', err);
      return;
    }
  }

  mediaRecorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) {
      audioChunks.push(e.data);
    }
  };

  mediaRecorder.onstop = async () => {
    // ONLY send if voice/audio was actually detected (saves Groq API 429 rate limit!)
    if (audioChunks.length > 0 && isCapturing && speechDetectedInCurrentChunk) {
      try {
        const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
        if (blob.size > 1200) { // Valid speech chunk
          const arrayBuffer = await blob.arrayBuffer();
          const base64Audio = arrayBufferToBase64(arrayBuffer);
          chrome.runtime.sendMessage({
            type: 'audio_chunk',
            audio_base64: base64Audio,
            format: '.webm'
          }).catch(() => {});
        }
      } catch (err) {
        console.error('[Sales Co-Pilot] Error sending audio chunk:', err);
      }
    }

    // Continue next recording cycle seamlessly
    if (isCapturing) {
      startRecordingCycle();
    }
  };

  mediaRecorder.start();

  // 750ms high-speed slices for instantaneous sub-second speech detection
  recordCycleTimeout = setTimeout(() => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      try {
        mediaRecorder.stop();
      } catch (e) {}
    }
  }, 750);
}

function stopAudioProcessing() {
  isCapturing = false;

  if (recordCycleTimeout) {
    clearTimeout(recordCycleTimeout);
    recordCycleTimeout = null;
  }

  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    try {
      mediaRecorder.stop();
    } catch (e) {}
    mediaRecorder = null;
  }

  if (audioContext) {
    try {
      audioContext.close();
    } catch (e) {}
    audioContext = null;
  }

  if (mediaStream) {
    try {
      mediaStream.getTracks().forEach(track => track.stop());
    } catch (e) {}
    mediaStream = null;
  }

  console.log('[Sales Co-Pilot] Audio processing stopped.');
}

function arrayBufferToBase64(buffer) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

