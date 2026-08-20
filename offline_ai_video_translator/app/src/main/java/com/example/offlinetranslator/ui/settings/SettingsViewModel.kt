package com.example.offlinetranslator.ui.settings

import android.app.Application
import android.net.Uri
import android.widget.Toast
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.offlinetranslator.OfflineTranslatorApp
import com.example.offlinetranslator.ai.model.ModelInfo
import com.example.offlinetranslator.ai.model.ModelType
import com.example.offlinetranslator.data.model.SubtitleDisplayMode
import com.example.offlinetranslator.data.model.UserPreferences
import com.example.offlinetranslator.data.repository.SettingsRepository
import com.example.offlinetranslator.domain.usecase.ManageModelsUseCase
import com.example.offlinetranslator.utils.FileUtils
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class SettingsViewModel(application: Application) : AndroidViewModel(application) {

    private val app = application as OfflineTranslatorApp
    private val settingsRepository: SettingsRepository = app.settingsRepository
    private val manageModelsUseCase: ManageModelsUseCase = app.manageModelsUseCase

    val userPreferences: StateFlow<UserPreferences> = settingsRepository.userPreferences.stateIn(
        scope = viewModelScope,
        started = SharingStarted.Eagerly,
        initialValue = UserPreferences()
    )

    val installedModels: StateFlow<List<ModelInfo>> = manageModelsUseCase.installedModels

    init {
        refreshModels()
    }

    fun refreshModels() {
        viewModelScope.launch {
            manageModelsUseCase.refreshModels()
        }
    }

    fun updateTheme(theme: String) {
        viewModelScope.launch {
            settingsRepository.updateTheme(theme)
        }
    }

    fun updateSubtitleFontSize(sizeSp: Float) {
        viewModelScope.launch {
            settingsRepository.updateSubtitleFontSize(sizeSp)
        }
    }

    fun updateSubtitleDelay(delayMs: Long) {
        viewModelScope.launch {
            settingsRepository.updateSubtitleDelay(delayMs)
        }
    }

    fun updateHighContrast(enabled: Boolean) {
        viewModelScope.launch {
            settingsRepository.updateHighContrast(enabled)
        }
    }

    fun updateDefaultSubtitleMode(mode: SubtitleDisplayMode) {
        viewModelScope.launch {
            settingsRepository.updateSubtitleMode(mode)
        }
    }

    fun importModelFile(
        uri: Uri,
        modelType: ModelType,
        sourceLang: String? = null,
        targetLang: String? = null
    ) {
        viewModelScope.launch {
            val fileName = FileUtils.getFileNameFromUri(app, uri)
            val success = manageModelsUseCase.importModel(uri, fileName, modelType, sourceLang, targetLang)
            if (success) {
                Toast.makeText(app, "Model imported successfully: $fileName", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(app, "Failed to import model.", Toast.LENGTH_SHORT).show()
            }
        }
    }

    fun deleteModel(modelInfo: ModelInfo) {
        viewModelScope.launch {
            manageModelsUseCase.deleteModel(modelInfo)
            Toast.makeText(app, "Model removed.", Toast.LENGTH_SHORT).show()
        }
    }
}
