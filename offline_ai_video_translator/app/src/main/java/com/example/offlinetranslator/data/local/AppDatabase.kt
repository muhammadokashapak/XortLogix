package com.example.offlinetranslator.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.example.offlinetranslator.data.local.dao.MediaDao
import com.example.offlinetranslator.data.local.dao.SubtitleDao
import com.example.offlinetranslator.data.local.dao.TranslationJobDao
import com.example.offlinetranslator.data.local.entity.MediaEntity
import com.example.offlinetranslator.data.local.entity.SubtitleEntity
import com.example.offlinetranslator.data.local.entity.TranslationJobEntity

@Database(
    entities = [
        MediaEntity::class,
        TranslationJobEntity::class,
        SubtitleEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {

    abstract fun mediaDao(): MediaDao
    abstract fun translationJobDao(): TranslationJobDao
    abstract fun subtitleDao(): SubtitleDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "offline_video_translator.db"
                ).fallbackToDestructiveMigration().build()
                INSTANCE = instance
                instance
            }
        }
    }
}
