package com.example.offlinetranslator.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.offlinetranslator.data.model.SubtitleDisplayMode
import com.example.offlinetranslator.data.model.TranscriptSegment

@Composable
fun SubtitleOverlay(
    activeSegment: TranscriptSegment?,
    mode: SubtitleDisplayMode,
    fontSizeSp: Float = 18f,
    highContrast: Boolean = true,
    modifier: Modifier = Modifier
) {
    if (mode == SubtitleDisplayMode.OFF || activeSegment == null) return

    val originalText = activeSegment.originalText.trim()
    val translatedText = activeSegment.translatedText?.trim()

    val showOriginal = (mode == SubtitleDisplayMode.ORIGINAL || mode == SubtitleDisplayMode.BOTH) && originalText.isNotEmpty()
    val showTranslation = (mode == SubtitleDisplayMode.TRANSLATION || mode == SubtitleDisplayMode.BOTH) && !translatedText.isNullOrEmpty()

    AnimatedVisibility(
        visible = showOriginal || showTranslation,
        enter = fadeIn(),
        exit = fadeOut(),
        modifier = modifier
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 32.dp),
            contentAlignment = Alignment.BottomCenter
        ) {
            Box(
                modifier = Modifier
                    .background(
                        color = if (highContrast) Color.Black.copy(alpha = 0.82f) else Color.Black.copy(alpha = 0.50f),
                        shape = RoundedCornerShape(10.dp)
                    )
                    .padding(horizontal = 16.dp, vertical = 8.dp)
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    if (showOriginal) {
                        Text(
                            text = originalText,
                            color = if (showTranslation) Color(0xFFE2E8F0) else Color.White,
                            fontSize = (if (showTranslation) fontSizeSp * 0.85f else fontSizeSp).sp,
                            fontWeight = if (showTranslation) FontWeight.Normal else FontWeight.Medium,
                            textAlign = TextAlign.Center,
                            lineHeight = ((if (showTranslation) fontSizeSp * 0.85f else fontSizeSp) * 1.25f).sp
                        )
                    }

                    if (showOriginal && showTranslation) {
                        Spacer(modifier = Modifier.height(4.dp))
                    }

                    if (showTranslation && translatedText != null) {
                        Text(
                            text = translatedText,
                            color = Color(0xFF5EEAD4), // Teal highlight for translated text
                            fontSize = (fontSizeSp * 1.05f).sp,
                            fontWeight = FontWeight.SemiBold,
                            textAlign = TextAlign.Center,
                            lineHeight = (fontSizeSp * 1.35f).sp
                        )
                    }
                }
            }
        }
    }
}
