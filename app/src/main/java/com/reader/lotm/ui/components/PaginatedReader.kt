package com.reader.lotm.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.accompanist.pager.ExperimentalPagerApi
import com.google.accompanist.pager.HorizontalPager
import com.google.accompanist.pager.rememberPagerState
import com.reader.lotm.data.local.ChapterEntity
import com.reader.lotm.utils.TextPaginator
import com.reader.lotm.utils.TapZone
import com.reader.lotm.utils.detectReaderGestures

@OptIn(ExperimentalPagerApi::class)
@Composable
fun PaginatedReader(
    chapter: ChapterEntity,
    fontSize: Float,
    fontFamily: String,
    initialPage: Int,
    gestureNavigationEnabled: Boolean,
    onPageChange: (Int) -> Unit,
    onTapZone: (TapZone) -> Unit,
    onLoadNextChapter: () -> Unit,
    onLoadPreviousChapter: () -> Unit,
    modifier: Modifier = Modifier
) {
    val density = LocalDensity.current
    val configuration = LocalConfiguration.current
    val screenHeightPx = with(density) { configuration.screenHeightDp.dp.toPx().toInt() }
    val screenWidthPx = with(density) { configuration.screenWidthDp.dp.toPx().toInt() }
    
    val fontFamilyValue = when (fontFamily) {
        "Sans-serif" -> FontFamily.SansSerif
        "Monospace" -> FontFamily.Monospace
        else -> FontFamily.Serif
    }
    
    val paginator = remember(chapter.content, fontSize, fontFamily, screenHeightPx) {
        TextPaginator(
            density = density,
            screenHeightPx = screenHeightPx,
            fontSize = fontSize,
            fontFamily = fontFamilyValue
        )
    }
    
    val pages = remember(chapter.content, fontSize, fontFamily, screenWidthPx) {
        paginator.paginateText(
            text = chapter.content ?: "",
            maxWidthPx = screenWidthPx - with(density) { 48.dp.toPx().toInt() }
        )
    }
    
    val pagerState = rememberPagerState(initialPage = initialPage.coerceIn(0, pages.size - 1))
    
    LaunchedEffect(pagerState.currentPage) {
        onPageChange(pagerState.currentPage)
        
        if (pagerState.currentPage == pages.size - 1) {
            onLoadNextChapter()
        } else if (pagerState.currentPage == 0) {
        }
    }
    
    Box(
        modifier = modifier
            .fillMaxSize()
            .then(
                if (gestureNavigationEnabled) {
                    Modifier.detectReaderGestures(onTap = onTapZone)
                } else {
                    Modifier
                }
            )
    ) {
        HorizontalPager(
            count = pages.size,
            state = pagerState,
            modifier = Modifier.fillMaxSize()
        ) { page ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 24.dp, vertical = 32.dp),
                verticalArrangement = Arrangement.Top
            ) {
                if (page == 0) {
                    Text(
                        text = chapter.title,
                        style = MaterialTheme.typography.headlineSmall.copy(
                            fontFamily = fontFamilyValue,
                            fontSize = (fontSize + 4).sp
                        ),
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(bottom = 16.dp)
                    )
                }
                
                Text(
                    text = pages[page],
                    style = MaterialTheme.typography.bodyLarge.copy(
                        fontFamily = fontFamilyValue,
                        fontSize = fontSize.sp,
                        lineHeight = (fontSize * 1.6).sp
                    )
                )
                
                Spacer(modifier = Modifier.weight(1f))
                
                Text(
                    text = "Page ${page + 1} of ${pages.size}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.align(Alignment.CenterHorizontally)
                )
            }
        }
    }
}
