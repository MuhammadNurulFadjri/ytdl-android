"""
YT Downloader - bang xd
download youtube jadi mp3/mp4
support playlist select, thumbnail, folder picker, stop download
"""

import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import re
import json
import threading
from functools import partial

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from kivy.utils import platform as kv_platform

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

if kv_platform == "android":
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    DEFAULT_DL = os.path.join(primary_external_storage_path(), "Download", "YTDownloader")
    CONF_PATH = os.path.join(primary_external_storage_path(), ".ytdl_config.json")
else:
    DEFAULT_DL = os.path.join(os.path.expanduser("~"), "Downloads", "YTDownloader")
    CONF_PATH = os.path.join(os.path.expanduser("~"), ".ytdl_config.json")


def load_dl_path():
    try:
        with open(CONF_PATH, "r") as f:
            p = json.load(f).get("dl_path", "")
            if p and os.path.isdir(p):
                return p
    except:
        pass
    return DEFAULT_DL


def save_dl_path(path):
    try:
        with open(CONF_PATH, "w") as f:
            json.dump({"dl_path": path}, f)
    except:
        pass


KV = """
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import hex kivy.utils.get_color_from_hex

<FlatBtn@ButtonBehavior+Label>:
    size_hint_y: None
    height: dp(42)
    font_size: sp(13)
    bold: True
    color: hex('1a1d23')
    bg: '34d399'
    canvas.before:
        Color:
            rgba: hex(self.bg) if self.state == 'normal' else [c*0.85 for c in hex(self.bg)[:3]] + [1]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(6)]

<OutlineBtn@ButtonBehavior+Label>:
    size_hint_y: None
    height: dp(42)
    font_size: sp(13)
    color: hex('c8ccd4')
    canvas.before:
        Color:
            rgba: hex('3a3f4b')
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(6)
            width: 1.1
        Color:
            rgba: hex('282d38') if self.state == 'normal' else hex('3a3f4b')
        RoundedRectangle:
            pos: self.x+1, self.y+1
            size: self.width-2, self.height-2
            radius: [dp(6)]

<StopBtn@ButtonBehavior+Label>:
    size_hint_y: None
    height: dp(42)
    font_size: sp(13)
    bold: True
    color: hex('ffffff')
    bg: 'f87171'
    canvas.before:
        Color:
            rgba: hex(self.bg) if self.state == 'normal' else [c*0.85 for c in hex(self.bg)[:3]] + [1]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(6)]

<SmallBtn@ButtonBehavior+Label>:
    size_hint: None, None
    size: dp(52), dp(26)
    font_size: sp(10)
    bold: True
    color: hex('c8ccd4')
    canvas.before:
        Color:
            rgba: hex('3a3f4b')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(4)]

<Tag@ToggleButton>:
    size_hint: None, None
    size: dp(64), dp(32)
    font_size: sp(12)
    background_color: 0,0,0,0
    background_normal: ''
    background_down: ''
    color: hex('c8ccd4') if self.state == 'normal' else hex('1a1d23')
    bold: True
    canvas.before:
        Color:
            rgba: hex('34d399') if self.state == 'down' else hex('282d38')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(4)]

<CheckBtn@ButtonBehavior+BoxLayout>:
    size_hint: None, None
    size: dp(28), dp(28)
    checked: True
    on_release: self.checked = not self.checked
    canvas.before:
        Color:
            rgba: hex('34d399') if self.checked else hex('3a3f4b')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(4)]
    Label:
        text: '\\u2713' if root.checked else ''
        font_size: sp(16)
        bold: True
        color: hex('1a1d23')
        halign: 'center'
        valign: 'middle'

<DlRow>:
    size_hint_y: None
    height: dp(72)
    padding: dp(6)
    spacing: dp(8)
    orientation: 'horizontal'
    canvas.before:
        Color:
            rgba: hex('282d38')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(4)]

    # checkbox
    CheckBtn:
        id: chk
        pos_hint: {'center_y': 0.5}
        checked: root.selected
        on_checked: root.selected = self.checked

    # thumbnail
    BoxLayout:
        size_hint: None, None
        size: dp(80), dp(52)
        pos_hint: {'center_y': 0.5}
        canvas.before:
            Color:
                rgba: hex('22262e')
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(3)]
        AsyncImage:
            source: root.thumb
            size_hint: None, None
            size: dp(80), dp(52)
            pos: self.parent.pos
            allow_stretch: True
            keep_ratio: True
            canvas.before:
                StencilPush
                RoundedRectangle:
                    pos: self.parent.pos
                    size: self.parent.size
                    radius: [dp(3)]
                StencilUse
            canvas.after:
                StencilUnUse
                RoundedRectangle:
                    pos: self.parent.pos
                    size: self.parent.size
                    radius: [dp(3)]
                StencilPop

    # info
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(3)
        padding: 0, dp(2)
        Label:
            text: root.title
            font_size: sp(11)
            color: hex('c8ccd4') if root.selected else hex('6b7280')
            text_size: self.width, None
            shorten: True
            shorten_from: 'right'
            halign: 'left'
            valign: 'top'
            size_hint_y: None
            height: sp(28)
            max_lines: 2
        Label:
            text: root.duration
            font_size: sp(10)
            color: hex('6b7280')
            halign: 'left'
            text_size: self.size
            size_hint_y: None
            height: sp(12)
            opacity: 1 if root.duration else 0
        BoxLayout:
            spacing: dp(6)
            size_hint_y: None
            height: dp(10)
            Widget:
                canvas:
                    Color:
                        rgba: hex('3a3f4b')
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(2)]
                    Color:
                        rgba: hex('34d399') if root.status == 'done' else (hex('f87171') if root.status == 'error' else (hex('fbbf24') if root.status == 'skip' else hex('60a5fa')))
                    RoundedRectangle:
                        pos: self.pos
                        size: self.width * (root.pct / 100.0), self.height
                        radius: [dp(2)]
            Label:
                text: root.note
                font_size: sp(10)
                color: hex('6b7280')
                size_hint_x: None
                width: dp(65)
                halign: 'right'
                text_size: self.size

<FolderPopup>:
    title: 'pilih folder'
    title_size: sp(14)
    title_color: hex('c8ccd4')
    separator_color: hex('3a3f4b')
    size_hint: 0.92, 0.8
    background_color: hex('1a1d23')
    background: ''
    canvas.before:
        Color:
            rgba: hex('1a1d23')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(8)
        padding: dp(4)
        Label:
            id: cur_path
            text: ''
            font_size: sp(11)
            color: hex('6b7280')
            halign: 'left'
            text_size: self.width, None
            size_hint_y: None
            height: sp(16)
            shorten: True
            shorten_from: 'left'
        FileChooserListView:
            id: fc
            path: root.start_path
            dirselect: True
            filters: [root.folder_filter]
            size_hint_y: 1
            canvas.before:
                Color:
                    rgba: hex('22262e')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(4)]
            on_path: cur_path.text = self.path
        BoxLayout:
            size_hint_y: None
            height: dp(42)
            spacing: dp(8)
            OutlineBtn:
                text: 'batal'
                on_release: root.dismiss()
            FlatBtn:
                text: 'pilih folder ini'
                on_release: root.pick()

<Root>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: hex('1a1d23')
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(50)
        padding: dp(16), 0
        Label:
            text: 'yt downloader'
            font_size: sp(16)
            bold: True
            color: hex('c8ccd4')
            halign: 'left'
            text_size: self.size
            valign: 'center'
        Label:
            text: 'v1.3'
            font_size: sp(10)
            color: hex('6b7280')
            halign: 'right'
            text_size: self.size
            valign: 'center'
            size_hint_x: None
            width: dp(36)

    Widget:
        size_hint_y: None
        height: dp(1)
        canvas:
            Color:
                rgba: hex('3a3f4b')
            Rectangle:
                pos: self.pos
                size: self.size

    ScrollView:
        do_scroll_x: False
        bar_width: dp(2)
        bar_color: hex('3a3f4b')

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: dp(16), dp(12)
            spacing: dp(12)

            # url
            Label:
                text: 'url'
                font_size: sp(11)
                color: hex('6b7280')
                halign: 'left'
                text_size: self.size
                size_hint_y: None
                height: sp(14)
            BoxLayout:
                size_hint_y: None
                height: dp(42)
                spacing: dp(6)
                TextInput:
                    id: inp
                    hint_text: 'youtube.com/watch?v=... atau /playlist?list=...'
                    multiline: False
                    font_size: sp(13)
                    foreground_color: hex('c8ccd4')
                    hint_text_color: hex('6b7280')
                    cursor_color: hex('34d399')
                    background_color: 0,0,0,0
                    padding: dp(10), dp(10)
                    canvas.before:
                        Color:
                            rgba: hex('22262e')
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(4)]
                        Color:
                            rgba: hex('3a3f4b')
                        Line:
                            rounded_rectangle: self.x, self.y, self.width, self.height, dp(4)
                            width: 1
                OutlineBtn:
                    text: 'paste'
                    size_hint_x: None
                    width: dp(56)
                    on_release: root.do_paste()

            # format + quality
            BoxLayout:
                size_hint_y: None
                height: dp(60)
                spacing: dp(16)
                BoxLayout:
                    orientation: 'vertical'
                    spacing: dp(6)
                    Label:
                        text: 'format'
                        font_size: sp(11)
                        color: hex('6b7280')
                        halign: 'left'
                        text_size: self.size
                        size_hint_y: None
                        height: sp(14)
                    BoxLayout:
                        spacing: dp(4)
                        size_hint_y: None
                        height: dp(32)
                        Tag:
                            text: 'mp3'
                            group: 'fmt'
                            state: 'down'
                            on_state: if self.state=='down': root.pick_fmt('mp3')
                        Tag:
                            text: 'mp4'
                            group: 'fmt'
                            on_state: if self.state=='down': root.pick_fmt('mp4')
                        Widget:
                BoxLayout:
                    orientation: 'vertical'
                    spacing: dp(6)
                    Label:
                        text: 'quality'
                        font_size: sp(11)
                        color: hex('6b7280')
                        halign: 'left'
                        text_size: self.size
                        size_hint_y: None
                        height: sp(14)
                    BoxLayout:
                        id: qual_row
                        spacing: dp(4)
                        size_hint_y: None
                        height: dp(32)

            # save to
            BoxLayout:
                size_hint_y: None
                height: dp(28)
                spacing: dp(6)
                Label:
                    text: root.dl_display
                    font_size: sp(11)
                    color: hex('6b7280')
                    halign: 'left'
                    text_size: self.width, None
                    shorten: True
                    shorten_from: 'left'
                    valign: 'center'
                SmallBtn:
                    text: 'ubah'
                    on_release: root.open_folder_picker()

            # tombol fetch + download/stop
            BoxLayout:
                size_hint_y: None
                height: dp(42)
                spacing: dp(8)
                OutlineBtn:
                    text: 'fetch'
                    on_release: root.fetch()
                FlatBtn:
                    id: btn_dl
                    text: 'download'
                    on_release: root.start_download()
                    opacity: 1 if not root.is_downloading else 0
                    disabled: root.is_downloading
                    size_hint_x: 1 if not root.is_downloading else 0.001
                StopBtn:
                    id: btn_stop
                    text: 'stop'
                    on_release: root.stop_download()
                    opacity: 1 if root.is_downloading else 0
                    disabled: not root.is_downloading
                    size_hint_x: 1 if root.is_downloading else 0.001

            # select all / deselect / counter
            BoxLayout:
                size_hint_y: None
                height: dp(26) if root.has_items else 0
                opacity: 1 if root.has_items else 0
                spacing: dp(6)
                SmallBtn:
                    text: 'semua'
                    size: dp(52), dp(26)
                    on_release: root.select_all(True)
                SmallBtn:
                    text: 'reset'
                    size: dp(52), dp(26)
                    on_release: root.select_all(False)
                Label:
                    text: root.sel_count_text
                    font_size: sp(10)
                    color: hex('6b7280')
                    halign: 'right'
                    text_size: self.size
                    valign: 'center'

            # status
            Label:
                id: lbl_status
                text: ''
                font_size: sp(11)
                color: hex('6b7280')
                halign: 'left'
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1] if self.text else 0
                markup: True

            # list
            BoxLayout:
                id: dl_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(6)

            Widget:
                size_hint_y: None
                height: dp(16)
"""


