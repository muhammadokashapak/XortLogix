package com.example.offlinetranslator.data.repository

import com.example.offlinetranslator.data.local.AppDatabase
import com.example.offlinetranslator.data.local.entity.SubtitleEntity
import com.example.offlinetranslator.data.local.entity.TranslationJobEntity
import com.example.offlinetranslator.data.model.TranscriptSegment
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class TranslationRepository(
    private val database: AppDatabase
) {
    private val subtitleDao = database.subtitleDao()
    private val jobDao = database.translationJobDao()

    fun getSubtitlesFlow(mediaHash: String): Flow<List<TranscriptSegment>> {
        return subtitleDao.getSubtitlesForMedia(mediaHash).map { list ->
            list.map { it.toDomain() }
        }
    }

    suspend fun getSubtitlesList(mediaHash: String): List<TranscriptSegment> {
        return subtitleDao.getSubtitlesListForMedia(mediaHash).map { it.toDomain() }
    }

    suspend fun saveSubtitles(mediaHash: String, segments: List<TranscriptSegment>) {
        val entities = segments.mapIndexed { index, seg ->
            SubtitleEntity(
                mediaHash = mediaHash,
                segmentIndex = index,
                startTimeMs = seg.startTimeMs,
                endTimeMs = seg.endTimeMs,
                originalText = seg.originalText,
                translatedText = seg.translatedText,
                confidence = seg.confidence
            )
        }
        subtitleDao.deleteSubtitlesForMedia(mediaHash)
        subtitleDao.insertSubtitles(entities)
    }

    suspend fun logTranslationJob(
        mediaId: Long,
        mediaHash: String,
        sourceLang: String,
        targetLang: String,
        status: String,
        totalSegments: Int,
        processingTimeMs: Long
    ) {
        val job = TranslationJobEntity(
            mediaId = mediaId,
            mediaHash = mediaHash,
            sourceLanguage = sourceLang,
            targetLanguage = targetLang,
            status = status,
            totalSegments = totalSegments,
            processingTimeMs = processingTimeMs
        )
        jobDao.insertJob(job)
    }

    private fun SubtitleEntity.toDomain(): TranscriptSegment {
        return TranscriptSegment(
            id = id,
            mediaHash = mediaHash,
            segmentIndex = segmentIndex,
            startTimeMs = startTimeMs,
            endTimeMs = endTimeMs,
            originalText = originalText,
            translatedText = translatedText,
            confidence = confidence
        )
    }
}
