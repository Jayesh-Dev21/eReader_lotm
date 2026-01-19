package com.reader.lotm.utils

import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.pointer.pointerInput

enum class TapZone {
    LEFT, CENTER, RIGHT
}

fun Modifier.detectReaderGestures(
    onTap: (TapZone) -> Unit
): Modifier = this.pointerInput(Unit) {
    detectTapGestures { offset: Offset ->
        val screenWidth = size.width.toFloat()
        val zone = when {
            offset.x < screenWidth * 0.25f -> TapZone.LEFT
            offset.x > screenWidth * 0.75f -> TapZone.RIGHT
            else -> TapZone.CENTER
        }
        onTap(zone)
    }
}
