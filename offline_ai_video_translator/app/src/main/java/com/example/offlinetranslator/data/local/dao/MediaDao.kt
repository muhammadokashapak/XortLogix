package com.example.offlinetranslator.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.offlinetranslator.data.local.entity.MediaEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface MediaDao {
    @Query("SELECT * FROM media_items ORDER BY updatedAt DESC")
    fun getAllMedia(): Flow<List<MediaEntity>>

    @Query("SELECT * FROM media_items WHERE hasTranslation = 1 ORDER BY updatedAt DESC")
    fun getTranslatedMedia(): Flow<List<MediaEntity>>

    @Query("SELECT * FROM media_items WHERE mediaHash = :hash LIMIT 1")
    suspend fun getMediaByHash(hash: String): MediaEntity?

    @Query("SELECT * FROM media_items WHERE id = :id LIMIT 1")
    suspend fun getMediaById(id: Long): MediaEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMedia(media: MediaEntity): Long

    @Update
    suspend fun updateMedia(media: MediaEntity)

    @Query("UPDATE media_items SET lastPlayedPositionMs = :positionMs, updatedAt = :timestamp WHERE mediaHash = :hash")
    suspend fun updatePlaybackPosition(hash: String, positionMs: Long, timestamp: Long = System.currentTimeMillis())

    @Query("DELETE FROM media_items WHERE id = :id")
    suspend fun deleteMedia(id: Long)

    @Query("DELETE FROM media_items WHERE mediaHash = :hash")
    suspend fun deleteMediaByHash(hash: String)
}
