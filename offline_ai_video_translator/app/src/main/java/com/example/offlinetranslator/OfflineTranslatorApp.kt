package com.example.offlinetranslator

import android.app.Application
import com.example.offlinetranslator.ai.model.AppModelManager
import com.example.offlinetranslator.ai.model.ModelManager
import com.example.offlinetranslator.ai.speech.SpeechRecognizerEngine
import com.example.offlinetranslator.ai.speech.WhisperOnnxSpeechRecognizer
import com.example.offlinetranslator.ai.translation.MarianOnnxTranslationEngine
import com.example.offlinetranslator.ai.translation.TranslationEngine
import com.example.offlinetranslator.data.local.AppDatabase
import com.example.offlinetranslator.data.repository.MediaRepository
import com.example.offlinetranslator.data.repository.SettingsRepository
import com.example.offlinetranslator.data.repository.TranslationRepository
import com.example.offlinetranslator.domain.usecase.GetSubtitlesUseCase
import com.example.offlinetranslator.domain.usecase.ManageModelsUseCase
import com.example.offlinetranslator.domain.usecase.ProcessMediaUseCase

class OfflineTranslatorApp : Application() {

    lateinit var database: AppDatabase
        private set

    lateinit var modelManager: ModelManager
        private set

    lateinit var speechRecognizerEngine: SpeechRecognizerEngine
        private set

    lateinit var translationEngine: TranslationEngine
        private set

    lateinit var mediaRepository: MediaRepository
        private set

    lateinit var translationRepository: TranslationRepository
        private set

    lateinit var settingsRepository: SettingsRepository
        private set

    lateinit var processMediaUseCase: ProcessMediaUseCase
        private set

    lateinit var getSubtitlesUseCase: GetSubtitlesUseCase
        private set

    lateinit var manageModelsUseCase: ManageModelsUseCase
        private set

    override fun onCreate() {
        super.onCreate()

        database = AppDatabase.getInstance(this)
        modelManager = AppModelManager(this)
        speechRecognizerEngine = WhisperOnnxSpeechRecognizer(this, modelManager)
        translationEngine = MarianOnnxTranslationEngine(this, modelManager)

        mediaRepository = MediaRepository(this, database)
        translationRepository = TranslationRepository(database)
        settingsRepository = SettingsRepository(this)

        processMediaUseCase = ProcessMediaUseCase(
            context = this,
            mediaRepository = mediaRepository,
            translationRepository = translationRepository,
            speechRecognizer = speechRecognizerEngine,
            translationEngine = translationEngine
        )

        getSubtitlesUseCase = GetSubtitlesUseCase(translationRepository)
        manageModelsUseCase = ManageModelsUseCase(modelManager)
    }
}
