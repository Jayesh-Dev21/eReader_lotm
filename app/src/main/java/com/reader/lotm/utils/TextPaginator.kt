package com.reader.lotm.utils

import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.sp

class TextPaginator(
    private val density: Density,
    private val screenHeightPx: Int,
    private val fontSize: Float,
    private val fontFamily: FontFamily
) {
    
    data class Page(
        val text: String,
        val pageNumber: Int,
        val totalPages: Int
    )
    
    fun paginateText(
        text: String,
        maxWidthPx: Int,
        paddingPx: Int = 64
    ): List<String> {
        val availableHeight = screenHeightPx - (paddingPx * 2)
        val lineHeight = with(density) { (fontSize * 1.5).sp.toPx() }
        val linesPerPage = (availableHeight / lineHeight).toInt().coerceAtLeast(1)
        
        val paragraphs = text.split("\n\n")
        val pages = mutableListOf<String>()
        var currentPage = StringBuilder()
        var currentLines = 0
        
        for (paragraph in paragraphs) {
            val paragraphLines = estimateLines(paragraph, maxWidthPx)
            
            if (currentLines + paragraphLines + 1 > linesPerPage) {
                if (currentPage.isNotEmpty()) {
                    pages.add(currentPage.toString().trim())
                    currentPage = StringBuilder()
                    currentLines = 0
                }
            }
            
            if (paragraphLines > linesPerPage) {
                val words = paragraph.split(" ")
                var tempLine = StringBuilder()
                
                for (word in words) {
                    if (tempLine.isEmpty()) {
                        tempLine.append(word)
                    } else {
                        tempLine.append(" ").append(word)
                    }
                    
                    if (estimateLines(tempLine.toString(), maxWidthPx) > 1 || currentLines >= linesPerPage) {
                        if (currentLines >= linesPerPage) {
                            pages.add(currentPage.toString().trim())
                            currentPage = StringBuilder()
                            currentLines = 0
                        }
                        currentPage.append(tempLine.substring(0, tempLine.length - word.length - 1)).append("\n\n")
                        currentLines++
                        tempLine = StringBuilder(word)
                    }
                }
                
                if (tempLine.isNotEmpty()) {
                    currentPage.append(tempLine).append("\n\n")
                    currentLines += estimateLines(tempLine.toString(), maxWidthPx)
                }
            } else {
                currentPage.append(paragraph).append("\n\n")
                currentLines += paragraphLines + 1
            }
        }
        
        if (currentPage.isNotEmpty()) {
            pages.add(currentPage.toString().trim())
        }
        
        return if (pages.isEmpty()) listOf(text) else pages
    }
    
    private fun estimateLines(text: String, maxWidthPx: Int): Int {
        val charWidth = with(density) { (fontSize * 0.5).sp.toPx() }
        val charsPerLine = (maxWidthPx / charWidth).toInt().coerceAtLeast(1)
        return (text.length / charsPerLine).coerceAtLeast(1)
    }
    
    fun getPageForScrollOffset(
        pages: List<String>,
        scrollOffset: Float,
        pageHeightPx: Float
    ): Int {
        return (scrollOffset / pageHeightPx).toInt().coerceIn(0, pages.size - 1)
    }
    
    fun getScrollOffsetForPage(
        pageNumber: Int,
        pageHeightPx: Float
    ): Float {
        return pageNumber * pageHeightPx
    }
}
