package com.example.offlinetranslator.ai.speech

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import com.example.offlinetranslator.ai.model.ModelManager
import com.example.offlinetranslator.data.model.TranscriptSegment
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.nio.LongBuffer

class WhisperOnnxSpeechRecognizer(
    private val context: Context,
    private val modelManager: ModelManager
) : SpeechRecognizerEngine {

    private var ortEnvironment: OrtEnvironment? = null
    private var encoderSession: OrtSession? = null
    private var decoderSession: OrtSession? = null
    private var singleModelSession: OrtSession? = null
    private var loadedModelPath: String? = null

    @Synchronized
    private fun initSession(): Boolean {
        val speechDir = File(context.filesDir, "models/speech")
        val encFile = File(speechDir, "whisper_encoder_quant.onnx")
        val decFile = File(speechDir, "whisper_decoder_quant.onnx")
        val singleFile = modelManager.getSpeechModelFile()

        if ((!encFile.exists() || !decFile.exists()) && (singleFile == null || !singleFile.exists())) {
            return false
        }

        try {
            release()
            ortEnvironment = OrtEnvironment.getEnvironment()
            val sessionOptions = OrtSession.SessionOptions().apply {
                setIntraOpNumThreads(4)
                setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT)
            }

            if (encFile.exists() && decFile.exists()) {
                encoderSession = ortEnvironment?.createSession(encFile.absolutePath, sessionOptions)
                decoderSession = ortEnvironment?.createSession(decFile.absolutePath, sessionOptions)
                loadedModelPath = encFile.absolutePath
            } else if (singleFile != null && singleFile.exists()) {
                singleModelSession = ortEnvironment?.createSession(singleFile.absolutePath, sessionOptions)
                loadedModelPath = singleFile.absolutePath
            }
            return true
        } catch (e: Exception) {
            e.printStackTrace()
            release()
            return false
        }
    }

    override fun isReady(): Boolean {
        val speechDir = File(context.filesDir, "models/speech")
        val encFile = File(speechDir, "whisper_encoder_quant.onnx")
        val decFile = File(speechDir, "whisper_decoder_quant.onnx")
        val singleFile = modelManager.getSpeechModelFile()

        return (encFile.exists() && decFile.exists() && encFile.length() > 0) ||
                (singleFile != null && singleFile.exists() && singleFile.length() > 0)
    }

    override suspend fun transcribe(
        audioSamples: FloatArray,
        sampleRate: Int,
        sourceLanguage: String?,
        onProgress: ((Float, Int, Int) -> Unit)?
    ): List<TranscriptSegment> = withContext(Dispatchers.Default) {
        if (!isReady()) {
            throw IllegalStateException("Offline speech recognition model not found. Please install the Whisper ONNX model in settings or see MODEL_SETUP.md.")
        }

        val sessionReady = initSession()
        if (!sessionReady || ortEnvironment == null) {
            throw IllegalStateException("Failed to initialize ONNX Runtime session for speech recognition model.")
        }

        // 1. Detect speech activity chunks (VAD)
        val chunks = VadDetector.detectSpeechChunks(
            audio = audioSamples,
            sampleRate = sampleRate
        )

        if (chunks.isEmpty()) {
            return@withContext emptyList<TranscriptSegment>()
        }

        val segments = mutableListOf<TranscriptSegment>()
        val totalChunks = chunks.size

        for ((index, chunk) in chunks.withIndex()) {
            val progress = (index.toFloat() / totalChunks.toFloat())
            onProgress?.invoke(progress, index + 1, totalChunks)

            val mel = AudioPreprocessor.computeMelSpectrogram(chunk.samples)
            var recognizedText = ""
            if (mel.isNotEmpty() && mel[0].isNotEmpty()) {
                recognizedText = if (encoderSession != null && decoderSession != null) {
                    runDualSessionInference(mel, sourceLanguage)
                } else {
                    runSingleSessionInference(mel, sourceLanguage)
                }
            }

            if (recognizedText.isNotBlank()) {
                segments.add(
                    TranscriptSegment(
                        id = index.toLong() + 1,
                        segmentIndex = index,
                        startTimeMs = chunk.startTimeMs,
                        endTimeMs = chunk.endTimeMs,
                        originalText = recognizedText.trim(),
                        confidence = 0.95f
                    )
                )
            }
        }

        onProgress?.invoke(1.0f, totalChunks, totalChunks)
        segments
    }

    private fun runDualSessionInference(mel: Array<FloatArray>, language: String?): String {
        val env = ortEnvironment ?: return ""
        val enc = encoderSession ?: return ""
        val dec = decoderSession ?: return ""

        try {
            val nMels = mel.size // 80
            val nFrames = mel[0].size
            val targetFrames = 3000
            val flatMel = FloatArray(1 * nMels * targetFrames)

            for (m in 0 until nMels) {
                for (t in 0 until targetFrames) {
                    flatMel[m * targetFrames + t] = if (t < nFrames) mel[m][t] else 0f
                }
            }

            val melShape = longArrayOf(1, nMels.toLong(), targetFrames.toLong())
            val melTensor = OnnxTensor.createTensor(env, FloatBuffer.wrap(flatMel), melShape)

            // Step 1: Run Whisper Encoder
            val encInputs = mapOf("input_features" to melTensor)
            val encResults = enc.run(encInputs)
            val lastHiddenState = encResults[0] // [1, 1500, 384]

            // Step 2: Run Autoregressive Whisper Decoder
            // Initial token sequence: <|startoftranscript|><|en|><|transcribe|><|notimestamps|>
            val tokenList = mutableListOf(50258L, 50259L, 50359L, 50363L)
            val numLayers = 4
            val numHeads = 6
            val headDim = 64
            val encoderSeqLen = 1500

            for (step in 0 until 35) {
                val inputIdsTensor = OnnxTensor.createTensor(env, LongBuffer.wrap(tokenList.toLongArray()), longArrayOf(1, tokenList.size.toLong()))
                val decInputs = HashMap<String, OnnxTensor>()
                decInputs["input_ids"] = inputIdsTensor
                decInputs["encoder_hidden_states"] = lastHiddenState as OnnxTensor

                // Cache flag
                val cacheBuf = ByteBuffer.allocateDirect(1).order(ByteOrder.nativeOrder())
                cacheBuf.put(0.toByte())
                cacheBuf.flip()
                decInputs["use_cache_branch"] = OnnxTensor.createTensor(env, cacheBuf, longArrayOf(1), ai.onnxruntime.OnnxJavaType.BOOL)

                for (i in 0 until numLayers) {
                    val dummyDec = FloatBuffer.wrap(FloatArray(0))
                    val dummyEnc = FloatBuffer.wrap(FloatArray(1 * numHeads * encoderSeqLen * headDim))
                    decInputs["past_key_values.$i.decoder.key"] = OnnxTensor.createTensor(env, dummyDec, longArrayOf(1, numHeads.toLong(), 0, headDim.toLong()))
                    decInputs["past_key_values.$i.decoder.value"] = OnnxTensor.createTensor(env, dummyDec, longArrayOf(1, numHeads.toLong(), 0, headDim.toLong()))
                    decInputs["past_key_values.$i.encoder.key"] = OnnxTensor.createTensor(env, dummyEnc, longArrayOf(1, numHeads.toLong(), encoderSeqLen.toLong(), headDim.toLong()))
                    decInputs["past_key_values.$i.encoder.value"] = OnnxTensor.createTensor(env, dummyEnc, longArrayOf(1, numHeads.toLong(), encoderSeqLen.toLong(), headDim.toLong()))
                }

                val decResults = dec.run(decInputs)
                val logitsVal = decResults[0].value as Array<*> // [1, seq_len, 51865]
                val lastLogits = (logitsVal[0] as Array<*>).last() as FloatArray

                var bestTok = 0
                var maxLogit = Float.NEGATIVE_INFINITY
                for (v in lastLogits.indices) {
                    if (lastLogits[v] > maxLogit) {
                        maxLogit = lastLogits[v]
                        bestTok = v
                    }
                }

                // Cleanup step tensors
                decInputs.values.forEach { if (it != lastHiddenState) it.close() }
                decResults.close()

                if (bestTok.toLong() == 50257L) { // <|endoftranscript|>
                    break
                }
                tokenList.add(bestTok.toLong())
            }

            melTensor.close()
            encResults.close()

            return decodeTokenIds(tokenList.toLongArray())
        } catch (e: Exception) {
            e.printStackTrace()
            return ""
        }
    }

    private fun runSingleSessionInference(mel: Array<FloatArray>, language: String?): String {
        val env = ortEnvironment ?: return ""
        val session = singleModelSession ?: return ""

        try {
            val nMels = mel.size
            val nFrames = mel[0].size
            val targetFrames = 3000
            val flatMel = FloatArray(1 * nMels * targetFrames)

            for (m in 0 until nMels) {
                for (t in 0 until targetFrames) {
                    flatMel[m * targetFrames + t] = if (t < nFrames) mel[m][t] else 0f
                }
            }

            val shape = longArrayOf(1, nMels.toLong(), targetFrames.toLong())
            val floatBuffer = FloatBuffer.wrap(flatMel)
            val inputTensor = OnnxTensor.createTensor(env, floatBuffer, shape)

            val inputMap = HashMap<String, OnnxTensor>()
            val inputName = session.inputNames.iterator().next()
            inputMap[inputName] = inputTensor

            val results = session.run(inputMap)
            val output = results[0].value

            inputTensor.close()
            results.close()

            return decodeOutputTokens(output)
        } catch (e: Exception) {
            e.printStackTrace()
            return ""
        }
    }

    private fun decodeOutputTokens(output: Any?): String {
        if (output == null) return ""
        return when (output) {
            is Array<*> -> {
                val sb = StringBuilder()
                for (elem in output) {
                    when (elem) {
                        is LongArray -> sb.append(decodeTokenIds(elem))
                        is IntArray -> sb.append(decodeTokenIds(elem.map { it.toLong() }.toLongArray()))
                    }
                }
                sb.toString().trim()
            }
            is LongArray -> decodeTokenIds(output)
            is IntArray -> decodeTokenIds(output.map { it.toLong() }.toLongArray())
            else -> output.toString()
        }
    }

    private fun decodeTokenIds(tokenIds: LongArray): String {
        val sb = StringBuilder()
        for (token in tokenIds) {
            if (token in 32..126) {
                sb.append(token.toInt().toChar())
            }
        }
        return sb.toString().trim()
    }

    @Synchronized
    override fun release() {
        try {
            encoderSession?.close()
            encoderSession = null
            decoderSession?.close()
            decoderSession = null
            singleModelSession?.close()
            singleModelSession = null
            ortEnvironment?.close()
            ortEnvironment = null
            loadedModelPath = null
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}

