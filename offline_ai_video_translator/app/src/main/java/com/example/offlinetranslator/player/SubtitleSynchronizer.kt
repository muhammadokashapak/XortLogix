package com.example.offlinetranslator.player

import com.example.offlinetranslator.data.model.TranscriptSegment
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class SubtitleSynchronizer {

    private var segments: List<TranscriptSegment> = emptyList()
    private val _currentActiveSegment = MutableStateFlow<TranscriptSegment?>(null)
    val currentActiveSegment: StateFlow<TranscriptSegment?> = _currentActiveSegment.asStateFlow()

    private var delayOffsetMs: Long = 0L

    fun setSubtitles(newSegments: List<TranscriptSegment>) {
        segments = newSegments.sortedBy { it.startTimeMs }
        _currentActiveSegment.value = null
    }

    fun setDelayOffset(offsetMs: Long) {
        delayOffsetMs = offsetMs
    }

    /**
     * Updates active subtitle based on playback position (in milliseconds).
     */
    fun updatePlaybackPosition(positionMs: Long) {
        if (segments.isEmpty()) {
            _currentActiveSegment.value = null
            return
        }

        val adjustedPosition = positionMs + delayOffsetMs
        val found = findSegment(adjustedPosition)
        if (_currentActiveSegment.value != found) {
            _currentActiveSegment.value = found
        }
    }

    private fun findSegment(positionMs: Long): TranscriptSegment? {
        if (segments.isEmpty()) return null

        var low = 0
        var high = segments.size - 1

        while (low <= high) {
            val mid = (low + high) ushr 1
            val seg = segments[mid]

            if (positionMs in seg.startTimeMs..seg.endTimeMs) {
                return seg
            } else if (positionMs < seg.startTimeMs) {
                high = mid - 1
            } else {
                low = mid + 1
            }
        }
        return null
    }

    fun clear() {
        segments = emptyList()
        _currentActiveSegment.value = null
    }
}
