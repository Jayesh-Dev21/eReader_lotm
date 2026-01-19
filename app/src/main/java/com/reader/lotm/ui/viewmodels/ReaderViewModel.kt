package com.reader.lotm.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.reader.lotm.data.local.ChapterEntity
import com.reader.lotm.data.local.DataStoreManager
import com.reader.lotm.data.models.ReadingMode
import com.reader.lotm.data.repository.BookRepository
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.launch

sealed class ReaderUiState {
    object Loading : ReaderUiState()
    data class Success(
        val chapter: ChapterEntity,
        val totalChapters: Int,
        val hasNext: Boolean,
        val hasPrevious: Boolean
    ) : ReaderUiState()
    data class Error(val message: String) : ReaderUiState()
}

@OptIn(FlowPreview::class)
class ReaderViewModel(
    private val repository: BookRepository,
    private val dataStoreManager: DataStoreManager
) : ViewModel() {
    
    private val _uiState = MutableStateFlow<ReaderUiState>(ReaderUiState.Loading)
    val uiState: StateFlow<ReaderUiState> = _uiState.asStateFlow()
    
    private val _currentChapterId = MutableStateFlow<Int?>(null)
    val currentChapterId: StateFlow<Int?> = _currentChapterId.asStateFlow()
    
    private val _readingMode = MutableStateFlow(ReadingMode.CONTINUOUS_SCROLL)
    val readingMode: StateFlow<ReadingMode> = _readingMode.asStateFlow()
    
    private val _fontSize = MutableStateFlow(16f)
    val fontSize: StateFlow<Float> = _fontSize.asStateFlow()
    
    private val _fontFamily = MutableStateFlow("Serif")
    val fontFamily: StateFlow<String> = _fontFamily.asStateFlow()
    
    private val _scrollOffset = MutableStateFlow(0f)
    val scrollOffset: StateFlow<Float> = _scrollOffset.asStateFlow()
    
    private val _pageNumber = MutableStateFlow(0)
    val pageNumber: StateFlow<Int> = _pageNumber.asStateFlow()
    
    private val _showControls = MutableStateFlow(false)
    val showControls: StateFlow<Boolean> = _showControls.asStateFlow()
    
    private val _gestureNavigationEnabled = MutableStateFlow(true)
    val gestureNavigationEnabled: StateFlow<Boolean> = _gestureNavigationEnabled.asStateFlow()
    
    init {
        loadPreferences()
        observeScrollPosition()
        observePageNumber()
    }
    
    private fun loadPreferences() {
        viewModelScope.launch {
            dataStoreManager.readingMode.collect { mode ->
                _readingMode.value = mode
            }
        }
        viewModelScope.launch {
            dataStoreManager.fontSize.collect { size ->
                _fontSize.value = size
            }
        }
        viewModelScope.launch {
            dataStoreManager.fontFamily.collect { family ->
                _fontFamily.value = family
            }
        }
        viewModelScope.launch {
            dataStoreManager.gestureNavigationEnabled.collect { enabled ->
                _gestureNavigationEnabled.value = enabled
            }
        }
    }
    
    private fun observeScrollPosition() {
        viewModelScope.launch {
            _scrollOffset
                .debounce(2000)
                .collect { offset ->
                    dataStoreManager.saveScrollOffset(offset)
                }
        }
    }
    
    private fun observePageNumber() {
        viewModelScope.launch {
            _pageNumber
                .debounce(2000)
                .collect { page ->
                    dataStoreManager.savePageNumber(page)
                }
        }
    }
    
    fun loadChapter(chapterId: Int) {
        viewModelScope.launch {
            try {
                _currentChapterId.value = chapterId
                
                val chapter = repository.getChapterByIdSync(chapterId)
                if (chapter == null) {
                    _uiState.value = ReaderUiState.Error("Chapter not found")
                    return@launch
                }
                
                val totalCount = repository.getChapterCountSync()
                val nextId = repository.getNextChapterId(chapterId)
                val prevId = repository.getPreviousChapterId(chapterId)
                
                _uiState.value = ReaderUiState.Success(
                    chapter = chapter,
                    totalChapters = totalCount,
                    hasNext = nextId != null,
                    hasPrevious = prevId != null
                )
                
                dataStoreManager.saveLastChapterId(chapterId)
                
                if (_readingMode.value == ReadingMode.CONTINUOUS_SCROLL) {
                    loadSavedScrollPosition()
                } else {
                    loadSavedPageNumber()
                }
            } catch (e: Exception) {
                _uiState.value = ReaderUiState.Error(
                    message = e.message ?: "Failed to load chapter"
                )
            }
        }
    }
    
    private suspend fun loadSavedScrollPosition() {
        dataStoreManager.scrollOffset.collect { offset ->
            _scrollOffset.value = offset
        }
    }
    
    private suspend fun loadSavedPageNumber() {
        dataStoreManager.pageNumber.collect { page ->
            _pageNumber.value = page
        }
    }
    
    fun loadNextChapter() {
        viewModelScope.launch {
            _currentChapterId.value?.let { currentId ->
                val nextId = repository.getNextChapterId(currentId)
                if (nextId != null) {
                    resetReadingPosition()
                    loadChapter(nextId)
                }
            }
        }
    }
    
    fun loadPreviousChapter() {
        viewModelScope.launch {
            _currentChapterId.value?.let { currentId ->
                val prevId = repository.getPreviousChapterId(currentId)
                if (prevId != null) {
                    resetReadingPosition()
                    loadChapter(prevId)
                }
            }
        }
    }
    
    fun updateScrollOffset(offset: Float) {
        _scrollOffset.value = offset
    }
    
    fun updatePageNumber(page: Int) {
        _pageNumber.value = page
    }
    
    fun toggleControls() {
        _showControls.value = !_showControls.value
    }
    
    fun hideControls() {
        _showControls.value = false
    }
    
    fun showControls() {
        _showControls.value = true
    }
    
    private fun resetReadingPosition() {
        _scrollOffset.value = 0f
        _pageNumber.value = 0
        viewModelScope.launch {
            dataStoreManager.saveScrollOffset(0f)
            dataStoreManager.savePageNumber(0)
        }
    }
    
    fun updateReadingMode(mode: ReadingMode) {
        _readingMode.value = mode
        viewModelScope.launch {
            dataStoreManager.saveReadingMode(mode)
        }
    }
    
    fun updateFontSize(size: Float) {
        _fontSize.value = size
        viewModelScope.launch {
            dataStoreManager.saveFontSize(size)
        }
    }
    
    fun updateFontFamily(family: String) {
        _fontFamily.value = family
        viewModelScope.launch {
            dataStoreManager.saveFontFamily(family)
        }
    }
}
