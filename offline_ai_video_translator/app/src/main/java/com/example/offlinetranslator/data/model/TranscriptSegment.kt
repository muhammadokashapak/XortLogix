package com.example.offlinetranslator.data.model

data class TranscriptSegment(
    val id: Long = 0,
    val mediaHash: String = "",
    val segmentIndex: Int = 0,
    val startTimeMs: Long,
    val endTimeMs: Long,
    val originalText: String,
    val translatedText: String? = null,
    val confidence: Float = 1.0f
)
