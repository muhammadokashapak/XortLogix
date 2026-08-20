package com.example.offlinetranslator.ui.history

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.offlinetranslator.OfflineTranslatorApp
import com.example.offlinetranslator.data.model.MediaItem
import com.example.offlinetranslator.data.repository.MediaRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class HistoryViewModel(application: Application) : AndroidViewModel(application) {

    private val app = application as OfflineTranslatorApp
    private val mediaRepository: MediaRepository = app.mediaRepository

    val historyItems: StateFlow<List<MediaItem>> = mediaRepository.translatedMedia.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = emptyList()
    )

    fun deleteHistoryItem(mediaHash: String) {
        viewModelScope.launch {
            mediaRepository.deleteMedia(mediaHash)
        }
    }
}
