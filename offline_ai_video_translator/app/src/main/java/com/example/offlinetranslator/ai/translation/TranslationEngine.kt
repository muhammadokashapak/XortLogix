package com.example.offlinetranslator.ai.translation

interface TranslationEngine {
    /**
     * Translates input text from source language to target language offline.
     */
    suspend fun translate(
        text: String,
        sourceLanguage: String,
        targetLanguage: String
    ): String

    /**
     * Batch translates a list of text segments offline.
     */
    suspend fun translateBatch(
        texts: List<String>,
        sourceLanguage: String,
        targetLanguage: String,
        onProgress: ((Float, Int, Int) -> Unit)? = null
    ): List<String>

    /**
     * Checks if the language pair model is installed and available offline.
     */
    fun isLanguagePairAvailable(sourceLanguage: String, targetLanguage: String): Boolean

    /**
     * Releases ONNX translation sessions from memory.
     */
    fun release()
}
