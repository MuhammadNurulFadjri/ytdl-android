# YT Downloader

download youtube jadi mp3/mp4. support playlist select, thumbnail, stop download.

by bang xd

## fitur

- paste link video / playlist
- pilih format mp3 atau mp4
- pilih kualitas (128k-320k / 360p-1080p)
- thumbnail tiap video
- centang video mana yg mau didownload
- stop download kapan aja
- pilih folder simpan
- dark theme

## build apk (github actions)

cara paling gampang, gratis, nggak perlu setup linux.

1. bikin repo baru di github
2. push semua file ini ke repo

```bash
cd ytdl-android
git init
git add .
git commit -m "init"
git remote add origin https://github.com/USERNAME/ytdl-android.git
git branch -M main
git push -u origin main
```

3. buka tab **Actions** di repo github
4. workflow "Build APK" jalan otomatis
5. tunggu ~30 menit
6. klik workflow run yg udah selesai > scroll bawah > download artifact **ytdownloader-apk**
7. extract zip, dapet file `.apk` - install ke hp

## test di desktop (windows)

```bash
py -3.12 -m venv venv
venv\Scripts\activate
pip install kivy yt-dlp
python main.py
```

butuh python 3.12, kivy belum support 3.13 di windows.

## struktur

```
ytdl-android/
├── main.py                        # app
├── buildozer.spec                 # config build android
├── .gitignore
├── .github/workflows/build.yml   # auto build apk
└── README.md
```

## catatan

- ffmpeg diperlukan untuk konversi mp3. di android, yt-dlp biasanya fallback ke format audio yg tersedia tanpa konversi. kalau butuh mp3 beneran, perlu bundle ffmpeg binary ke apk.
- pertama kali build di github actions bisa lama (~40 menit) karena download sdk. build berikutnya lebih cepat karena cache.
- file hasil download di android ada di `/Download/YTDownloader/`, bisa diubah dari app.
