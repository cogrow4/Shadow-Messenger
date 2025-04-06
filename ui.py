import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit, 
                            QVBoxLayout, QWidget, QLineEdit, QLabel, QHBoxLayout,
                            QDialog, QInputDialog, QMessageBox, QGroupBox, QFrame,
                            QCheckBox, QSpinBox, QMenuBar, QMenu, QTabWidget,
                            QFormLayout, QComboBox, QSlider, QStackedWidget, QSizePolicy)
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QSize, QRect, QSettings, QTimer
from PyQt6.QtGui import QColor, QPalette, QFont, QTextCursor, QTextBlockFormat, QTextCharFormat, QAction
from network import MessengerNetwork

class MessageReceiver(QObject):
    message_received = pyqtSignal(str)

class ConnectionRequestDialog(QDialog):
    def __init__(self, username, ip, port, parent=None):
        super().__init__(parent)
        self.username = username
        self.ip = ip
        self.port = port
        self.result = False
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Connection Request")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Message
        message = QLabel(f"{self.username} ({self.ip}:{self.port}) wants to connect to you.")
        message.setWordWrap(True)
        layout.addWidget(message)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        accept_button = QPushButton("Accept")
        accept_button.clicked.connect(self.accept_connection)
        
        refuse_button = QPushButton("Refuse")
        refuse_button.clicked.connect(self.refuse_connection)
        
        button_layout.addWidget(accept_button)
        button_layout.addWidget(refuse_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def accept_connection(self):
        self.result = True
        self.accept()
        
    def refuse_connection(self):
        self.result = False
        self.accept()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Appearance tab
        appearance_tab = QWidget()
        appearance_layout = QFormLayout()
        
        # Theme selection
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(self.parent.theme)
        appearance_layout.addRow(theme_label, self.theme_combo)
        
        # Font size
        font_size_label = QLabel("Font Size:")
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 16)
        self.font_size_slider.setValue(self.parent.font_size)
        self.font_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.font_size_slider.setTickInterval(1)
        appearance_layout.addRow(font_size_label, self.font_size_slider)
        
        # Message bubble style
        bubble_style_label = QLabel("Message Style:")
        self.bubble_style_combo = QComboBox()
        self.bubble_style_combo.addItems(["Modern", "Classic", "Minimal"])
        self.bubble_style_combo.setCurrentText(self.parent.message_style)
        appearance_layout.addRow(bubble_style_label, self.bubble_style_combo)
        
        appearance_tab.setLayout(appearance_layout)
        
        # Security tab
        security_tab = QWidget()
        security_layout = QFormLayout()
        
        # Auto-accept connections
        self.auto_accept_check = QCheckBox("Auto-accept connections from known peers")
        self.auto_accept_check.setChecked(self.parent.auto_accept)
        security_layout.addRow("", self.auto_accept_check)
        
        # Save chat history
        self.save_history_check = QCheckBox("Save chat history")
        self.save_history_check.setChecked(self.parent.save_history)
        security_layout.addRow("", self.save_history_check)
        
        security_tab.setLayout(security_layout)
        
        # Network tab
        network_tab = QWidget()
        network_layout = QFormLayout()
        
        # Default port
        default_port_label = QLabel("Default Port:")
        self.default_port_spin = QSpinBox()
        self.default_port_spin.setRange(1024, 65535)
        self.default_port_spin.setValue(self.parent.default_port)
        network_layout.addRow(default_port_label, self.default_port_spin)
        
        # Connection timeout
        timeout_label = QLabel("Connection Timeout (seconds):")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 60)
        self.timeout_spin.setValue(self.parent.connection_timeout)
        network_layout.addRow(timeout_label, self.timeout_spin)
        
        # Auto-reconnect
        self.auto_reconnect_check = QCheckBox("Auto-reconnect on connection loss")
        self.auto_reconnect_check.setChecked(self.parent.auto_reconnect)
        network_layout.addRow("", self.auto_reconnect_check)
        
        network_tab.setLayout(network_layout)
        
        # Add tabs to tab widget
        tab_widget.addTab(appearance_tab, "Appearance")
        tab_widget.addTab(security_tab, "Security")
        tab_widget.addTab(network_tab, "Network")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_settings(self):
        # Save appearance settings
        self.parent.theme = self.theme_combo.currentText()
        self.parent.font_size = self.font_size_slider.value()
        self.parent.message_style = self.bubble_style_combo.currentText()
        
        # Save security settings
        self.parent.auto_accept = self.auto_accept_check.isChecked()
        self.parent.save_history = self.save_history_check.isChecked()
        
        # Save network settings
        self.parent.default_port = self.default_port_spin.value()
        self.parent.connection_timeout = self.timeout_spin.value()
        self.parent.auto_reconnect = self.auto_reconnect_check.isChecked()
        
        # Apply changes
        self.parent.apply_theme()
        self.parent.save_settings()
        
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.accept()

