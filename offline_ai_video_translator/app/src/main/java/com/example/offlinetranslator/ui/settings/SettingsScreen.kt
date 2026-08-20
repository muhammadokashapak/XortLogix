package com.example.offlinetranslator.ui.settings

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.offlinetranslator.ai.model.ModelType
import com.example.offlinetranslator.ui.components.AppTopBar
import com.example.offlinetranslator.ui.components.ModelStatusCard
import com.example.offlinetranslator.ui.theme.EmeraldSuccess
import com.example.offlinetranslator.ui.theme.Slate400
import com.example.offlinetranslator.ui.theme.VlcBackground
import com.example.offlinetranslator.ui.theme.VlcOrange
import com.example.offlinetranslator.ui.theme.VlcSurface
import com.example.offlinetranslator.ui.theme.VlcSurfaceElevated

@Composable
fun SettingsScreen(
    viewModel: SettingsViewModel,
    onNavigateBack: () -> Unit
) {
    val prefs by viewModel.userPreferences.collectAsState()
    val models by viewModel.installedModels.collectAsState()

    var selectedModelTypeToImport by remember { mutableStateOf<ModelType?>(null) }

    val modelFilePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let { sourceUri ->
            selectedModelTypeToImport?.let { type ->
                viewModel.importModelFile(sourceUri, type)
            }
        }

    }

    Scaffold(
        containerColor = VlcBackground,
        topBar = {
            AppTopBar(
                title = "Settings & AI Models",
                canNavigateBack = true,
                onNavigateBack = onNavigateBack,
                actions = {
                    IconButton(onClick = { viewModel.refreshModels() }) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Refresh Models",
                            tint = Color.White
                        )
                    }
                }
            )
        }
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Section 1: Subtitle Appearance
            item {
                Text(
                    text = "Subtitle Appearance",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = VlcOrange
                )
            }

            item {
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = VlcSurfaceElevated),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = "Font Size (${prefs.subtitleFontSizeSp.toInt()} sp)",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.SemiBold,
                            color = Color.White
                        )
                        Slider(
                            value = prefs.subtitleFontSizeSp,
                            onValueChange = { viewModel.updateSubtitleFontSize(it) },
                            valueRange = 12f..32f,
                            steps = 9,
                            colors = SliderDefaults.colors(
                                thumbColor = VlcOrange,
                                activeTrackColor = VlcOrange
                            )
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text(
                                    text = "High-Contrast Subtitle Box",
                                    style = MaterialTheme.typography.bodyMedium,
                                    fontWeight = FontWeight.SemiBold,
                                    color = Color.White
                                )
                                Text(
                                    text = "Dark translucent box behind subtitles for readability",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = Slate400
                                )
                            }
                            Switch(
                                checked = prefs.highContrastBackground,
                                onCheckedChange = { viewModel.updateHighContrast(it) },
                                colors = SwitchDefaults.colors(
                                    checkedThumbColor = Color.Black,
                                    checkedTrackColor = VlcOrange
                                )
                            )
                        }
                    }
                }
            }

            // Section 2: Active AI Models
            item {
                Text(
                    text = "Active On-Device AI Models",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = VlcOrange
                )
            }

            item {
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = VlcSurface,
                    border = androidx.compose.foundation.BorderStroke(1.dp, EmeraldSuccess.copy(alpha = 0.3f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(14.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.CheckCircle,
                            contentDescription = null,
                            tint = EmeraldSuccess,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                text = "100% Pre-Installed & Ready",
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = "Whisper STT (99+ Languages) and Neural Translation are pre-bundled. Zero cloud setup needed.",
                                style = MaterialTheme.typography.bodySmall,
                                color = Slate400
                            )
                        }
                    }
                }
            }

            // Active Installed Models List
            items(models) { modelInfo ->
                ModelStatusCard(
                    modelInfo = modelInfo,
                    onDeleteClick = { viewModel.deleteModel(modelInfo) }
                )
            }

            // Optional Language Packs Section
            item {
                Spacer(modifier = Modifier.height(8.dp))
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = VlcSurface),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.1f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = "Add More Languages (Optional)",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "English to Urdu is pre-installed. You can optionally import extra MarianMT language packs (.onnx) anytime.",
                            style = MaterialTheme.typography.bodySmall,
                            color = Slate400
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        OutlinedButton(
                            onClick = {
                                selectedModelTypeToImport = ModelType.TRANSLATION
                                modelFilePicker.launch("*/*")
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.Default.Add, contentDescription = null, tint = VlcOrange)
                            Spacer(modifier = Modifier.width(6.dp))
                            Text("Import Extra Language Model (.onnx)", color = Color.White)
                        }
                    }
                }
            }
        }
    }
}
