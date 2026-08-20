package com.example.offlinetranslator.data.repository

import android.content.Context
import android.net.Uri
import com.example.offlinetranslator.data.local.AppDatabase
import com.example.offlinetranslator.data.local.entity.MediaEntity
import com.example.offlinetranslator.data.model.MediaItem
import com.example.offlinetranslator.utils.FileUtils
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class MediaRepository(
    private val context: Context,
    private val database: AppDatabase
) {
    private val mediaDao = database.mediaDao()

    val allMedia: Flow<List<MediaItem>> = mediaDao.getAllMedia().map { list ->
        list.map { it.toDomain() }
    }

    val translatedMedia: Flow<List<MediaItem>> = mediaDao.getTranslatedMedia().map { list ->
        list.map { it.toDomain() }
    }

    suspend fun getMediaByHash(hash: String): MediaItem? {
        return mediaDao.getMediaByHash(hash)?.toDomain()
    }

    suspend fun saveOrUpdateMedia(
        uri: Uri,
        fileName: String,
        durationMs: Long,
        sizeBytes: Long,
        mimeType: String?,
        isVideo: Boolean,
        hasTranslation: Boolean = false,
        detectedLanguage: String? = null,
        targetLanguage: String? = null
    ): MediaItem {
        val hash = FileUtils.generateMediaHash(context, uri, fileName)
        val existing = mediaDao.getMediaByHash(hash)

        val entity = MediaEntity(
            id = existing?.id ?: 0,
            uriString = uri.toString(),
            fileName = fileName,
            durationMs = if (durationMs > 0) durationMs else (existing?.durationMs ?: 0L),
            sizeBytes = sizeBytes,
            mimeType = mimeType,
            isVideo = isVideo,
            mediaHash = hash,
            lastPlayedPositionMs = existing?.lastPlayedPositionMs ?: 0L,
            hasTranslation = hasTranslation || (existing?.hasTranslation == true),
            detectedLanguage = detectedLanguage ?: existing?.detectedLanguage,
            targetLanguage = targetLanguage ?: existing?.targetLanguage,
            createdAt = existing?.createdAt ?: System.currentTimeMillis(),
            updatedAt = System.currentTimeMillis()
        )

        val id = mediaDao.insertMedia(entity)
        return entity.copy(id = if (existing != null) existing.id else id).toDomain()
    }

    suspend fun updatePlaybackPosition(mediaHash: String, positionMs: Long) {
        mediaDao.updatePlaybackPosition(mediaHash, positionMs)
    }

    suspend fun deleteMedia(mediaHash: String) {
        mediaDao.deleteMediaByHash(mediaHash)
    }

    private fun MediaEntity.toDomain(): MediaItem {
        return MediaItem(
            id = id,
            uri = Uri.parse(uriString),
            fileName = fileName,
            durationMs = durationMs,
            sizeBytes = sizeBytes,
            mimeType = mimeType,
            isVideo = isVideo,
            mediaHash = mediaHash,
            lastPlayedPositionMs = lastPlayedPositionMs,
            hasTranslation = hasTranslation,
            detectedLanguage = detectedLanguage,
            targetLanguage = targetLanguage,
            createdAt = createdAt
        )
    }
}
