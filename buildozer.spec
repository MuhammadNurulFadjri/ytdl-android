[app]
title = YT Downloader
package.name = ytdownloader
package.domain = com.bangxd
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.3.0

# requirements - keep minimal, avoid C-compilation heavy packages
# yt-dlp works without brotli/pycryptodomex (just slower/fewer features)
requirements = python3,kivy,yt-dlp,pyjnius,android,certifi,mutagen,websockets

# android
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.arch = arm64-v8a
android.allow_backup = True

# appearance
orientation = portrait
fullscreen = 0
android.presplash_color = #1a1d23

# build
log_level = 2
warn_on_root = 0

# p4a
p4a.branch = develop
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 0
