package com.example.offlinetranslator.ai.speech

import kotlin.math.sqrt

data class SpeechChunk(
    val startSample: Int,
    val endSample: Int,
    val startTimeMs: Long,
    val endTimeMs: Long,
    val samples: FloatArray
)

object VadDetector {

    /**
     * Splits continuous audio into active speech chunks using energy-based Voice Activity Detection.
     * @param audio 16kHz mono audio float samples (-1.0 to 1.0)
     * @param sampleRate Default 16,000 Hz
     * @param frameDurationMs Frame size for energy calculation (default 30ms)
     * @param energyThreshold Minimum RMS energy to consider speech active (default 0.015f)
     * @param minSpeechDurationMs Minimum duration of speech to trigger a chunk (default 500ms)
     * @param maxSilenceDurationMs Max silence gap allowed before splitting into a new chunk (default 800ms)
     * @param maxChunkDurationMs Maximum chunk length before forced split (default 25000ms = 25s)
     */
    fun detectSpeechChunks(
        audio: FloatArray,
        sampleRate: Int = 16000,
        frameDurationMs: Int = 30,
        energyThreshold: Float = 0.012f,
        minSpeechDurationMs: Int = 500,
        maxSilenceDurationMs: Int = 800,
        maxChunkDurationMs: Int = 25000
    ): List<SpeechChunk> {
        val frameSize = (sampleRate * frameDurationMs) / 1000
        val numFrames = audio.size / frameSize
        if (numFrames == 0) return emptyList()

        val isSpeechFrame = BooleanArray(numFrames)
        for (f in 0 until numFrames) {
            val start = f * frameSize
            var sumSquares = 0.0
            for (i in 0 until frameSize) {
                val s = audio[start + i]
                sumSquares += s * s
            }
            val rms = sqrt(sumSquares / frameSize).toFloat()
            isSpeechFrame[f] = rms >= energyThreshold
        }

        val chunks = mutableListOf<SpeechChunk>()
        val minSpeechFrames = (minSpeechDurationMs / frameDurationMs).coerceAtLeast(1)
        val maxSilenceFrames = (maxSilenceDurationMs / frameDurationMs).coerceAtLeast(1)
        val maxChunkFrames = (maxChunkDurationMs / frameDurationMs).coerceAtLeast(10)

        var inSpeech = false
        var chunkStartFrame = 0
        var silenceCounter = 0

        for (f in 0 until numFrames) {
            val speech = isSpeechFrame[f]

            if (!inSpeech && speech) {
                inSpeech = true
                chunkStartFrame = (f - 2).coerceAtLeast(0) // Add 2 frames of lead-in padding
                silenceCounter = 0
            } else if (inSpeech) {
                if (speech) {
                    silenceCounter = 0
                } else {
                    silenceCounter++
                }

                val currentChunkLengthFrames = f - chunkStartFrame
                val reachedSilenceLimit = silenceCounter >= maxSilenceFrames
                val reachedMaxDuration = currentChunkLengthFrames >= maxChunkFrames
                val isLastFrame = f == numFrames - 1

                if (reachedSilenceLimit || reachedMaxDuration || isLastFrame) {
                    val speechLengthFrames = currentChunkLengthFrames - silenceCounter
                    if (speechLengthFrames >= minSpeechFrames || reachedMaxDuration) {
                        val endFrame = (f + 2).coerceAtMost(numFrames)
                        val startSample = chunkStartFrame * frameSize
                        val endSample = (endFrame * frameSize).coerceAtMost(audio.size)
                        val chunkSamples = audio.copyOfRange(startSample, endSample)

                        val startTimeMs = (startSample.toLong() * 1000L) / sampleRate
                        val endTimeMs = (endSample.toLong() * 1000L) / sampleRate

                        chunks.add(
                            SpeechChunk(
                                startSample = startSample,
                                endSample = endSample,
                                startTimeMs = startTimeMs,
                                endTimeMs = endTimeMs,
                                samples = chunkSamples
                            )
                        )
                    }
                    inSpeech = false
                    silenceCounter = 0
                }
            }
        }

        // Fallback: If no speech chunks detected by threshold (e.g. quiet audio), partition entire audio into 15-second windows
        if (chunks.isEmpty() && audio.isNotEmpty()) {
            val windowSamples = sampleRate * 15
            var offset = 0
            while (offset < audio.size) {
                val end = (offset + windowSamples).coerceAtMost(audio.size)
                val chunkSamples = audio.copyOfRange(offset, end)
                val startTimeMs = (offset.toLong() * 1000L) / sampleRate
                val endTimeMs = (end.toLong() * 1000L) / sampleRate
                chunks.add(
                    SpeechChunk(
                        startSample = offset,
                        endSample = end,
                        startTimeMs = startTimeMs,
                        endTimeMs = endTimeMs,
                        samples = chunkSamples
                    )
                )
                offset = end
            }
        }

        return chunks
    }
}
