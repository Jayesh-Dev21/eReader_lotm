package com.reader.lotm.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.reader.lotm.data.models.ReadingMode
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "reading_preferences")

class DataStoreManager(private val context: Context) {
    companion object {
        private val LAST_CHAPTER_ID = intPreferencesKey("last_chapter_id")
        private val SCROLL_OFFSET = floatPreferencesKey("scroll_offset")
        private val PAGE_NUMBER = intPreferencesKey("page_number")
        private val READING_MODE = stringPreferencesKey("reading_mode")
        private val FONT_SIZE = floatPreferencesKey("font_size")
        private val FONT_FAMILY = stringPreferencesKey("font_family")
        private val THEME = stringPreferencesKey("theme")
        private val AMOLED_MODE = stringPreferencesKey("amoled_mode")
        private val GESTURE_NAVIGATION_ENABLED = stringPreferencesKey("gesture_nav")
    }

    val lastChapterId: Flow<Int?> = context.dataStore.data.map { prefs ->
        prefs[LAST_CHAPTER_ID]
    }

    val scrollOffset: Flow<Float> = context.dataStore.data.map { prefs ->
        prefs[SCROLL_OFFSET] ?: 0f
    }

    val pageNumber: Flow<Int> = context.dataStore.data.map { prefs ->
        prefs[PAGE_NUMBER] ?: 0
    }

    val readingMode: Flow<ReadingMode> = context.dataStore.data.map { prefs ->
        when (prefs[READING_MODE]) {
            "PAGINATED" -> ReadingMode.PAGINATED
            else -> ReadingMode.CONTINUOUS_SCROLL
        }
    }

    val fontSize: Flow<Float> = context.dataStore.data.map { prefs ->
        prefs[FONT_SIZE] ?: 16f
    }

    val fontFamily: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[FONT_FAMILY] ?: "Serif"
    }

    val theme: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[THEME] ?: "Dark"
    }

    val amoledMode: Flow<Boolean> = context.dataStore.data.map { prefs ->
        prefs[AMOLED_MODE]?.let { it == "true" } ?: true  // Default to true
    }

    val gestureNavigationEnabled: Flow<Boolean> = context.dataStore.data.map { prefs ->
        prefs[GESTURE_NAVIGATION_ENABLED] != "false"
    }

    suspend fun saveLastChapterId(chapterId: Int) {
        context.dataStore.edit { prefs ->
            prefs[LAST_CHAPTER_ID] = chapterId
        }
    }

    suspend fun saveScrollOffset(offset: Float) {
        context.dataStore.edit { prefs ->
            prefs[SCROLL_OFFSET] = offset
        }
    }

    suspend fun savePageNumber(page: Int) {
        context.dataStore.edit { prefs ->
            prefs[PAGE_NUMBER] = page
        }
    }

    suspend fun saveReadingMode(mode: ReadingMode) {
        context.dataStore.edit { prefs ->
            prefs[READING_MODE] = mode.name
        }
    }

    suspend fun saveFontSize(size: Float) {
        context.dataStore.edit { prefs ->
            prefs[FONT_SIZE] = size
        }
    }

    suspend fun saveFontFamily(family: String) {
        context.dataStore.edit { prefs ->
            prefs[FONT_FAMILY] = family
        }
    }

    suspend fun saveTheme(themeName: String) {
        context.dataStore.edit { prefs ->
            prefs[THEME] = themeName
        }
    }

    suspend fun saveAmoledMode(enabled: Boolean) {
        context.dataStore.edit { prefs ->
            prefs[AMOLED_MODE] = if (enabled) "true" else "false"
        }
    }

    suspend fun saveGestureNavigationEnabled(enabled: Boolean) {
        context.dataStore.edit { prefs ->
            prefs[GESTURE_NAVIGATION_ENABLED] = if (enabled) "true" else "false"
        }
    }

    suspend fun clearReadingPosition() {
        context.dataStore.edit { prefs ->
            prefs.remove(LAST_CHAPTER_ID)
            prefs.remove(SCROLL_OFFSET)
            prefs.remove(PAGE_NUMBER)
        }
    }
}
