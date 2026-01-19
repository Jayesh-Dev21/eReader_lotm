package com.reader.lotm.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.TextDecrease
import androidx.compose.material.icons.filled.TextIncrease
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.reader.lotm.data.models.ReadingMode

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReadingControls(
    fontSize: Float,
    fontFamily: String,
    readingMode: ReadingMode,
    onFontSizeChange: (Float) -> Unit,
    onFontFamilyChange: (String) -> Unit,
    onReadingModeChange: (ReadingMode) -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 3.dp
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = "Font Size: ${fontSize.toInt()}sp",
                style = MaterialTheme.typography.labelLarge
            )
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = { onFontSizeChange((fontSize - 2f).coerceAtLeast(12f)) }) {
                    Icon(Icons.Default.TextDecrease, contentDescription = "Decrease font size")
                }
                
                Slider(
                    value = fontSize,
                    onValueChange = onFontSizeChange,
                    valueRange = 12f..28f,
                    steps = 7,
                    modifier = Modifier.weight(1f)
                )
                
                IconButton(onClick = { onFontSizeChange((fontSize + 2f).coerceAtMost(28f)) }) {
                    Icon(Icons.Default.TextIncrease, contentDescription = "Increase font size")
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                text = "Font Family",
                style = MaterialTheme.typography.labelLarge
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                FilterChip(
                    selected = fontFamily == "Serif",
                    onClick = { onFontFamilyChange("Serif") },
                    label = { Text("Serif") }
                )
                FilterChip(
                    selected = fontFamily == "Sans-serif",
                    onClick = { onFontFamilyChange("Sans-serif") },
                    label = { Text("Sans Serif") }
                )
                FilterChip(
                    selected = fontFamily == "Monospace",
                    onClick = { onFontFamilyChange("Monospace") },
                    label = { Text("Monospace") }
                )
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                text = "Reading Mode",
                style = MaterialTheme.typography.labelLarge
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                FilterChip(
                    selected = readingMode == ReadingMode.CONTINUOUS_SCROLL,
                    onClick = { onReadingModeChange(ReadingMode.CONTINUOUS_SCROLL) },
                    label = { Text("Continuous") }
                )
                FilterChip(
                    selected = readingMode == ReadingMode.PAGINATED,
                    onClick = { onReadingModeChange(ReadingMode.PAGINATED) },
                    label = { Text("Paginated") }
                )
            }
        }
    }
}
