package com.example.offlinetranslator.ui.processing

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.example.offlinetranslator.data.model.ProcessingState
import com.example.offlinetranslator.ui.components.AppTopBar
import com.example.offlinetranslator.ui.theme.EmeraldSuccess
import com.example.offlinetranslator.ui.theme.RoseError
import com.example.offlinetranslator.ui.theme.Slate400
import com.example.offlinetranslator.ui.theme.TealAccent

@Composable
fun ProcessingScreen(
    viewModel: ProcessingViewModel,
    onNavigateBack: () -> Unit,
    onNavigateToPlayer: (String) -> Unit
) {
    val mediaItem by viewModel.mediaItem.collectAsState()
    val state by viewModel.processingState.collectAsState()

    val progressValue = when (state) {
        is ProcessingState.PreparingAudio -> 0.15f
        is ProcessingState.DetectingSpeech -> 0.35f
        is ProcessingState.Transcribing -> {
            val s = state as ProcessingState.Transcribing
            0.35f + (s.progress * 0.35f)
        }
        is ProcessingState.Translating -> {
            val s = state as ProcessingState.Translating
            0.70f + (s.progress * 0.25f)
        }
        is ProcessingState.SyncingSubtitles -> 0.98f
        is ProcessingState.Completed -> 1.0f
        else -> 0f
    }

    val stageMessage = when (state) {
        is ProcessingState.PreparingAudio -> (state as ProcessingState.PreparingAudio).message
        is ProcessingState.DetectingSpeech -> (state as ProcessingState.DetectingSpeech).message
        is ProcessingState.Transcribing -> (state as ProcessingState.Transcribing).message
        is ProcessingState.Translating -> (state as ProcessingState.Translating).message
        is ProcessingState.SyncingSubtitles -> (state as ProcessingState.SyncingSubtitles).message
        is ProcessingState.Completed -> "Processing Complete!"
        is ProcessingState.Error -> (state as ProcessingState.Error).errorMessage
        is ProcessingState.Cancelled -> "Processing was cancelled."
        is ProcessingState.Idle -> "Initializing offline pipeline..."
    }

    Scaffold(
        topBar = {
            AppTopBar(
                title = "Offline AI Processing",
                canNavigateBack = true,
                onNavigateBack = {
                    viewModel.cancelProcessing()
                    onNavigateBack()
                }
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Header Info Card
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text(
                        text = mediaItem?.fileName ?: "Selected Media",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 2
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = MaterialTheme.colorScheme.surfaceVariant
                        ) {
                            Text(
                                text = "100% Offline",
                                style = MaterialTheme.typography.bodySmall,
                                color = EmeraldSuccess,
                                fontWeight = FontWeight.SemiBold,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                            )
                        }

                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = TealAccent.copy(alpha = 0.15f)
                        ) {
                            Text(
                                text = "On-Device Neural Engine",
                                style = MaterialTheme.typography.bodySmall,
                                color = TealAccent,
                                fontWeight = FontWeight.Medium,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                            )
                        }
                    }
                }
            }

            // Progress Display Area
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.fillMaxWidth()
            ) {
                when (state) {
                    is ProcessingState.Completed -> {
                        Box(
                            modifier = Modifier
                                .size(88.dp)
                                .clip(CircleShape)
                                .background(EmeraldSuccess.copy(alpha = 0.2f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.CheckCircle,
                                contentDescription = null,
                                tint = EmeraldSuccess,
                                modifier = Modifier.size(54.dp)
                            )
                        }
                    }
                    is ProcessingState.Error -> {
                        Box(
                            modifier = Modifier
                                .size(88.dp)
                                .clip(CircleShape)
                                .background(RoseError.copy(alpha = 0.2f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.Error,
                                contentDescription = null,
                                tint = RoseError,
                                modifier = Modifier.size(54.dp)
                            )
                        }
                    }
                    else -> {
                        CircularProgressIndicator(
                            progress = { progressValue },
                            modifier = Modifier.size(88.dp),
                            color = com.example.offlinetranslator.ui.theme.VlcOrange,
                            strokeWidth = 6.dp
                        )
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))

                Text(
                    text = "${(progressValue * 100).toInt()}%",
                    style = MaterialTheme.typography.headlineLarge,
                    fontWeight = FontWeight.Bold,
                    color = com.example.offlinetranslator.ui.theme.VlcOrange
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = stageMessage,
                    style = MaterialTheme.typography.bodyLarge,
                    color = if (state is ProcessingState.Error) RoseError else Slate400,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.padding(horizontal = 16.dp)
                )

                Spacer(modifier = Modifier.height(16.dp))

                LinearProgressIndicator(
                    progress = { progressValue },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                        .clip(RoundedCornerShape(4.dp)),
                    color = com.example.offlinetranslator.ui.theme.VlcOrange,
                    trackColor = MaterialTheme.colorScheme.surfaceVariant
                )
            }

            // Bottom Actions
            Column(modifier = Modifier.fillMaxWidth()) {
                if (state is ProcessingState.Completed) {
                    val completedState = state as ProcessingState.Completed
                    Button(
                        onClick = { onNavigateToPlayer(completedState.mediaHash) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = com.example.offlinetranslator.ui.theme.VlcOrange)
                    ) {
                        Icon(imageVector = Icons.Default.PlayArrow, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Play with Subtitles (${completedState.segmentsCount} Segments)",
                            fontWeight = FontWeight.Bold
                        )
                    }
                } else if (state is ProcessingState.Error || state is ProcessingState.Cancelled) {
                    Button(
                        onClick = onNavigateBack,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp)
                    ) {
                        Text("Return to Media")
                    }
                } else {
                    OutlinedButton(
                        onClick = {
                            viewModel.cancelProcessing()
                            onNavigateBack()
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp)
                    ) {
                        Icon(imageVector = Icons.Default.Close, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Cancel Processing")
                    }
                }
            }
        }
    }
}
