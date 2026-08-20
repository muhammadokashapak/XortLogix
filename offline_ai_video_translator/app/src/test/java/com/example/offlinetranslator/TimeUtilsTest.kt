package com.example.offlinetranslator

import com.example.offlinetranslator.data.model.TranscriptSegment
import com.example.offlinetranslator.subtitle.SrtExporter
import com.example.offlinetranslator.subtitle.SubtitleParser
import com.example.offlinetranslator.subtitle.VttExporter
import com.example.offlinetranslator.utils.TimeUtils
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class TimeUtilsTest {

    @Test
    fun testFormatDuration() {
        assertEquals("00:00", TimeUtils.formatDuration(0L))
        assertEquals("01:15", TimeUtils.formatDuration(75000L))
        assertEquals("01:05:30", TimeUtils.formatDuration(3930000L))
    }

    @Test
    fun testFormatSrtTime() {
        assertEquals("00:00:05,500", TimeUtils.formatSrtTime(5500L))
        assertEquals("01:02:03,045", TimeUtils.formatSrtTime(3723045L))
    }

    @Test
    fun testSrtExportAndParsing() {
        val segments = listOf(
            TranscriptSegment(id = 1, startTimeMs = 1000, endTimeMs = 3500, originalText = "First line", translatedText = "پہلی لائن"),
            TranscriptSegment(id = 2, startTimeMs = 4000, endTimeMs = 6000, originalText = "Second line", translatedText = "دوسری لائن")
        )

        val srtOutput = SrtExporter.exportToSrt(segments, includeOriginal = true, includeTranslation = true)
        assertTrue(srtOutput.contains("00:00:01,000 --> 00:00:03,500"))
        assertTrue(srtOutput.contains("First line"))
        assertTrue(srtOutput.contains("پہلی لائن"))

        val parsed = SubtitleParser.parse(srtOutput, "test_hash")
        assertEquals(2, parsed.size)
        assertEquals(1000L, parsed[0].startTimeMs)
        assertEquals(3500L, parsed[0].endTimeMs)
    }

    @Test
    fun testVttExport() {
        val segments = listOf(
            TranscriptSegment(id = 1, startTimeMs = 2000, endTimeMs = 4000, originalText = "Web VTT text")
        )
        val vttOutput = VttExporter.exportToVtt(segments)
        assertTrue(vttOutput.startsWith("WEBVTT"))
        assertTrue(vttOutput.contains("00:00:02.000 --> 00:00:04.000"))
    }
}
