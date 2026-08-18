# TS6 Overlay (Windows)

[English Version](#english-version) | [Deutsche Version](#deutsche-version)

---

## English Version

A standalone TeamSpeak 6 overlay for Windows. Written in Python (PySide6) to display actively speaking users dynamically.

### Features
* **Real-time Talk Status:** Displays users currently speaking in your channel.
* **Lockable Position:** Move the overlay anywhere on your screen and lock it to make it click-through.
* **Transparent UI:** Unobtrusive design with dynamic resizing.
* **System Tray Control:** Manage settings, language, and updates directly via the taskbar.
* **Bilingual:** Available in English and German.

### Important Note
For the overlay to be visible while gaming, your games must be set to **Borderless Window** or **Windowed** mode. In exclusive Fullscreen mode, the game bypasses the operating system's window manager, hiding the overlay.

### Created Files
Upon launching, the application automatically creates the following files in its directory:
* `ts_overlay_config.json`: Stores the TeamSpeak API key and language preference.
* `ts_overlay_log_*.log`: Log files for troubleshooting. A maximum of 5 log files are kept; the oldest is automatically deleted.

### Installation & Usage
1. Download the latest `ts_overlay.exe` from the [Releases](https://github.com/taker1988/ts6-overlay/releases) page.
2. Run the executable.
3. Open TeamSpeak 6 and authorize the new connection request for the overlay.
4. Right-click the red icon in your System Tray to adjust settings or lock the overlay.

---

## Deutsche Version

Ein eigenständiges TeamSpeak 6 Overlay für Windows. Geschrieben in Python (PySide6), um aktuell sprechende Nutzer dynamisch anzuzeigen.

### Funktionen
* **Echtzeit Sprecher-Anzeige:** Zeigt an, wer gerade in deinem Channel spricht.
* **Position fixieren:** Platziere das Overlay frei auf dem Bildschirm und fixiere es, um Klicks an das Spiel durchzureichen.
* **Transparente UI:** Unauffälliges Design mit dynamischer Größenanpassung.
* **System Tray Steuerung:** Verwalte Einstellungen, Sprache und Updates direkt über die Taskleiste.
* **Zweisprachig:** Verfügbar in Deutsch und Englisch.

### Wichtiger Hinweis
Damit das Overlay im Spiel sichtbar ist, müssen Spiele im **Randlosen Fenster (Borderless Window)** oder im **Fenstermodus** ausgeführt werden. Im exklusiven Vollbildmodus umgeht das Spiel den Fenster-Manager des Betriebssystems, wodurch das Overlay verdeckt wird.

### Erstellte Dateien
Beim Start erstellt die Anwendung automatisch folgende Dateien in ihrem Verzeichnis:
* `ts_overlay_config.json`: Speichert den TeamSpeak API-Key und die Spracheinstellung.
* `ts_overlay_log_*.log`: Log-Dateien zur Fehlerbehebung. Es werden maximal 5 Dateien gespeichert; die älteste wird automatisch gelöscht.

### Installation & Nutzung
1. Lade die aktuellste `ts_overlay.exe` von der [Releases](https://github.com/taker1988/ts6-overlay/releases) Seite herunter.
2. Starte die Anwendung.
3. Öffne TeamSpeak 6 und erlaube die Verbindungsanfrage für das Overlay.
4. Mache einen Rechtsklick auf das rote Icon im System Tray (Taskleiste), um Einstellungen vorzunehmen oder das Overlay zu sperren.
