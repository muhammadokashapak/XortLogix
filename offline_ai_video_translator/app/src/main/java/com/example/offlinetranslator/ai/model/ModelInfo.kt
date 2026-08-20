package com.example.offlinetranslator.ai.model

import java.io.File

data class ModelInfo(
    val id: String,
    val name: String,
    val type: ModelType,
    val sourceLang: String? = null,
    val targetLang: String? = null,
    val modelFile: File,
    val vocabFile: File? = null,
    val isInstalled: Boolean = false,
    val sizeBytes: Long = 0L,
    val description: String = ""
)
