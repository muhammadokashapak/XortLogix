package com.example.offlinetranslator.audio

import android.content.Context
import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import android.net.Uri
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.nio.ByteBuffer
import java.nio.ByteOrder

object AudioExtractor {

    private const val TARGET_SAMPLE_RATE = 16000
    private const val TIMEOUT_US = 5000L

    /**
     * Extracts and decodes audio from a media content URI into a normalized 16kHz mono FloatArray.
     */
    suspend fun extract16kHzMonoSamples(
        context: Context,
        mediaUri: Uri,
        onProgress: ((Float) -> Unit)? = null
    ): FloatArray = withContext(Dispatchers.IO) {
        val extractor = MediaExtractor()
        try {
            extractor.setDataSource(context, mediaUri, null)
        } catch (e: Exception) {
            extractor.release()
            throw IllegalArgumentException("Cannot open media source: ${e.message}", e)
        }

        var audioTrackIndex = -1
        var format: MediaFormat? = null

        for (i in 0 until extractor.trackCount) {
            val trackFormat = extractor.getTrackFormat(i)
            val mime = trackFormat.getString(MediaFormat.KEY_MIME) ?: ""
            if (mime.startsWith("audio/")) {
                audioTrackIndex = i
                format = trackFormat
                break
            }
        }

        if (audioTrackIndex == -1 || format == null) {
            extractor.release()
            throw IllegalStateException("No audio track found in the selected media file.")
        }

        extractor.selectTrack(audioTrackIndex)
        val mime = format.getString(MediaFormat.KEY_MIME) ?: ""
        val originalSampleRate = if (format.containsKey(MediaFormat.KEY_SAMPLE_RATE)) {
            format.getInteger(MediaFormat.KEY_SAMPLE_RATE)
        } else {
            44100
        }
        val channelCount = if (format.containsKey(MediaFormat.KEY_CHANNEL_COUNT)) {
            format.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
        } else {
            2
        }
        val durationUs = if (format.containsKey(MediaFormat.KEY_DURATION)) {
            format.getLong(MediaFormat.KEY_DURATION)
        } else {
            1L
        }

        val codec = MediaCodec.createDecoderByType(mime)
        codec.configure(format, null, null, 0)
        codec.start()

        val pcmList = ArrayList<Float>()
        val bufferInfo = MediaCodec.BufferInfo()
        var isEOS = false

        try {
            while (!isEOS) {
                val inputIndex = codec.dequeueInputBuffer(TIMEOUT_US)
                if (inputIndex >= 0) {
                    val inputBuffer = codec.getInputBuffer(inputIndex)
                    if (inputBuffer != null) {
                        val sampleSize = extractor.readSampleData(inputBuffer, 0)
                        if (sampleSize < 0) {
                            codec.queueInputBuffer(
                                inputIndex, 0, 0, 0L,
                                MediaCodec.BUFFER_FLAG_END_OF_STREAM
                            )
                            isEOS = true
                        } else {
                            val sampleTime = extractor.sampleTime
                            codec.queueInputBuffer(inputIndex, 0, sampleSize, sampleTime, 0)
                            extractor.advance()

                            if (durationUs > 0) {
                                val progress = (sampleTime.toFloat() / durationUs.toFloat()).coerceIn(0f, 1f)
                                onProgress?.invoke(progress)
                            }
                        }
                    }
                }

                var outputIndex = codec.dequeueOutputBuffer(bufferInfo, TIMEOUT_US)
                while (outputIndex >= 0) {
                    val outputBuffer = codec.getOutputBuffer(outputIndex)
                    if (outputBuffer != null && bufferInfo.size > 0) {
                        outputBuffer.position(bufferInfo.offset)
                        outputBuffer.limit(bufferInfo.offset + bufferInfo.size)
                        outputBuffer.order(ByteOrder.LITTLE_ENDIAN)

                        val shortBuffer = outputBuffer.asShortBuffer()
                        val numShorts = shortBuffer.remaining()
                        val numFrames = numShorts / channelCount

                        for (f in 0 until numFrames) {
                            var sum = 0.0f
                            for (c in 0 until channelCount) {
                                sum += shortBuffer.get() / 32768.0f
                            }
                            pcmList.add(sum / channelCount.toFloat())
                        }
                    }
                    codec.releaseOutputBuffer(outputIndex, false)
                    if ((bufferInfo.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0) {
                        isEOS = true
                        break
                    }
                    outputIndex = codec.dequeueOutputBuffer(bufferInfo, TIMEOUT_US)
                }
            }
        } finally {
            try {
                codec.stop()
                codec.release()
            } catch (_: Exception) {}
            extractor.release()
        }

        val rawPcm = pcmList.toFloatArray()

        // Resample to TARGET_SAMPLE_RATE (16,000 Hz) if needed
        return@withContext if (originalSampleRate != TARGET_SAMPLE_RATE && rawPcm.isNotEmpty()) {
            resampleLinear(rawPcm, originalSampleRate, TARGET_SAMPLE_RATE)
        } else {
            rawPcm
        }
    }

    private fun resampleLinear(input: FloatArray, srcRate: Int, targetRate: Int): FloatArray {
        val ratio = targetRate.toDouble() / srcRate.toDouble()
        val targetLength = (input.size * ratio).toInt()
        val output = FloatArray(targetLength)

        for (i in 0 until targetLength) {
            val srcIndex = i / ratio
            val indexFloor = srcIndex.toInt().coerceIn(0, input.size - 1)
            val indexCeil = (indexFloor + 1).coerceIn(0, input.size - 1)
            val fraction = (srcIndex - indexFloor).toFloat()

            output[i] = input[indexFloor] * (1f - fraction) + input[indexCeil] * fraction
        }
        return output
    }
}
