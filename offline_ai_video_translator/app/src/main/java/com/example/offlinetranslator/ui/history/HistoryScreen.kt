package com.example.offlinetranslator.ui.history

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.History
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.offlinetranslator.ui.components.AppTopBar
import com.example.offlinetranslator.ui.components.EmptyStateView
import com.example.offlinetranslator.ui.home.MediaListItem

@Composable
fun HistoryScreen(
    viewModel: HistoryViewModel,
    onNavigateBack: () -> Unit,
    onNavigateToPlayer: (String) -> Unit
) {
    val historyItems by viewModel.historyItems.collectAsState()

    Scaffold(
        topBar = {
            AppTopBar(
                title = "Translation History",
                canNavigateBack = true,
                onNavigateBack = onNavigateBack
            )
        }
    ) { innerPadding ->
        if (historyItems.isEmpty()) {
            EmptyStateView(
                icon = Icons.Default.History,
                title = "No Translation History",
                description = "Translated media and transcripts will automatically appear here.",
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
            )
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(historyItems) { item ->
                    MediaListItem(
                        media = item,
                        onClick = { onNavigateToPlayer(item.mediaHash) }
                    )
                }
            }
        }
    }
}
