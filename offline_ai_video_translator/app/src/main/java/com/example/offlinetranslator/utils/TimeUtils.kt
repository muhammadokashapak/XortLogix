package com.example.offlinetranslator.utils

import java.util.Locale
import java.util.concurrent.TimeUnit

object TimeUtils {

    /**
     * Formats milliseconds into standard playback time format "MM:SS" or "HH:MM:SS".
     */
    fun formatDuration(ms: Long): String {
        if (ms <= 0) return "00:00"
        val hours = TimeUnit.MILLISECONDS.toHours(ms)
        val minutes = TimeUnit.MILLISECONDS.toMinutes(ms) % 60
        val seconds = TimeUnit.MILLISECONDS.toSeconds(ms) % 60
        return if (hours > 0) {
            String.format(Locale.US, "%02d:%02d:%02d", hours, minutes, seconds)
        } else {
            String.format(Locale.US, "%02d:%02d", minutes, seconds)
        }
    }

    /**
     * Formats milliseconds into SRT subtitle timestamp format: "00:01:23,456"
     */
    fun formatSrtTime(ms: Long): String {
        val safeMs = ms.coerceAtLeast(0)
        val hours = TimeUnit.MILLISECONDS.toHours(safeMs)
        val minutes = TimeUnit.MILLISECONDS.toMinutes(safeMs) % 60
        val seconds = TimeUnit.MILLISECONDS.toSeconds(safeMs) % 60
        val millis = safeMs % 1000
        return String.format(Locale.US, "%02d:%02d:%02d,%03d", hours, minutes, seconds, millis)
    }

    /**
     * Formats milliseconds into WebVTT timestamp format: "00:01:23.456"
     */
    fun formatVttTime(ms: Long): String {
        val safeMs = ms.coerceAtLeast(0)
        val hours = TimeUnit.MILLISECONDS.toHours(safeMs)
        val minutes = TimeUnit.MILLISECONDS.toMinutes(safeMs) % 60
        val seconds = TimeUnit.MILLISECONDS.toSeconds(safeMs) % 60
        val millis = safeMs % 1000
        return String.format(Locale.US, "%02d:%02d:%02d.%03d", hours, minutes, seconds, millis)
    }
}