class ChatApp(QMainWindow):
    def __init__(self, port=5555):
        super().__init__()
        self.message_receiver = MessageReceiver()
        
        # Initialize settings
        self.settings = QSettings('ShadowTextMessenger', 'Settings')
        
        # Set default values for settings before UI initialization
        self.theme = 'Dark'
        self.font_size = 10
        self.message_style = 'Modern'
        self.auto_accept = False  # Changed to False by default
        self.save_history = True
        self.default_port = port
        self.connection_timeout = 15
        self.auto_reconnect = True
        self.advanced_enabled = False  # Advanced settings disabled by default
        
        # Get username
        self.username = self.get_username()
        
        self.network = MessengerNetwork(
            listen_port=port, 
            message_callback=self.message_receiver.message_received.emit,
            username=self.username
        )
        
        # Connect the message sent signal
        self.network.message_sent.connect(self.handle_message_sent)
        # Connect the key exchange complete signal
        self.network.key_exchange_complete.connect(self.handle_key_exchange_complete)
        # Connect the connection request signal
        self.network.connection_request.connect(self.handle_connection_request)
        # Connect the connection status signal
        self.network.connection_status.connect(self.handle_connection_status)
        
        self.setWindowTitle(f"Shadow Text - {self.username} (Port: {port})")
        
        # Make window responsive to screen size
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.8)  # 80% of screen width
        height = int(screen.height() * 0.8)  # 80% of screen height
        self.setGeometry(100, 100, width, height)
        
        # Initialize UI first
        self.init_ui()
        
        # Now load settings after UI elements are created
        self.load_settings()
        
        # Connect the message receiver to update the UI
        self.message_receiver.message_received.connect(self.display_received_message)
        
        # Store connected peers
        self.connected_peers = {}
        
        # Store pending connections
        self.pending_connections = {}
        
        # Apply saved theme
        self.apply_theme()
        
        # Set minimum size to prevent UI from becoming too small
        self.setMinimumSize(600, 500)
        
        # Set size policy to make widgets expand properly
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Connect resize event to adjust text areas
        self.resizeEvent = self.handle_resize
    
    def load_settings(self):
        """Load settings from QSettings"""
        # Appearance
        self.theme = self.settings.value('appearance/theme', 'Dark')
        self.font_size = int(self.settings.value('appearance/font_size', 10))
        self.message_style = self.settings.value('appearance/message_style', 'Modern')
        
        # Security
        self.auto_accept = self.settings.value('security/auto_accept', True, type=bool)
        self.save_history = self.settings.value('security/save_history', True, type=bool)
        
        # Network
        self.default_port = int(self.settings.value('network/default_port', 5555))
        self.connection_timeout = int(self.settings.value('network/connection_timeout', 15))
        self.auto_reconnect = self.settings.value('network/auto_reconnect', True, type=bool)
        self.advanced_enabled = self.settings.value('network/advanced_enabled', False, type=bool)  # Load advanced settings state
        
        # Load UI state
        advanced_visible = self.settings.value('ui/advanced_settings_visible', False, type=bool)
        self.advanced_checkbox.setChecked(advanced_visible)
        
        # Restore window geometry and state
        geometry = self.settings.value('ui/window_geometry')
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Default size based on screen
            screen = QApplication.primaryScreen().geometry()
            width = int(screen.width() * 0.8)
            height = int(screen.height() * 0.8)
            self.setGeometry(100, 100, width, height)
            
        state = self.settings.value('ui/window_state')
        if state:
            self.restoreState(state)

    def save_settings(self):
        """Save settings to QSettings"""
        # Appearance
        self.settings.setValue('appearance/theme', self.theme)
        self.settings.setValue('appearance/font_size', self.font_size)
        self.settings.setValue('appearance/message_style', self.message_style)
        
        # Security
        self.settings.setValue('security/auto_accept', self.auto_accept)
        self.settings.setValue('security/save_history', self.save_history)
        
        # Network
        self.settings.setValue('network/default_port', self.default_port)
        self.settings.setValue('network/connection_timeout', self.connection_timeout)
        self.settings.setValue('network/auto_reconnect', self.auto_reconnect)
        self.settings.setValue('network/advanced_enabled', self.advanced_enabled)  # Save advanced settings state
        
        # Save UI state
        self.settings.setValue('ui/advanced_settings_visible', self.advanced_checkbox.isChecked())
        self.settings.setValue('ui/window_geometry', self.saveGeometry())
        self.settings.setValue('ui/window_state', self.saveState())
        
        self.settings.sync()
        
        # Apply settings immediately
        self.apply_theme()
        
        # Update UI elements
        self.auto_reconnect_check.setChecked(self.auto_reconnect)
        self.timeout_input.setValue(self.connection_timeout)
        self.listen_port_input.setValue(self.default_port)
        self.port_input.setValue(self.default_port)

    def apply_theme(self):
        """Apply the current theme settings"""
        if self.theme == 'Dark':
            self.set_dark_theme()
        else:
            self.set_light_theme()
        
        # Apply font size
        font = self.font()
        font.setPointSize(self.font_size)
        self.setFont(font)
        
        # Apply message style
        self.apply_message_style()
        
        # Update all widgets with the new font
        for widget in self.findChildren(QWidget):
            widget.setFont(font)

    def set_dark_theme(self):
        """Set a dark theme for the application"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        self.setPalette(palette)
        
        # Set stylesheet for additional styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #353535;
            }
            QGroupBox {
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QPushButton {
                background-color: #2a82da;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
            QPushButton:pressed {
                background-color: #1a72ca;
            }
            QPushButton:disabled {
                background-color: #555555;
            }
            QLineEdit, QTextEdit {
                background-color: #252525;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                color: white;
            }
            QTextEdit {
                selection-background-color: #2a82da;
            }
            QCheckBox {
                color: white;
            }
            QSpinBox {
                background-color: #252525;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                color: white;
            }
            QMenuBar {
                background-color: #353535;
                color: white;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #2a82da;
            }
            QMenu {
                background-color: #353535;
                color: white;
                border: 1px solid #555555;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #2a82da;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #353535;
            }
            QTabBar::tab {
                background-color: #252525;
                color: white;
                padding: 5px 10px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #2a82da;
            }
            QLabel {
                color: white;
            }
            QComboBox {
                background-color: #252525;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
            }
            QSlider::groove:horizontal {
                border: 1px solid #555555;
                height: 8px;
                background: #252525;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #2a82da;
                border: none;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #3a92ea;
            }
        """)

    def set_light_theme(self):
        """Set a light theme for the application"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(230, 230, 230))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        
        self.setPalette(palette)
        
        # Set stylesheet for additional styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #1084e3;
            }
            QPushButton:pressed {
                background-color: #006cc1;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLineEdit, QTextEdit {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                color: black;
            }
            QTextEdit {
                selection-background-color: #0078d7;
            }
            QCheckBox {
                color: black;
            }
            QSpinBox {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                color: black;
            }
            QMenuBar {
                background-color: #f0f0f0;
                color: black;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QMenu {
                background-color: #f0f0f0;
                color: black;
                border: 1px solid #cccccc;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #f0f0f0;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: black;
                padding: 5px 10px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0078d7;
                color: white;
            }
            QLabel {
                color: black;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                color: black;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid black;
            }
            QSlider::groove:horizontal {
                border: 1px solid #cccccc;
                height: 8px;
                background: #e0e0e0;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0078d7;
                border: none;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #1084e3;
            }
        """)

    def apply_message_style(self):
        """Apply the current message style"""
        if self.message_style == 'Modern':
            self.sent_message_color = QColor(42, 130, 218)  # Blue
            self.received_message_color = QColor(45, 45, 45) if self.theme == 'Dark' else QColor(240, 240, 240)  # Dark gray or light gray
        elif self.message_style == 'Classic':
            self.sent_message_color = QColor(0, 120, 215)  # Windows blue
            self.received_message_color = QColor(240, 240, 240) if self.theme == 'Dark' else QColor(220, 220, 220)  # Light gray
        else:  # Minimal
            self.sent_message_color = QColor(60, 60, 60) if self.theme == 'Dark' else QColor(200, 200, 200)  # Dark gray or light gray
            self.received_message_color = QColor(45, 45, 45) if self.theme == 'Dark' else QColor(220, 220, 220)  # Darker gray or lighter gray

    def init_ui(self):
        # Create menu bar
        self.create_menu_bar()
        
        # Main layout with proper spacing
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Chat display area (Moved to top)
        chat_group = QGroupBox("Chat")
        chat_layout = QVBoxLayout()
        chat_layout.setSpacing(8)

        # Create a container for the text area with proper spacing
        text_container = QWidget()
        text_container_layout = QVBoxLayout()
        text_container_layout.setContentsMargins(0, 0, 0, 0)  # Removed bottom margin
        
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setMinimumHeight(400)
        self.text_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.text_area.textChanged.connect(self.auto_scroll_to_bottom)
        text_container_layout.addWidget(self.text_area)
        text_container.setLayout(text_container_layout)
        chat_layout.addWidget(text_container)

        # Message input area (Moved to bottom)
        input_container = QWidget()
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)  # Removed top margin
        
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setEnabled(False)
        self.message_input.keyPressEvent = self.handle_message_key_press
        input_layout.addWidget(self.message_input)

        # Button layout for Send and File buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setEnabled(False)
        button_layout.addWidget(self.send_button)
        
        self.file_button = QPushButton("File")
        self.file_button.clicked.connect(self.send_file)
        self.file_button.setEnabled(False)
        button_layout.addWidget(self.file_button)
        
        input_layout.addLayout(button_layout)
        input_container.setLayout(input_layout)
        chat_layout.addWidget(input_container)
        
        chat_group.setLayout(chat_layout)
        chat_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(chat_group)

        # Connection details in a group box (Moved to bottom)
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QVBoxLayout()
        conn_layout.setSpacing(8)
        
        # Username display
        username_layout = QHBoxLayout()
        username_label = QLabel("Your Username:")
        self.username_display = QLabel(self.username)
        self.username_display.setStyleSheet("font-weight: bold; color: #2a82da;")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_display)
        conn_layout.addLayout(username_layout)
        
        # IP input
        ip_layout = QHBoxLayout()
        ip_label = QLabel("Receiver IP:")
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter IP address (e.g., 127.0.0.1)")
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_input)
        conn_layout.addLayout(ip_layout)
        
        # Peer username input
        peer_layout = QHBoxLayout()
        peer_label = QLabel("Peer Username:")
        self.peer_input = QLineEdit()
        self.peer_input.setPlaceholderText("Enter peer's username")
        peer_layout.addWidget(peer_label)
        peer_layout.addWidget(self.peer_input)
        conn_layout.addLayout(peer_layout)
        
        # Advanced settings checkbox
        self.advanced_checkbox = QCheckBox("Advanced Settings")
        self.advanced_checkbox.setChecked(False)
        self.advanced_checkbox.stateChanged.connect(self.toggle_advanced_settings)
        conn_layout.addWidget(self.advanced_checkbox)
        
        # Advanced settings container
        self.advanced_container = QWidget()
        advanced_layout = QVBoxLayout()
        advanced_layout.setSpacing(8)
        
        # Listening port input
        listen_port_layout = QHBoxLayout()
        listen_port_label = QLabel("Listening Port:")
        self.listen_port_input = QSpinBox()
        self.listen_port_input.setRange(1024, 65535)
        self.listen_port_input.setValue(self.default_port)
        listen_port_layout.addWidget(listen_port_label)
        listen_port_layout.addWidget(self.listen_port_input)
        advanced_layout.addLayout(listen_port_layout)
        
        # Port input
        port_layout = QHBoxLayout()
        port_label = QLabel("Receiver Port:")
        self.port_input = QSpinBox()
        self.port_input.setRange(1024, 65535)
        self.port_input.setValue(self.default_port)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        advanced_layout.addLayout(port_layout)
        
        # Connection timeout
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Connection Timeout (seconds):")
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(5, 60)
        self.timeout_input.setValue(self.connection_timeout)
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_input)
        advanced_layout.addLayout(timeout_layout)
        
        # Auto-reconnect checkbox
        self.auto_reconnect_check = QCheckBox("Auto-reconnect on connection loss")
        self.auto_reconnect_check.setChecked(self.auto_reconnect)
        advanced_layout.addWidget(self.auto_reconnect_check)
        
        self.advanced_container.setLayout(advanced_layout)
        self.advanced_container.setVisible(False)
        conn_layout.addWidget(self.advanced_container)
        
        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_peer)
        conn_layout.addWidget(self.connect_button)
        
        # Disconnect button
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_from_peer)
        self.disconnect_button.setEnabled(False)
        conn_layout.addWidget(self.disconnect_button)
        
        conn_group.setLayout(conn_layout)
        main_layout.addWidget(conn_group)

        # Status bar
        self.statusBar().showMessage("Ready to connect")

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        # Set up a custom resize event to ensure text area is properly sized
        self.resizeEvent = self.custom_resize_event

    def create_menu_bar(self):
        """Create the menu bar with settings and help options"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Preferences action
        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self.show_settings)
        file_menu.addAction(preferences_action)
        
        # Add separator
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def show_settings(self):
        """Show the settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Apply settings immediately
            self.apply_theme()
            
            # Update UI elements
            self.auto_reconnect_check.setChecked(self.auto_reconnect)
            self.timeout_input.setValue(self.connection_timeout)
            self.listen_port_input.setValue(self.default_port)
            self.port_input.setValue(self.default_port)
    
    def show_about(self):
        """Show the about dialog"""
        QMessageBox.about(self, "About Shadow Text Messenger", 
                         "Shadow Text Messenger v1.0\n\n"
                         "A secure messaging application with end-to-end encryption.\n\n"
                         "Created by Coen Greenleaf\n"
                         "© 2023 Shadow Text Messenger")
    
    def toggle_advanced_settings(self, state):
        """Toggle visibility of advanced settings"""
        self.advanced_container.setVisible(state == Qt.CheckState.Checked.value)
        self.advanced_enabled = state == Qt.CheckState.Checked.value
        self.settings.setValue('network/advanced_enabled', self.advanced_enabled)

    def handle_message_key_press(self, event):
        """Handle key press events in the message input"""
        # Check if Enter was pressed without Shift (Shift+Enter for new line)
        if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # Send the message
            self.send_message()
            # Accept the event to prevent default handling
            event.accept()
        else:
            # Let the default handler process other keys
            QTextEdit.keyPressEvent(self.message_input, event)

    def display_received_message(self, message):
        """Display a received message in the text area with speech bubble style"""
        print(f"Received message: {message[:50]}...")  # Print first 50 chars for debugging
        
        try:
            # Try to parse the message as JSON
            import json
            message_data = json.loads(message)
            
            # Handle different message types
            if message_data.get("type") == "file":
                # Handle file message
                self.show_file_received_dialog(
                    message_data.get("username", "Unknown"),
                    message_data.get("filename", "unknown"),
                    message_data
                )
                return
            elif message_data.get("type") == "message":
                # Handle regular message
                username = message_data.get("username", "Unknown")
                content = message_data.get("content", "")
                
                # Create a block format for the message bubble
                block_format = QTextBlockFormat()
                block_format.setBackground(self.received_message_color)
                block_format.setLeftMargin(10)
                block_format.setRightMargin(10)
                block_format.setTopMargin(5)
                block_format.setBottomMargin(5)
                
                # Create a char format for the username
                username_format = QTextCharFormat()
                username_format.setForeground(QColor(42, 130, 218))  # Blue color for username
                username_format.setFontWeight(QFont.Weight.Bold)
                
                # Create a char format for the message content
                content_format = QTextCharFormat()
                content_format.setForeground(QColor(255, 255, 255) if self.theme == 'Dark' else QColor(0, 0, 0))  # White or black color for content
                
                # Insert the message with formatting
                cursor = self.text_area.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertBlock(block_format)
                
                # Insert username
                cursor.insertText(username + ": ", username_format)
                
                # Insert content
                cursor.insertText(content, content_format)
                
                # Add a newline after the message
                cursor.insertBlock()
            else:
                # Unknown message type, display as system message
                self.display_system_message(f"Received unknown message type: {message_data.get('type', 'unknown')}")
                
        except json.JSONDecodeError:
            # Not a JSON message, handle as legacy format
            if ": " in message:
                username, content = message.split(": ", 1)
                # Create a JSON-like structure for legacy messages
                message_data = {
                    "type": "message",
                    "username": username,
                    "content": content
                }
                # Recursively call with the new format
                self.display_received_message(json.dumps(message_data))
            else:
                # System message (no username)
                self.display_system_message(message)
        except Exception as e:
            print(f"Error handling message: {str(e)}")
            self.display_system_message(f"Error processing message: {str(e)}")
        
        # Ensure we scroll to the bottom
        self.auto_scroll_to_bottom()

    def display_system_message(self, message):
        """Display a system message in the text area"""
        block_format = QTextBlockFormat()
        block_format.setBackground(QColor(60, 60, 60) if self.theme == 'Dark' else QColor(220, 220, 220))  # Medium gray for system messages
        block_format.setLeftMargin(10)
        block_format.setRightMargin(10)
        block_format.setTopMargin(5)
        block_format.setBottomMargin(5)
        
        char_format = QTextCharFormat()
        char_format.setForeground(QColor(200, 200, 200) if self.theme == 'Dark' else QColor(100, 100, 100))  # Light gray for system messages
        
        cursor = self.text_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertBlock(block_format)
        cursor.insertText(message, char_format)
        cursor.insertBlock()

    def show_file_received_dialog(self, sender, filename, file_data):
        """Show dialog for received file"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("File Received")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # Message
        message = QLabel(f"{sender} has sent {filename} to you.")
        message.setWordWrap(True)
        layout.addWidget(message)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        open_button = QPushButton("Open")
        open_button.clicked.connect(lambda: self.open_received_file(file_data, dialog))
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_received_file(file_data, dialog))
        
        button_layout.addWidget(open_button)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        dialog.exec()
        
    def open_received_file(self, file_data, dialog):
        """Open a received file"""
        import tempfile
        import base64
        import os
        import subprocess
        
        try:
            # Create temp directory if it doesn't exist
            temp_dir = os.path.join(tempfile.gettempdir(), "ShadowMessenger")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                
            # Create temp file
            filename = file_data.get("filename", "unknown")
            temp_path = os.path.join(temp_dir, filename)
            
            # Decode and write file content
            content_b64 = file_data.get("content", "")
            content = base64.b64decode(content_b64)
            
            with open(temp_path, 'wb') as f:
                f.write(content)
                
            # Open file with default application
            if os.name == 'nt':  # Windows
                os.startfile(temp_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.call(('open', temp_path))
                
            # Close dialog
            dialog.accept()
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")
            
    def save_received_file(self, file_data, dialog):
        """Save a received file"""
        from PyQt6.QtWidgets import QFileDialog
        import base64
        
        try:
            # Get save location from user
            filename = file_data.get("filename", "unknown")
            save_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save File", 
                filename, 
                "All Files (*.*)"
            )
            
            if not save_path:
                return  # User cancelled
                
            # Decode and write file content
            content_b64 = file_data.get("content", "")
            content = base64.b64decode(content_b64)
            
            with open(save_path, 'wb') as f:
                f.write(content)
                
            # Show success message
            self.text_area.append(f"File saved to: {save_path}")
            
            # Close dialog
            dialog.accept()
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

    def handle_message_sent(self, success, error_message):
        """Handle the result of sending a message"""
        if success:
            # Message was sent successfully, clear the input
            self.message_input.clear()
        else:
            # Show error message
            self.text_area.append(f"Error: {error_message}")
            self.statusBar().showMessage(f"Error: {error_message}", 5000)  # Show for 5 seconds
            
            # Check if we need to reconnect
            if "connection lost" in error_message.lower() and self.auto_reconnect:
                self.reconnect_to_peer()

    def handle_key_exchange_complete(self, peer_username):
        """Handle key exchange completion"""
        print(f"Key exchange completed with {peer_username}")
        
        # Enable message input and buttons
        self.message_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.file_button.setEnabled(True)
        self.disconnect_button.setEnabled(True)
        
        # Display connection message only if not already connected
        if peer_username not in self.connected_peers:
            self.display_system_message(f"System: Connected to {peer_username}")
            self.statusBar().showMessage(f"Connected to {peer_username}", 5000)
        
        # Set the peer's username in the input field if not already set
        if not self.peer_input.text():
            self.peer_input.setText(peer_username)
            
        # Add to connected peers if not already there
        if peer_username not in self.connected_peers:
            self.connected_peers[peer_username] = {
                "ip": self.ip_input.text(),
                "port": self.port_input.value()
            }
            print(f"Added {peer_username} to connected peers")
            
            # Remove from pending connections
            if peer_username in self.pending_connections:
                del self.pending_connections[peer_username]

    def handle_connection_status(self, peer_username, connected):
        """Handle connection status changes"""
        if connected:
            if peer_username not in self.connected_peers:
                self.statusBar().showMessage(f"Connected to {peer_username}")
                self.message_input.setEnabled(True)
                self.send_button.setEnabled(True)
                self.file_button.setEnabled(True)
                self.disconnect_button.setEnabled(True)  # Enable disconnect button
                self.display_received_message(f"System: Connected to {peer_username}")
        else:
            self.statusBar().showMessage("Disconnected")
            self.message_input.setEnabled(False)
            self.send_button.setEnabled(False)
            self.file_button.setEnabled(False)
            self.disconnect_button.setEnabled(False)  # Disable disconnect button
            self.display_received_message(f"System: Disconnected from {peer_username}")
            
            # Attempt auto-reconnect if enabled
            if self.advanced_enabled and self.auto_reconnect_check.isChecked():
                self.statusBar().showMessage("Attempting to reconnect...")
                QTimer.singleShot(5000, lambda: self.connect_to_peer())

    def handle_connection_request(self, peer_username, peer_ip, peer_port):
        """Handle incoming connection request"""
        # Check if we initiated this connection
        if peer_username in self.pending_connections:
            # We initiated this connection, automatically accept
            if not self.network.accept_connection(peer_ip, peer_port, peer_username):
                self.text_area.append(f"Connection to {peer_username} failed")
                self.statusBar().showMessage("Connection acceptance failed", 5000)
                if peer_username in self.pending_connections:
                    del self.pending_connections[peer_username]
            return
            
        # Check if auto-accept is enabled and we know this peer
        if self.auto_accept and peer_username in self.connected_peers:
            # Auto-accept the connection
            if not self.network.accept_connection(peer_ip, peer_port, peer_username):
                self.text_area.append(f"Connection to {peer_username} failed")
                self.statusBar().showMessage("Connection acceptance failed", 5000)
                if peer_username in self.pending_connections:
                    del self.pending_connections[peer_username]
            return
            
        # Show connection request dialog for incoming connections
        dialog = ConnectionRequestDialog(peer_username, peer_ip, peer_port, self)
        dialog.exec()
        
        if dialog.result:
            # User accepted the connection
            # Store the connection info
            self.pending_connections[peer_username] = {
                "ip": peer_ip,
                "port": peer_port
            }
            
            # Fill in the connection details
            self.ip_input.setText(peer_ip)
            self.port_input.setValue(peer_port)
            self.peer_input.setText(peer_username)
            
            # Accept the connection and exchange keys
            if not self.network.accept_connection(peer_ip, peer_port, peer_username):
                self.text_area.append(f"Connection to {peer_username} failed")
                self.statusBar().showMessage("Connection acceptance failed", 5000)
                if peer_username in self.pending_connections:
                    del self.pending_connections[peer_username]
        else:
            # User refused the connection
            self.statusBar().showMessage(f"Connection refused", 5000)
            
            # Refuse the connection
            self.network.refuse_connection(peer_ip, peer_port)
            if peer_username in self.pending_connections:
                del self.pending_connections[peer_username]

    def connect_to_peer(self):
        """Connect to a peer and exchange keys"""
        receiver_ip = self.ip_input.text().strip()
        port = self.port_input.value()
        peer_username = self.peer_input.text().strip()
        
        # Input validation
        if not receiver_ip:
            self.display_system_message("Error: Please enter a receiver IP address")
            self.statusBar().showMessage("Error: Please enter a receiver IP address", 5000)
            return
            
        if not peer_username:
            self.display_system_message("Error: Please enter the peer's username")
            self.statusBar().showMessage("Error: Please enter the peer's username", 5000)
            return
            
        # Check if already connected to this peer
        if peer_username in self.connected_peers:
            self.display_system_message(f"Already connected to {peer_username}")
            self.statusBar().showMessage(f"Already connected to {peer_username}", 5000)
            return
            
        # Check if there's a pending connection
        if peer_username in self.pending_connections:
            self.display_system_message(f"Connection to {peer_username} already in progress")
            self.statusBar().showMessage(f"Connection in progress...", 5000)
            return

        try:
            # Validate IP address format
            import socket
            try:
                socket.inet_aton(receiver_ip)
            except socket.error:
                self.display_system_message("Error: Invalid IP address format")
                self.statusBar().showMessage("Error: Invalid IP address format", 5000)
                return
                
            # Store the connection info
            self.pending_connections[peer_username] = {
                "ip": receiver_ip,
                "port": port
            }
            
            # Update status
            self.statusBar().showMessage(f"Connecting to {peer_username}...", 0)
            
            # Initiate connection request
            if not self.network.initiate_connection(receiver_ip, port, peer_username):
                self.display_system_message(f"Connection to {peer_username} refused")
                self.statusBar().showMessage(f"Connection refused", 5000)
                if peer_username in self.pending_connections:
                    del self.pending_connections[peer_username]
            else:
                self.display_system_message(f"Connection request sent to {peer_username}")
                
        except ConnectionRefusedError:
            self.display_system_message(f"Connection refused by {peer_username}")
            self.statusBar().showMessage(f"Connection refused", 5000)
            if peer_username in self.pending_connections:
                del self.pending_connections[peer_username]
        except TimeoutError:
            self.display_system_message(f"Connection to {peer_username} timed out")
            self.statusBar().showMessage(f"Connection timed out", 5000)
            if peer_username in self.pending_connections:
                del self.pending_connections[peer_username]
        except Exception as e:
            self.display_system_message(f"Error connecting: {str(e)}")
            self.statusBar().showMessage(f"Error connecting: {str(e)}", 5000)
            if peer_username in self.pending_connections:
                del self.pending_connections[peer_username]

    def send_message(self):
        """Send a message to the connected peer"""
        peer_username = self.peer_input.text().strip()
        message = self.message_input.toPlainText().strip()
        
        # Input validation
        if not peer_username:
            self.display_system_message("Error: Please enter the peer's username")
            self.statusBar().showMessage("Error: Please enter the peer's username", 5000)
            return
            
        if not message:
            self.display_system_message("Error: Please enter a message")
            self.statusBar().showMessage("Error: Please enter a message", 5000)
            return
            
        # Check connection status
        if peer_username not in self.connected_peers:
            self.display_system_message(f"Error: Not connected to {peer_username}. Please connect first.")
            self.statusBar().showMessage(f"Error: Not connected to {peer_username}", 5000)
            return

        try:
            peer_info = self.connected_peers[peer_username]
            receiver_ip = peer_info["ip"]
            port = peer_info["port"]
            
            # Display the message in the UI with speech bubble style
            block_format = QTextBlockFormat()
            block_format.setBackground(self.sent_message_color)
            block_format.setLeftMargin(10)
            block_format.setRightMargin(10)
            block_format.setTopMargin(5)
            block_format.setBottomMargin(5)
            block_format.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            char_format = QTextCharFormat()
            char_format.setForeground(QColor(255, 255, 255) if self.theme == 'Dark' else QColor(0, 0, 0))  # White or black color for sent messages
            
            cursor = self.text_area.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertBlock(block_format)
            cursor.insertText(f"You: {message}", char_format)
            cursor.insertBlock()
            
            # Scroll to the bottom
            self.text_area.verticalScrollBar().setValue(self.text_area.verticalScrollBar().maximum())
            
            # Clear the input field before sending
            self.message_input.clear()
            
            # Create JSON message
            import json
            message_data = {
                "type": "message",
                "username": self.username,
                "content": message
            }
            json_message = json.dumps(message_data)
            
            # Send the message asynchronously
            print(f"Sending message to {peer_username} at {receiver_ip}:{port}")
            self.network.send_message(receiver_ip, port, json_message, peer_username)
            
        except ConnectionError:
            self.display_system_message(f"Connection lost with {peer_username}")
            self.statusBar().showMessage("Connection lost", 5000)
            # Attempt to reconnect if auto-reconnect is enabled
            if self.auto_reconnect:
                self.reconnect_to_peer()
        except TimeoutError:
            self.display_system_message(f"Message send timed out to {peer_username}")
            self.statusBar().showMessage("Send timeout", 5000)
        except Exception as e:
            self.display_system_message(f"Error sending message: {str(e)}")
            self.statusBar().showMessage(f"Error sending message: {str(e)}", 5000)
            print(f"Exception in send_message: {str(e)}")

    def send_file(self):
        """Open file dialog and send the selected file"""
        from PyQt6.QtWidgets import QFileDialog
        import os
        import tempfile
        import base64
        
        # Check if connected to a peer
        peer_username = self.peer_input.text().strip()
        if not peer_username or peer_username not in self.connected_peers:
            self.text_area.append("Error: Not connected to a peer. Please connect first.")
            self.statusBar().showMessage("Error: Not connected to a peer", 5000)
            return
            
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select File to Send", 
            "", 
            "All Files (*.*)"
        )
        
        if not file_path:
            return  # User cancelled
            
        # Get file name and size
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Check file size (limit to 10MB for now)
        if file_size > 10 * 1024 * 1024:
            self.text_area.append(f"Error: File too large. Maximum size is 10MB.")
            self.statusBar().showMessage("Error: File too large", 5000)
            return
            
        try:
            # Show status message
            self.statusBar().showMessage(f"Sending file: {file_name}...", 0)  # 0 means no timeout
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
                
            # Convert to base64 for transmission
            file_content_b64 = base64.b64encode(file_content).decode()
            
            # Create a message with file information
            file_message = {
                "type": "file",
                "filename": file_name,
                "content": file_content_b64
            }
            
            # Convert to JSON string
            import json
            file_message_json = json.dumps(file_message)
            
            # Get peer info
            peer_info = self.connected_peers[peer_username]
            receiver_ip = peer_info["ip"]
            port = peer_info["port"]
            
            # Send the file message
            self.network.send_message(receiver_ip, port, file_message_json, peer_username)
            
            # Display in chat
            self.text_area.append(f"You sent a file: {file_name}")
            
            # Update status message
            self.statusBar().showMessage(f"File sent: {file_name}", 5000)
            
        except Exception as e:
            self.text_area.append(f"Error sending file: {str(e)}")
            self.statusBar().showMessage(f"Error sending file: {str(e)}", 5000)

    def closeEvent(self, event):
        """Handle application close event"""
        # Clean up resources
        self.cleanup()
        event.accept()
    
    def cleanup(self):
        """Clean up resources before closing"""
        try:
            # Disconnect from all peers
            for peer_username, peer_info in list(self.connected_peers.items()):
                try:
                    self.network.disconnect_from_peer(peer_info["ip"], peer_info["port"])
                    self.text_area.append(f"Disconnected from {peer_username}")
                except Exception as e:
                    print(f"Error disconnecting from {peer_username}: {str(e)}")
            
            # Clean up network resources
            self.network.cleanup()
            
            # Save settings
            self.save_settings()
            
            # Clear any pending connections
            self.pending_connections.clear()
            self.connected_peers.clear()
            
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
    
    def get_username(self):
        """Get username from user"""
        username, ok = QInputDialog.getText(
            self, 
            'Username', 
            'Enter your username:',
            QLineEdit.EchoMode.Normal,
            'Anonymous'
        )
        if ok and username:
            return username
        return 'Anonymous'

    def reconnect_to_peer(self):
        """Attempt to reconnect to the current peer"""
        peer_username = self.peer_input.text().strip()
        if not peer_username or peer_username not in self.connected_peers:
            return
            
        peer_info = self.connected_peers[peer_username]
        receiver_ip = peer_info["ip"]
        port = peer_info["port"]
        
        self.text_area.append(f"Attempting to reconnect to {peer_username}...")
        self.statusBar().showMessage(f"Reconnecting to {peer_username}...", 5000)
        
        try:
            # Remove from connected peers first
            del self.connected_peers[peer_username]
            
            # Disable message input and send button
            self.message_input.setEnabled(False)
            self.send_button.setEnabled(False)
            
            # Initiate connection request
            if not self.network.initiate_connection(receiver_ip, port, peer_username):
                self.text_area.append(f"Reconnection to {peer_username} failed")
                self.statusBar().showMessage(f"Reconnection failed", 5000)
            else:
                # Store the connection info
                self.pending_connections[peer_username] = {
                    "ip": receiver_ip,
                    "port": port
                }
        except Exception as e:
            self.text_area.append(f"Error reconnecting: {str(e)}")
            self.statusBar().showMessage(f"Error reconnecting: {str(e)}", 5000)

    def handle_resize(self, event):
        """Handle window resize event"""
        # Adjust text areas to fit new window size
        self.text_area.setMinimumHeight(int(self.height() * 0.7))  # Increased to 70% of window height
        self.text_area.setMaximumHeight(int(self.height() * 0.7))  # Increased to 70% of window height
        self.message_input.setMaximumHeight(int(self.height() * 0.2))  # Increased to 20% of window height
        
        # Ensure we scroll to the bottom after resize
        self.auto_scroll_to_bottom()

    def auto_scroll_to_bottom(self):
        """Scroll to the bottom of the text area"""
        # Get the scrollbar
        scrollbar = self.text_area.verticalScrollBar()
        
        # Set the scrollbar to the maximum value (bottom)
        scrollbar.setValue(scrollbar.maximum())
        
        # Force an immediate update
        QApplication.processEvents()
        
        # Double-check that we're at the bottom
        if scrollbar.value() != scrollbar.maximum():
            # If not at the bottom, try again after a short delay
            QTimer.singleShot(50, lambda: scrollbar.setValue(scrollbar.maximum()))

    def disconnect_from_peer(self):
        """Disconnect from the current peer"""
        peer_username = self.peer_input.text().strip()
        if not peer_username or peer_username not in self.connected_peers:
            self.display_system_message("Error: Not connected to any peer")
            self.statusBar().showMessage("Error: Not connected to any peer", 5000)
            return
            
        try:
            peer_info = self.connected_peers[peer_username]
            receiver_ip = peer_info["ip"]
            port = peer_info["port"]
            
            # Disconnect from the peer
            self.network.disconnect_from_peer(receiver_ip, port)
            
            # Remove from connected peers
            del self.connected_peers[peer_username]
            
            # Disable message input and buttons
            self.message_input.setEnabled(False)
            self.send_button.setEnabled(False)
            self.file_button.setEnabled(False)
            self.disconnect_button.setEnabled(False)
            
            # Display disconnect message
            self.display_system_message(f"System: Disconnected from {peer_username}")
            self.statusBar().showMessage(f"Disconnected from {peer_username}", 5000)
            
        except Exception as e:
            self.display_system_message(f"Error disconnecting: {str(e)}")
            self.statusBar().showMessage(f"Error disconnecting: {str(e)}", 5000)

    def custom_resize_event(self, event):
        """Custom resize event to ensure text area is properly sized and aligned from the bottom"""
        # Call the parent class's resize event first
        super().resizeEvent(event)
        
        # Calculate the available height for the chat area
        available_height = self.height() - 200  # Approximate height for other UI elements
        
        # Set the text area to take up most of the available space
        text_height = int(available_height * 0.7)  # 70% of available height
        self.text_area.setMinimumHeight(text_height)
        self.text_area.setMaximumHeight(text_height)
        
        # Set the input area to take up the remaining space
        input_height = int(available_height * 0.3)  # 30% of available height
        self.message_input.setMaximumHeight(input_height)
        
        # Ensure we scroll to the bottom after resize
        self.auto_scroll_to_bottom()
        
        # Force a layout update
        self.updateGeometry()

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Shadow Text Messenger')
    parser.add_argument('--port', type=int, default=5555, help='Port number to listen on')
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    window = ChatApp(port=args.port)
    window.show()
    sys.exit(app.exec())