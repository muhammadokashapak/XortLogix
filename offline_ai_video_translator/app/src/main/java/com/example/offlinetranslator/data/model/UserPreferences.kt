package com.example.offlinetranslator.data.model

data class UserPreferences(
    val themeMode: String = "SYSTEM", // SYSTEM, DARK, LIGHT
    val defaultSourceLanguage: String = "auto",
    val defaultTargetLanguage: String = "ur", // Urdu default, or es, ar, fr, etc.
    val defaultSubtitleMode: SubtitleDisplayMode = SubtitleDisplayMode.BOTH,
    val subtitleFontSizeSp: Float = 18f,
    val subtitleDelayMs: Long = 0L,
    val defaultPlaybackSpeed: Float = 1.0f,
    val highContrastBackground: Boolean = true
)
