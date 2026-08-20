package com.example.offlinetranslator

import com.example.offlinetranslator.ai.speech.VadDetector
import com.example.offlinetranslator.ai.translation.SimpleTokenizer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class TranslationEngineTest {

    @Test
    fun testTokenizerEncodeDecode() {
        val tokenizer = SimpleTokenizer(null)
        val text = "Hello world welcome"
        val ids = tokenizer.encode(text)
        assertNotNull(ids)
        assertTrue(ids.isNotEmpty())
    }

    @Test
    fun testVadDetectorWithSilenceAndAudio() {
        // Create 2 seconds of silence, then 2 seconds of high energy tone, then 2 seconds of silence
        val sampleRate = 16000
        val totalSamples = sampleRate * 6
        val audio = FloatArray(totalSamples)

        // Add 2 seconds tone in middle
        for (i in (sampleRate * 2) until (sampleRate * 4)) {
            audio[i] = 0.5f * kotlin.math.sin(2.0 * kotlin.math.PI * 440.0 * i / sampleRate).toFloat()
        }

        val chunks = VadDetector.detectSpeechChunks(
            audio = audio,
            sampleRate = sampleRate,
            energyThreshold = 0.01f
        )

        assertTrue("Should detect active speech chunk", chunks.isNotEmpty())
        val chunk = chunks[0]
        assertTrue("Start time should cover speech onset", chunk.startTimeMs <= 2000L)
        assertTrue("End time should cover speech offset", chunk.endTimeMs >= 4000L)
    }
}

