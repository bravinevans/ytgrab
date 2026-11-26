#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PyQt6.QtCore import QProcess, QStandardPaths
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

STYLESHEET = """
QMainWindow, QWidget {
    background-color: #141517;
    color: #e4e6eb;
    font-family: "Noto Sans", "Inter", sans-serif;
    font-size: 13px;
}
QFrame#Card {
    background-color: #1c1e21;
    border: 1px solid #2c2f34;
    border-radius: 6px;
}
QLabel#Title {
    font-size: 17px;
    font-weight: 700;
    color: #f4f5f7;
}
QLabel#Muted {
    color: #8e9299;
    font-size: 12px;
}
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit#UrlBox {
    background-color: #111214;
    border: 1px solid #32363c;
    border-radius: 4px;
    padding: 7px 10px;
    color: #f0f2f5;
    selection-background-color: #3a414a;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit#UrlBox:focus {
    border: 1px solid #6b7280;
}
QPushButton {
    background-color: #272a2f;
    border: 1px solid #383c43;
    border-radius: 4px;
    padding: 7px 14px;
    color: #e4e6eb;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #32363d;
}
QPushButton:disabled {
    background-color: #1a1c1f;
    color: #5c6066;
    border-color: #25272b;
}
QPushButton#Primary {
    background-color: #e4e6eb;
    color: #111214;
    border: 1px solid #e4e6eb;
}
QPushButton#Primary:hover {
    background-color: #ffffff;
}
QPushButton#Primary:disabled {
    background-color: #2c2f34;
    color: #6c7077;
    border-color: #2c2f34;
}
QPushButton#Danger {
    background-color: #2d1b1e;
    color: #f28b82;
    border: 1px solid #5c2b30;
}
QPushButton#Danger:hover {
    background-color: #3b2226;
}
QProgressBar {
    background-color: #111214;
    border: 1px solid #2c2f34;
    border-radius: 4px;
    height: 18px;
    text-align: center;
    color: #e4e6eb;
    font-size: 11px;
    font-weight: 600;
}
QProgressBar::chunk {
    background-color: #9ca3af;
    border-radius: 3px;
}
QPlainTextEdit#LogBox {
    background-color: #0e0f11;
    border: 1px solid #26292e;
    border-radius: 4px;
    color: #a8adb5;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11.5px;
    padding: 6px;
}
"""


def parse_youtube_url(raw_url: str) -> tuple[str, str | None, str | None]:
    url = raw_url.strip()
    if not url:
        return "single", None, None

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    video_id = qs.get("v", [None])[0]
    list_id = qs.get("list", [None])[0]

    if not video_id and "youtu.be" in parsed.netloc:
        path_id = parsed.path.lstrip("/").split("/")[0]
        if path_id:
            video_id = path_id

    if list_id:
        if list_id.startswith("RD"):
            if not video_id and len(list_id) >= 13:
                video_id = list_id[2:13]
            return "automix", video_id, list_id
        return "playlist", video_id, list_id

    return "single", video_id, None


class YTGrabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ytgrab")
        self.setMinimumSize(720, 640)
        self.process: QProcess | None = None
        self.queue: list[str] = []
        self.queue_index = 0
        self.queue_total = 0
        self.had_errors = False
        self.cancelled = False

        data_dir = Path(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
            or (Path.home() / ".local" / "share" / "ytgrab")
        )
        data_dir.mkdir(parents=True, exist_ok=True)
        self.archive_file = data_dir / "archive.txt"

        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("ytgrab")
        title.setObjectName("Title")
        subtitle = QLabel("Universal yt-dlp batch & playlist extractor")
        subtitle.setObjectName("Muted")
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch()
        layout.addLayout(header)

        # Input Card
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(11)

        url_header = QHBoxLayout()
        url_header.addWidget(QLabel("URLs (one per line):"))
        self.detected_badge = QLabel("Ready")
        self.detected_badge.setObjectName("Muted")
        url_header.addStretch()
        url_header.addWidget(self.detected_badge)
        card_layout.addLayout(url_header)

        url_row = QHBoxLayout()
        self.url_box = QPlainTextEdit()
        self.url_box.setObjectName("UrlBox")
        self.url_box.setFixedHeight(84)
        self.url_box.setPlaceholderText(
            "Paste one or more YouTube links (videos, playlists, or RD Auto-Mixes) — one per line..."
        )
        self.url_box.textChanged.connect(self._on_urls_changed)

        url_btns = QVBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.clicked.connect(self._paste_clipboard)
        clear_url_btn = QPushButton("Clear")
        clear_url_btn.clicked.connect(self.url_box.clear)
        url_btns.addWidget(paste_btn)
        url_btns.addWidget(clear_url_btn)
        url_btns.addStretch()

        url_row.addWidget(self.url_box)
        url_row.addLayout(url_btns)
        card_layout.addLayout(url_row)

        # Mode & Format Row
        opts_row = QHBoxLayout()
        opts_row.addWidget(QLabel("Link Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Auto-Detect per URL (Recommended)",
            "Force Single Video",
            "Force Playlist",
            "Force Auto-Mix (RD)",
        ])
        opts_row.addWidget(self.mode_combo)

        opts_row.addSpacing(10)
        opts_row.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "MP3 (Best V0 Audio)",
            "M4A (AAC Audio)",
            "FLAC (Lossless Audio)",
            "MP4 (1080p Video)",
            "Best Video + Audio (MKV)",
        ])
        opts_row.addWidget(self.format_combo)

        opts_row.addSpacing(10)
        opts_row.addWidget(QLabel("Max Tracks:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(0, 500)
        self.limit_spin.setValue(30)
        self.limit_spin.setSpecialValueText("Unlimited")
        opts_row.addWidget(self.limit_spin)
        card_layout.addLayout(opts_row)

        # Resilience & Metadata Row 1
        flags_row1 = QHBoxLayout()
        self.chk_metadata = QCheckBox("Embed Thumbnail & Metadata")
        self.chk_metadata.setChecked(True)

        self.chk_archive = QCheckBox("Skip Already Downloaded (Archive)")
        self.chk_archive.setChecked(True)

        flags_row1.addWidget(self.chk_metadata)
        flags_row1.addSpacing(14)
        flags_row1.addWidget(self.chk_archive)
        flags_row1.addStretch()
        card_layout.addLayout(flags_row1)

        # Resilience Row 2
        flags_row2 = QHBoxLayout()
        self.chk_pacing = QCheckBox("Anti-403 Pacing (3-7s sleep)")
        self.chk_pacing.setChecked(True)

        self.chk_cookies = QCheckBox("Browser Cookies:")
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["firefox", "chromium", "brave", "chrome", "vivaldi", "edge"])
        self.browser_combo.setEnabled(False)
        self.chk_cookies.toggled.connect(self.browser_combo.setEnabled)

        flags_row2.addWidget(self.chk_pacing)
        flags_row2.addSpacing(14)
        flags_row2.addWidget(self.chk_cookies)
        flags_row2.addWidget(self.browser_combo)
        flags_row2.addStretch()
        card_layout.addLayout(flags_row2)

        # Output Folder Row
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Save to:"))
        music_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MusicLocation)
        if not music_dir or not os.path.isdir(music_dir):
            music_dir = os.path.expanduser("~")
        self.dir_input = QLineEdit(music_dir)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._choose_dir)
        out_row.addWidget(self.dir_input)
        out_row.addWidget(browse_btn)
        card_layout.addLayout(out_row)

        layout.addWidget(card)

        # Progress Section
        prog_header = QHBoxLayout()
        self.status_label = QLabel("Idle")
        self.track_label = QLabel("")
        self.track_label.setObjectName("Muted")
        prog_header.addWidget(self.status_label)
        prog_header.addStretch()
        prog_header.addWidget(self.track_label)
        layout.addLayout(prog_header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Log Console
        self.log_box = QPlainTextEdit()
        self.log_box.setObjectName("LogBox")
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

        # Action Buttons
        btn_row = QHBoxLayout()
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.log_box.clear)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("Danger")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_download)

        self.download_btn = QPushButton("Download")
        self.download_btn.setObjectName("Primary")
        self.download_btn.clicked.connect(self._start_queue)

        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.download_btn)
        layout.addLayout(btn_row)

    def _get_urls(self) -> list[str]:
        return [line.strip() for line in self.url_box.toPlainText().splitlines() if line.strip()]

    def _paste_clipboard(self):
        text = QApplication.clipboard().text()
        if not text:
            return
        existing = self.url_box.toPlainText().strip()
        cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        self.url_box.setPlainText(f"{existing}\n{cleaned}".strip() if existing else cleaned)

    def _choose_dir(self):
        chosen = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.dir_input.text())
        if chosen:
            self.dir_input.setText(chosen)

    def _on_urls_changed(self):
        urls = self._get_urls()
        if not urls:
            self.detected_badge.setText("Ready")
            return

        counts = {"single": 0, "playlist": 0, "automix": 0}
        for u in urls:
            mode, _, _ = parse_youtube_url(u)
            counts[mode] += 1

        if len(urls) == 1:
            mode, video_id, _ = parse_youtube_url(urls[0])
            labels = {
                "automix": f"1 URL • RD Auto-Mix (seed: {video_id or 'unknown'})",
                "playlist": "1 URL • Standard Playlist",
                "single": "1 URL • Single Video",
            }
            self.detected_badge.setText(labels[mode])
        else:
            parts = [f"{v} {k}" for k, v in counts.items() if v > 0]
            self.detected_badge.setText(f"{len(urls)} URLs queued ({', '.join(parts)})")

    def _resolve_mode_for_url(self, raw_url: str) -> str:
        choice = self.mode_combo.currentIndex()
        if choice == 1:
            return "single"
        if choice == 2:
            return "playlist"
        if choice == 3:
            return "automix"
        mode, _, _ = parse_youtube_url(raw_url)
        return mode

    def _build_command(self, raw_url: str) -> tuple[str, list[str]]:
        mode = self._resolve_mode_for_url(raw_url)
        _, video_id, list_id = parse_youtube_url(raw_url)
        out_dir = self.dir_input.text().strip() or os.path.expanduser("~")

        args = ["--newline", "--progress", "--ignore-errors"]
        is_batch = mode in ("automix", "playlist")

        if mode == "automix":
            target_url = (
                f"https://www.youtube.com/watch?v={video_id}&list={list_id}"
                if (list_id and video_id)
                else raw_url
            )
            args.append("--yes-playlist")
            if self.limit_spin.value() > 0:
                args.extend(["--playlist-end", str(self.limit_spin.value())])
            out_template = os.path.join(out_dir, "%(playlist_title)s", "%(playlist_index)s - %(title)s.%(ext)s")

        elif mode == "playlist":
            target_url = raw_url
            args.append("--yes-playlist")
            if self.limit_spin.value() > 0:
                args.extend(["--playlist-end", str(self.limit_spin.value())])
            out_template = os.path.join(out_dir, "%(playlist_title)s", "%(playlist_index)s - %(title)s.%(ext)s")

        else:
            target_url = raw_url
            args.append("--no-playlist")
            out_template = os.path.join(out_dir, "%(title)s.%(ext)s")

        fmt = self.format_combo.currentText()
        if fmt.startswith("MP3"):
            args.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
        elif fmt.startswith("M4A"):
            args.extend(["-x", "--audio-format", "m4a", "--audio-quality", "0"])
        elif fmt.startswith("FLAC"):
            args.extend(["-x", "--audio-format", "flac"])
        elif fmt.startswith("MP4"):
            args.extend(["-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best"])
        else:
            args.extend(["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mkv"])

        if self.chk_metadata.isChecked():
            args.extend(["--embed-thumbnail", "--add-metadata"])

        if self.chk_archive.isChecked():
            args.extend(["--download-archive", str(self.archive_file)])

        if is_batch and self.chk_pacing.isChecked():
            args.extend(["--sleep-requests", "1.5", "--sleep-interval", "3", "--max-sleep-interval", "7"])

        if self.chk_cookies.isChecked():
            args.extend(["--cookies-from-browser", self.browser_combo.currentText()])

        args.extend(["-o", out_template, target_url])
        return "yt-dlp", args

    def _cleanup_orphaned_thumbnails(self):
        out_dir = Path(self.dir_input.text().strip() or os.path.expanduser("~"))
        if not out_dir.is_dir():
            return
        removed = 0
        for ext in ("*.webp", "*.jpg"):
            for thumb in out_dir.glob(f"**/{ext}"):
                if len(thumb.relative_to(out_dir).parts) <= 2:
                    try:
                        thumb.unlink()
                        removed += 1
                    except OSError:
                        pass
        if removed:
            self.log_box.appendPlainText(f"[ytgrab] Cleaned up {removed} orphaned thumbnail file(s).")

    def _start_queue(self):
        urls = self._get_urls()
        if not urls:
            self.status_label.setText("Paste at least one URL first.")
            return

        self.queue = urls
        self.queue_index = 0
        self.queue_total = len(urls)
        self.had_errors = False
        self.cancelled = False

        self.log_box.clear()
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self._run_next_in_queue()

    def _run_next_in_queue(self):
        if self.cancelled or self.queue_index >= self.queue_total:
            self._finish_queue()
            return

        current_url = self.queue[self.queue_index]
        self.queue_index += 1

        cmd, args = self._build_command(current_url)
        self.log_box.appendPlainText(f"\n=== Queue [{self.queue_index}/{self.queue_total}] ===")
        self.log_box.appendPlainText(f"$ {cmd} {' '.join(args)}\n")

        self.progress_bar.setValue(0)
        self.status_label.setText(f"Queue {self.queue_index}/{self.queue_total}: Starting...")
        self.track_label.setText(f"URL {self.queue_index} of {self.queue_total}")

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._on_process_output)
        self.process.finished.connect(self._on_item_finished)
        self.process.start(cmd, args)

    def _cancel_download(self):
        self.cancelled = True
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.status_label.setText("Cancelling...")
            self.process.terminate()
            if not self.process.waitForFinished(2000):
                self.process.kill()

    def _on_process_output(self):
        if not self.process:
            return
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        prefix = f"URL {self.queue_index}/{self.queue_total}"
        for line in data.splitlines():
            clean = line.strip()
            if not clean:
                continue

            item_match = re.search(r"Downloading item (\d+) of (\d+)", clean)
            if item_match:
                cur, tot = item_match.group(1), item_match.group(2)
                self.track_label.setText(f"{prefix} • Track {cur} of {tot}")

            pct_match = re.search(r"\[download\]\s+(\d+(?:\.\d+)?)%", clean)
            if pct_match:
                pct = float(pct_match.group(1))
                self.progress_bar.setValue(int(pct))
                self.status_label.setText(f"{prefix}: Downloading... {pct:.1f}%")
                continue

            if "Sleeping" in clean and "seconds" in clean:
                self.status_label.setText(f"{prefix}: Pacing requests (anti-403 sleep)...")

            if "[ExtractAudio]" in clean:
                self.status_label.setText(f"{prefix}: Converting audio with ffmpeg...")

            self.log_box.appendPlainText(clean)

    def _on_item_finished(self, exit_code: int, _exit_status):
        if exit_code != 0:
            self.had_errors = True
        self._run_next_in_queue()

    def _finish_queue(self):
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self._cleanup_orphaned_thumbnails()

        if self.cancelled:
            self.status_label.setText("Cancelled by user")
        elif not self.had_errors:
            self.progress_bar.setValue(100)
            self.status_label.setText(f"Completed ({self.queue_total} URL{'s' if self.queue_total != 1 else ''})")
        else:
            self.status_label.setText("Queue finished with some warnings/errors (see log)")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    win = YTGrabWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
