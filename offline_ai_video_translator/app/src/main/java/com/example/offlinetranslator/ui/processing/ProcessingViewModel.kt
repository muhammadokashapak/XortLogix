package com.example.offlinetranslator.ui.processing

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.offlinetranslator.OfflineTranslatorApp
import com.example.offlinetranslator.data.model.MediaItem
import com.example.offlinetranslator.data.model.ProcessingState
import com.example.offlinetranslator.data.repository.MediaRepository
import com.example.offlinetranslator.domain.usecase.ProcessMediaUseCase
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class ProcessingViewModel(
    application: Application,
    private val mediaHash: String,
    private val sourceLang: String,
    private val targetLang: String
) : AndroidViewModel(application) {

    private val app = application as OfflineTranslatorApp
    private val mediaRepository: MediaRepository = app.mediaRepository
    private val processMediaUseCase: ProcessMediaUseCase = app.processMediaUseCase

    private val _mediaItem = MutableStateFlow<MediaItem?>(null)
    val mediaItem: StateFlow<MediaItem?> = _mediaItem.asStateFlow()

    private val _processingState = MutableStateFlow<ProcessingState>(ProcessingState.Idle)
    val processingState: StateFlow<ProcessingState> = _processingState.asStateFlow()

    private var processJob: Job? = null

    init {
        loadMediaAndStart()
    }

    private fun loadMediaAndStart() {
        viewModelScope.launch {
            val item = mediaRepository.getMediaByHash(mediaHash)
            _mediaItem.value = item
            if (item != null) {
                startProcessing(item)
            } else {
                _processingState.value = ProcessingState.Error("Media item not found in database.")
            }
        }
    }

    private fun startProcessing(item: MediaItem) {
        processJob?.cancel()
        processJob = viewModelScope.launch {
            processMediaUseCase.execute(
                mediaUri = item.uri,
                fileName = item.fileName,
                durationMs = item.durationMs,
                sizeBytes = item.sizeBytes,
                mimeType = item.mimeType,
                isVideo = item.isVideo,
                sourceLanguage = sourceLang,
                targetLanguage = targetLang
            ).collectLatest { state ->
                _processingState.value = state
            }
        }
    }

    fun cancelProcessing() {
        processJob?.cancel()
        processJob = null
        _processingState.value = ProcessingState.Cancelled
    }
}
