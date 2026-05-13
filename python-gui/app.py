#!/usr/bin/env python3
"""
ATEM REC OBS Timecode GUI

Aplicação desktop em Python/PySide6 para macOS, com backend de comunicação ATEM
executado por um helper Node.js baseado em atem-connection. A GUI controla IP,
FPS e arquivo TXT usado pelo OBS, preservando a lógica estável do projeto
original para leitura do status REC/timecode.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QProcess, QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "ATEM REC OBS Timecode"
ORG_NAME = "HendricSiqueira"
DEFAULT_IP = "192.168.2.146"
DEFAULT_FPS = 60
DEFAULT_UPDATE_MS = 100
DEFAULT_RECONNECT_MS = 5000


@dataclass
class AppConfig:
    atem_ip: str
    fps: int
    output_file: str
    update_interval_ms: int
    reconnect_interval_ms: int
    auto_clear_on_start: bool


class AtemGui(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings(ORG_NAME, APP_NAME)
        self.process: QProcess | None = None
        self.is_running = False
        self.current_status = "idle"
        self.script_dir = Path(__file__).resolve().parent
        self.bridge_script = self.script_dir / "backend" / "atem_node_bridge.js"
        self.default_output = self.script_dir / "rec-live.txt"

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(860, 620)
        self._build_ui()
        self._build_menu()
        self._load_settings()
        self._apply_idle_state("Pronto para conectar")

        self.file_watch_timer = QTimer(self)
        self.file_watch_timer.setInterval(1000)
        self.file_watch_timer.timeout.connect(self._refresh_file_hint)
        self.file_watch_timer.start()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Arquivo")

        open_output_action = QAction("Abrir pasta do TXT", self)
        open_output_action.triggered.connect(self.open_output_folder)
        file_menu.addAction(open_output_action)

        file_menu.addSeparator()
        quit_action = QAction("Sair", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = self.menuBar().addMenu("Ajuda")
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)

        title = QLabel("ATEM REC OBS Timecode")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        root.addWidget(title)

        subtitle = QLabel(
            "Monitore o REC/timecode da ATEM e atualize um TXT de uma linha para leitura no OBS."
        )
        subtitle.setStyleSheet("color: #555;")
        root.addWidget(subtitle)

        config_group = QGroupBox("Configuração")
        config_layout = QGridLayout(config_group)
        config_layout.setHorizontalSpacing(12)
        config_layout.setVerticalSpacing(10)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Ex.: 192.168.2.146")
        config_layout.addWidget(QLabel("IP da ATEM:"), 0, 0)
        config_layout.addWidget(self.ip_input, 0, 1)

        self.fps_combo = QComboBox()
        for fps in [23, 24, 25, 29, 30, 50, 59, 60]:
            self.fps_combo.addItem(str(fps), fps)
        self.fps_combo.setEditable(True)
        config_layout.addWidget(QLabel("FPS:"), 0, 2)
        config_layout.addWidget(self.fps_combo, 0, 3)

        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText(str(self.default_output))
        browse_button = QPushButton("Escolher...")
        browse_button.clicked.connect(self.choose_output_file)
        config_layout.addWidget(QLabel("Arquivo TXT para OBS:"), 1, 0)
        config_layout.addWidget(self.output_input, 1, 1, 1, 2)
        config_layout.addWidget(browse_button, 1, 3)

        advanced_group = QGroupBox("Ajustes avançados")
        advanced_layout = QFormLayout(advanced_group)
        self.update_spin = QSpinBox()
        self.update_spin.setRange(50, 2000)
        self.update_spin.setSingleStep(50)
        self.update_spin.setSuffix(" ms")
        advanced_layout.addRow("Atualização do TXT:", self.update_spin)

        self.reconnect_spin = QSpinBox()
        self.reconnect_spin.setRange(1000, 60000)
        self.reconnect_spin.setSingleStep(500)
        self.reconnect_spin.setSuffix(" ms")
        advanced_layout.addRow("Tentativa de reconexão:", self.reconnect_spin)

        self.clear_on_start = QCheckBox("Reescrever mensagem inicial ao conectar")
        advanced_layout.addRow("", self.clear_on_start)

        config_layout.addWidget(advanced_group, 2, 0, 1, 4)
        root.addWidget(config_group)

        status_group = QGroupBox("Status ao vivo")
        status_layout = QGridLayout(status_group)
        status_layout.setSpacing(12)

        self.connection_badge = QLabel("DESCONECTADO")
        self.connection_badge.setAlignment(Qt.AlignCenter)
        self.connection_badge.setMinimumHeight(44)
        self.connection_badge.setStyleSheet(self._badge_style("#6b7280"))
        status_layout.addWidget(QLabel("Conexão:"), 0, 0)
        status_layout.addWidget(self.connection_badge, 0, 1)

        self.rec_badge = QLabel("AGUARDANDO")
        self.rec_badge.setAlignment(Qt.AlignCenter)
        self.rec_badge.setMinimumHeight(44)
        self.rec_badge.setStyleSheet(self._badge_style("#6b7280"))
        status_layout.addWidget(QLabel("REC:"), 0, 2)
        status_layout.addWidget(self.rec_badge, 0, 3)

        self.preview_label = QLabel("Aguardando REC na ATEM...")
        preview_font = QFont("Menlo")
        preview_font.setPointSize(20)
        preview_font.setBold(True)
        self.preview_label.setFont(preview_font)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.preview_label.setMinimumHeight(88)
        self.preview_label.setStyleSheet(
            "background: #111827; color: #f9fafb; border-radius: 10px; padding: 18px;"
        )
        status_layout.addWidget(self.preview_label, 1, 0, 1, 4)

        self.file_hint = QLabel("")
        self.file_hint.setStyleSheet("color: #555;")
        status_layout.addWidget(self.file_hint, 2, 0, 1, 4)

        root.addWidget(status_group)

        controls = QHBoxLayout()
        self.start_button = QPushButton("Conectar e iniciar")
        self.start_button.setMinimumHeight(44)
        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button = QPushButton("Parar")
        self.stop_button.setMinimumHeight(44)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        root.addLayout(controls)

        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(140)
        self.log_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        log_layout.addWidget(self.log_output)
        root.addWidget(log_group, 1)

        self.setStatusBar(QStatusBar(self))

    def _badge_style(self, color: str) -> str:
        return (
            f"background: {color}; color: white; border-radius: 8px; "
            "font-weight: 700; padding: 8px 14px; letter-spacing: 0.5px;"
        )

    def _load_settings(self) -> None:
        self.ip_input.setText(self.settings.value("atem_ip", DEFAULT_IP))
        fps_value = int(self.settings.value("fps", DEFAULT_FPS))
        index = self.fps_combo.findData(fps_value)
        if index >= 0:
            self.fps_combo.setCurrentIndex(index)
        else:
            self.fps_combo.setEditText(str(fps_value))
        self.output_input.setText(self.settings.value("output_file", str(self.default_output)))
        self.update_spin.setValue(int(self.settings.value("update_interval_ms", DEFAULT_UPDATE_MS)))
        self.reconnect_spin.setValue(int(self.settings.value("reconnect_interval_ms", DEFAULT_RECONNECT_MS)))
        self.clear_on_start.setChecked(self.settings.value("auto_clear_on_start", "true") == "true")
        self._refresh_file_hint()

    def _save_settings(self, cfg: AppConfig) -> None:
        self.settings.setValue("atem_ip", cfg.atem_ip)
        self.settings.setValue("fps", cfg.fps)
        self.settings.setValue("output_file", cfg.output_file)
        self.settings.setValue("update_interval_ms", cfg.update_interval_ms)
        self.settings.setValue("reconnect_interval_ms", cfg.reconnect_interval_ms)
        self.settings.setValue("auto_clear_on_start", "true" if cfg.auto_clear_on_start else "false")
        self.settings.sync()

    def _current_config(self) -> AppConfig:
        ip = self.ip_input.text().strip()
        fps_text = self.fps_combo.currentText().strip()
        output = self.output_input.text().strip() or str(self.default_output)
        if not ip:
            raise ValueError("Informe o IP da ATEM.")
        try:
            fps = int(float(fps_text))
        except ValueError as exc:
            raise ValueError("Informe um FPS válido, por exemplo 60 ou 30.") from exc
        if fps <= 0:
            raise ValueError("O FPS precisa ser maior que zero.")
        return AppConfig(
            atem_ip=ip,
            fps=fps,
            output_file=output,
            update_interval_ms=self.update_spin.value(),
            reconnect_interval_ms=self.reconnect_spin.value(),
            auto_clear_on_start=self.clear_on_start.isChecked(),
        )

    def choose_output_file(self) -> None:
        current = self.output_input.text().strip() or str(self.default_output)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Escolher arquivo TXT para o OBS",
            current,
            "Arquivos de texto (*.txt);;Todos os arquivos (*)",
        )
        if path:
            self.output_input.setText(path)
            self._refresh_file_hint()

    def start_monitoring(self) -> None:
        try:
            cfg = self._current_config()
        except ValueError as exc:
            QMessageBox.warning(self, "Configuração inválida", str(exc))
            return

        node_path = shutil.which("node")
        if not node_path:
            QMessageBox.critical(
                self,
                "Node.js não encontrado",
                "O backend de comunicação com a ATEM usa o pacote atem-connection via Node.js. "
                "Instale o Node.js LTS no macOS e execute npm install na pasta python-gui.",
            )
            return

        if not self.bridge_script.exists():
            QMessageBox.critical(self, "Backend não encontrado", f"Arquivo ausente: {self.bridge_script}")
            return

        package_dir = self.script_dir
        node_modules = package_dir / "node_modules" / "atem-connection"
        if not node_modules.exists():
            QMessageBox.critical(
                self,
                "Dependências Node ausentes",
                "Execute `npm install` dentro da pasta python-gui antes de iniciar a conexão.",
            )
            return

        output_path = Path(cfg.output_file).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if cfg.auto_clear_on_start:
            self._atomic_write(output_path, "⏺ Aguardando REC na ATEM...")

        self._save_settings(cfg)
        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(package_dir))
        self.process.setProgram(node_path)
        self.process.setArguments(
            [
                str(self.bridge_script),
                "--ip",
                cfg.atem_ip,
                "--fps",
                str(cfg.fps),
                "--output",
                str(output_path),
                "--update-ms",
                str(cfg.update_interval_ms),
                "--reconnect-ms",
                str(cfg.reconnect_interval_ms),
            ]
        )
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._process_finished)
        self.process.errorOccurred.connect(self._process_error)
        self.process.start()

        self.is_running = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self._set_inputs_enabled(False)
        self._apply_connecting_state(f"Conectando à ATEM em {cfg.atem_ip}...")
        self._log(f"Iniciando monitoramento: IP={cfg.atem_ip}, FPS={cfg.fps}, TXT={output_path}")

    def stop_monitoring(self) -> None:
        if self.process and self.process.state() != QProcess.NotRunning:
            self._log("Parando monitoramento...")
            self.process.terminate()
            if not self.process.waitForFinished(2500):
                self.process.kill()
        self._reset_process_state("Monitoramento parado")

    def _process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        status = "normal" if exit_status == QProcess.NormalExit else "com falha"
        self._log(f"Processo finalizado ({status}), código {exit_code}.")
        self._reset_process_state("Monitoramento finalizado")

    def _process_error(self, error: QProcess.ProcessError) -> None:
        self._log(f"Erro no processo: {error.name}")

    def _reset_process_state(self, message: str) -> None:
        self.is_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._set_inputs_enabled(True)
        self._apply_idle_state(message)
        self.process = None

    def _set_inputs_enabled(self, enabled: bool) -> None:
        for widget in [
            self.ip_input,
            self.fps_combo,
            self.output_input,
            self.update_spin,
            self.reconnect_spin,
            self.clear_on_start,
        ]:
            widget.setEnabled(enabled)

    def _read_stdout(self) -> None:
        if not self.process:
            return
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        for line in data.splitlines():
            self._handle_bridge_line(line.strip())

    def _read_stderr(self) -> None:
        if not self.process:
            return
        data = bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line.strip():
                self._log(f"Backend: {line.strip()}")

    def _handle_bridge_line(self, line: str) -> None:
        if not line:
            return
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            self._log(line)
            return

        event_type = event.get("type", "log")
        text = event.get("text") or event.get("message") or ""

        if event_type == "connected":
            self._apply_connected_state(text or "Conectado à ATEM")
        elif event_type == "disconnected":
            self._apply_connecting_state(text or "Desconectado. Tentando reconectar...")
        elif event_type == "recording":
            self._apply_recording_state(text)
        elif event_type == "stopped":
            self._apply_stopped_state(text)
        elif event_type == "idle":
            self._apply_waiting_rec_state(text)
        elif event_type == "waiting_tc":
            self._apply_waiting_tc_state(text)
        elif event_type == "error":
            self._log(f"Erro: {text}")
            self.statusBar().showMessage(text)
        else:
            self._log(text or line)

    def _apply_idle_state(self, text: str) -> None:
        self.connection_badge.setText("DESCONECTADO")
        self.connection_badge.setStyleSheet(self._badge_style("#6b7280"))
        self.rec_badge.setText("AGUARDANDO")
        self.rec_badge.setStyleSheet(self._badge_style("#6b7280"))
        self.preview_label.setText(text)
        self.statusBar().showMessage(text)

    def _apply_connecting_state(self, text: str) -> None:
        self.connection_badge.setText("CONECTANDO")
        self.connection_badge.setStyleSheet(self._badge_style("#f59e0b"))
        self.rec_badge.setText("AGUARDANDO")
        self.rec_badge.setStyleSheet(self._badge_style("#6b7280"))
        self.preview_label.setText(text)
        self.statusBar().showMessage(text)

    def _apply_connected_state(self, text: str) -> None:
        self.connection_badge.setText("CONECTADO")
        self.connection_badge.setStyleSheet(self._badge_style("#16a34a"))
        self.statusBar().showMessage(text)
        self._log(text)

    def _apply_waiting_rec_state(self, text: str) -> None:
        self.connection_badge.setText("CONECTADO")
        self.connection_badge.setStyleSheet(self._badge_style("#16a34a"))
        self.rec_badge.setText("SEM REC")
        self.rec_badge.setStyleSheet(self._badge_style("#6b7280"))
        self.preview_label.setText(text)
        self.statusBar().showMessage(text)

    def _apply_waiting_tc_state(self, text: str) -> None:
        self.rec_badge.setText("REC")
        self.rec_badge.setStyleSheet(self._badge_style("#dc2626"))
        self.preview_label.setText(text)
        self.statusBar().showMessage(text)

    def _apply_recording_state(self, text: str) -> None:
        self.connection_badge.setText("CONECTADO")
        self.connection_badge.setStyleSheet(self._badge_style("#16a34a"))
        self.rec_badge.setText("GRAVANDO")
        self.rec_badge.setStyleSheet(self._badge_style("#dc2626"))
        self.preview_label.setText(text)
        self.statusBar().showMessage(text)

    def _apply_stopped_state(self, text: str) -> None:
        self.rec_badge.setText("PARADO")
        self.rec_badge.setStyleSheet(self._badge_style("#2563eb"))
        self.preview_label.setText(text)
        self.statusBar().showMessage(text)
        self._log(text)

    def _log(self, text: str) -> None:
        if not text:
            return
        self.log_output.append(text)

    def _refresh_file_hint(self) -> None:
        path = Path((self.output_input.text().strip() if hasattr(self, "output_input") else "") or self.default_output).expanduser()
        exists = path.exists()
        state = "existe" if exists else "será criado ao iniciar"
        self.file_hint.setText(f"Arquivo OBS: {path} ({state})")

    def open_output_folder(self) -> None:
        path = Path(self.output_input.text().strip() or self.default_output).expanduser()
        folder = path.parent
        if sys.platform == "darwin":
            QProcess.startDetached("open", [str(folder)])
        else:
            QProcess.startDetached("xdg-open", [str(folder)])

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "Sobre",
            "ATEM REC OBS Timecode\n\n"
            "GUI em Python para macOS/Apple Silicon.\n"
            "A comunicação com a ATEM é feita por um helper local baseado em atem-connection, "
            "mantendo compatibilidade com o comportamento do projeto Node.js original.",
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - API Qt
        if self.process and self.process.state() != QProcess.NotRunning:
            self.stop_monitoring()
        event.accept()

    @staticmethod
    def _atomic_write(path: Path, text: str) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    window = AtemGui()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
