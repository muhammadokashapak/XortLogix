package com.example.offlinetranslator.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "media_items",
    indices = [Index(value = ["mediaHash"], unique = true)]
)
data class MediaEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val uriString: String,
    val fileName: String,
    val durationMs: Long,
    val sizeBytes: Long,
    val mimeType: String?,
    val isVideo: Boolean,
    val mediaHash: String,
    val lastPlayedPositionMs: Long = 0L,
    val hasTranslation: Boolean = false,
    val detectedLanguage: String? = null,
    val targetLanguage: String? = null,
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
)
