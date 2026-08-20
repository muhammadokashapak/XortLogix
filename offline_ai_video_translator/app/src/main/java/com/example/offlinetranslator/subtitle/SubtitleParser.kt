package com.example.offlinetranslator.subtitle

import com.example.offlinetranslator.data.model.TranscriptSegment
import java.util.regex.Pattern

object SubtitleParser {

    private val SRT_TIME_PATTERN = Pattern.compile("(\\d{2}):(\\d{2}):(\\d{2})[,.](\\d{3})\\s*-->\\s*(\\d{2}):(\\d{2}):(\\d{2})[,.](\\d{3})")

    /**
     * Parses SRT or WebVTT string into a list of TranscriptSegments.
     */
    fun parse(content: String, mediaHash: String = ""): List<TranscriptSegment> {
        val lines = content.lines()
        val segments = mutableListOf<TranscriptSegment>()
        var currentStart = 0L
        var currentEnd = 0L
        val textBuilder = StringBuilder()
        var segmentIndex = 0

        for (rawLine in lines) {
            val line = rawLine.trim()
            if (line.isEmpty() || line.startsWith("WEBVTT") || line.all { it.isDigit() }) {
                if (currentEnd > currentStart && textBuilder.isNotBlank()) {
                    segments.add(
                        TranscriptSegment(
                            id = segmentIndex.toLong() + 1,
                            mediaHash = mediaHash,
                            segmentIndex = segmentIndex++,
                            startTimeMs = currentStart,
                            endTimeMs = currentEnd,
                            originalText = textBuilder.toString().trim()
                        )
                    )
                    textBuilder.clear()
                    currentStart = 0L
                    currentEnd = 0L
                }
                continue
            }

            val matcher = SRT_TIME_PATTERN.matcher(line)
            if (matcher.find()) {
                if (currentEnd > currentStart && textBuilder.isNotBlank()) {
                    segments.add(
                        TranscriptSegment(
                            id = segmentIndex.toLong() + 1,
                            mediaHash = mediaHash,
                            segmentIndex = segmentIndex++,
                            startTimeMs = currentStart,
                            endTimeMs = currentEnd,
                            originalText = textBuilder.toString().trim()
                        )
                    )
                    textBuilder.clear()
                }

                val h1 = matcher.group(1)?.toLongOrNull() ?: 0L
                val m1 = matcher.group(2)?.toLongOrNull() ?: 0L
                val s1 = matcher.group(3)?.toLongOrNull() ?: 0L
                val ms1 = matcher.group(4)?.toLongOrNull() ?: 0L
                currentStart = (h1 * 3600 + m1 * 60 + s1) * 1000 + ms1

                val h2 = matcher.group(5)?.toLongOrNull() ?: 0L
                val m2 = matcher.group(6)?.toLongOrNull() ?: 0L
                val s2 = matcher.group(7)?.toLongOrNull() ?: 0L
                val ms2 = matcher.group(8)?.toLongOrNull() ?: 0L
                currentEnd = (h2 * 3600 + m2 * 60 + s2) * 1000 + ms2
            } else {
                if (textBuilder.isNotEmpty()) textBuilder.append("\n")
                textBuilder.append(line)
            }
        }

        if (currentEnd > currentStart && textBuilder.isNotBlank()) {
            segments.add(
                TranscriptSegment(
                    id = segmentIndex.toLong() + 1,
                    mediaHash = mediaHash,
                    segmentIndex = segmentIndex,
                    startTimeMs = currentStart,
                    endTimeMs = currentEnd,
                    originalText = textBuilder.toString().trim()
                )
            )
        }

        return segments
    }
}
