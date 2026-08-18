import sys
import json
import os
import glob
import logging
from datetime import datetime
from PySide6.QtCore import Qt, QUrl, QPoint
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                               QSystemTrayIcon, QMenu, QFrame, QMessageBox, 
                               QSizeGrip, QHBoxLayout)
from PySide6.QtWebSockets import QWebSocket
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

TS_WS_URL = "ws://127.0.0.1:5899"
CONFIG_FILE = "ts_overlay_config.json"
VERSION = "v1.0.0"
GITHUB_REPO = "https://github.com/taker1988/ts6-overlay"
GITHUB_API_LATEST = "https://api.github.com/repos/taker1988/ts6-overlay/releases/latest"

LANG = {
    "de": {
        "lock": "Position fixieren",
        "quit": "Beenden",
        "lang": "Sprache",
        "app_name": "TS6 Overlay by taker1988",
        "about": "Über",
        "update_check": "Auf Updates prüfen",
        "waiting": "Warte auf TeamSpeak Daten...",
        "update_ok": "Du nutzt die aktuellste Version.",
        "update_new": "Eine neue Version ist verfügbar!",
        "update_err": "Update-Prüfung fehlgeschlagen.",
        "developer": "Entwickler"
    },
    "en": {
        "lock": "Lock Position",
        "quit": "Quit",
        "lang": "Language",
        "app_name": "TS6 Overlay by taker1988",
        "about": "About",
        "update_check": "Check for updates",
        "waiting": "Waiting for TeamSpeak data...",
        "update_ok": "You are using the latest version.",
        "update_new": "A new version is available!",
        "update_err": "Update check failed.",
        "developer": "Developer"
    }
}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def setup_logging():
    log_pattern = "ts_overlay_log_*.log"
    logs = sorted(glob.glob(log_pattern))
    
    while len(logs) >= 5:
        oldest_log = logs.pop(0)
        try:
            os.remove(oldest_log)
        except OSError:
            pass

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"ts_overlay_log_{current_time}.log"

    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info(f"Log-Datei erstellt: {log_file}")
    return log_file

class TSOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.is_locked = False
        self.old_pos = QPoint()
        self.users = {}
        self.known_names = {}
        
        self.config = self.load_config()
        self.api_key = self.config.get("api_key")
        self.current_lang = self.config.get("lang", "de")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setMinimumSize(250, 100)
        
        icon_path = resource_path("ts6icon.ico")
        self.setWindowIcon(QIcon(icon_path))

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_frame = QFrame(self)
        self.main_layout.addWidget(self.main_frame)

        self.layout = QVBoxLayout(self.main_frame)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        self.placeholder = QLabel(LANG[self.current_lang]["waiting"])
        self.apply_style(self.placeholder, False)
        self.layout.addWidget(self.placeholder)
        
        self.layout.addStretch()

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addStretch()
        self.size_grip = QSizeGrip(self)
        self.bottom_layout.addWidget(self.size_grip)
        self.layout.addLayout(self.bottom_layout)

        self.net_manager = QNetworkAccessManager(self)
        self.net_manager.finished.connect(self.on_update_check_finished)

        self.setup_tray()
        self.setup_websocket()
        self.update_window_style()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Fehler beim Laden der Konfiguration: {e}")
        return {"api_key": None, "lang": "de"}

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"api_key": self.api_key, "lang": self.current_lang}, f)
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Konfiguration: {e}")

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        icon_path = resource_path("ts6icon.ico")
        self.tray_icon.setIcon(QIcon(icon_path))
        
        self.tray_menu = QMenu()
        self.build_menus(self.tray_menu)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def build_menus(self, parent_menu):
        self.lock_action = QAction(LANG[self.current_lang]["lock"], self)
        self.lock_action.setCheckable(True)
        self.lock_action.setChecked(self.is_locked)
        self.lock_action.triggered.connect(self.toggle_lock)
        parent_menu.addAction(self.lock_action)
        
        parent_menu.addSeparator()

        self.lang_menu = QMenu(LANG[self.current_lang]["lang"], parent_menu)
        self.action_de = QAction("Deutsch", self)
        self.action_en = QAction("English", self)
        self.action_de.triggered.connect(lambda: self.change_language("de"))
        self.action_en.triggered.connect(lambda: self.change_language("en"))
        self.lang_menu.addAction(self.action_de)
        self.lang_menu.addAction(self.action_en)
        parent_menu.addMenu(self.lang_menu)
        
        self.update_action = QAction(LANG[self.current_lang]["update_check"], self)
        self.update_action.triggered.connect(self.check_update)
        parent_menu.addAction(self.update_action)
        
        self.about_action = QAction(LANG[self.current_lang]["about"], self)
        self.about_action.triggered.connect(self.show_about)
        parent_menu.addAction(self.about_action)
        
        parent_menu.addSeparator()

        self.quit_action = QAction(LANG[self.current_lang]["quit"], self)
        self.quit_action.triggered.connect(QApplication.instance().quit)
        parent_menu.addAction(self.quit_action)

    def change_language(self, lang_code):
        self.current_lang = lang_code
        self.save_config()
        self.update_ui_texts()

    def update_ui_texts(self):
        self.tray_menu.clear()
        self.build_menus(self.tray_menu)
        
        if not self.users:
            self.placeholder.setText(LANG[self.current_lang]["waiting"])

    def show_about(self):
        msg = QMessageBox()
        msg.setWindowTitle(LANG[self.current_lang]["about"])
        text = (
            f"<b>{LANG[self.current_lang]['app_name']}</b><br><br>"
            f"Version: {VERSION}<br>"
            f"{LANG[self.current_lang]['developer']}: taker1988<br><br>"
            f"GitHub Repository:<br>"
            f"<a href='{GITHUB_REPO}'>{GITHUB_REPO}</a>"
        )
        msg.setText(text)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        
        icon_path = resource_path("ts6icon.ico")
        msg.setIconPixmap(QPixmap(icon_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
        msg.exec()

    def check_update(self):
        logging.info("Suche nach Updates...")
        req = QNetworkRequest(QUrl(GITHUB_API_LATEST))
        self.net_manager.get(req)

    def on_update_check_finished(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            try:
                data = json.loads(reply.readAll().data().decode())
                latest_version = data.get("tag_name", VERSION)
                if latest_version != VERSION:
                    logging.info(f"Update verfügbar: {latest_version}")
                    QMessageBox.information(None, LANG[self.current_lang]["update_check"], f"{LANG[self.current_lang]['update_new']}\nLatest: {latest_version}")
                else:
                    logging.info("Kein Update verfügbar.")
                    QMessageBox.information(None, LANG[self.current_lang]["update_check"], LANG[self.current_lang]["update_ok"])
            except Exception as e:
                logging.error(f"Fehler beim Verarbeiten der Update-Antwort: {e}")
                QMessageBox.warning(None, LANG[self.current_lang]["update_check"], LANG[self.current_lang]["update_err"])
        else:
            logging.error(f"Netzwerkfehler bei Update-Prüfung: {reply.errorString()}")
            QMessageBox.warning(None, LANG[self.current_lang]["update_check"], LANG[self.current_lang]["update_err"])
        reply.deleteLater()

    def setup_websocket(self):
        self.ws = QWebSocket()
        self.ws.connected.connect(self.on_connected)
        self.ws.textMessageReceived.connect(self.on_message)
        self.ws.errorOccurred.connect(self.on_ws_error)
        self.ws.open(QUrl(TS_WS_URL))

    def on_ws_error(self, error):
        logging.error(f"WebSocket Fehler: {error}")

    def update_window_style(self):
        style = "QFrame { background-color: rgba(0, 0, 0, 30); border: 1px solid rgba(255, 255, 255, 15); border-radius: 4px; }"
        self.main_frame.setStyleSheet(style)
        
        if self.is_locked:
            self.size_grip.hide()
        else:
            self.size_grip.show()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, self.is_locked)
        self.update_window_style()
        self.apply_style(self.placeholder, False)
        for label in self.users.values():
            self.apply_style(label, is_talking=False)
        self.hide()
        self.show()

    def apply_style(self, label, is_talking=False):
        if is_talking:
            bg_color = "rgba(76, 175, 80, 50)" 
            border = "2px solid #4CAF50"       
        else:
            bg_color = "transparent"
            border = "2px solid transparent"   

        style = f"""
            QLabel {{
                color: white;
                background-color: {bg_color};
                border: {border};
                border-radius: 4px;
                padding: 4px;
                margin: 2px;
            }}
        """
        label.setStyleSheet(style)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_locked:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if not self.is_locked and not self.old_pos.isNull():
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = QPoint()

    def on_connected(self):
        logging.info("WebSocket verbunden. Sende Auth-Payload.")
        auth_payload = {
            "type": "auth",
            "payload": {
                "identifier": "ts6-custom-overlay",
                "version": "1.0.0",
                "name": LANG["de"]["app_name"],
                "description": "Overlay for Linux and Windows",
                "content": {}
            }
        }
        
        if self.api_key:
            auth_payload["payload"]["content"]["apiKey"] = self.api_key
            
        self.ws.sendTextMessage(json.dumps(auth_payload))

    def scrape_for_users(self, obj):
        if isinstance(obj, dict):
            c_id = obj.get("id") or obj.get("clientId")
            props = obj.get("properties")
            if isinstance(props, dict):
                name = props.get("nickname")
                if c_id is not None and name:
                    str_id = str(c_id)
                    self.known_names[str_id] = name
                    if str_id not in self.users:
                        self.update_user(str_id, name, False)
            for v in obj.values():
                self.scrape_for_users(v)
        elif isinstance(obj, list):
            for item in obj:
                self.scrape_for_users(item)

    def on_message(self, message):
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            logging.error(f"Fehler beim Decodieren der JSON-Nachricht: {e}")
            return

        msg_type = data.get("type", "")
        payload = data.get("payload", {})

        if msg_type != "auth":
            logging.debug(f"Event: {msg_type} | Payload: {json.dumps(payload)}")

        self.scrape_for_users(data)

        if msg_type == "auth":
            api_key = payload.get("apiKey")
            if api_key and api_key != self.api_key:
                logging.info("Neuer API-Key empfangen und gespeichert.")
                self.api_key = api_key
                self.save_config()
            
            req_payload = {
                "type": "clientList",
                "payload": {}
            }
            self.ws.sendTextMessage(json.dumps(req_payload))

        client_id = str(payload.get("clientId", payload.get("id", "")))
        props = payload.get("properties", payload)
        
        if client_id and ("flagTalking" in props or "status" in payload):
            val = props.get("flagTalking") if "flagTalking" in props else payload.get("status")
            is_talking = str(val).lower() in ("1", "true")
            name = self.known_names.get(client_id, self.get_existing_name(client_id)) 
            
            if name != "Unknown":
                logging.debug(f"Sprecher-Status erkannt: {name} ({client_id}) -> {is_talking}")
                self.update_user(client_id, name, is_talking)

    def get_existing_name(self, client_id):
        if client_id in self.users:
            return self.users[client_id].property("raw_name")
        return "Unknown"

    def update_user(self, client_id, name, is_talking):
        self.placeholder.hide()
        
        if client_id not in self.users:
            label = QLabel()
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setProperty("raw_name", name)
            self.layout.insertWidget(self.layout.count() - 2, label)
            self.users[client_id] = label

        label = self.users[client_id]
        label.setProperty("raw_name", name)
        
        speaker_icon = "&nbsp;<span style='color: #4CAF50;'>🔊</span>" if is_talking else ""
        label.setText(f"<span style='color: #2196F3;'>👤</span> {name}{speaker_icon}")
        
        self.apply_style(label, is_talking)

if __name__ == "__main__":
    setup_logging()
    logging.info("TS6 Overlay wird gestartet.")
    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)
    
    icon_path = resource_path("ts6icon.ico")
    app.setWindowIcon(QIcon(icon_path))
    
    overlay = TSOverlay()
    overlay.show()
    sys.exit(app.exec())