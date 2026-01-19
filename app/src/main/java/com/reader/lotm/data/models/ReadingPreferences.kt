package com.reader.lotm.data.models

data class ReadingPreferences(
    val readingMode: ReadingMode = ReadingMode.CONTINUOUS_SCROLL,
    val fontSize: Float = 16f,
    val fontFamily: String = "Serif",
    val theme: String = "Dark",
    val amoledMode: Boolean = true,
    val gestureNavigationEnabled: Boolean = true
)
