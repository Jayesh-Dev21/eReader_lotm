package com.reader.lotm.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.reader.lotm.data.models.ReadingMode
import com.reader.lotm.ui.viewmodels.SettingsViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    viewModel: SettingsViewModel,
    onBackClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val preferences by viewModel.preferences.collectAsState()
    val isDarkTheme by viewModel.isDarkTheme.collectAsState()
    val amoledMode by viewModel.amoledMode.collectAsState()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            Text(
                text = "Reading Preferences",
                style = MaterialTheme.typography.titleLarge
            )
            
            Divider()
            
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "Reading Mode",
                    style = MaterialTheme.typography.titleMedium
                )
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    FilterChip(
                        selected = preferences.readingMode == ReadingMode.CONTINUOUS_SCROLL,
                        onClick = { viewModel.updateReadingMode(ReadingMode.CONTINUOUS_SCROLL) },
                        label = { Text("Continuous Scroll") }
                    )
                    FilterChip(
                        selected = preferences.readingMode == ReadingMode.PAGINATED,
                        onClick = { viewModel.updateReadingMode(ReadingMode.PAGINATED) },
                        label = { Text("Paginated") }
                    )
                }
            }
            
            Divider()
            
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "Font Size: ${preferences.fontSize.toInt()}sp",
                    style = MaterialTheme.typography.titleMedium
                )
                Slider(
                    value = preferences.fontSize,
                    onValueChange = { viewModel.updateFontSize(it) },
                    valueRange = 12f..28f,
                    steps = 7
                )
            }
            
            Divider()
            
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "Font Family",
                    style = MaterialTheme.typography.titleMedium
                )
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    FilterChip(
                        selected = preferences.fontFamily == "Serif",
                        onClick = { viewModel.updateFontFamily("Serif") },
                        label = { Text("Serif") }
                    )
                    FilterChip(
                        selected = preferences.fontFamily == "Sans-serif",
                        onClick = { viewModel.updateFontFamily("Sans-serif") },
                        label = { Text("Sans Serif") }
                    )
                    FilterChip(
                        selected = preferences.fontFamily == "Monospace",
                        onClick = { viewModel.updateFontFamily("Monospace") },
                        label = { Text("Monospace") }
                    )
                }
            }
            
            Divider()
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "Dark Theme",
                    style = MaterialTheme.typography.titleMedium
                )
                Switch(
                    checked = isDarkTheme,
                    onCheckedChange = { viewModel.updateTheme(it) }
                )
            }
            
            Divider()
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "AMOLED Black",
                        style = MaterialTheme.typography.titleMedium
                    )
                    Text(
                        text = "Pure black background for OLED screens",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Switch(
                    checked = amoledMode,
                    onCheckedChange = { viewModel.updateAmoledMode(it) },
                    enabled = isDarkTheme
                )
            }
            
            Divider()
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "Gesture Navigation",
                        style = MaterialTheme.typography.titleMedium
                    )
                    Text(
                        text = "Tap screen edges to navigate chapters",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Switch(
                    checked = preferences.gestureNavigationEnabled,
                    onCheckedChange = { viewModel.updateGestureNavigation(it) }
                )
            }
        }
    }
}
