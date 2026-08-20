package com.example.offlinetranslator.ai.translation

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import com.example.offlinetranslator.ai.model.ModelManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.nio.LongBuffer

class MarianOnnxTranslationEngine(
    private val context: Context,
    private val modelManager: ModelManager
) : TranslationEngine {

    private var ortEnvironment: OrtEnvironment? = null
    private var currentSession: OrtSession? = null
    private var currentPair: String? = null
    private var currentTokenizer: SimpleTokenizer? = null

    override fun isLanguagePairAvailable(sourceLanguage: String, targetLanguage: String): Boolean {
        if (sourceLanguage.equals(targetLanguage, ignoreCase = true)) return true
        return modelManager.isTranslationModelAvailable(sourceLanguage, targetLanguage)
    }

    @Synchronized
    private fun ensureSession(sourceLanguage: String, targetLanguage: String): Boolean {
        val pairKey = "${sourceLanguage.lowercase()}_${targetLanguage.lowercase()}"
        if (currentSession != null && currentPair == pairKey) {
            return true
        }

        val modelFile = modelManager.getTranslationModelFile(sourceLanguage, targetLanguage)
        val vocabFile = modelManager.getTranslationVocabFile(sourceLanguage, targetLanguage)

        if (modelFile == null || !modelFile.exists()) {
            return false
        }

        try {
            release()
            ortEnvironment = OrtEnvironment.getEnvironment()
            val opts = OrtSession.SessionOptions().apply {
                setIntraOpNumThreads(4)
                setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT)
            }
            currentSession = ortEnvironment?.createSession(modelFile.absolutePath, opts)
            currentTokenizer = SimpleTokenizer(vocabFile)
            currentPair = pairKey
            return true
        } catch (e: Exception) {
            e.printStackTrace()
            release()
            return false
        }
    }

    override suspend fun translate(
        text: String,
        sourceLanguage: String,
        targetLanguage: String
    ): String = withContext(Dispatchers.Default) {
        if (text.isBlank()) return@withContext ""
        if (sourceLanguage.equals(targetLanguage, ignoreCase = true)) {
            return@withContext text
        }

        if (!isLanguagePairAvailable(sourceLanguage, targetLanguage)) {
            throw IllegalStateException(
                "Offline translation model for $sourceLanguage -> $targetLanguage is not installed. Please install language pack in Settings."
            )
        }

        val ready = ensureSession(sourceLanguage, targetLanguage)
        if (!ready || currentSession == null || ortEnvironment == null) {
            throw IllegalStateException("Failed to initialize ONNX translation session for $sourceLanguage -> $targetLanguage.")
        }

        try {
            val env = ortEnvironment!!
            val session = currentSession!!
            val tokenizer = currentTokenizer ?: SimpleTokenizer(null)

            val inputIds = tokenizer.encode(text)
            val shape = longArrayOf(1, inputIds.size.toLong())
            val tensor = OnnxTensor.createTensor(env, LongBuffer.wrap(inputIds), shape)

            val inputMap = HashMap<String, OnnxTensor>()
            inputMap["input_ids"] = tensor

            if (session.inputNames.contains("attention_mask")) {
                val mask = LongArray(inputIds.size) { 1L }
                val maskTensor = OnnxTensor.createTensor(env, LongBuffer.wrap(mask), shape)
                inputMap["attention_mask"] = maskTensor
            }

            if (session.inputNames.contains("decoder_input_ids")) {
                // Seq2Seq autoregressive generation
                val decTokens = mutableListOf(0L) // Start with pad token
                for (step in 0 until 35) {
                    val decShape = longArrayOf(1, decTokens.size.toLong())
                    val decTensor = OnnxTensor.createTensor(env, LongBuffer.wrap(decTokens.toLongArray()), decShape)
                    inputMap["decoder_input_ids"] = decTensor

                    val stepResults = session.run(inputMap)
                    val logitsVal = stepResults[0].value as Array<*> // [1, seq_len, vocab_size]
                    val lastRow = (logitsVal[0] as Array<*>).last() as FloatArray

                    var bestTok = 0
                    var maxLogit = Float.NEGATIVE_INFINITY
                    for (v in lastRow.indices) {
                        if (lastRow[v] > maxLogit) {
                            maxLogit = lastRow[v]
                            bestTok = v
                        }
                    }

                    decTensor.close()
                    stepResults.close()

                    if (bestTok == 0 || bestTok == 1) { // EOS or PAD
                        break
                    }
                    decTokens.add(bestTok.toLong())
                }

                inputMap["input_ids"]?.close()
                inputMap["attention_mask"]?.close()

                val translated = tokenizer.decode(decTokens.toLongArray())
                return@withContext if (translated.isNotBlank()) translated else text
            } else {
                val results = session.run(inputMap)
                val outputVal = results[0].value
                tensor.close()
                inputMap["attention_mask"]?.close()
                results.close()

                val outputIds = extractTokenIds(outputVal)
                val translated = tokenizer.decode(outputIds)
                return@withContext if (translated.isNotBlank()) translated else text
            }
        } catch (e: Exception) {
            e.printStackTrace()
            return@withContext text
        }
    }


    override suspend fun translateBatch(
        texts: List<String>,
        sourceLanguage: String,
        targetLanguage: String,
        onProgress: ((Float, Int, Int) -> Unit)?
    ): List<String> = withContext(Dispatchers.Default) {
        if (texts.isEmpty()) return@withContext emptyList()
        if (sourceLanguage.equals(targetLanguage, ignoreCase = true)) return@withContext texts

        val results = mutableListOf<String>()
        val total = texts.size

        for ((index, item) in texts.withIndex()) {
            val translated = translate(item, sourceLanguage, targetLanguage)
            results.add(translated)
            val progress = (index + 1).toFloat() / total.toFloat()
            onProgress?.invoke(progress, index + 1, total)
        }

        results
    }

    private fun extractTokenIds(outputVal: Any?): LongArray {
        return when (outputVal) {
            is LongArray -> outputVal
            is Array<*> -> {
                val list = mutableListOf<Long>()
                for (elem in outputVal) {
                    if (elem is LongArray) list.addAll(elem.toList())
                    else if (elem is Long) list.add(elem)
                    else if (elem is IntArray) list.addAll(elem.map { it.toLong() })
                }
                list.toLongArray()
            }
            else -> LongArray(0)
        }
    }

    @Synchronized
    override fun release() {
        try {
            currentSession?.close()
            currentSession = null
            ortEnvironment?.close()
            ortEnvironment = null
            currentPair = null
            currentTokenizer = null
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}
