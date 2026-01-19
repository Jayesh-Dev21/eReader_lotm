package com.reader.lotm

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.rememberNavController
import com.google.accompanist.systemuicontroller.rememberSystemUiController
import com.reader.lotm.data.local.AppDatabase
import com.reader.lotm.data.local.DataStoreManager
import com.reader.lotm.data.repository.BookRepository
import com.reader.lotm.data.scraper.NovelScraper
import com.reader.lotm.navigation.NavGraph
import com.reader.lotm.ui.theme.LoTMReaderTheme
import com.reader.lotm.ui.viewmodels.ChapterListViewModel
import com.reader.lotm.ui.viewmodels.ReaderViewModel
import com.reader.lotm.ui.viewmodels.SettingsViewModel

class MainActivity : ComponentActivity() {
    
    private lateinit var database: AppDatabase
    private lateinit var dataStoreManager: DataStoreManager
    private lateinit var repository: BookRepository
    
    private lateinit var chapterListViewModel: ChapterListViewModel
    private lateinit var readerViewModel: ReaderViewModel
    private lateinit var settingsViewModel: SettingsViewModel
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        database = AppDatabase.getInstance(applicationContext)
        dataStoreManager = DataStoreManager(applicationContext)
        val scraper = NovelScraper()
        repository = BookRepository(database.chapterDao(), scraper)
        
        chapterListViewModel = ChapterListViewModel(repository)
        readerViewModel = ReaderViewModel(repository, dataStoreManager)
        settingsViewModel = SettingsViewModel(dataStoreManager)
        
        setContent {
            val isDarkTheme by settingsViewModel.isDarkTheme.collectAsState()
            val amoledMode by settingsViewModel.amoledMode.collectAsState()
            val systemUiController = rememberSystemUiController()
            
            LoTMReaderTheme(
                darkTheme = isDarkTheme,
                amoledMode = amoledMode
            ) {
                systemUiController.setSystemBarsColor(
                    color = MaterialTheme.colorScheme.background,
                    darkIcons = !isDarkTheme && !amoledMode
                )
                
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val navController = rememberNavController()
                    
                    NavGraph(
                        navController = navController,
                        chapterListViewModel = chapterListViewModel,
                        readerViewModel = readerViewModel,
                        settingsViewModel = settingsViewModel
                    )
                }
            }
        }
    }
}
