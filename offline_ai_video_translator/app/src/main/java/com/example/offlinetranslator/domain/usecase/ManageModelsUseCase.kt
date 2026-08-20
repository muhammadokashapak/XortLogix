package com.example.offlinetranslator.domain.usecase

import android.net.Uri
import com.example.offlinetranslator.ai.model.ModelInfo
import com.example.offlinetranslator.ai.model.ModelManager
import com.example.offlinetranslator.ai.model.ModelType
import kotlinx.coroutines.flow.StateFlow

class ManageModelsUseCase(
    private val modelManager: ModelManager
) {
    val installedModels: StateFlow<List<ModelInfo>> = modelManager.installedModels

    suspend fun refreshModels() {
        modelManager.refreshInstalledModels()
    }

    suspend fun importModel(
        uri: Uri,
        fileName: String,
        type: ModelType,
        sourceLang: String? = null,
        targetLang: String? = null
    ): Boolean {
        return modelManager.importModel(uri, fileName, type, sourceLang, targetLang)
    }

    suspend fun deleteModel(modelInfo: ModelInfo): Boolean {
        return modelManager.deleteModel(modelInfo)
    }

    fun isReadyForTranslation(sourceLang: String, targetLang: String): Boolean {
        val speechReady = modelManager.isSpeechModelAvailable()
        val transReady = if (sourceLang.equals(targetLang, ignoreCase = true)) true else modelManager.isTranslationModelAvailable(sourceLang, targetLang)
        return speechReady && transReady
    }
}
