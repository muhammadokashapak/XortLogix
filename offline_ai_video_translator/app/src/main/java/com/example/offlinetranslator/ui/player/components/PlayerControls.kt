package com.example.offlinetranslator.ui.player.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
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
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.AspectRatio
import androidx.compose.material.icons.filled.ClosedCaption
import androidx.compose.material.icons.filled.ClosedCaptionDisabled
import androidx.compose.material.icons.filled.Forward10
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.LockOpen
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Replay10
import androidx.compose.material.icons.filled.Speed
import androidx.compose.material.icons.filled.Translate
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.offlinetranslator.data.model.SubtitleDisplayMode
import com.example.offlinetranslator.ui.theme.VlcOrange
import com.example.offlinetranslator.utils.TimeUtils

@Composable
fun PlayerControls(
    isVisible: Boolean,
    title: String,
    isPlaying: Boolean,
    isBuffering: Boolean,
    currentPositionMs: Long,
    durationMs: Long,
    playbackSpeed: Float,
    subtitleMode: SubtitleDisplayMode,
    onTogglePlayPause: () -> Unit,
    onSeek: (Long) -> Unit,
    onSeekForward: () -> Unit,
    onSeekBackward: () -> Unit,
    onSpeedChange: (Float) -> Unit,
    onToggleSubtitleMode: () -> Unit,
    onOpenTranslationSheet: () -> Unit,
    onNavigateBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    var speedMenuExpanded by remember { mutableStateOf(false) }
    var isLocked by remember { mutableStateOf(false) }
    var aspectMode by remember { mutableStateOf("FIT") }

    // Double tap feedback
    var showRewindAnim by remember { mutableStateOf(false) }
    var showForwardAnim by remember { mutableStateOf(false) }

    Box(
        modifier = modifier
            .fillMaxSize()
            .pointerInput(Unit) {
                detectTapGestures(
                    onDoubleTap = { offset ->
                        if (offset.x < size.width / 2) {
                            onSeekBackward()
                            showRewindAnim = true
                        } else {
                            onSeekForward()
                            showForwardAnim = true
                        }
                    }
                )
            }
    ) {
        // Quick Jump Feedback animations
        if (showRewindAnim) {
            Box(
                modifier = Modifier
                    .align(Alignment.CenterStart)
                    .padding(start = 48.dp)
                    .size(80.dp)
                    .clip(CircleShape)
                    .background(Color.Black.copy(alpha = 0.6f)),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(Icons.Default.Replay10, contentDescription = "-10s", tint = VlcOrange, modifier = Modifier.size(36.dp))
                    Text("-10s", color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
            androidx.compose.runtime.LaunchedEffect(showRewindAnim) {
                kotlinx.coroutines.delay(650)
                showRewindAnim = false
            }
        }

        if (showForwardAnim) {
            Box(
                modifier = Modifier
                    .align(Alignment.CenterEnd)
                    .padding(end = 48.dp)
                    .size(80.dp)
                    .clip(CircleShape)
                    .background(Color.Black.copy(alpha = 0.6f)),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(Icons.Default.Forward10, contentDescription = "+10s", tint = VlcOrange, modifier = Modifier.size(36.dp))
                    Text("+10s", color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
            androidx.compose.runtime.LaunchedEffect(showForwardAnim) {
                kotlinx.coroutines.delay(650)
                showForwardAnim = false
            }
        }

        // Lock button when locked
        if (isLocked) {
            IconButton(
                onClick = { isLocked = false },
                modifier = Modifier
                    .align(Alignment.CenterStart)
                    .padding(16.dp)
                    .size(48.dp)
                    .clip(CircleShape)
                    .background(Color.Black.copy(alpha = 0.7f))
            ) {
                Icon(Icons.Default.Lock, contentDescription = "Unlock", tint = VlcOrange)
            }
            return@Box
        }

        // Normal HUD Controls
        AnimatedVisibility(
            visible = isVisible,
            enter = fadeIn(),
            exit = fadeOut(),
            modifier = Modifier.fillMaxSize()
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(
                        Brush.verticalGradient(
                            colors = listOf(
                                Color.Black.copy(alpha = 0.75f),
                                Color.Transparent,
                                Color.Black.copy(alpha = 0.85f)
                            )
                        )
                    )
            ) {
                // ================= TOP BAR =================
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .align(Alignment.TopCenter)
                        .padding(horizontal = 12.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                            tint = Color.White
                        )
                    }

                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .padding(horizontal = 8.dp)
                    ) {
                        Text(
                            text = title,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color.White,
                            maxLines = 1
                        )
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(4.dp))
                                    .background(VlcOrange.copy(alpha = 0.2f))
                                    .padding(horizontal = 6.dp, vertical = 2.dp)
                            ) {
                                Text(
                                    text = "VLC AI PLAYER",
                                    color = VlcOrange,
                                    fontSize = 9.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = "Live Subtitles Active",
                                color = Color.White.copy(alpha = 0.7f),
                                fontSize = 11.sp
                            )
                        }
                    }

                    // Aspect Ratio Button
                    IconButton(onClick = {
                        aspectMode = when (aspectMode) {
                            "FIT" -> "FILL"
                            "FILL" -> "16:9"
                            "16:9" -> "4:3"
                            else -> "FIT"
                        }
                    }) {
                        Icon(
                            imageVector = Icons.Default.AspectRatio,
                            contentDescription = "Aspect Ratio",
                            tint = Color.White
                        )
                    }

                    // Subtitle CC Button
                    IconButton(onClick = onToggleSubtitleMode) {
                        Icon(
                            imageVector = if (subtitleMode != SubtitleDisplayMode.OFF) Icons.Default.ClosedCaption else Icons.Default.ClosedCaptionDisabled,
                            contentDescription = "Subtitles",
                            tint = if (subtitleMode != SubtitleDisplayMode.OFF) VlcOrange else Color.White.copy(alpha = 0.6f)
                        )
                    }

                    // Translation AI Sheet
                    IconButton(onClick = onOpenTranslationSheet) {
                        Icon(
                            imageVector = Icons.Default.Translate,
                            contentDescription = "Translate",
                            tint = VlcOrange
                        )
                    }

                    // Lock Button
                    IconButton(onClick = { isLocked = true }) {
                        Icon(
                            imageVector = Icons.Default.LockOpen,
                            contentDescription = "Lock Screen",
                            tint = Color.White.copy(alpha = 0.7f)
                        )
                    }
                }

                // ================= CENTER PLAY/PAUSE & BUFF =================
                Box(
                    modifier = Modifier.align(Alignment.Center),
                    contentAlignment = Alignment.Center
                ) {
                    if (isBuffering) {
                        CircularProgressIndicator(
                            color = VlcOrange,
                            modifier = Modifier.size(56.dp),
                            strokeWidth = 4.dp
                        )
                    } else {
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(24.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // Jump -10s
                            IconButton(
                                onClick = onSeekBackward,
                                modifier = Modifier
                                    .size(48.dp)
                                    .clip(CircleShape)
                                    .background(Color.White.copy(alpha = 0.15f))
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Replay10,
                                    contentDescription = "Rewind 10s",
                                    tint = Color.White,
                                    modifier = Modifier.size(28.dp)
                                )
                            }

                            // Big Center Play/Pause in VLC Orange
                            Surface(
                                onClick = onTogglePlayPause,
                                shape = CircleShape,
                                color = VlcOrange,
                                shadowElevation = 8.dp,
                                modifier = Modifier.size(68.dp)
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(
                                        imageVector = if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                                        contentDescription = if (isPlaying) "Pause" else "Play",
                                        tint = Color.Black,
                                        modifier = Modifier.size(40.dp)
                                    )
                                }
                            }

                            // Jump +10s
                            IconButton(
                                onClick = onSeekForward,
                                modifier = Modifier
                                    .size(48.dp)
                                    .clip(CircleShape)
                                    .background(Color.White.copy(alpha = 0.15f))
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Forward10,
                                    contentDescription = "Forward 10s",
                                    tint = Color.White,
                                    modifier = Modifier.size(28.dp)
                                )
                            }
                        }
                    }
                }

                // ================= BOTTOM BAR (VLC Style) =================
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .align(Alignment.BottomCenter)
                        .padding(horizontal = 16.dp, vertical = 12.dp)
                ) {
                    // Time Labels & Slider
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = TimeUtils.formatDuration(currentPositionMs),
                            color = Color.White,
                            fontSize = 12.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Medium
                        )

                        Text(
                            text = "-${TimeUtils.formatDuration((durationMs - currentPositionMs).coerceAtLeast(0L))}",
                            color = Color.White.copy(alpha = 0.8f),
                            fontSize = 12.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Medium
                        )
                    }

                    // Scrubber Slider
                    Slider(
                        value = if (durationMs > 0) currentPositionMs.toFloat() / durationMs.toFloat() else 0f,
                        onValueChange = { frac ->
                            val targetMs = (frac * durationMs).toLong()
                            onSeek(targetMs)
                        },
                        colors = SliderDefaults.colors(
                            thumbColor = VlcOrange,
                            activeTrackColor = VlcOrange,
                            inactiveTrackColor = Color.White.copy(alpha = 0.25f)
                        ),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(24.dp)
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    // Bottom Quick Actions Bar (Speed, Subtitle Mode, Aspect Ratio, Sheet)
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // Subtitle Mode Quick Pill
                        Surface(
                            onClick = onToggleSubtitleMode,
                            shape = RoundedCornerShape(20.dp),
                            color = if (subtitleMode != SubtitleDisplayMode.OFF) VlcOrange.copy(alpha = 0.25f) else Color.White.copy(alpha = 0.12f),
                            border = androidx.compose.foundation.BorderStroke(
                                1.dp,
                                if (subtitleMode != SubtitleDisplayMode.OFF) VlcOrange else Color.White.copy(alpha = 0.2f)
                            )
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(4.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.ClosedCaption,
                                    contentDescription = null,
                                    tint = if (subtitleMode != SubtitleDisplayMode.OFF) VlcOrange else Color.White,
                                    modifier = Modifier.size(16.dp)
                                )
                                Text(
                                    text = subtitleMode.name,
                                    color = if (subtitleMode != SubtitleDisplayMode.OFF) VlcOrange else Color.White,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }

                        // Speed Selector Pill
                        Box {
                            Surface(
                                onClick = { speedMenuExpanded = true },
                                shape = RoundedCornerShape(20.dp),
                                color = Color.White.copy(alpha = 0.12f),
                                border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.2f))
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Speed,
                                        contentDescription = null,
                                        tint = Color.White,
                                        modifier = Modifier.size(16.dp)
                                    )
                                    Text(
                                        text = "${playbackSpeed}x",
                                        color = Color.White,
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                            }

                            DropdownMenu(
                                expanded = speedMenuExpanded,
                                onDismissRequest = { speedMenuExpanded = false }
                            ) {
                                listOf(0.5f, 0.75f, 1.0f, 1.25f, 1.5f, 2.0f).forEach { speed ->
                                    DropdownMenuItem(
                                        text = { Text("${speed}x", color = if (speed == playbackSpeed) VlcOrange else Color.Unspecified) },
                                        onClick = {
                                            onSpeedChange(speed)
                                            speedMenuExpanded = false
                                        }
                                    )
                                }
                            }
                        }

                        // Aspect Ratio Mode Pill
                        Surface(
                            onClick = {
                                aspectMode = when (aspectMode) {
                                    "FIT" -> "FILL"
                                    "FILL" -> "16:9"
                                    "16:9" -> "4:3"
                                    else -> "FIT"
                                }
                            },
                            shape = RoundedCornerShape(20.dp),
                            color = Color.White.copy(alpha = 0.12f),
                            border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.2f))
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(4.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.AspectRatio,
                                    contentDescription = null,
                                    tint = Color.White,
                                    modifier = Modifier.size(16.dp)
                                )
                                Text(
                                    text = aspectMode,
                                    color = Color.White,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }

                        // AI Translation Panel Button
                        Surface(
                            onClick = onOpenTranslationSheet,
                            shape = RoundedCornerShape(20.dp),
                            color = VlcOrange,
                            shadowElevation = 4.dp
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(4.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Translate,
                                    contentDescription = null,
                                    tint = Color.Black,
                                    modifier = Modifier.size(16.dp)
                                )
                                Text(
                                    text = "Translate",
                                    color = Color.Black,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}
