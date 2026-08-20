package com.example.offlinetranslator.subtitle

import com.example.offlinetranslator.data.model.TranscriptSegment
import com.example.offlinetranslator.utils.TimeUtils

object SrtExporter {

    /**
     * Converts a list of TranscriptSegments into standard SubRip (.srt) subtitle text.
     */
    fun exportToSrt(
        segments: List<TranscriptSegment>,
        includeOriginal: Boolean = true,
        includeTranslation: Boolean = true
    ): String {
        val sb = StringBuilder()
        var index = 1

        for (seg in segments) {
            val original = seg.originalText.trim()
            val translated = seg.translatedText?.trim()

            val textToDisplay = when {
                includeOriginal && includeTranslation && !translated.isNullOrEmpty() -> {
                    "$original\n$translated"
                }
                includeTranslation && !translated.isNullOrEmpty() -> translated
                else -> original
            }

            if (textToDisplay.isNotBlank()) {
                sb.append(index++).append("\n")
                sb.append(TimeUtils.formatSrtTime(seg.startTimeMs))
                    .append(" --> ")
                    .append(TimeUtils.formatSrtTime(seg.endTimeMs))
                    .append("\n")
                sb.append(textToDisplay).append("\n\n")
            }
        }
        return sb.toString()
    }
}
