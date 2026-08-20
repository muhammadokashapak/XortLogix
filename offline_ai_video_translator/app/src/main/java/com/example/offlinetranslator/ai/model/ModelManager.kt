package com.example.offlinetranslator.ai.model

import android.content.Context
import android.net.Uri
import com.example.offlinetranslator.utils.FileUtils
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream

interface ModelManager {
    val installedModels: StateFlow<List<ModelInfo>>
    fun isSpeechModelAvailable(): Boolean
    fun isTranslationModelAvailable(source: String, target: String): Boolean
    fun getSpeechModelFile(): File?
    fun getTranslationModelFile(source: String, target: String): File?
    fun getTranslationVocabFile(source: String, target: String): File?
    suspend fun refreshInstalledModels()
    suspend fun importModel(sourceUri: Uri, targetFileName: String, modelType: ModelType, sourceLang: String? = null, targetLang: String? = null): Boolean
    suspend fun deleteModel(modelInfo: ModelInfo): Boolean
}

class AppModelManager(private val context: Context) : ModelManager {

    private val baseModelsDir = File(context.filesDir, "models")
    private val speechModelsDir = File(baseModelsDir, "speech")
    private val translationModelsDir = File(baseModelsDir, "translation")

    private val _installedModels = MutableStateFlow<List<ModelInfo>>(emptyList())
    override val installedModels: StateFlow<List<ModelInfo>> = _installedModels.asStateFlow()

    init {
        speechModelsDir.mkdirs()
        translationModelsDir.mkdirs()
        extractBundledAssetsIfNeeded()
    }

