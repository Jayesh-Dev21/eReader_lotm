package com.reader.lotm.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.reader.lotm.data.local.DataStoreManager
import com.reader.lotm.data.models.ReadingMode
import com.reader.lotm.data.models.ReadingPreferences
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch

class SettingsViewModel(
    private val dataStoreManager: DataStoreManager
) : ViewModel() {
    
    private val _preferences = MutableStateFlow(ReadingPreferences())
    val preferences: StateFlow<ReadingPreferences> = _preferences.asStateFlow()
    
    private val _isDarkTheme = MutableStateFlow(false)
    val isDarkTheme: StateFlow<Boolean> = _isDarkTheme.asStateFlow()
    
    private val _amoledMode = MutableStateFlow(false)
    val amoledMode: StateFlow<Boolean> = _amoledMode.asStateFlow()
    
    init {
        loadPreferences()
    }
    
    private fun loadPreferences() {
        viewModelScope.launch {
            combine(
                dataStoreManager.readingMode,
                dataStoreManager.fontSize,
                dataStoreManager.fontFamily,
                dataStoreManager.theme,
                dataStoreManager.amoledMode,
                dataStoreManager.gestureNavigationEnabled
            ) { flows ->
                val mode = flows[0] as ReadingMode
                val size = flows[1] as Float
                val family = flows[2] as String
                val theme = flows[3] as String
                val amoled = flows[4] as Boolean
                val gestureNav = flows[5] as Boolean
                
                _isDarkTheme.value = theme == "Dark" || amoled
                _amoledMode.value = amoled
                ReadingPreferences(
                    readingMode = mode,
                    fontSize = size,
                    fontFamily = family,
                    theme = theme,
                    amoledMode = amoled,
                    gestureNavigationEnabled = gestureNav
                )
            }.collect { prefs ->
                _preferences.value = prefs
            }
        }
    }
    
    fun updateReadingMode(mode: ReadingMode) {
        viewModelScope.launch {
            dataStoreManager.saveReadingMode(mode)
        }
    }
    
    fun updateFontSize(size: Float) {
        viewModelScope.launch {
            dataStoreManager.saveFontSize(size)
        }
    }
    
    fun updateFontFamily(family: String) {
        viewModelScope.launch {
            dataStoreManager.saveFontFamily(family)
        }
    }
    
    fun updateTheme(isDark: Boolean) {
        viewModelScope.launch {
            dataStoreManager.saveTheme(if (isDark) "Dark" else "Light")
        }
    }
    
    fun updateAmoledMode(enabled: Boolean) {
        viewModelScope.launch {
            dataStoreManager.saveAmoledMode(enabled)
        }
    }
    
    fun updateGestureNavigation(enabled: Boolean) {
        viewModelScope.launch {
            dataStoreManager.saveGestureNavigationEnabled(enabled)
        }
    }
}
