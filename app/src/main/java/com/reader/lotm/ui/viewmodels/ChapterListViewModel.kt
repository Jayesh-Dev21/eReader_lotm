package com.reader.lotm.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.reader.lotm.data.local.ChapterEntity
import com.reader.lotm.data.repository.BookRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class ChapterListUiState {
    object Loading : ChapterListUiState()
    data class Success(val chapters: List<ChapterEntity>, val totalCount: Int) : ChapterListUiState()
    data class Error(val message: String) : ChapterListUiState()
}

class ChapterListViewModel(
    private val repository: BookRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow<ChapterListUiState>(ChapterListUiState.Loading)
    val uiState: StateFlow<ChapterListUiState> = _uiState.asStateFlow()
    
    init {
        loadChapters()
    }
    
    private fun loadChapters() {
        viewModelScope.launch {
            try {
                repository.getAllChapters().collect { chapters ->
                    _uiState.value = ChapterListUiState.Success(
                        chapters = chapters,
                        totalCount = chapters.size
                    )
                }
            } catch (e: Exception) {
                _uiState.value = ChapterListUiState.Error(
                    message = e.message ?: "Unknown error occurred"
                )
            }
        }
    }
    
    fun refresh() {
        _uiState.value = ChapterListUiState.Loading
        loadChapters()
    }
}
