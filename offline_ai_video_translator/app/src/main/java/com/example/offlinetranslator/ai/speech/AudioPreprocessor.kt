package com.example.offlinetranslator.ai.speech

import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.ln
import kotlin.math.log10
import kotlin.math.sin
import kotlin.math.sqrt

object AudioPreprocessor {

    private const val SAMPLE_RATE = 16000
    private const val N_FFT = 400
    private const val HOP_LENGTH = 160
    private const val N_MELS = 80

    /**
     * Computes the 80-bin log mel-spectrogram for Whisper models.
     * Output shape: [80, num_frames] flattened or 2D array.
     */
    fun computeMelSpectrogram(audio: FloatArray): Array<FloatArray> {
        val window = FloatArray(N_FFT) { i ->
            (0.5 - 0.5 * cos(2.0 * PI * i / N_FFT)).toFloat()
        }

        val numFrames = (audio.size - N_FFT) / HOP_LENGTH + 1
        if (numFrames <= 0) return Array(N_MELS) { FloatArray(0) }

        val melFilters = createMelFilterBank(SAMPLE_RATE, N_FFT, N_MELS)
        val melSpectrogram = Array(N_MELS) { FloatArray(numFrames) }

        val frame = FloatArray(N_FFT)
        val real = FloatArray(N_FFT)
        val imag = FloatArray(N_FFT)
        val powerSpec = FloatArray(N_FFT / 2 + 1)

        for (t in 0 until numFrames) {
            val offset = t * HOP_LENGTH
            for (i in 0 until N_FFT) {
                frame[i] = if (offset + i < audio.size) audio[offset + i] * window[i] else 0f
            }

            fft(frame, real, imag)

            for (i in 0..N_FFT / 2) {
                powerSpec[i] = real[i] * real[i] + imag[i] * imag[i]
            }

            for (m in 0 until N_MELS) {
                var melEnergy = 0.0f
                val filter = melFilters[m]
                for (i in 0..N_FFT / 2) {
                    melEnergy += powerSpec[i] * filter[i]
                }
                // Log compression with clamp
                val logMel = ln(maxOf(melEnergy, 1e-10f))
                melSpectrogram[m][t] = logMel
            }
        }

        // Global normalization across mel-spectrogram (standard for Whisper)
        var maxVal = Float.NEGATIVE_INFINITY
        for (m in 0 until N_MELS) {
            for (t in 0 until numFrames) {
                if (melSpectrogram[m][t] > maxVal) maxVal = melSpectrogram[m][t]
            }
        }

        for (m in 0 until N_MELS) {
            for (t in 0 until numFrames) {
                val clamped = maxOf(melSpectrogram[m][t], maxVal - 8.0f)
                melSpectrogram[m][t] = (clamped + 4.0f) / 4.0f
            }
        }

        return melSpectrogram
    }

    private fun hzToMel(hz: Float): Float = 2595.0f * log10(1.0f + hz / 700.0f)
    private fun melToHz(mel: Float): Float = 700.0f * (Math.pow(10.0, (mel / 2595.0).toDouble()).toFloat() - 1.0f)

    private fun createMelFilterBank(sampleRate: Int, nFft: Int, nMels: Int): Array<FloatArray> {
        val numFreqs = nFft / 2 + 1
        val minMel = hzToMel(0f)
        val maxMel = hzToMel(sampleRate / 2f)

        val melPoints = FloatArray(nMels + 2) { i ->
            minMel + i * (maxMel - minMel) / (nMels + 1)
        }

        val binPoints = IntArray(nMels + 2) { i ->
            val hz = melToHz(melPoints[i])
            ((nFft + 1) * hz / sampleRate).toInt().coerceIn(0, numFreqs - 1)
        }

        val filters = Array(nMels) { FloatArray(numFreqs) }
        for (m in 0 until nMels) {
            val left = binPoints[m]
            val center = binPoints[m + 1]
            val right = binPoints[m + 2]

            for (k in left until center) {
                if (center != left) filters[m][k] = (k - left).toFloat() / (center - left)
            }
            for (k in center until right) {
                if (right != center) filters[m][k] = (right - k).toFloat() / (right - center)
            }
        }
        return filters
    }

    private fun fft(input: FloatArray, real: FloatArray, imag: FloatArray) {
        val n = input.size
        for (i in 0 until n) {
            real[i] = input[i]
            imag[i] = 0f
        }

        var j = 0
        for (i in 0 until n - 1) {
            if (i < j) {
                val tempR = real[i]; real[i] = real[j]; real[j] = tempR
                val tempI = imag[i]; imag[i] = imag[j]; imag[j] = tempI
            }
            var k = n shr 1
            while (k <= j) {
                j -= k
                k = k shr 1
            }
            j += k
        }

        var l = 2
        while (l <= n) {
            val ang = -2.0 * PI / l
            var wlenR = cos(ang).toFloat()
            var wlenI = sin(ang).toFloat()
            var i = 0
            while (i < n) {
                var wR = 1.0f
                var wI = 0.0f
                for (k in 0 until l / 2) {
                    val uR = real[i + k]
                    val uI = imag[i + k]
                    val vR = real[i + k + l / 2] * wR - imag[i + k + l / 2] * wI
                    val vI = real[i + k + l / 2] * wI + imag[i + k + l / 2] * wR
                    real[i + k] = uR + vR
                    imag[i + k] = uI + vI
                    real[i + k + l / 2] = uR - vR
                    imag[i + k + l / 2] = uI - vI
                    val nextWR = wR * wlenR - wI * wlenI
                    val nextWI = wR * wlenI + wI * wlenR
                    wR = nextWR
                    wI = nextWI
                }
                i += l
            }
            l = l shl 1
        }
    }
}
