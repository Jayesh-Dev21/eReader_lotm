package com.reader.lotm.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.reader.lotm.data.models.ReadingMode
import com.reader.lotm.ui.components.ContinuousReader
import com.reader.lotm.ui.components.PaginatedReader
import com.reader.lotm.ui.components.ProgressIndicator
import com.reader.lotm.ui.components.ReadingControls
import com.reader.lotm.ui.viewmodels.ReaderUiState
import com.reader.lotm.ui.viewmodels.ReaderViewModel
import com.reader.lotm.utils.TapZone

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReaderScreen(
    viewModel: ReaderViewModel,
    onBackClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()
    val showControls by viewModel.showControls.collectAsState()
    val readingMode by viewModel.readingMode.collectAsState()
    val fontSize by viewModel.fontSize.collectAsState()
    val fontFamily by viewModel.fontFamily.collectAsState()
    val pageNumber by viewModel.pageNumber.collectAsState()
    val gestureNavigationEnabled by viewModel.gestureNavigationEnabled.collectAsState()
    
    Scaffold(
        topBar = {
            AnimatedVisibility(
                visible = showControls,
                enter = slideInVertically(initialOffsetY = { -it }),
                exit = slideOutVertically(targetOffsetY = { -it })
            ) {
                TopAppBar(
                    title = { 
                        when (val state = uiState) {
                            is ReaderUiState.Success -> Text(state.chapter.title, maxLines = 1)
                            else -> Text("Reader")
                        }
                    },
                    navigationIcon = {
                        IconButton(onClick = onBackClick) {
                            Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                        }
                    },
                    actions = {
                        IconButton(onClick = { viewModel.toggleControls() }) {
                            Icon(Icons.Default.Menu, contentDescription = "Toggle controls")
                        }
                    }
                )
            }
        },
        bottomBar = {
            AnimatedVisibility(
                visible = showControls,
                enter = slideInVertically(initialOffsetY = { it }),
                exit = slideOutVertically(targetOffsetY = { it })
            ) {
                Column {
                    when (val state = uiState) {
                        is ReaderUiState.Success -> {
                            ProgressIndicator(
                                currentChapter = (state.chapter.orderIndex ?: state.chapter.id) + 1,
                                totalChapters = state.totalChapters,
                                currentPage = if (readingMode == ReadingMode.PAGINATED) pageNumber else null,
                                totalPages = null
                            )
                        }
                        else -> {}
                    }
                    
                    ReadingControls(
                        fontSize = fontSize,
                        fontFamily = fontFamily,
                        readingMode = readingMode,
                        onFontSizeChange = { viewModel.updateFontSize(it) },
                        onFontFamilyChange = { viewModel.updateFontFamily(it) },
                        onReadingModeChange = { viewModel.updateReadingMode(it) }
                    )
                }
            }
        }
    ) { paddingValues ->
        Box(
            modifier = modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            when (val state = uiState) {
                is ReaderUiState.Loading -> {
                    CircularProgressIndicator(
                        modifier = Modifier.align(Alignment.Center)
                    )
                }
                
                is ReaderUiState.Success -> {
                    when (readingMode) {
                        ReadingMode.CONTINUOUS_SCROLL -> {
                            ContinuousReader(
                                chapter = state.chapter,
                                fontSize = fontSize,
                                fontFamily = fontFamily,
                                gestureNavigationEnabled = gestureNavigationEnabled,
                                onScrollOffsetChange = { viewModel.updateScrollOffset(it) },
                                onTapZone = { zone ->
                                    when (zone) {
                                        TapZone.LEFT -> if (gestureNavigationEnabled && state.hasPrevious) {
                                            viewModel.loadPreviousChapter()
                                        }
                                        TapZone.CENTER -> viewModel.toggleControls()
                                        TapZone.RIGHT -> if (gestureNavigationEnabled && state.hasNext) {
                                            viewModel.loadNextChapter()
                                        }
                                    }
                                },
                                onLoadNextChapter = {
                                    if (state.hasNext) {
                                        viewModel.loadNextChapter()
                                    }
                                }
                            )
                        }
                        
                        ReadingMode.PAGINATED -> {
                            PaginatedReader(
                                chapter = state.chapter,
                                fontSize = fontSize,
                                fontFamily = fontFamily,
                                initialPage = pageNumber,
                                gestureNavigationEnabled = gestureNavigationEnabled,
                                onPageChange = { viewModel.updatePageNumber(it) },
                                onTapZone = { zone ->
                                    when (zone) {
                                        TapZone.LEFT -> if (gestureNavigationEnabled && state.hasPrevious) {
                                            viewModel.loadPreviousChapter()
                                        }
                                        TapZone.CENTER -> viewModel.toggleControls()
                                        TapZone.RIGHT -> if (gestureNavigationEnabled && state.hasNext) {
                                            viewModel.loadNextChapter()
                                        }
                                    }
                                },
                                onLoadNextChapter = {
                                    if (state.hasNext) {
                                        viewModel.loadNextChapter()
                                    }
                                },
                                onLoadPreviousChapter = {
                                    if (state.hasPrevious) {
                                        viewModel.loadPreviousChapter()
                                    }
                                }
                            )
                        }
                    }
                }
                
                is ReaderUiState.Error -> {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(32.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = "Error: ${state.message}",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.error
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(onClick = onBackClick) {
                            Text("Go Back")
                        }
                    }
                }
            }
        }
    }
}
