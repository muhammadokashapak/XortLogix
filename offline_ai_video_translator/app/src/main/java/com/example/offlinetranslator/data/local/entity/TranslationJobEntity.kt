package com.example.offlinetranslator.data.local.entity

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "translation_jobs",
    foreignKeys = [
        ForeignKey(
            entity = MediaEntity::class,
            parentColumns = ["id"],
            childColumns = ["mediaId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index(value = ["mediaId"]), Index(value = ["mediaHash"])]
)
data class TranslationJobEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val mediaId: Long,
    val mediaHash: String,
    val sourceLanguage: String,
    val targetLanguage: String,
    val status: String, // COMPLETED, FAILED, IN_PROGRESS
    val totalSegments: Int = 0,
    val processingTimeMs: Long = 0L,
    val createdAt: Long = System.currentTimeMillis()
)
