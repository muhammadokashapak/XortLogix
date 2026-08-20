package com.example.offlinetranslator.navigation

import android.app.Application
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.example.offlinetranslator.ui.history.HistoryScreen
import com.example.offlinetranslator.ui.history.HistoryViewModel
import com.example.offlinetranslator.ui.home.HomeScreen
import com.example.offlinetranslator.ui.home.HomeViewModel
import com.example.offlinetranslator.ui.player.MediaPlayerScreen
import com.example.offlinetranslator.ui.player.MediaPlayerViewModel
import com.example.offlinetranslator.ui.processing.ProcessingScreen
import com.example.offlinetranslator.ui.processing.ProcessingViewModel
import com.example.offlinetranslator.ui.settings.SettingsScreen
import com.example.offlinetranslator.ui.settings.SettingsViewModel

@Composable
fun AppNavHost(
    navController: NavHostController,
    modifier: Modifier = Modifier
) {
    val application = LocalContext.current.applicationContext as Application

    NavHost(
        navController = navController,
        startDestination = Screen.Home.route,
        modifier = modifier
    ) {
        composable(Screen.Home.route) {
            val homeViewModel: HomeViewModel = viewModel()
            HomeScreen(
                viewModel = homeViewModel,
                onNavigateToPlayer = { hash ->
                    navController.navigate(Screen.Player.createRoute(hash))
                },
                onNavigateToHistory = {
                    navController.navigate(Screen.History.route)
                },
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                }
            )
        }

        composable(
            route = Screen.Player.route,
            arguments = listOf(navArgument("mediaHash") { type = NavType.StringType })
        ) { backStackEntry ->
            val mediaHash = backStackEntry.arguments?.getString("mediaHash") ?: ""
            val playerViewModel: MediaPlayerViewModel = viewModel(
                key = mediaHash,
                factory = object : androidx.lifecycle.ViewModelProvider.Factory {
                    @Suppress("UNCHECKED_CAST")
                    override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                        return MediaPlayerViewModel(application, mediaHash) as T
                    }
                }
            )

            MediaPlayerScreen(
                viewModel = playerViewModel,
                onNavigateBack = { navController.popBackStack() },
                onNavigateToProcessing = { hash, src, tgt ->
                    navController.navigate(Screen.Processing.createRoute(hash, src, tgt))
                },
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                }
            )
        }

        composable(
            route = Screen.Processing.route,
            arguments = listOf(
                navArgument("mediaHash") { type = NavType.StringType },
                navArgument("sourceLang") { type = NavType.StringType },
                navArgument("targetLang") { type = NavType.StringType }
            )
        ) { backStackEntry ->
            val mediaHash = backStackEntry.arguments?.getString("mediaHash") ?: ""
            val sourceLang = backStackEntry.arguments?.getString("sourceLang") ?: "auto"
            val targetLang = backStackEntry.arguments?.getString("targetLang") ?: "ur"

            val processingViewModel: ProcessingViewModel = viewModel(
                key = "$mediaHash-$sourceLang-$targetLang",
                factory = object : androidx.lifecycle.ViewModelProvider.Factory {
                    @Suppress("UNCHECKED_CAST")
                    override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                        return ProcessingViewModel(application, mediaHash, sourceLang, targetLang) as T
                    }
                }
            )

            ProcessingScreen(
                viewModel = processingViewModel,
                onNavigateBack = { navController.popBackStack() },
                onNavigateToPlayer = { hash ->
                    navController.navigate(Screen.Player.createRoute(hash)) {
                        popUpTo(Screen.Home.route)
                    }
                }
            )
        }

        composable(Screen.History.route) {
            val historyViewModel: HistoryViewModel = viewModel()
            HistoryScreen(
                viewModel = historyViewModel,
                onNavigateBack = { navController.popBackStack() },
                onNavigateToPlayer = { hash ->
                    navController.navigate(Screen.Player.createRoute(hash))
                }
            )
        }

        composable(Screen.Settings.route) {
            val settingsViewModel: SettingsViewModel = viewModel()
            SettingsScreen(
                viewModel = settingsViewModel,
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}
