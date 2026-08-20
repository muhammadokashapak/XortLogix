package com.example.offlinetranslator.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.example.offlinetranslator.data.local.entity.TranslationJobEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface TranslationJobDao {
    @Query("SELECT * FROM translation_jobs ORDER BY createdAt DESC")
    fun getAllJobs(): Flow<List<TranslationJobEntity>>

    @Query("SELECT * FROM translation_jobs WHERE mediaHash = :hash ORDER BY createdAt DESC LIMIT 1")
    suspend fun getLatestJobForMedia(hash: String): TranslationJobEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertJob(job: TranslationJobEntity): Long

    @Query("DELETE FROM translation_jobs WHERE mediaHash = :hash")
    suspend fun deleteJobsByMediaHash(hash: String)
}
