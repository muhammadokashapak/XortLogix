package com.example.offlinetranslator.audio

import java.io.File
import java.io.FileOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

object WavUtils {

    /**
     * Saves 16kHz 16-bit mono FloatArray samples to a valid PCM WAV file.
     */
    fun saveAsWavFile(samples: FloatArray, outputFile: File, sampleRate: Int = 16000) {
        val numChannels: Short = 1
        val bitsPerSample: Short = 16
        val byteRate = sampleRate * numChannels * bitsPerSample / 8
        val blockAlign = (numChannels * bitsPerSample / 8).toShort()
        val dataSize = samples.size * 2
        val totalDataLen = dataSize + 36

        FileOutputStream(outputFile).use { fos ->
            val header = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN)
            header.put("RIFF".toByteArray())
            header.putInt(totalDataLen)
            header.put("WAVE".toByteArray())
            header.put("fmt ".toByteArray())
            header.putInt(16) // Subchunk1Size for PCM
            header.putShort(1) // AudioFormat 1 = PCM
            header.putShort(numChannels)
            header.putInt(sampleRate)
            header.putInt(byteRate)
            header.putShort(blockAlign)
            header.putShort(bitsPerSample)
            header.put("data".toByteArray())
            header.putInt(dataSize)

            fos.write(header.array())

            val audioBuffer = ByteBuffer.allocate(samples.size * 2).order(ByteOrder.LITTLE_ENDIAN)
            for (sample in samples) {
                val clamped = sample.coerceIn(-1.0f, 1.0f)
                val s16 = (clamped * 32767.0f).toInt().toShort()
                audioBuffer.putShort(s16)
            }
            fos.write(audioBuffer.array())
        }
    }
}
