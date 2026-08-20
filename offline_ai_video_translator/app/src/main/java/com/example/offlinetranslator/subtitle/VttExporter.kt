package com.example.offlinetranslator.subtitle

import com.example.offlinetranslator.data.model.TranscriptSegment
import com.example.offlinetranslator.utils.TimeUtils

object VttExporter {

    /**
     * Converts a list of TranscriptSegments into standard WebVTT (.vtt) format.
     */
    fun exportToVtt(
        segments: List<TranscriptSegment>,
        includeOriginal: Boolean = true,
        includeTranslation: Boolean = true
    ): String {
        val sb = StringBuilder()
        sb.append("WEBVTT\n\n")

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
                sb.append(TimeUtils.formatVttTime(seg.startTimeMs))
                    .append(" --> ")
                    .append(TimeUtils.formatVttTime(seg.endTimeMs))
                    .append("\n")
                sb.append(textToDisplay).append("\n\n")
            }
        }
        return sb.toString()
    }
}
