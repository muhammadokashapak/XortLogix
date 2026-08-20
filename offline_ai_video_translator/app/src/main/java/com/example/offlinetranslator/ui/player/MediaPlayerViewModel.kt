package com.example.offlinetranslator.ui.player

import android.app.Application
import android.content.Context
import android.os.Environment
import android.widget.Toast
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.offlinetranslator.OfflineTranslatorApp
import com.example.offlinetranslator.data.model.MediaItem
import com.example.offlinetranslator.data.model.SubtitleDisplayMode
import com.example.offlinetranslator.data.model.TranscriptSegment
import com.example.offlinetranslator.data.repository.MediaRepository
import com.example.offlinetranslator.data.repository.SettingsRepository
import com.example.offlinetranslator.data.repository.TranslationRepository
import com.example.offlinetranslator.domain.usecase.ManageModelsUseCase
import com.example.offlinetranslator.player.SubtitleSynchronizer
import com.example.offlinetranslator.player.VideoPlayerController
import com.example.offlinetranslator.subtitle.SrtExporter
import com.example.offlinetranslator.subtitle.VttExporter
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.io.File
import java.io.FileOutputStream

class MediaPlayerViewModel(
    application: Application,
    private val mediaHash: String
) : AndroidViewModel(application) {

    private val app = application as OfflineTranslatorApp
    private val mediaRepository: MediaRepository = app.mediaRepository
    private val translationRepository: TranslationRepository = app.translationRepository
    private val settingsRepository: SettingsRepository = app.settingsRepository
    private val manageModelsUseCase: ManageModelsUseCase = app.manageModelsUseCase

    val playerController = VideoPlayerController(application, viewModelScope)
    val subtitleSynchronizer = SubtitleSynchronizer()

    private val _mediaItem = MutableStateFlow<MediaItem?>(null)
    val mediaItem: StateFlow<MediaItem?> = _mediaItem.asStateFlow()

    private val _subtitles = MutableStateFlow<List<TranscriptSegment>>(emptyList())
    val subtitles: StateFlow<List<TranscriptSegment>> = _subtitles.asStateFlow()

    val activeSegment: StateFlow<TranscriptSegment?> = subtitleSynchronizer.currentActiveSegment

    private val _subtitleMode = MutableStateFlow(SubtitleDisplayMode.BOTH)
    val subtitleMode: StateFlow<SubtitleDisplayMode> = _subtitleMode.asStateFlow()

    private val _sourceLang = MutableStateFlow("auto")
    val sourceLang: StateFlow<String> = _sourceLang.asStateFlow()

    private val _targetLang = MutableStateFlow("ur")
    val targetLang: StateFlow<String> = _targetLang.asStateFlow()

    private val _isModelAvailable = MutableStateFlow(true)
    val isModelAvailable: StateFlow<Boolean> = _isModelAvailable.asStateFlow()

    private val _isLiveTranslating = MutableStateFlow(false)
    val isLiveTranslating: StateFlow<Boolean> = _isLiveTranslating.asStateFlow()

    private val _liveTranslationMessage = MutableStateFlow("")
    val liveTranslationMessage: StateFlow<String> = _liveTranslationMessage.asStateFlow()

    val userPreferences = settingsRepository.userPreferences.stateIn(
        scope = viewModelScope,
        started = SharingStarted.Eagerly,
        initialValue = com.example.offlinetranslator.data.model.UserPreferences()
    )

    init {
        loadMedia()
        loadSubtitles()
        observePlayback()
    }

    private fun loadMedia() {
        viewModelScope.launch {
            val item = mediaRepository.getMediaByHash(mediaHash)
            _mediaItem.value = item
            if (item != null) {
                _sourceLang.value = item.detectedLanguage ?: "auto"
                _targetLang.value = item.targetLanguage ?: "ur"
                playerController.prepareMedia(item.uri, item.lastPlayedPositionMs)
                checkModelAvailability()

                // Check if subtitles already exist, otherwise auto-start live streaming in background
                val existing = translationRepository.getSubtitlesList(mediaHash)
                if (existing.isEmpty()) {
                    startLiveTranslation(_sourceLang.value, _targetLang.value)
                }

            }
        }
    }

    private fun loadSubtitles() {
        viewModelScope.launch {
            translationRepository.getSubtitlesFlow(mediaHash).collectLatest { segments ->
                _subtitles.value = segments
                subtitleSynchronizer.setSubtitles(segments)
            }
        }
    }

    fun startLiveTranslation(source: String? = null, target: String? = null) {
        val item = _mediaItem.value ?: return
        val src = source ?: _sourceLang.value
        val tgt = target ?: _targetLang.value

        viewModelScope.launch {
            _isLiveTranslating.value = true
            _liveTranslationMessage.value = "AI listening & generating live subtitles..."

            app.processMediaUseCase.execute(
                mediaUri = item.uri,
                fileName = item.fileName,
                durationMs = item.durationMs,
                sizeBytes = item.sizeBytes,
                mimeType = item.mimeType,
                isVideo = item.isVideo,
                sourceLanguage = src,
                targetLanguage = tgt
            ).collectLatest { state ->
                when (state) {
                    is com.example.offlinetranslator.data.model.ProcessingState.PreparingAudio -> {
                        _liveTranslationMessage.value = "Extracting audio for AI..."
                    }
                    is com.example.offlinetranslator.data.model.ProcessingState.Transcribing -> {
                        _liveTranslationMessage.value = "Transcribing speech on-device..."
                    }
                    is com.example.offlinetranslator.data.model.ProcessingState.Translating -> {
                        _liveTranslationMessage.value = "Translating speech to ${tgt.uppercase()}..."
                    }
                    is com.example.offlinetranslator.data.model.ProcessingState.Completed -> {
                        _isLiveTranslating.value = false
                        _liveTranslationMessage.value = "Live subtitles synced"
                    }
                    is com.example.offlinetranslator.data.model.ProcessingState.Error -> {
                        _isLiveTranslating.value = false
                        _liveTranslationMessage.value = ""
                    }
                    else -> {}
                }
            }
        }
    }

    private fun observePlayback() {
        viewModelScope.launch {
            playerController.currentPosition.collectLatest { pos ->
                subtitleSynchronizer.updatePlaybackPosition(pos)
                if (pos > 0 && pos % 5000 < 200) {
                    mediaRepository.updatePlaybackPosition(mediaHash, pos)
                }
            }
        }
    }

    fun setSubtitleMode(mode: SubtitleDisplayMode) {
        _subtitleMode.value = mode
    }

    fun setLanguages(source: String, target: String) {
        _sourceLang.value = source
        _targetLang.value = target
        checkModelAvailability()
    }

    fun checkModelAvailability() {
        _isModelAvailable.value = manageModelsUseCase.isReadyForTranslation(_sourceLang.value, _targetLang.value)
    }

    fun exportSubtitles(asVtt: Boolean) {
        viewModelScope.launch {
            val segs = _subtitles.value
            if (segs.isEmpty()) {
                Toast.makeText(app, "No subtitles available to export.", Toast.LENGTH_SHORT).show()
                return@launch
            }

            val fileName = _mediaItem.value?.fileName?.substringBeforeLast(".") ?: "subtitles"
            val ext = if (asVtt) "vtt" else "srt"
            val content = if (asVtt) SrtExporter.exportToSrt(segs) else VttExporter.exportToVtt(segs)

            try {
                val downloadsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
                val targetFile = File(downloadsDir, "${fileName}_translated.$ext")
                FileOutputStream(targetFile).use { it.write(content.toByteArray()) }
                Toast.makeText(app, "Exported: ${targetFile.name}", Toast.LENGTH_LONG).show()
            } catch (e: Exception) {
                Toast.makeText(app, "Export failed: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        playerController.release()
        subtitleSynchronizer.clear()
    }
}

