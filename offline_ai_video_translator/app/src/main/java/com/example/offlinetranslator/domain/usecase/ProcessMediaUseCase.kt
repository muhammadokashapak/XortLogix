package com.example.offlinetranslator.domain.usecase

import android.content.Context
import android.net.Uri
import com.example.offlinetranslator.ai.speech.SpeechRecognizerEngine
import com.example.offlinetranslator.ai.translation.TranslationEngine
import com.example.offlinetranslator.audio.AudioExtractor
import com.example.offlinetranslator.data.model.ProcessingState
import com.example.offlinetranslator.data.model.TranscriptSegment
import com.example.offlinetranslator.data.repository.MediaRepository
import com.example.offlinetranslator.data.repository.TranslationRepository
import com.example.offlinetranslator.utils.FileUtils
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn

class ProcessMediaUseCase(
    private val context: Context,
    private val mediaRepository: MediaRepository,
    private val translationRepository: TranslationRepository,
    private val speechRecognizer: SpeechRecognizerEngine,
    private val translationEngine: TranslationEngine
) {

    fun execute(
        mediaUri: Uri,
        fileName: String,
        durationMs: Long,
        sizeBytes: Long,
        mimeType: String?,
        isVideo: Boolean,
        sourceLanguage: String,
        targetLanguage: String
    ): Flow<ProcessingState> = flow {
        val startTime = System.currentTimeMillis()
        val mediaHash = FileUtils.generateMediaHash(context, mediaUri, fileName)

        try {
            // Stage 1: Audio Extraction
            emit(ProcessingState.PreparingAudio(0.0f, "Extracting audio track..."))
            val audioSamples = AudioExtractor.extract16kHzMonoSamples(
                context = context,
                mediaUri = mediaUri,
                onProgress = { p ->
                    // Emits progress inside extraction
                }
            )

            if (audioSamples.isEmpty()) {
                emit(ProcessingState.Error("No valid audio stream could be extracted from this media."))
                return@flow
            }

            emit(ProcessingState.PreparingAudio(1.0f, "Audio extracted and resampled to 16kHz."))

            // Stage 2 & 3: Speech Recognition (VAD + STT)
            emit(ProcessingState.Transcribing(0.0f, 0, 1, sourceLanguage, "Transcribing speech on-device..."))
            val rawSegments = speechRecognizer.transcribe(
                audioSamples = audioSamples,
                sampleRate = 16000,
                sourceLanguage = if (sourceLanguage == "auto") null else sourceLanguage,
                onProgress = { p, current, total ->
                    // Progress updates
                }
            )

            if (rawSegments.isEmpty()) {
                emit(ProcessingState.Error("No speech detected in this media file.", isRecoverable = true))
                return@flow
            }

            emit(
                ProcessingState.Transcribing(
                    progress = 1.0f,
                    currentSegment = rawSegments.size,
                    totalSegments = rawSegments.size,
                    detectedLanguage = sourceLanguage,
                    message = "Transcription complete (${rawSegments.size} segments)."
                )
            )

            // Stage 4: Translation
            emit(
                ProcessingState.Translating(
                    progress = 0.0f,
                    currentSegment = 0,
                    totalSegments = rawSegments.size,
                    sourceLang = sourceLanguage,
                    targetLang = targetLanguage,
                    message = "Translating segments locally ($sourceLanguage -> $targetLanguage)..."
                )
            )

            val translatedSegments = mutableListOf<TranscriptSegment>()
            val originalTexts = rawSegments.map { it.originalText }
            val translatedTexts = translationEngine.translateBatch(
                texts = originalTexts,
                sourceLanguage = sourceLanguage,
                targetLanguage = targetLanguage,
                onProgress = { p, cur, tot ->
                    // Translation progress
                }
            )

            for (i in rawSegments.indices) {
                val orig = rawSegments[i]
                val trans = if (i < translatedTexts.size) translatedTexts[i] else orig.originalText
                translatedSegments.add(
                    orig.copy(
                        mediaHash = mediaHash,
                        translatedText = trans
                    )
                )
            }

            // Stage 5: Subtitle Sync & Persistence
            emit(ProcessingState.SyncingSubtitles(0.95f, "Saving synchronized subtitles to database..."))
            translationRepository.saveSubtitles(mediaHash, translatedSegments)

            val savedMedia = mediaRepository.saveOrUpdateMedia(
                uri = mediaUri,
                fileName = fileName,
                durationMs = durationMs,
                sizeBytes = sizeBytes,
                mimeType = mimeType,
                isVideo = isVideo,
                hasTranslation = true,
                detectedLanguage = sourceLanguage,
                targetLanguage = targetLanguage
            )

            val totalTime = System.currentTimeMillis() - startTime
            translationRepository.logTranslationJob(
                mediaId = savedMedia.id,
                mediaHash = mediaHash,
                sourceLang = sourceLanguage,
                targetLang = targetLanguage,
                status = "COMPLETED",
                totalSegments = translatedSegments.size,
                processingTimeMs = totalTime
            )

            emit(
                ProcessingState.Completed(
                    totalDurationMs = durationMs,
                    segmentsCount = translatedSegments.size,
                    mediaHash = mediaHash
                )
            )
        } catch (c: CancellationException) {
            emit(ProcessingState.Cancelled)
        } catch (e: Exception) {
            e.printStackTrace()
            emit(ProcessingState.Error(e.message ?: "An unknown error occurred during offline processing."))
        } finally {
            speechRecognizer.release()
            translationEngine.release()
        }
    }.flowOn(Dispatchers.Default)
}
