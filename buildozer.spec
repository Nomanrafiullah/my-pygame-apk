[app]
title           = Dua's Pink Paradise
package.name    = duasparadise
package.domain  = org.duasparadise
source.dir      = .
source.include_exts = py,png,jpg,kv,atlas
version         = 1.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer,pillow

orientation     = landscape
fullscreen      = 1

android.permissions     = READ_EXTERNAL_STORAGE
android.api             = 33
android.minapi          = 21
android.ndk             = 25b
android.archs           = arm64-v8a, armeabi-v7a
android.allow_backup    = True

# Icons (replace with your own 512x512 pink icon)
# icon.filename = %(source.dir)s/assets/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
