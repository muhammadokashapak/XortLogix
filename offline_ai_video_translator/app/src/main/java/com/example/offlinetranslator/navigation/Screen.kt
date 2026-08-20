package com.example.offlinetranslator.navigation

sealed class Screen(val route: String) {
    data object Home : Screen("home")
    data object History : Screen("history")
    data object Settings : Screen("settings")

    data object Player : Screen("player/{mediaHash}") {
        fun createRoute(mediaHash: String) = "player/$mediaHash"
    }

    data object Processing : Screen("processing/{mediaHash}/{sourceLang}/{targetLang}") {
        fun createRoute(mediaHash: String, sourceLang: String, targetLang: String) =
            "processing/$mediaHash/$sourceLang/$targetLang"
    }
}
