package com.example.offlinetranslator.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.example.offlinetranslator.data.local.entity.SubtitleEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface SubtitleDao {
    @Query("SELECT * FROM subtitles WHERE mediaHash = :mediaHash ORDER BY startTimeMs ASC")
    fun getSubtitlesForMedia(mediaHash: String): Flow<List<SubtitleEntity>>

    @Query("SELECT * FROM subtitles WHERE mediaHash = :mediaHash ORDER BY startTimeMs ASC")
    suspend fun getSubtitlesListForMedia(mediaHash: String): List<SubtitleEntity>

    @Query("SELECT * FROM subtitles WHERE mediaHash = :mediaHash AND :positionMs >= startTimeMs AND :positionMs <= endTimeMs LIMIT 1")
    suspend fun getActiveSubtitle(mediaHash: String, positionMs: Long): SubtitleEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSubtitles(subtitles: List<SubtitleEntity>)

    @Query("DELETE FROM subtitles WHERE mediaHash = :mediaHash")
    suspend fun deleteSubtitlesForMedia(mediaHash: String)
}
