[app]
title           = Dua's Pink Paradise
package.name    = duasparadise
package.domain  = org.duasparadise
source.dir      = .
source.include_exts = py,png,jpg,kv,atlas

# Using stable production versions compatible with Python 3.11 
requirements = python3==3.11.1,kivy==2.3.0,kivymd==1.2.0,plyer,pillow

version         = 1.0
orientation     = landscape
fullscreen      = 1

android.permissions     = READ_EXTERNAL_STORAGE
android.api             = 33
android.minapi          = 21
android.ndk             = 25b
android.archs           = arm64-v8a, armeabi-v7a
android.allow_backup    = True

# Crucial: Ensures Android licenses are accepted at compile-time natively
android.accept_sdk_license = True

# Disable custom icon references completely until the build passes cleanly
# icon.filename = %(source.dir)s/assets/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
