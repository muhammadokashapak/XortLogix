# Proguard rules for Offline Video Translator

# Keep ONNX Runtime JNI classes
-keep class ai.onnxruntime.** { *; }

# Keep Room entities and DAOs
-keep class androidx.room.** { *; }
-dontwarn androidx.room.paging.**

# Keep Media3 ExoPlayer classes
-keep class androidx.media3.** { *; }
