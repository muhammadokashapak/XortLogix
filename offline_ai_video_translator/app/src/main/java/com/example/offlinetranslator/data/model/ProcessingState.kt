package com.example.offlinetranslator.data.model

sealed class ProcessingState {
    data object Idle : ProcessingState()

    data class PreparingAudio(
        val progress: Float = 0f,
        val message: String = "Preparing and extracting audio stream..."
    ) : ProcessingState()

    data class DetectingSpeech(
        val progress: Float = 0f,
        val chunksDetected: Int = 0,
        val message: String = "Detecting voice activity (VAD)..."
    ) : ProcessingState()

    data class Transcribing(
        val progress: Float = 0f,
        val currentSegment: Int = 0,
        val totalSegments: Int = 0,
        val detectedLanguage: String? = null,
        val message: String = "Transcribing speech offline..."
    ) : ProcessingState()

    data class Translating(
        val progress: Float = 0f,
        val currentSegment: Int = 0,
        val totalSegments: Int = 0,
        val sourceLang: String,
        val targetLang: String,
        val message: String = "Translating text locally..."
    ) : ProcessingState()

    data class SyncingSubtitles(
        val progress: Float = 0.95f,
        val message: String = "Synchronizing subtitle timestamps..."
    ) : ProcessingState()

    data class Completed(
        val totalDurationMs: Long,
        val segmentsCount: Int,
        val mediaHash: String
    ) : ProcessingState()

    data class Error(
        val errorMessage: String,
        val isRecoverable: Boolean = true
    ) : ProcessingState()

    data object Cancelled : ProcessingState()
}
