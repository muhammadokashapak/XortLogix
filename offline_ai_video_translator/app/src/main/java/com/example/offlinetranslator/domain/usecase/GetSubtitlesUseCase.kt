package com.example.offlinetranslator.domain.usecase

import com.example.offlinetranslator.data.model.TranscriptSegment
import com.example.offlinetranslator.data.repository.TranslationRepository
import kotlinx.coroutines.flow.Flow

class GetSubtitlesUseCase(
    private val translationRepository: TranslationRepository
) {
    fun getSubtitlesFlow(mediaHash: String): Flow<List<TranscriptSegment>> {
        return translationRepository.getSubtitlesFlow(mediaHash)
    }

    suspend fun getSubtitlesList(mediaHash: String): List<TranscriptSegment> {
        return translationRepository.getSubtitlesList(mediaHash)
    }
}
