package com.example.offlinetranslator.ui.player

import android.view.ViewGroup
import android.widget.FrameLayout
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.util.UnstableApi
import androidx.media3.ui.PlayerView
import com.example.offlinetranslator.ui.components.SubtitleOverlay
import com.example.offlinetranslator.ui.player.components.PlayerControls
import com.example.offlinetranslator.ui.player.components.TranslationControlSheet
import kotlinx.coroutines.delay

@UnstableApi
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MediaPlayerScreen(



    viewModel: MediaPlayerViewModel,
    onNavigateBack: () -> Unit,
    onNavigateToProcessing: (mediaHash: String, sourceLang: String, targetLang: String) -> Unit,
    onNavigateToSettings: () -> Unit
) {
    val context = LocalContext.current
    val mediaItem by viewModel.mediaItem.collectAsState()
    val isPlaying by viewModel.playerController.isPlaying.collectAsState()
    val isBuffering by viewModel.playerController.isBuffering.collectAsState()
    val currentPositionMs by viewModel.playerController.currentPosition.collectAsState()
    val durationMs by viewModel.playerController.duration.collectAsState()
    val playbackSpeed by viewModel.playerController.playbackSpeed.collectAsState()
    val activeSegment by viewModel.activeSegment.collectAsState()
    val subtitleMode by viewModel.subtitleMode.collectAsState()
    val sourceLang by viewModel.sourceLang.collectAsState()
    val targetLang by viewModel.targetLang.collectAsState()
    val isModelAvailable by viewModel.isModelAvailable.collectAsState()
    val userPreferences by viewModel.userPreferences.collectAsState()

    val isLiveTranslating by viewModel.isLiveTranslating.collectAsState()
    val liveTranslationMessage by viewModel.liveTranslationMessage.collectAsState()

    var controlsVisible by remember { mutableStateOf(true) }
    var isSheetOpen by remember { mutableStateOf(false) }
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    // Auto hide controls after 4 seconds when playing
    LaunchedEffect(controlsVisible, isPlaying) {
        if (controlsVisible && isPlaying) {
            delay(4000L)
            controlsVisible = false
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            viewModel.playerController.pause()
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            .clickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = null
            ) {
                controlsVisible = !controlsVisible
            }
    ) {
        // ExoPlayer Media3 View
        AndroidView(
            factory = { ctx ->
                PlayerView(ctx).apply {
                    player = viewModel.playerController.exoPlayer
                    useController = false // Custom Compose controls used
                    layoutParams = FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                    )
                }
            },
            modifier = Modifier.fillMaxSize()
        )

        // Subtitle Overlay
        SubtitleOverlay(
            activeSegment = activeSegment,
            mode = subtitleMode,
            fontSizeSp = userPreferences.subtitleFontSizeSp,
            highContrast = userPreferences.highContrastBackground,
            modifier = Modifier.align(Alignment.BottomCenter)
        )

        // Player Controls (Play, Seek, Scrubber, Title, Speed, Live Subtitle indicator)
        PlayerControls(
            isVisible = controlsVisible,
            title = mediaItem?.fileName ?: "Playing Media",
            isPlaying = isPlaying,
            isBuffering = isBuffering,
            currentPositionMs = currentPositionMs,
            durationMs = durationMs,
            playbackSpeed = playbackSpeed,
            subtitleMode = subtitleMode,
            isLiveTranslating = isLiveTranslating,
            liveTranslationMessage = liveTranslationMessage,
            targetLang = targetLang,
            onTogglePlayPause = { viewModel.playerController.togglePlayPause() },
            onSeek = { viewModel.playerController.seekTo(it) },
            onSeekForward = { viewModel.playerController.seekForward(10000L) },
            onSeekBackward = { viewModel.playerController.seekBackward(10000L) },
            onSpeedChange = { viewModel.playerController.setPlaybackSpeed(it) },
            onToggleSubtitleMode = {
                val modes = com.example.offlinetranslator.data.model.SubtitleDisplayMode.entries
                val nextIdx = (subtitleMode.ordinal + 1) % modes.size
                viewModel.setSubtitleMode(modes[nextIdx])
            },
            onOpenTranslationSheet = { isSheetOpen = true },
            onNavigateBack = onNavigateBack
        )

        // Translation Bottom Sheet
        if (isSheetOpen) {
            TranslationControlSheet(
                sheetState = sheetState,
                hasExistingTranslation = mediaItem?.hasTranslation == true,
                sourceLang = sourceLang,
                targetLang = targetLang,
                subtitleMode = subtitleMode,
                subtitleDelayMs = userPreferences.subtitleDelayMs,
                fontSizeSp = userPreferences.subtitleFontSizeSp,
                isModelAvailable = isModelAvailable,
                onSourceLangChange = { viewModel.setLanguages(it, targetLang) },
                onTargetLangChange = { viewModel.setLanguages(sourceLang, it) },
                onSubtitleModeChange = { viewModel.setSubtitleMode(it) },
                onSubtitleDelayChange = { /* handled in settings */ },
                onFontSizeChange = { /* handled in settings */ },
                onStartTranslation = {
                    isSheetOpen = false
                    viewModel.startLiveTranslation(sourceLang, targetLang)
                },
                onReprocessTranslation = {
                    isSheetOpen = false
                    viewModel.startLiveTranslation(sourceLang, targetLang)
                },
                onExportSrt = { viewModel.exportSubtitles(asVtt = false) },
                onExportVtt = { viewModel.exportSubtitles(asVtt = true) },
                onNavigateToSettings = {
                    isSheetOpen = false
                    onNavigateToSettings()
                },
                onDismiss = { isSheetOpen = false }
            )
        }
    }
}

