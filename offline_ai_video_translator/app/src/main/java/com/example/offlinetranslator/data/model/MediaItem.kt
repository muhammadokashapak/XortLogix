package com.example.offlinetranslator.data.model

import android.net.Uri

data class MediaItem(
    val id: Long = 0,
    val uri: Uri,
    val fileName: String,
    val durationMs: Long = 0L,
    val sizeBytes: Long = 0L,
    val mimeType: String? = null,
    val isVideo: Boolean = true,
    val mediaHash: String = "",
    val lastPlayedPositionMs: Long = 0L,
    val hasTranslation: Boolean = false,
    val detectedLanguage: String? = null,
    val targetLanguage: String? = null,
    val createdAt: Long = System.currentTimeMillis()
)
