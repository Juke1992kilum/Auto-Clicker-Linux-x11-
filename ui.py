import threading

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QSpinBox,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)

from core.config import load_config, save_config
from core.clicker import ClickController
from core.hotkey import GlobalHotkey


# ============================================================
# SIGNAL BRIDGE
# ============================================================

class SignalBridge(QObject):
    hotkey_pressed = pyqtSignal()


# ============================================================
# MAIN WINDOW
# ============================================================

class AutoClickerWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.cfg = load_config()
        self.clicker = ClickController()
        self.listener = None  # ✅ for safe shutdown

        self.bridge = SignalBridge()
        self.bridge.hotkey_pressed.connect(self.toggle_clicking)

        self.setWindowTitle("AutoClicker Pro")
        self.setMinimumSize(380, 450)

        self.setStyleSheet(self.load_styles())

        self.build_ui()
        self.load_ui_values()

        self.start_hotkey_listener()

    # --------------------------------------------------------
    # UI BUILD
    # --------------------------------------------------------

    def build_ui(self):
        root = QVBoxLayout()
        root.setSpacing(14)
        root.setContentsMargins(16, 16, 16, 16)

        title = QLabel("AutoClicker Pro")
        subtitle = QLabel("Fast, minimal, global autoclicker")

        title.setObjectName("title")
        subtitle.setObjectName("subtitle")

        root.addWidget(title)
        root.addWidget(subtitle)

        # ---------------- INTERVAL ----------------
        interval_card = self.create_card("Click Interval")

        self.minutes = self.make_spinbox(0, 9999)
        self.seconds = self.make_spinbox(0, 59)
        self.milliseconds = self.make_spinbox(1, 999)  # ✅ SHOULD FIX: avoid 0ms crash

        interval_layout = QHBoxLayout()
        interval_layout.setSpacing(10)

        interval_layout.addWidget(self.labeled_box("Min", self.minutes))
        interval_layout.addWidget(self.labeled_box("Sec", self.seconds))
        interval_layout.addWidget(self.labeled_box("Ms", self.milliseconds))

        interval_card.layout().addLayout(interval_layout)
        root.addWidget(interval_card)

        # ---------------- HOTKEY ----------------
        hotkey_card = self.create_card("Global Hotkey")

        self.hotkey = QComboBox()
        self.hotkey.addItems(
            ["F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12"]
        )
        self.hotkey.setMinimumHeight(36)

        hotkey_card.layout().addWidget(self.hotkey)
        root.addWidget(hotkey_card)

        # ---------------- STATUS ----------------
        status_card = self.create_card("Status")

        self.status = QLabel("Stopped")
        self.status.setObjectName("status_off")

        status_card.layout().addWidget(self.status)
        root.addWidget(status_card)

        # ---------------- BUTTONS ----------------
        controls = QHBoxLayout()

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")

        self.start_button.setObjectName("start")
        self.stop_button.setObjectName("stop")

        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)

        root.addLayout(controls)

        self.setLayout(root)

        # signals
        self.start_button.clicked.connect(self.start_clicking)
        self.stop_button.clicked.connect(self.stop_clicking)

        self.minutes.valueChanged.connect(self.save_settings)
        self.seconds.valueChanged.connect(self.save_settings)
        self.milliseconds.valueChanged.connect(self.save_settings)
        self.hotkey.currentTextChanged.connect(self.hotkey_changed)

    # --------------------------------------------------------
    # FIXED SPINBOX
    # --------------------------------------------------------

    def make_spinbox(self, minimum, maximum):
        box = QSpinBox()

        box.setRange(minimum, maximum)
        box.setFixedWidth(110)
        box.setFixedHeight(34)

        box.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        box.setKeyboardTracking(True)
        box.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)

        line = box.lineEdit()
        line.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return box

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------

    def create_card(self, title):
        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        label = QLabel(title)
        label.setObjectName("card_title")

        layout.addWidget(label)
        return card

    def labeled_box(self, label_text, widget):
        container = QVBoxLayout()
        container.setSpacing(4)

        label = QLabel(label_text)
        label.setObjectName("small_label")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container.addWidget(label)
        container.addWidget(widget)

        box = QFrame()
        box.setLayout(container)
        return box

    # --------------------------------------------------------
    # CONFIG (SAFE GET FIX)
    # --------------------------------------------------------

    def load_ui_values(self):
        cfg = self.cfg

        self.minutes.setValue(cfg.get("minutes", 0))
        self.seconds.setValue(cfg.get("seconds", 0))
        self.milliseconds.setValue(cfg.get("milliseconds", 100))
        self.hotkey.setCurrentText(cfg.get("hotkey", "F6"))

        self.update_interval()

    def update_interval(self):
        total = (
            self.minutes.value() * 60
            + self.seconds.value()
            + self.milliseconds.value() / 1000
        )

        # safety clamp
        self.clicker.interval = max(total, 0.001)

    def save_settings(self):
        self.update_interval()

        self.cfg["minutes"] = self.minutes.value()
        self.cfg["seconds"] = self.seconds.value()
        self.cfg["milliseconds"] = self.milliseconds.value()

        save_config(self.cfg)

    def hotkey_changed(self, value):
        self.cfg["hotkey"] = value
        save_config(self.cfg)

    # --------------------------------------------------------
    # CONTROL
    # --------------------------------------------------------

    def start_clicking(self):
        self.update_interval()
        self.clicker.start()
        self.status.setText("Running")

    def stop_clicking(self):
        self.clicker.stop()
        self.status.setText("Stopped")

    def toggle_clicking(self):
        if self.clicker.running:
            self.stop_clicking()
        else:
            self.start_clicking()

    # --------------------------------------------------------
    # HOTKEY (SAFE REF + STOP SUPPORT)
    # --------------------------------------------------------

    def start_hotkey_listener(self):
        self.listener = GlobalHotkey(
            self.cfg.get("hotkey", "F6"),
            lambda: self.bridge.hotkey_pressed.emit(),
        )

        thread = threading.Thread(
            target=self.listener.run,
            daemon=True,
        )
        thread.start()

    def closeEvent(self, event):
        # safe shutdown
        try:
            if self.listener:
                self.listener.stop()
        except:
            pass

        self.clicker.stop()
        event.accept()

    # --------------------------------------------------------
    # STYLE (unchanged)
    # --------------------------------------------------------

    def load_styles(self):
        return """
        QWidget {
            background-color: #0f1115;
            color: #eaeaea;
            font-size: 13px;
        }

        #title {
            font-size: 22px;
            font-weight: bold;
        }

        #subtitle {
            color: #9aa4b2;
        }

        #card {
            background-color: #171a21;
            border-radius: 12px;
            padding: 12px;
        }

        #card_title {
            font-weight: bold;
        }

        QSpinBox, QComboBox {
            background-color: #1f2430;
            border: 1px solid #2b3242;
            border-radius: 6px;
            padding: 6px;
            color: white;
        }

        QPushButton#start {
            background-color: #FF6A3D;
            color: black;
            padding: 10px;
            border-radius: 8px;
        }

        QPushButton#stop {
            background-color: #2b3242;
            color: white;
            padding: 10px;
            border-radius: 8px;
        }
        """