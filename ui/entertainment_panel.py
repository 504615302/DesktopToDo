from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QCursor
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSizePolicy,
    QStackedWidget,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from ui.icons import stroke_icon
from ui.framed_dialog import FramedDialog
from ui.styles import Theme


def format_duration(milliseconds: int) -> str:
    total_seconds = max(0, int(round(milliseconds / 1000)))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


class _ResponsiveVideoStage(QWidget):
    def __init__(self, display: QStackedWidget, parent=None):
        super().__init__(parent)
        self._display = display
        self._display.setParent(self)
        self._scale_percent = 100
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(180, 101)

    def set_display_scale(self, percent: int) -> None:
        self._scale_percent = percent
        self._layout_display()

    def display_geometry(self):
        return self._display.geometry()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._layout_display()

    def _layout_display(self) -> None:
        if self.width() <= 0 or self.height() <= 0:
            return
        available_width = max(1, int(self.width() * self._scale_percent / 100))
        available_height = max(1, int(self.height() * self._scale_percent / 100))
        display_height = min(available_height, max(1, available_width * 9 // 16))
        display_width = min(available_width, display_height * 16 // 9)
        x = (self.width() - display_width) // 2
        y = (self.height() - display_height) // 2
        self._display.setGeometry(x, y, display_width, display_height)


class EntertainmentSettingsDialog(FramedDialog):
    def __init__(self, theme: Theme, panel: "EntertainmentPanel", parent=None):
        super().__init__(theme, "播放设置", parent, width=360)
        self._theme = theme
        self._panel = panel

        self.file_label = QLabel(panel._file_text)
        self.file_label.setWordWrap(True)
        self.root.addWidget(self.file_label)

        self.select_button = QPushButton("选择视频")
        self.select_button.setMinimumHeight(34)
        self.select_button.clicked.connect(self._select_video)
        self.stop_button = QPushButton("停止")
        self.stop_button.setMinimumHeight(34)
        self.stop_button.clicked.connect(panel._stop)
        buttons = QHBoxLayout()
        buttons.addWidget(self.select_button)
        buttons.addWidget(self.stop_button)
        self.root.addLayout(buttons)

        volume_head = QHBoxLayout()
        volume_head.addWidget(self.caption("音量"))
        self.volume_value = QLabel(f"{int(round(panel.audio_output.volume() * 100))}%")
        self.volume_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        volume_head.addWidget(self.volume_value)
        self.root.addLayout(volume_head)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(round(panel.audio_output.volume() * 100)))
        self.volume_slider.valueChanged.connect(self._set_volume)
        self.root.addWidget(self.volume_slider)

        self.mute_check = QCheckBox("静音")
        self.mute_check.setChecked(panel.audio_output.isMuted())
        self.mute_check.toggled.connect(panel.audio_output.setMuted)
        self.root.addWidget(self.mute_check)

        size_head = QHBoxLayout()
        size_head.addWidget(self.caption("画面大小"))
        self.size_value = QLabel(f"{panel._display_scale}%")
        self.size_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        size_head.addWidget(self.size_value)
        self.root.addLayout(size_head)
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(50, 100)
        self.size_slider.setValue(panel._display_scale)
        self.size_slider.valueChanged.connect(self._set_display_scale)
        self.root.addWidget(self.size_slider)

    def _select_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择本地视频",
            str(Path.home()),
            "Videos (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm);;All Files (*)",
        )
        if path:
            self._panel._load_video(Path(path))
            self.accept()

    def _set_volume(self, value: int) -> None:
        self._panel._set_volume(value)
        self.volume_value.setText(f"{value}%")

    def _set_display_scale(self, value: int) -> None:
        self._panel._set_display_scale(value)
        self.size_value.setText(f"{value}%")


class EntertainmentPanel(QWidget):
    cinema_mode_changed = Signal(bool)

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._source_path: Path | None = None
        self._cinema_mode = False
        self._file_text = "未选择视频"
        self._display_scale = 100

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.8)
        self.player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget()
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.player.setVideoOutput(self.video_widget)

        self.placeholder = QLabel("选择一个本地视频，在页面内播放")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setWordWrap(True)

        self.display = QStackedWidget()
        self.display.addWidget(self.placeholder)
        self.display.addWidget(self.video_widget)

        self.video_stage = _ResponsiveVideoStage(self.display)
        self.video_stage.setObjectName("videoStage")

        stage_host = QHBoxLayout()
        stage_host.setContentsMargins(0, 0, 0, 0)
        stage_host.addWidget(self.video_stage, 1)

        self.play_button = QPushButton()
        self.play_button.setToolTip("播放")
        self.play_button.clicked.connect(self._toggle_playback)
        self.cinema_button = QPushButton("影音模式")
        self.cinema_button.clicked.connect(
            lambda: self.set_cinema_mode(not self._cinema_mode)
        )
        self.settings_button = QPushButton()
        self.settings_button.setToolTip("播放设置")
        self.settings_button.clicked.connect(self._open_settings)
        for button in (self.play_button, self.settings_button):
            button.setFixedSize(44, 36)
            button.setIconSize(QSize(18, 18))
        self.cinema_button.setMinimumWidth(84)
        self.cinema_button.setMinimumHeight(36)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderPressed.connect(self._seek_from_slider)
        self.position_slider.sliderMoved.connect(self.player.setPosition)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        controls.addWidget(self.position_slider, 1)
        controls.addWidget(self.play_button)
        controls.addWidget(self.cinema_button)
        controls.addWidget(self.settings_button)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addLayout(stage_host, 1)
        root.addLayout(controls)

        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.errorOccurred.connect(self._on_player_error)

        self._set_display_scale(self._display_scale)
        self._apply_styles()
        self._sync_control_icons()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._apply_styles()
        self._sync_control_icons()

    def pause(self) -> None:
        self.player.pause()

    def handle_key(self, event) -> bool:
        key = event.key()
        if key == Qt.Key.Key_Left:
            self.adjust_position(-5)
            return True
        if key == Qt.Key.Key_Right:
            self.adjust_position(5)
            return True
        if key == Qt.Key.Key_Up:
            self.adjust_volume(5)
            return True
        if key == Qt.Key.Key_Down:
            self.adjust_volume(-5)
            return True
        return False

    def adjust_position(self, delta_seconds: int) -> None:
        duration = self.player.duration()
        target = max(0, self.player.position() + delta_seconds * 1000)
        if duration > 0:
            target = min(int(duration), target)
        self.player.setPosition(target)
        self.position_slider.setValue(target)
        QToolTip.showText(
            QCursor.pos(),
            f"{format_duration(target)} / {format_duration(duration)}",
            self,
        )

    def adjust_volume(self, delta_percent: int) -> None:
        value = max(0, min(100, round(self.audio_output.volume() * 100 + delta_percent)))
        self._set_volume(value)
        QToolTip.showText(QCursor.pos(), f"音量 {value}%", self)

    def set_cinema_mode(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if self._cinema_mode == enabled:
            return
        self._cinema_mode = enabled
        self.cinema_button.setText("退出影音" if enabled else "影音模式")
        self.cinema_mode_changed.emit(enabled)

    def _choose_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择本地视频",
            str(Path.home()),
            "Videos (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm);;All Files (*)",
        )
        if path:
            self._load_video(Path(path))

    def _load_video(self, path: Path) -> None:
        self._source_path = path
        self._file_text = path.name
        self.display.setCurrentWidget(self.video_widget)
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.play()

    def _toggle_playback(self) -> None:
        if self._source_path is None:
            self._choose_video()
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _stop(self) -> None:
        self.player.pause()
        self.player.setPosition(0)

    def _set_volume(self, value: int) -> None:
        self.audio_output.setVolume(value / 100.0)

    def _set_display_scale(self, percent: int) -> None:
        self._display_scale = percent
        self.video_stage.set_display_scale(percent)

    def _seek_from_slider(self) -> None:
        self.player.setPosition(self.position_slider.value())

    def _on_duration_changed(self, duration: int) -> None:
        self.position_slider.setRange(0, max(0, int(duration)))
        self._update_time_label()

    def _on_position_changed(self, position: int) -> None:
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(max(0, int(position)))
        self.position_slider.blockSignals(False)
        self._update_time_label()

    def _on_playback_state_changed(self, state) -> None:
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_button.setToolTip("暂停" if playing else "播放")
        self._sync_control_icons()

    def _on_player_error(self, _error, message: str) -> None:
        if self._source_path is not None:
            self._file_text = f"{self._source_path.name} - {message}"

    def _update_time_label(self) -> None:
        self.position_slider.setToolTip(
            f"{format_duration(self.player.position())} / "
            f"{format_duration(self.player.duration())}"
        )

    def _apply_styles(self) -> None:
        radius = max(6, min(12, self._theme.radius))
        self.placeholder.setStyleSheet(
            f"background: {self._theme.surface}; color: {self._theme.text_secondary}; "
            f"border: 1px solid {self._theme.border}; border-radius: {radius}px; font-size: 13px;"
        )
        self.video_stage.setStyleSheet(
            f"#videoStage {{ background: transparent; }}"
        )
        self.settings_button.setToolTip("播放设置")

    def _sync_control_icons(self) -> None:
        color = self._theme.text
        playing = self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        self.play_button.setIcon(stroke_icon("pause" if playing else "play", color))
        self.settings_button.setIcon(stroke_icon("settings", color))

    def _open_settings(self) -> None:
        EntertainmentSettingsDialog(self._theme, self, self.window()).exec()