def _get_thumb(vid_id):
    if vid_id:
        return f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg"
    return ""

def _extract_id(url):
    for p in [r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})', r'(?:embed/)([a-zA-Z0-9_-]{11})']:
        m = re.search(p, str(url))
        if m:
            return m.group(1)
    return ""

def _fmt_dur(sec):
    if not sec:
        return ""
    sec = int(sec)
    if sec >= 3600:
        return f"{sec//3600}:{(sec%3600)//60:02d}:{sec%60:02d}"
    return f"{sec//60}:{sec%60:02d}"


class FolderPopup(Popup):
    start_path = StringProperty("")

    def __init__(self, start, callback, **kw):
        self.start_path = start if os.path.isdir(start) else os.path.expanduser("~")
        self._cb = callback
        super().__init__(**kw)

    @staticmethod
    def folder_filter(folder, filename, is_dir):
        return is_dir

    def pick(self):
        fc = self.ids.fc
        sel = fc.selection
        chosen = sel[0] if sel and os.path.isdir(sel[0]) else fc.path
        if self._cb:
            self._cb(chosen)
        self.dismiss()


class DlRow(BoxLayout):
    title = StringProperty("")
    thumb = StringProperty("")
    duration = StringProperty("")
    pct = NumericProperty(0)
    status = StringProperty("wait")
    note = StringProperty("...")
    selected = BooleanProperty(True)


