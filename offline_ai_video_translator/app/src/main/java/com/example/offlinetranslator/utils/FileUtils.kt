package com.example.offlinetranslator.utils

import android.content.Context
import android.database.Cursor
import android.net.Uri
import android.provider.OpenableColumns
import java.io.File
import java.io.InputStream
import java.security.MessageDigest
import java.util.Locale

object FileUtils {

    /**
     * Formats bytes into human readable string (e.g. 14.5 MB, 1.2 GB)
     */
    fun formatFileSize(bytes: Long): String {
        if (bytes <= 0) return "0 B"
        val units = arrayOf("B", "KB", "MB", "GB", "TB")
        val digitGroups = (Math.log10(bytes.toDouble()) / Math.log10(1024.0)).toInt()
        val formatted = bytes / Math.pow(1024.0, digitGroups.toDouble())
        return String.format(Locale.US, "%.1f %s", formatted, units[digitGroups])
    }

    /**
     * Extracts filename from a content URI safely.
     */
    fun getFileNameFromUri(context: Context, uri: Uri): String {
        var name = "media_${System.currentTimeMillis()}"
        if (uri.scheme == "content") {
            val cursor: Cursor? = context.contentResolver.query(uri, null, null, null, null)
            cursor?.use {
                if (it.moveToFirst()) {
                    val index = it.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    if (index != -1) {
                        name = it.getString(index)
                    }
                }
            }
        } else if (uri.scheme == "file") {
            name = File(uri.path ?: "").name
        }
        return name
    }

    /**
     * Generates a stable media hash based on URI, file name and size for caching without reading full GBs of video.
     */
    fun generateMediaHash(context: Context, uri: Uri, fileName: String): String {
        var size: Long = 0
        try {
            context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE)
                    if (sizeIndex != -1) {
                        size = cursor.getLong(sizeIndex)
                    }
                }
            }
        } catch (_: Exception) {}

        val rawInput = "$uri|$fileName|$size"
        val md = MessageDigest.getInstance("SHA-256")
        val digest = md.digest(rawInput.toByteArray())
        return digest.joinToString("") { "%02x".format(it) }
    }

    /**
     * Determines whether a given MIME type or file extension is video.
     */
    fun isVideoMime(mimeType: String?, fileName: String): Boolean {
        if (mimeType?.startsWith("video/") == true) return true
        val lower = fileName.lowercase()
        return lower.endsWith(".mp4") || lower.endsWith(".mkv") ||
                lower.endsWith(".webm") || lower.endsWith(".mov") ||
                lower.endsWith(".3gp") || lower.endsWith(".avi")
    }
}