    private fun extractBundledAssetsIfNeeded() {
        try {
            val rootAssets = context.assets.list("models") ?: return
            if (rootAssets.isNotEmpty()) {
                copyAssetDirectory("models", baseModelsDir)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun copyAssetDirectory(assetDir: String, targetDir: File) {
        val items = context.assets.list(assetDir) ?: return
        targetDir.mkdirs()
        for (item in items) {
            val assetPath = "$assetDir/$item"
            val targetFile = File(targetDir, item)
            val subItems = context.assets.list(assetPath)
            if (subItems.isNullOrEmpty()) {
                // It's a file
                if (!targetFile.exists() || targetFile.length() == 0L) {
                    try {
                        context.assets.open(assetPath).use { input ->
                            FileOutputStream(targetFile).use { output ->
                                input.copyTo(output)
                            }
                        }
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }
                }
            } else {
                // It's a subdirectory
                copyAssetDirectory(assetPath, targetFile)
            }
        }
    }

    override fun isSpeechModelAvailable(): Boolean {
        return getSpeechModelFile()?.exists() == true
    }

    override fun isTranslationModelAvailable(source: String, target: String): Boolean {
        return getTranslationModelFile(source, target)?.exists() == true
    }

    override fun getSpeechModelFile(): File? {
        val candidates = listOf(
            File(speechModelsDir, "whisper_encoder_quant.onnx"),
            File(speechModelsDir, "whisper_tiny_quant.onnx"),
            File(speechModelsDir, "whisper_tiny.onnx"),
            File(speechModelsDir, "whisper_base_quant.onnx"),
            File(speechModelsDir, "whisper_base.onnx"),
            File(speechModelsDir, "speech_model.onnx")
        )
        return candidates.firstOrNull { it.exists() && it.length() > 0 }
    }


    override fun getTranslationModelFile(source: String, target: String): File? {
        val s = source.lowercase().trim()
        val t = target.lowercase().trim()
        val pairDir = File(translationModelsDir, "${s}_${t}")
        val candidates = listOf(
            File(pairDir, "model.onnx"),
            File(pairDir, "opus_mt_${s}_${t}.onnx"),
            File(translationModelsDir, "opus_mt_${s}_${t}.onnx"),
            File(translationModelsDir, "${s}_${t}.onnx")
        )
        return candidates.firstOrNull { it.exists() && it.length() > 0 }
    }

    override fun getTranslationVocabFile(source: String, target: String): File? {
        val s = source.lowercase().trim()
        val t = target.lowercase().trim()
        val pairDir = File(translationModelsDir, "${s}_${t}")
        val candidates = listOf(
            File(pairDir, "source.spm"),
            File(pairDir, "vocab.json"),
            File(pairDir, "target.spm"),
            File(translationModelsDir, "${s}_${t}_vocab.json")
        )
        return candidates.firstOrNull { it.exists() && it.length() > 0 }
    }

    override suspend fun refreshInstalledModels() = withContext(Dispatchers.IO) {
        val models = mutableListOf<ModelInfo>()

        // Check speech models
        val speechFile = getSpeechModelFile()
        models.add(
            ModelInfo(
                id = "speech_whisper",
                name = "Whisper On-Device STT",
                type = ModelType.SPEECH_RECOGNITION,
                modelFile = speechFile ?: File(speechModelsDir, "whisper_tiny_quant.onnx"),
                isInstalled = speechFile?.exists() == true,
                sizeBytes = speechFile?.length() ?: 0L,
                description = "Quantized Whisper ONNX model for offline speech-to-text recognition."
            )
        )

        // Supported translation language pairs
        val pairs = listOf(
            Pair("en", "ur") to "English → Urdu (MarianMT)",
            Pair("en", "es") to "English → Spanish (MarianMT)",
            Pair("en", "ar") to "English → Arabic (MarianMT)",
            Pair("en", "fr") to "English → French (MarianMT)",
            Pair("en", "de") to "English → German (MarianMT)",
            Pair("en", "hi") to "English → Hindi (MarianMT)",
            Pair("en", "zh") to "English → Chinese (MarianMT)",
            Pair("en", "ru") to "English → Russian (MarianMT)",
            Pair("en", "tr") to "English → Turkish (MarianMT)"
        )

        for ((pair, label) in pairs) {
            val (src, tgt) = pair
            val modelFile = getTranslationModelFile(src, tgt) ?: File(File(translationModelsDir, "${src}_${tgt}"), "model.onnx")
            val vocabFile = getTranslationVocabFile(src, tgt)
            val installed = modelFile.exists() && modelFile.length() > 0
            models.add(
                ModelInfo(
                    id = "trans_${src}_${tgt}",
                    name = label,
                    type = ModelType.TRANSLATION,
                    sourceLang = src,
                    targetLang = tgt,
                    modelFile = modelFile,
                    vocabFile = vocabFile,
                    isInstalled = installed,
                    sizeBytes = if (installed) modelFile.length() else 0L,
                    description = "Offline neural machine translation pack for $src to $tgt."
                )
            )
        }

        _installedModels.value = models
    }

    override suspend fun importModel(
        sourceUri: Uri,
        targetFileName: String,
        modelType: ModelType,
        sourceLang: String?,
        targetLang: String?
    ): Boolean = withContext(Dispatchers.IO) {
        try {
            val destDir = when (modelType) {
                ModelType.SPEECH_RECOGNITION -> speechModelsDir
                ModelType.TRANSLATION -> {
                    if (!sourceLang.isNullOrEmpty() && !targetLang.isNullOrEmpty()) {
                        val dir = File(translationModelsDir, "${sourceLang.lowercase()}_${targetLang.lowercase()}")
                        dir.mkdirs()
                        dir
                    } else {
                        translationModelsDir
                    }
                }
            }
            destDir.mkdirs()

            val destFile = File(destDir, targetFileName)
            context.contentResolver.openInputStream(sourceUri)?.use { input ->
                FileOutputStream(destFile).use { output ->
                    input.copyTo(output)
                }
            }
            refreshInstalledModels()
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    override suspend fun deleteModel(modelInfo: ModelInfo): Boolean = withContext(Dispatchers.IO) {
        try {
            if (modelInfo.modelFile.exists()) {
                modelInfo.modelFile.delete()
            }
            modelInfo.vocabFile?.let {
                if (it.exists()) it.delete()
            }
            refreshInstalledModels()
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
}