class Root(BoxLayout):
    fmt = StringProperty("mp3")
    qual = StringProperty("best")
    videos = ListProperty([])
    dl_path = StringProperty("")
    dl_display = StringProperty("")
    is_downloading = BooleanProperty(False)
    has_items = BooleanProperty(False)
    sel_count_text = StringProperty("")

    _q = {
        "mp3": [("128k", "128"), ("192k", "192"), ("320k", "320")],
        "mp4": [("360p", "360"), ("720p", "720"), ("1080p", "1080")],
    }

    def __init__(self, **kw):
        super().__init__(**kw)
        self._stop_flag = threading.Event()
        self._dl_thread = None
        self.dl_path = load_dl_path()
        os.makedirs(self.dl_path, exist_ok=True)
        self._update_dl_display()
        Clock.schedule_once(self._setup, 0)

    def _update_dl_display(self):
        p = self.dl_path
        home = os.path.expanduser("~")
        if p.startswith(home):
            p = "~" + p[len(home):]
        self.dl_display = f"simpan ke: {p}"

    def _update_sel_count(self, *a):
        rows = list(self.ids.dl_list.children)
        total = len(rows)
        sel = sum(1 for r in rows if r.selected)
        self.sel_count_text = f"{sel}/{total} dipilih"

    def _setup(self, dt):
        self._fill_qual()
        if kv_platform == "android":
            request_permissions([
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
            ])

    def open_folder_picker(self):
        FolderPopup(start=self.dl_path, callback=self._folder_picked).open()

    def _folder_picked(self, path):
        self.dl_path = path
        os.makedirs(self.dl_path, exist_ok=True)
        save_dl_path(path)
        self._update_dl_display()
        self._msg(f"[color=34d399]folder: {path}[/color]")

    def pick_fmt(self, f):
        self.fmt = f
        self._fill_qual()

    def _fill_qual(self):
        box = self.ids.qual_row
        box.clear_widgets()
        first = True
        for label, val in self._q[self.fmt]:
            from kivy.factory import Factory
            t = Factory.Tag()
            t.text = label
            t.group = "qual"
            t.bind(on_release=partial(self._pick_qual, val))
            if first:
                t.state = "down"
                self.qual = val
                first = False
            box.add_widget(t)
        box.add_widget(BoxLayout())

    def _pick_qual(self, val, inst):
        if inst.state == "down":
            self.qual = val

    def select_all(self, state):
        for row in self.ids.dl_list.children:
            row.selected = state
            row.ids.chk.checked = state
        self._update_sel_count()

    def do_paste(self):
        try:
            t = Clipboard.paste()
            if t:
                self.ids.inp.text = t.strip()
        except:
            pass

    def _msg(self, txt):
        self.ids.lbl_status.text = txt

    # --- fetch ---
    def fetch(self):
        url = self.ids.inp.text.strip()
        if not url:
            self._msg("[color=f87171]masukin url dulu[/color]")
            return
        if not HAS_YTDLP:
            self._msg("[color=f87171]yt-dlp belum terinstall[/color]")
            return
        if self.is_downloading:
            self._msg("[color=fbbf24]tunggu download selesai atau stop dulu[/color]")
            return

        self._msg("[color=60a5fa]loading...[/color]")
        self.ids.dl_list.clear_widgets()
        self.videos = []
        self.has_items = False
        threading.Thread(target=self._fetch_bg, args=(url,), daemon=True).start()

    def _fetch_bg(self, url):
        try:
            opts = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist", "skip_download": True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

            vids = []
            if "entries" in info:
                for e in info["entries"]:
                    if not e:
                        continue
                    vid_id = e.get("id", "")
                    vid_url = e.get("url") or e.get("webpage_url") or f"https://www.youtube.com/watch?v={vid_id}"
                    if not vid_id:
                        vid_id = _extract_id(vid_url)
                    vids.append({
                        "url": vid_url, "title": e.get("title", "?"),
                        "id": vid_id, "thumb": _get_thumb(vid_id),
                        "duration": _fmt_dur(e.get("duration", 0)),
                    })
                txt = f"[color=34d399]playlist: {info.get('title','?')}[/color] ({len(vids)} video)"
            else:
                vid_id = info.get("id", "") or _extract_id(url)
                vids.append({
                    "url": info.get("webpage_url", url), "title": info.get("title", "?"),
                    "id": vid_id, "thumb": _get_thumb(vid_id),
                    "duration": _fmt_dur(info.get("duration", 0)),
                })
                txt = f"[color=34d399]{info.get('title','?')}[/color] {_fmt_dur(info.get('duration', 0))}"

            Clock.schedule_once(partial(self._fetched, vids, txt), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._msg(f"[color=f87171]{str(e)[:100]}[/color]"), 0)

    def _fetched(self, vids, txt, dt):
        self.videos = vids
        self._msg(txt)
        lst = self.ids.dl_list
        lst.clear_widgets()
        for v in vids:
            row = DlRow()
            row.title = v["title"]
            row.thumb = v["thumb"]
            row.duration = v["duration"]
            row.vid_url = v["url"]
            row.bind(selected=lambda *a: Clock.schedule_once(lambda dt: self._update_sel_count(), 0))
            lst.add_widget(row)
        self.has_items = len(vids) > 0
        self._update_sel_count()

    # --- download ---
    def start_download(self):
        if not self.videos:
            self._msg("[color=f87171]fetch dulu[/color]")
            return
        if not HAS_YTDLP:
            return

        # cek ada yg dipilih nggak
        rows = list(self.ids.dl_list.children[::-1])
        sel_rows = [r for r in rows if r.selected]
        if not sel_rows:
            self._msg("[color=fbbf24]pilih minimal 1 video[/color]")
            return

        self._stop_flag.clear()
        self.is_downloading = True
        self._msg("[color=60a5fa]downloading...[/color]")
        self._dl_thread = threading.Thread(target=self._dl_bg, daemon=True)
        self._dl_thread.start()

    def stop_download(self):
        self._stop_flag.set()
        self._msg("[color=fbbf24]stopping...[/color]")

    def _dl_bg(self):
        rows = list(self.ids.dl_list.children[::-1])
        ok = 0
        fail = 0
        skip = 0
        stopped = False

        for row in rows:
            # cek stop
            if self._stop_flag.is_set():
                stopped = True
                Clock.schedule_once(partial(self._upd, row, 0, "skip", "stopped"), 0)
                continue

            # skip yg nggak dipilih
            if not row.selected:
                skip += 1
                Clock.schedule_once(partial(self._upd, row, 0, "skip", "skip"), 0)
                continue

            url = row.vid_url
            Clock.schedule_once(partial(self._upd, row, 0, "dl", "0%"), 0)

            try:
                if self.fmt == "mp3":
                    opts = {
                        "format": "bestaudio/best",
                        "outtmpl": os.path.join(self.dl_path, "%(title)s.%(ext)s"),
                        "postprocessors": [{
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": self.qual,
                        }],
                        "progress_hooks": [lambda d, r=row: self._hook(d, r)],
                        "quiet": True, "no_warnings": True,
                    }
                else:
                    opts = {
                        "format": f"bestvideo[height<={self.qual}]+bestaudio/best[height<={self.qual}]/best",
                        "outtmpl": os.path.join(self.dl_path, "%(title)s.%(ext)s"),
                        "merge_output_format": "mp4",
                        "progress_hooks": [lambda d, r=row: self._hook(d, r)],
                        "quiet": True, "no_warnings": True,
                    }

                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])

                if self._stop_flag.is_set():
                    stopped = True
                    Clock.schedule_once(partial(self._upd, row, row.pct, "skip", "stopped"), 0)
                    continue

                ok += 1
                Clock.schedule_once(partial(self._upd, row, 100, "done", "ok"), 0)
            except Exception as e:
                fail += 1
                Clock.schedule_once(partial(self._upd, row, 0, "error", str(e)[:30]), 0)

        # summary
        parts = []
        if ok:
            parts.append(f"[color=34d399]{ok} selesai[/color]")
        if fail:
            parts.append(f"[color=f87171]{fail} gagal[/color]")
        if stopped:
            parts.append(f"[color=fbbf24]dihentikan[/color]")
        if skip and not stopped:
            parts.append(f"[color=6b7280]{skip} dilewati[/color]")
        s = "  ".join(parts) if parts else "[color=6b7280]selesai[/color]"

        Clock.schedule_once(lambda dt: self._msg(s), 0)
        Clock.schedule_once(lambda dt: setattr(self, 'is_downloading', False), 0)

    def _hook(self, d, row):
        # cek stop di tengah download
        if self._stop_flag.is_set():
            raise Exception("stopped by user")

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            got = d.get("downloaded_bytes", 0)
            p = (got / total * 100) if total else 0
            spd = d.get("speed")
            if spd:
                s = f"{spd/1024:.0f}k/s" if spd < 1048576 else f"{spd/1048576:.1f}m/s"
            else:
                s = "..."
            Clock.schedule_once(partial(self._upd, row, p, "dl", f"{p:.0f}% {s}"), 0)
        elif d["status"] == "finished":
            Clock.schedule_once(partial(self._upd, row, 95, "dl", "convert..."), 0)

    @staticmethod
    def _upd(row, pct, status, note, dt):
        row.pct = pct
        row.status = status
        row.note = note


class YTDLApp(App):
    title = "yt downloader"

    def build(self):
        Builder.load_string(KV)
        Window.clearcolor = (0.102, 0.114, 0.137, 1)
        return Root()

    def on_start(self):
        if kv_platform == "android":
            try:
                from jnius import autoclass
                act = autoclass("org.kivy.android.PythonActivity").mActivity
                clr = autoclass("android.graphics.Color")
                act.getWindow().setStatusBarColor(clr.parseColor("#1a1d23"))
            except:
                pass


if __name__ == "__main__":
    YTDLApp().run()
