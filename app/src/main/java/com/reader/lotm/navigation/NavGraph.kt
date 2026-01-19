package com.reader.lotm.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.reader.lotm.ui.screens.ChapterListScreen
import com.reader.lotm.ui.screens.ReaderScreen
import com.reader.lotm.ui.screens.SettingsScreen
import com.reader.lotm.ui.viewmodels.ChapterListViewModel
import com.reader.lotm.ui.viewmodels.ReaderViewModel
import com.reader.lotm.ui.viewmodels.SettingsViewModel

sealed class Screen(val route: String) {
    object ChapterList : Screen("chapter_list")
    object Reader : Screen("reader/{chapterId}") {
        fun createRoute(chapterId: Int) = "reader/$chapterId"
    }
    object Settings : Screen("settings")
}

@Composable
fun NavGraph(
    navController: NavHostController,
    chapterListViewModel: ChapterListViewModel,
    readerViewModel: ReaderViewModel,
    settingsViewModel: SettingsViewModel,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = Screen.ChapterList.route,
        modifier = modifier
    ) {
        composable(Screen.ChapterList.route) {
            ChapterListScreen(
                viewModel = chapterListViewModel,
                onChapterClick = { chapterId ->
                    navController.navigate(Screen.Reader.createRoute(chapterId))
                },
                onSettingsClick = {
                    navController.navigate(Screen.Settings.route)
                }
            )
        }
        
        composable(
            route = Screen.Reader.route,
            arguments = listOf(
                navArgument("chapterId") { type = NavType.IntType }
            )
        ) { backStackEntry ->
            val chapterId = backStackEntry.arguments?.getInt("chapterId") ?: 1
            
            readerViewModel.loadChapter(chapterId)
            
            ReaderScreen(
                viewModel = readerViewModel,
                onBackClick = {
                    navController.popBackStack()
                }
            )
        }
        
        composable(Screen.Settings.route) {
            SettingsScreen(
                viewModel = settingsViewModel,
                onBackClick = {
                    navController.popBackStack()
                }
            )
        }
    }
}
