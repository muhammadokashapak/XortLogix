package com.example.offlinetranslator.ui.home

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Audiotrack
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Movie
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.PlayCircle
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.ScrollableTabRow
import androidx.compose.material3.Surface
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.offlinetranslator.data.model.MediaItem
import com.example.offlinetranslator.ui.components.EmptyStateView
import com.example.offlinetranslator.ui.theme.EmeraldSuccess
import com.example.offlinetranslator.ui.theme.Slate400
import com.example.offlinetranslator.ui.theme.VlcBackground
import com.example.offlinetranslator.ui.theme.VlcOrange
import com.example.offlinetranslator.ui.theme.VlcOrangeDark
import com.example.offlinetranslator.ui.theme.VlcSurface
import com.example.offlinetranslator.ui.theme.VlcSurfaceElevated
import com.example.offlinetranslator.utils.TimeUtils

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: HomeViewModel,
    onNavigateToPlayer: (String) -> Unit,
    onNavigateToHistory: () -> Unit,
    onNavigateToSettings: () -> Unit
) {
    val recentMedia by viewModel.recentMedia.collectAsState()
    val isSpeechReady by viewModel.isOfflineSpeechReady.collectAsState()
    var selectedTab by remember { mutableIntStateOf(0) }
    val tabs = listOf("All Media", "Video", "Audio", "AI Translated")

    // SAF File Picker
    val mediaPickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let { viewModel.onMediaSelected(it, isVideo = true, onNavigateToPlayer) }
    }

    Scaffold(
        containerColor = VlcBackground,
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(36.dp)
                                .clip(RoundedCornerShape(8.dp))
                                .background(VlcOrange),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.PlayArrow,
                                contentDescription = "VLC AI",
                                tint = Color.Black,
                                modifier = Modifier.size(24.dp)
                            )
                        }

                        Spacer(modifier = Modifier.width(10.dp))

                        Column {
                            Text(
                                text = "VLC AI Player",
                                style = MaterialTheme.typography.titleLarge,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                            Text(
                                text = "100% Offline AI Subtitles",
                                style = MaterialTheme.typography.bodySmall,
                                color = VlcOrange
                            )
                        }
                    }
                },
                actions = {
                    IconButton(onClick = onNavigateToHistory) {
                        Icon(
                            imageVector = Icons.Default.History,
                            contentDescription = "History",
                            tint = Color.White
                        )
                    }
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(
                            imageVector = Icons.Default.Settings,
                            contentDescription = "Settings",
                            tint = Color.White
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = VlcBackground
                )
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { mediaPickerLauncher.launch("*/*") },
                containerColor = VlcOrange,
                contentColor = Color.Black,
                shape = CircleShape
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(Icons.Default.Add, contentDescription = "Open")
                    Text("Open Media", fontWeight = FontWeight.Bold)
                }
            }
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            // Category Tabs
            ScrollableTabRow(
                selectedTabIndex = selectedTab,
                containerColor = VlcBackground,
                contentColor = VlcOrange,
                edgePadding = 16.dp,
                divider = {}
            ) {
                tabs.forEachIndexed { index, title ->
                    Tab(
                        selected = selectedTab == index,
                        onClick = { selectedTab = index },
                        text = {
                            Text(
                                text = title,
                                fontWeight = if (selectedTab == index) FontWeight.Bold else FontWeight.Normal,
                                color = if (selectedTab == index) VlcOrange else Slate400
                            )
                        }
                    )
                }
            }

            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // Offline AI Status Banner
                item {
                    VlcStatusBanner(
                        isReady = true,
                        onConfigureClick = onNavigateToSettings
                    )
                }

                // Filter items according to tab
                val filteredMedia = when (selectedTab) {
                    1 -> recentMedia.filter { it.isVideo }
                    2 -> recentMedia.filter { !it.isVideo }
                    3 -> recentMedia.filter { it.hasTranslation }
                    else -> recentMedia
                }

                if (filteredMedia.isEmpty()) {
                    item {
                        EmptyStateView(
                            icon = Icons.Default.PlayCircle,
                            title = "No Media Files Yet",
                            description = "Tap '+ Open Media' below to pick any video or audio file and play with live AI translated subtitles."
                        )
                    }
                } else {
                    items(filteredMedia) { media ->
                        VlcMediaCard(
                            media = media,
                            onClick = { onNavigateToPlayer(media.mediaHash) }
                        )
                    }
                }

                item {
                    Spacer(modifier = Modifier.height(72.dp))
                }
            }
        }
    }
}

@Composable
fun VlcStatusBanner(
    isReady: Boolean,
    onConfigureClick: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = VlcSurface,
        border = androidx.compose.foundation.BorderStroke(1.dp, VlcOrange.copy(alpha = 0.3f)),
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onConfigureClick() }
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

            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "100% Offline AI Ready",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(4.dp))
                            .background(EmeraldSuccess.copy(alpha = 0.2f))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text("PRE-INSTALLED", color = EmeraldSuccess, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                    }
                }
                Text(
                    text = "Whisper STT + MarianMT Translation are active. Zero setup required.",
                    style = MaterialTheme.typography.bodySmall,
                    color = Slate400
                )
            }
        }
    }
}

@Composable
fun VlcMediaCard(
    media: MediaItem,
    onClick: () -> Unit
) {
    var menuExpanded by remember { mutableStateOf(false) }

    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = VlcSurfaceElevated),
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() }
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(56.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(if (media.isVideo) VlcOrangeDark.copy(alpha = 0.3f) else VlcOrange.copy(alpha = 0.2f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = if (media.isVideo) Icons.Default.Movie else Icons.Default.Audiotrack,
                    contentDescription = null,
                    tint = VlcOrange,
                    modifier = Modifier.size(30.dp)
                )

                if (media.hasTranslation) {
                    Box(
                        modifier = Modifier
                            .align(Alignment.BottomEnd)
                            .padding(2.dp)
                            .clip(RoundedCornerShape(4.dp))
                            .background(Color.Black.copy(alpha = 0.8f))
                            .padding(horizontal = 4.dp, vertical = 1.dp)
                    ) {
                        Text("CC", color = VlcOrange, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }

            Spacer(modifier = Modifier.width(14.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = media.fileName,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.SemiBold,
                    color = Color.White,
                    maxLines = 1
                )

                Spacer(modifier = Modifier.height(4.dp))

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (media.durationMs > 0) {
                        Text(
                            text = TimeUtils.formatDuration(media.durationMs),
                            style = MaterialTheme.typography.bodySmall,
                            color = Slate400
                        )
                        Text("•", color = Slate400, fontSize = 10.sp)
                    }

                    if (media.hasTranslation) {
                        Text("•", color = Slate400, fontSize = 10.sp)
                        Text(
                            text = "${media.detectedLanguage ?: "Auto"} → ${media.targetLanguage ?: "ur"}",
                            style = MaterialTheme.typography.bodySmall,
                            color = EmeraldSuccess,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            // Quick Play button
            IconButton(onClick = onClick) {
                Icon(
                    imageVector = Icons.Default.PlayCircle,
                    contentDescription = "Play",
                    tint = VlcOrange,
                    modifier = Modifier.size(36.dp)
                )
            }
        }
    }
}


