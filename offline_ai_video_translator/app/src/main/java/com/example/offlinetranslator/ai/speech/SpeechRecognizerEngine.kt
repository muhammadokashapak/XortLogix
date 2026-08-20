package com.example.offlinetranslator.ai.speech

import com.example.offlinetranslator.data.model.TranscriptSegment

interface SpeechRecognizerEngine {
    /**
     * Transcribes raw 16kHz mono PCM audio samples into timestamped transcript segments.
     * @param audioSamples FloatArray of normalized 16kHz mono audio samples (-1.0 to 1.0)
     * @param sourceLanguage Optional source language code ("en", "auto", etc.)
     * @param onProgress Callback invoked during chunk transcription (progress between 0.0 and 1.0)
     * @return List of timestamped TranscriptSegment
     */
    suspend fun transcribe(
        audioSamples: FloatArray,
        sampleRate: Int = 16000,
        sourceLanguage: String? = null,
        onProgress: ((Float, Int, Int) -> Unit)? = null
    ): List<TranscriptSegment>

    /**
     * Checks if the underlying model is loaded and ready.
     */
    fun isReady(): Boolean

    /**
     * Releases ONNX sessions and memory resources.
     */
    fun release()
}
