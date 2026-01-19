package com.reader.lotm.ui.components

import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.Divider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.reader.lotm.data.local.ChapterEntity
import com.reader.lotm.utils.TapZone

@Composable
fun ContinuousReader(
    chapter: ChapterEntity,
    fontSize: Float,
    fontFamily: String,
    gestureNavigationEnabled: Boolean,
    onScrollOffsetChange: (Float) -> Unit,
    onTapZone: (TapZone) -> Unit,
    onLoadNextChapter: () -> Unit,
    modifier: Modifier = Modifier
) {
    val listState = rememberLazyListState()
    
    // Parse paragraphs - split by double newlines and filter blanks
    val paragraphs = remember(chapter.content) {
        chapter.content?.split(Regex("\n\n+"))
            ?.map { it.trim() }
            ?.filter { it.isNotBlank() }
            ?: emptyList()
    }
    
    // Track scroll position
    LaunchedEffect(listState.firstVisibleItemScrollOffset) {
        val offset = listState.firstVisibleItemIndex * 1000f + listState.firstVisibleItemScrollOffset
        onScrollOffsetChange(offset)
    }
    
    // Auto-load next chapter when near end
    LaunchedEffect(listState.layoutInfo) {
        val lastVisibleItem = listState.layoutInfo.visibleItemsInfo.lastOrNull()
        if (lastVisibleItem != null && lastVisibleItem.index >= paragraphs.size - 1) {
            onLoadNextChapter()
        }
    }
    
    val fontFamilyValue = when (fontFamily) {
        "Sans-serif" -> FontFamily.SansSerif
        "Monospace" -> FontFamily.Monospace
        else -> FontFamily.Serif
    }
    
    val density = LocalDensity.current
    
    Box(
        modifier = modifier
            .fillMaxSize()
            .then(
                if (gestureNavigationEnabled) {
                    Modifier.pointerInput(Unit) {
                        detectTapGestures { offset ->
                            val screenWidth = size.width
                            val screenHeight = size.height
                            
                            val zone = when {
                                offset.y < screenHeight * 0.3f -> TapZone.CENTER  // Top tap
                                offset.y > screenHeight * 0.7f -> TapZone.CENTER  // Bottom tap
                                offset.x < screenWidth * 0.3f -> TapZone.LEFT
                                offset.x > screenWidth * 0.7f -> TapZone.RIGHT
                                else -> TapZone.CENTER
                            }
                            
                            onTapZone(zone)
                        }
                    }
                } else {
                    Modifier
                }
            )
    ) {
        LazyColumn(
            state = listState,
            contentPadding = PaddingValues(
                horizontal = 20.dp,
                vertical = 40.dp
            ),
            modifier = Modifier.fillMaxSize()
        ) {
            // Chapter title
            item {
                Text(
                    text = chapter.title,
                    style = MaterialTheme.typography.headlineMedium.copy(
                        fontFamily = fontFamilyValue,
                        fontSize = (fontSize + 6).sp,
                        lineHeight = (fontSize + 8).sp
                    ),
                    color = MaterialTheme.colorScheme.primary,
                    textAlign = TextAlign.Start,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 28.dp)
                )
            }
            
            // Chapter paragraphs
            items(
                count = paragraphs.size,
                key = { index -> "paragraph_$index" }
            ) { index ->
                Text(
                    text = paragraphs[index],
                    style = MaterialTheme.typography.bodyLarge.copy(
                        fontFamily = fontFamilyValue,
                        fontSize = fontSize.sp,
                        lineHeight = (fontSize * 1.75).sp,
                        letterSpacing = 0.15.sp
                    ),
                    color = MaterialTheme.colorScheme.onSurface,
                    textAlign = TextAlign.Justify,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 20.dp)
                )
            }
            
            // End of chapter indicator
            item {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 24.dp)
                ) {
                    Divider(
                        thickness = 1.dp,
                        color = MaterialTheme.colorScheme.outlineVariant
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "Loading next chapter...",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }
    }
}
