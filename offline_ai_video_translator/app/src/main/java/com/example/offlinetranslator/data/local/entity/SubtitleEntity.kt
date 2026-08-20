package com.example.offlinetranslator.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "subtitles",
    indices = [
        Index(value = ["mediaHash"]),
        Index(value = ["startTimeMs", "endTimeMs"])
    ]
)
data class SubtitleEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val mediaHash: String,
    val segmentIndex: Int,
    val startTimeMs: Long,
    val endTimeMs: Long,
    val originalText: String,
    val translatedText: String? = null,
    val confidence: Float = 1.0f
)
