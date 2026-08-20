package com.example.offlinetranslator

import com.example.offlinetranslator.data.model.TranscriptSegment
import com.example.offlinetranslator.player.SubtitleSynchronizer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test

class SubtitleSyncTest {

    private lateinit var synchronizer: SubtitleSynchronizer

    @Before
    fun setup() {
        synchronizer = SubtitleSynchronizer()
    }

    @Test
    fun testSubtitleSynchronizationExactMatch() {
        val segments = listOf(
            TranscriptSegment(id = 1, startTimeMs = 1000, endTimeMs = 3000, originalText = "Hello world", translatedText = "ہیلو دنیا"),
            TranscriptSegment(id = 2, startTimeMs = 3500, endTimeMs = 6000, originalText = "How are you?", translatedText = "آپ کیسے ہیں؟"),
            TranscriptSegment(id = 3, startTimeMs = 7000, endTimeMs = 9000, originalText = "Goodbye", translatedText = "خدا حافظ")
        )
        synchronizer.setSubtitles(segments)

        // Before any segment
        synchronizer.updatePlaybackPosition(500)
        assertNull(synchronizer.currentActiveSegment.value)

        // Inside segment 1
        synchronizer.updatePlaybackPosition(2000)
        val active1 = synchronizer.currentActiveSegment.value
        assertNotNull(active1)
        assertEquals("Hello world", active1?.originalText)
        assertEquals("ہیلو دنیا", active1?.translatedText)

        // In silence gap between segment 1 and 2
        synchronizer.updatePlaybackPosition(3200)
        assertNull(synchronizer.currentActiveSegment.value)

        // Inside segment 2
        synchronizer.updatePlaybackPosition(4000)
        assertEquals("How are you?", synchronizer.currentActiveSegment.value?.originalText)

        // After all segments
        synchronizer.updatePlaybackPosition(12000)
        assertNull(synchronizer.currentActiveSegment.value)
    }

    @Test
    fun testSubtitleDelayOffset() {
        val segments = listOf(
            TranscriptSegment(id = 1, startTimeMs = 2000, endTimeMs = 4000, originalText = "Delayed text")
        )
        synchronizer.setSubtitles(segments)

        // Apply +500ms delay offset
        synchronizer.setDelayOffset(500L)

        // Playback at 1600ms -> adjusted to 2100ms -> should match segment
        synchronizer.updatePlaybackPosition(1600)
        assertNotNull(synchronizer.currentActiveSegment.value)
        assertEquals("Delayed text", synchronizer.currentActiveSegment.value?.originalText)
    }
}
