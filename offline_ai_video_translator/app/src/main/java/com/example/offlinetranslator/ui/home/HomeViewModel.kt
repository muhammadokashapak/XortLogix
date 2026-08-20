package com.example.offlinetranslator.ui.home

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.offlinetranslator.OfflineTranslatorApp
import com.example.offlinetranslator.ai.model.ModelManager
import com.example.offlinetranslator.data.model.MediaItem
import com.example.offlinetranslator.data.repository.MediaRepository
import com.example.offlinetranslator.utils.FileUtils
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class HomeViewModel(application: Application) : AndroidViewModel(application) {

    private val app = application as OfflineTranslatorApp
    private val mediaRepository: MediaRepository = app.mediaRepository
    private val modelManager: ModelManager = app.modelManager

    val recentMedia: StateFlow<List<MediaItem>> = mediaRepository.allMedia.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = emptyList()
    )

    private val _isOfflineSpeechReady = MutableStateFlow(false)
    val isOfflineSpeechReady: StateFlow<Boolean> = _isOfflineSpeechReady.asStateFlow()

    init {
        checkOfflineReadiness()
    }

    fun checkOfflineReadiness() {
        viewModelScope.launch {
            modelManager.refreshInstalledModels()
            _isOfflineSpeechReady.value = modelManager.isSpeechModelAvailable()
        }
    }

    fun onMediaSelected(uri: Uri, isVideo: Boolean, onNavigateToPlayer: (String) -> Unit) {
        viewModelScope.launch {
            val fileName = FileUtils.getFileNameFromUri(app, uri)
            val media = mediaRepository.saveOrUpdateMedia(
                uri = uri,
                fileName = fileName,
                durationMs = 0L,
                sizeBytes = 0L,
                mimeType = if (isVideo) "video/*" else "audio/*",
                isVideo = isVideo
            )
            onNavigateToPlayer(media.mediaHash)
        }
    }
}
