package com.example.offlinetranslator

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.rememberNavController
import com.example.offlinetranslator.navigation.AppNavHost
import com.example.offlinetranslator.navigation.Screen
import com.example.offlinetranslator.ui.theme.OfflineVideoTranslatorTheme
import com.example.offlinetranslator.utils.FileUtils
import com.example.offlinetranslator.utils.PermissionUtils
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {
        // Permissions handled
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Request storage/media permissions if not granted
        if (!PermissionUtils.hasMediaPermissions(this)) {
            permissionLauncher.launch(PermissionUtils.getRequiredMediaPermissions())
        }

        val app = application as OfflineTranslatorApp
        val incomingUri: Uri? = intent?.data

        setContent {
            val userPrefs by app.settingsRepository.userPreferences.collectAsState(
                initial = com.example.offlinetranslator.data.model.UserPreferences()
            )

            val isDark = when (userPrefs.themeMode) {
                "DARK" -> true
                "LIGHT" -> false
                else -> isSystemInDarkTheme()
            }

            OfflineVideoTranslatorTheme(darkTheme = isDark) {
                Surface(
                    modifier = Modifier.fillMaxSize()
                ) {
                    val navController = rememberNavController()
                    AppNavHost(navController = navController)

                    // Handle incoming video/audio intent from external file manager
                    if (incomingUri != null) {
                        val fileName = FileUtils.getFileNameFromUri(this@MainActivity, incomingUri)
                        val isVideo = FileUtils.isVideoMime(contentResolver.getType(incomingUri), fileName)
                        CoroutineScope(Dispatchers.Main).launch {
                            val media = app.mediaRepository.saveOrUpdateMedia(
                                uri = incomingUri,
                                fileName = fileName,
                                durationMs = 0L,
                                sizeBytes = 0L,
                                mimeType = contentResolver.getType(incomingUri),
                                isVideo = isVideo
                            )
                            navController.navigate(Screen.Player.createRoute(media.mediaHash))
                        }
                    }
                }
            }
        }
    }
}
