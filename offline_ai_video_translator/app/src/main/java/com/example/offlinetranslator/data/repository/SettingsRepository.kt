package com.example.offlinetranslator.data.repository

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.example.offlinetranslator.data.model.SubtitleDisplayMode
import com.example.offlinetranslator.data.model.UserPreferences
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "user_settings")

class SettingsRepository(private val context: Context) {

    private val KEY_THEME = stringPreferencesKey("theme_mode")
    private val KEY_SOURCE_LANG = stringPreferencesKey("source_lang")
    private val KEY_TARGET_LANG = stringPreferencesKey("target_lang")
    private val KEY_SUBTITLE_MODE = stringPreferencesKey("subtitle_mode")
    private val KEY_FONT_SIZE = floatPreferencesKey("font_size")
    private val KEY_SUBTITLE_DELAY = longPreferencesKey("subtitle_delay")
    private val KEY_PLAYBACK_SPEED = floatPreferencesKey("playback_speed")
    private val KEY_HIGH_CONTRAST = booleanPreferencesKey("high_contrast")

    val userPreferences: Flow<UserPreferences> = context.dataStore.data.map { prefs ->
        UserPreferences(
            themeMode = prefs[KEY_THEME] ?: "SYSTEM",
            defaultSourceLanguage = prefs[KEY_SOURCE_LANG] ?: "auto",
            defaultTargetLanguage = prefs[KEY_TARGET_LANG] ?: "ur",
            defaultSubtitleMode = try {
                SubtitleDisplayMode.valueOf(prefs[KEY_SUBTITLE_MODE] ?: SubtitleDisplayMode.BOTH.name)
            } catch (_: Exception) {
                SubtitleDisplayMode.BOTH
            },
            subtitleFontSizeSp = prefs[KEY_FONT_SIZE] ?: 18f,
            subtitleDelayMs = prefs[KEY_SUBTITLE_DELAY] ?: 0L,
            defaultPlaybackSpeed = prefs[KEY_PLAYBACK_SPEED] ?: 1.0f,
            highContrastBackground = prefs[KEY_HIGH_CONTRAST] ?: true
        )
    }

    suspend fun updateTheme(mode: String) {
        context.dataStore.edit { it[KEY_THEME] = mode }
    }

    suspend fun updateLanguages(source: String, target: String) {
        context.dataStore.edit {
            it[KEY_SOURCE_LANG] = source
            it[KEY_TARGET_LANG] = target
        }
    }

    suspend fun updateSubtitleMode(mode: SubtitleDisplayMode) {
        context.dataStore.edit { it[KEY_SUBTITLE_MODE] = mode.name }
    }

    suspend fun updateSubtitleFontSize(sizeSp: Float) {
        context.dataStore.edit { it[KEY_FONT_SIZE] = sizeSp }
    }

    suspend fun updateSubtitleDelay(delayMs: Long) {
        context.dataStore.edit { it[KEY_SUBTITLE_DELAY] = delayMs }
    }

    suspend fun updatePlaybackSpeed(speed: Float) {
        context.dataStore.edit { it[KEY_PLAYBACK_SPEED] = speed }
    }

    suspend fun updateHighContrast(enabled: Boolean) {
        context.dataStore.edit { it[KEY_HIGH_CONTRAST] = enabled }
    }
}
