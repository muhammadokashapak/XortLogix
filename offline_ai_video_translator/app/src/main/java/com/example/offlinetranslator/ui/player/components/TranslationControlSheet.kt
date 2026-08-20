package com.example.offlinetranslator.ui.player.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Translate
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.SheetState
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.offlinetranslator.data.model.SubtitleDisplayMode
import com.example.offlinetranslator.ui.components.LanguageSelectorDropdown
import com.example.offlinetranslator.ui.theme.EmeraldSuccess
import com.example.offlinetranslator.ui.theme.RoseError
import com.example.offlinetranslator.ui.theme.Slate400
import com.example.offlinetranslator.ui.theme.VlcOrange
import com.example.offlinetranslator.ui.theme.VlcSurfaceElevated


@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TranslationControlSheet(
    sheetState: SheetState,
    hasExistingTranslation: Boolean,
    sourceLang: String,
    targetLang: String,
    subtitleMode: SubtitleDisplayMode,
    subtitleDelayMs: Long,
    fontSizeSp: Float,
    isModelAvailable: Boolean,
    onSourceLangChange: (String) -> Unit,
    onTargetLangChange: (String) -> Unit,
    onSubtitleModeChange: (SubtitleDisplayMode) -> Unit,
    onSubtitleDelayChange: (Long) -> Unit,
    onFontSizeChange: (Float) -> Unit,
    onStartTranslation: () -> Unit,
    onReprocessTranslation: () -> Unit,
    onExportSrt: () -> Unit,
    onExportVtt: () -> Unit,
    onNavigateToSettings: () -> Unit,
    onDismiss: () -> Unit
) {
    val sourceLanguages = listOf(
        "auto" to "Auto Detect",
        "en" to "English",
        "zh" to "Chinese (中文)",
        "ja" to "Japanese (日本語)",
        "ur" to "Urdu (اردو)",
        "es" to "Spanish (Español)",
        "ar" to "Arabic (العربية)",
        "hi" to "Hindi (हिन्दी)",
        "fr" to "French (Français)",
        "de" to "German (Deutsch)",
        "ru" to "Russian (Русский)",
        "tr" to "Turkish (Türkçe)"
    )

    val targetLanguages = listOf(
        "ur" to "Urdu (اردو)",
        "en" to "English",
        "es" to "Spanish (Español)",
        "zh" to "Chinese (中文)",
        "ja" to "Japanese (日本語)",
        "ar" to "Arabic (العربية)",
        "hi" to "Hindi (हिन्दी)",
        "fr" to "French (Français)",
        "de" to "German (Deutsch)",
        "ru" to "Russian (Русский)",
        "tr" to "Turkish (Türkçe)"
    )

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = VlcSurfaceElevated
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 8.dp)

        ) {
            Text(
                text = "Translation & Subtitles",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Language Selectors
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                LanguageSelectorDropdown(
                    label = "Source",
                    selectedCode = sourceLang,
                    languageOptions = sourceLanguages,
                    onLanguageSelected = onSourceLangChange,
                    modifier = Modifier.weight(1f)
                )

                LanguageSelectorDropdown(
                    label = "Translate To",
                    selectedCode = targetLang,
                    languageOptions = targetLanguages,
                    onLanguageSelected = onTargetLangChange,
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Model Availability Status
            if (!isModelAvailable) {
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = RoseError.copy(alpha = 0.15f),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.Warning,
                            contentDescription = null,
                            tint = RoseError
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Required model not installed",
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.SemiBold,
                                color = RoseError
                            )
                            Text(
                                text = "Install speech or $sourceLang->$targetLang translation pack.",
                                style = MaterialTheme.typography.bodySmall,
                                color = Slate400
                            )
                        }
                        OutlinedButton(onClick = onNavigateToSettings) {
                            Text("Setup", color = RoseError)
                        }
                    }
                }
                Spacer(modifier = Modifier.height(16.dp))
            }

            // Subtitle Display Modes
            Text(
                text = "Display Mode",
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                SubtitleDisplayMode.entries.forEach { mode ->
                    FilterChip(
                        selected = subtitleMode == mode,
                        onClick = { onSubtitleModeChange(mode) },
                        label = { Text(mode.label) }
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Action Buttons
            if (hasExistingTranslation) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Button(
                        onClick = onDismiss,
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = com.example.offlinetranslator.ui.theme.VlcOrange,
                            contentColor = androidx.compose.ui.graphics.Color.Black
                        )
                    ) {
                        Icon(imageVector = Icons.Default.PlayArrow, contentDescription = null)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Play With Subtitles", fontWeight = FontWeight.Bold)
                    }

                    OutlinedButton(
                        onClick = onReprocessTranslation,
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(imageVector = Icons.Default.Refresh, contentDescription = null)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Reprocess")
                    }
                }
            } else {
                Button(
                    onClick = onStartTranslation,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = com.example.offlinetranslator.ui.theme.VlcOrange,
                        contentColor = androidx.compose.ui.graphics.Color.Black
                    )
                ) {
                    Icon(imageVector = Icons.Default.Translate, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Start Live AI Translation", fontWeight = FontWeight.Bold)
                }
            }


            // Subtitle Export Actions
            if (hasExistingTranslation) {
                Spacer(modifier = Modifier.height(12.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedButton(
                        onClick = onExportSrt,
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(imageVector = Icons.Default.Download, contentDescription = null)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Export SRT")
                    }

                    OutlinedButton(
                        onClick = onExportVtt,
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(imageVector = Icons.Default.Download, contentDescription = null)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Export VTT")
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}
