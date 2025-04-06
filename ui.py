import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit, 
                            QVBoxLayout, QWidget, QLineEdit, QLabel, QHBoxLayout,
                            QDialog, QInputDialog, QMessageBox, QFileDialog, QSplitter,
                            QListWidget, QListWidgetItem, QFrame, QMenu, QToolButton,
                            QStyle, QStyleFactory, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QSize, QPoint, pyqtSignal, QUrl
from PyQt6.QtGui import (QTextCursor, QColor, QPalette, QFont, QIcon, QAction, QPixmap,
                        QTextDocument, QPainter, QBrush, QPen)
from network import MessengerNetwork

class MessageBubble(QFrame):
    def __init__(self, message, is_self=True, parent=None):
        super().__init__(parent)
        self.is_self = is_self
        self.message = message
        self.init_ui()
        
    def init_ui(self):
        # Set frame style
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        # Set background color based on sender
        if self.is_self:
            self.setStyleSheet("""
                QFrame {
                    background-color: #007AFF;
                    border-radius: 15px;
                    padding: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #E9E9EB;
                    border-radius: 15px;
                    padding: 10px;
                }
            """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Add message label
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # Set text color based on sender
        if self.is_self:
            message_label.setStyleSheet("color: white;")
        else:
            message_label.setStyleSheet("color: black;")
        
        layout.addWidget(message_label)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # Set minimum width
        self.setMinimumWidth(100)
        
        # Set maximum width
        self.setMaximumWidth(400)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set up painter
        if self.is_self:
            painter.setBrush(QBrush(QColor("#007AFF")))
            painter.setPen(QPen(QColor("#007AFF")))
        else:
            painter.setBrush(QBrush(QColor("#E9E9EB")))
            painter.setPen(QPen(QColor("#E9E9EB")))
        
        # Draw rounded rectangle
        painter.drawRoundedRect(self.rect(), 15, 15)
        
        # Call parent paint event
        super().paintEvent(event)

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
        self.setStyleSheet("""
            QDialog {
                background-color: #F2F2F7;
            }
            QLabel {
                color: #000000;
                font-size: 14px;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
            QPushButton#refuseButton {
                background-color: #FF3B30;
            }
            QPushButton#refuseButton:hover {
                background-color: #D63026;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Message
        message = QLabel(f"{self.username} ({self.ip}:{self.port}) wants to connect to you.")
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        accept_button = QPushButton("Accept")
        accept_button.clicked.connect(self.accept_connection)
        
        refuse_button = QPushButton("Refuse")
        refuse_button.setObjectName("refuseButton")
        refuse_button.clicked.connect(self.refuse_connection)
        
        button_layout.addWidget(accept_button)
        button_layout.addWidget(refuse_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Set fixed size
        self.setFixedSize(300, 150)
        
    def accept_connection(self):
        self.result = True
        self.accept()
        
    def refuse_connection(self):
        self.result = False
        self.accept()

class FileReceivedDialog(QDialog):
    def __init__(self, username, filename, filepath, parent=None):
        super().__init__(parent)
        self.username = username
        self.filename = filename
        self.filepath = filepath
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("File Received")
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #F2F2F7;
            }
            QLabel {
                color: #000000;
                font-size: 14px;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Message
        message = QLabel(f"{self.username} sent this file to you: {self.filename}")
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        open_button = QPushButton("Open")
        open_button.clicked.connect(self.open_file)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_file)
        
        button_layout.addWidget(open_button)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Set fixed size
        self.setFixedSize(300, 150)
        
    def open_file(self):
        # Open the file with the default application
        os.startfile(self.filepath) if sys.platform == 'win32' else os.system(f'xdg-open "{self.filepath}"')
        self.accept()
        
    def save_file(self):
        # Ask user where to save the file
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save File", 
            os.path.expanduser("~/Downloads") + "/" + self.filename,
            "All Files (*.*)"
        )
        
        if save_path:
            # Copy the file to the selected location
            import shutil
            shutil.copy2(self.filepath, save_path)
            QMessageBox.information(self, "File Saved", f"File saved to {save_path}")
        
        self.accept()

class SettingsDialog(QDialog):
    def __init__(self, port, username, parent=None):
        super().__init__(parent)
        self.port = port
        self.username = username
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #F2F2F7;
            }
            QLabel {
                color: #000000;
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #C7C7CC;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Port input
        port_layout = QHBoxLayout()
        port_label = QLabel("Port:")
        self.port_input = QLineEdit(str(self.port))
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        layout.addLayout(port_layout)
        
        # Username input
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        self.username_input = QLineEdit(self.username)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Set fixed size
        self.setFixedSize(300, 200)
        
    def save_settings(self):
        try:
            self.port = int(self.port_input.text())
            self.username = self.username_input.text()
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Port must be a number.")

class ChatApp(QMainWindow):
    def __init__(self, port=5555, username="Anonymous"):
        super().__init__()
        self.port = port
        self.username = username
        self.network = None
        self.current_peer = None
        self.message_bubbles = {}  # Store message bubbles
        self.init_ui()
        self.init_network()
        
    def init_ui(self):
        self.setWindowTitle(f"Shadow Messenger - {self.username}")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F2F2F7;
            }
            QListWidget {
                background-color: #F2F2F7;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #C7C7CC;
            }
            QListWidget::item:selected {
                background-color: #E5E5EA;
                color: black;
            }
            QTextEdit {
                background-color: white;
                border: none;
                font-size: 14px;
            }
            QLineEdit {
                padding: 10px;
                border: 1px solid #C7C7CC;
                border-radius: 20px;
                background-color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
            QPushButton:disabled {
                background-color: #C7C7CC;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 15px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #E5E5EA;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #F2F2F7; border-bottom: 1px solid #C7C7CC;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        # Add title
        title = QLabel("Shadow Messenger")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Add settings button
        settings_button = QToolButton()
        settings_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        settings_button.setToolTip("Settings")
        settings_button.clicked.connect(self.show_settings)
        header_layout.addWidget(settings_button)
        
        sidebar_layout.addWidget(header)
        
        # Create peer list
        self.peer_list = QListWidget()
        self.peer_list.itemClicked.connect(self.select_peer)
        sidebar_layout.addWidget(self.peer_list)
        
        # Add connect button
        connect_button = QPushButton("Connect to Peer")
        connect_button.clicked.connect(self.show_connect_dialog)
        sidebar_layout.addWidget(connect_button)
        
        # Create chat area
        chat_area = QWidget()
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setSpacing(0)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create chat header
        chat_header = QWidget()
        chat_header.setFixedHeight(60)
        chat_header.setStyleSheet("background-color: #F2F2F7; border-bottom: 1px solid #C7C7CC;")
        chat_header_layout = QHBoxLayout(chat_header)
        chat_header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Add peer name
        self.peer_name_label = QLabel("Select a peer to chat")
        self.peer_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        chat_header_layout.addWidget(self.peer_name_label)
        
        chat_layout.addWidget(chat_header)
        
        # Create chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: white;")
        chat_layout.addWidget(self.chat_display)
        
        # Create input area
        input_area = QWidget()
        input_area.setFixedHeight(60)
        input_area.setStyleSheet("background-color: #F2F2F7; border-top: 1px solid #C7C7CC;")
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(10, 5, 10, 5)
        
        # Add message input
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        # Add file button
        file_button = QToolButton()
        file_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        file_button.setToolTip("Send File")
        file_button.clicked.connect(self.send_file)
        input_layout.addWidget(file_button)
        
        # Add send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setEnabled(False)
        input_layout.addWidget(self.send_button)
        
        chat_layout.addWidget(input_area)
        
        # Add widgets to splitter
        splitter.addWidget(sidebar)
        splitter.addWidget(chat_area)
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Set focus to message input
        self.message_input.setFocus()
        
    def init_network(self):
        # Initialize network
        self.network = MessengerNetwork(listen_port=self.port, username=self.username)
        
        # Connect signals
        self.network.message_received.connect(self.handle_message_received)
        self.network.file_received.connect(self.handle_file_received)
        self.network.connection_request.connect(self.handle_connection_request)
        self.network.connection_status.connect(self.handle_connection_status)
        self.network.connection_closed.connect(self.handle_connection_closed)
        
    def show_connect_dialog(self):
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Connect to Peer")
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #F2F2F7;
            }
            QLabel {
                color: #000000;
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #C7C7CC;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add inputs
        ip_layout = QHBoxLayout()
        ip_label = QLabel("IP:")
        ip_input = QLineEdit()
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(ip_input)
        layout.addLayout(ip_layout)
        
        port_layout = QHBoxLayout()
        port_label = QLabel("Port:")
        port_input = QLineEdit()
        port_layout.addWidget(port_label)
        port_layout.addWidget(port_input)
        layout.addLayout(port_layout)
        
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_input = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(username_input)
        layout.addLayout(username_layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(lambda: self.connect_to_peer(
            ip_input.text().strip(),
            port_input.text().strip(),
            username_input.text().strip(),
            dialog
        ))
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(connect_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Set fixed size
        dialog.setFixedSize(300, 200)
        
        # Show dialog
        dialog.exec()
        
    def connect_to_peer(self, peer_ip, peer_port, peer_username, dialog=None):
        # Validate inputs
        if not peer_ip or not peer_port or not peer_username:
            QMessageBox.warning(self, "Invalid Input", "Please enter peer IP, port, and username.")
            return
        
        try:
            peer_port = int(peer_port)
        except ValueError:
            QMessageBox.warning(self, "Invalid Port", "Port must be a number.")
            return
        
        # Connect to peer
        success = self.network.initiate_connection(peer_ip, peer_port, peer_username)
        
        if success:
            # Add peer to list if not already there
            self.add_peer_to_list(peer_username)
            
            # Select the peer
            self.select_peer_by_name(peer_username)
            
            # Close dialog if it exists
            if dialog:
                dialog.accept()
        else:
            QMessageBox.warning(self, "Connection Failed", f"Failed to connect to {peer_username}")
    
    def disconnect_from_peer(self):
        if self.current_peer:
            success = self.network.disconnect_from_peer(self.current_peer)
            
            if success:
                self.add_message("System", f"Disconnected from {self.current_peer}")
                self.current_peer = None
                self.peer_name_label.setText("Select a peer to chat")
                self.send_button.setEnabled(False)
                self.message_input.setEnabled(False)
            else:
                QMessageBox.warning(self, "Disconnect Failed", f"Failed to disconnect from {self.current_peer}")
    
    def send_message(self):
        if not self.current_peer:
            QMessageBox.warning(self, "Not Connected", "You are not connected to any peer.")
            return
        
        message = self.message_input.text().strip()
        if not message:
            return
        
        # Send message
        success = self.network.send_message(self.current_peer, message)
        
        if success:
            self.add_message(self.username, message)
            self.message_input.clear()
        else:
            QMessageBox.warning(self, "Send Failed", "Failed to send message.")
    
    def send_file(self):
        if not self.current_peer:
            QMessageBox.warning(self, "Not Connected", "You are not connected to any peer.")
            return
        
        # Open file dialog
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Send",
            os.path.expanduser("~"),
            "All Files (*.*)"
        )
        
        if filepath:
            # Send file
            success = self.network.send_file(self.current_peer, filepath)
            
            if success:
                filename = os.path.basename(filepath)
                self.add_message(self.username, f"Sent file: {filename}")
            else:
                QMessageBox.warning(self, "Send Failed", "Failed to send file.")
    
    def handle_message_received(self, username, message):
        self.add_message(username, message)
        
        # Add peer to list if not already there
        self.add_peer_to_list(username)
    
    def handle_file_received(self, username, filename, filepath):
        # Show file received dialog
        dialog = FileReceivedDialog(username, filename, filepath, self)
        dialog.exec()
        
        # Add message to chat
        self.add_message(username, f"Sent file: {filename}")
        
        # Add peer to list if not already there
        self.add_peer_to_list(username)
    
    def handle_connection_request(self, username, ip, port):
        # Show connection request dialog
        dialog = ConnectionRequestDialog(username, ip, port, self)
        dialog.exec()
        
        if dialog.result:
            # Accept connection
            success = self.network.accept_connection(ip, port, username)
            
            if success:
                # Add peer to list if not already there
                self.add_peer_to_list(username)
                
                # Select the peer
                self.select_peer_by_name(username)
            else:
                QMessageBox.warning(self, "Connection Failed", f"Failed to connect to {username}")
        else:
            # Refuse connection
            self.network.refuse_connection(ip, port, username)
    
    def handle_connection_status(self, username, success):
        if success:
            self.add_message("System", f"Connected to {username}")
            
            # Add peer to list if not already there
            self.add_peer_to_list(username)
            
            # Select the peer
            self.select_peer_by_name(username)
        else:
            self.add_message("System", f"Connection to {username} failed")
    
    def handle_connection_closed(self, username):
        self.add_message("System", f"{username} disconnected")
        
        if self.current_peer == username:
            self.current_peer = None
            self.peer_name_label.setText("Select a peer to chat")
            self.send_button.setEnabled(False)
            self.message_input.setEnabled(False)
    
    def add_message(self, username, message):
        # Create message bubble
        bubble = MessageBubble(message, username == self.username)
        
        # Store bubble
        bubble_id = f"bubble_{username}_{message}"
        self.message_bubbles[bubble_id] = bubble
        
        # Add bubble to chat display
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Add username if not system message
        if username != "System":
            cursor.insertHtml(f"<p style='margin: 5px 0;'><b>{username}:</b></p>")
        
        # Insert bubble
        self.chat_display.document().addResource(
            QTextDocument.ResourceType.ImageResource,
            QUrl(bubble_id),
            bubble.grab()
        )
        
        # Scroll to bottom
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()
        
        # Clean up old bubbles
        self.cleanup_old_bubbles()
    
    def cleanup_old_bubbles(self):
        # Keep only the last 100 bubbles
        if len(self.message_bubbles) > 100:
            # Remove oldest bubbles
            for bubble_id in list(self.message_bubbles.keys())[:-100]:
                del self.message_bubbles[bubble_id]
    
    def add_peer_to_list(self, username):
        # Check if peer is already in list
        for i in range(self.peer_list.count()):
            if self.peer_list.item(i).text() == username:
                return
        
        # Add peer to list
        item = QListWidgetItem(username)
        self.peer_list.addItem(item)
    
    def select_peer(self, item):
        username = item.text()
        self.select_peer_by_name(username)
    
    def select_peer_by_name(self, username):
        # Set current peer
        self.current_peer = username
        
        # Update UI
        self.peer_name_label.setText(username)
        self.send_button.setEnabled(True)
        self.message_input.setEnabled(True)
        
        # Clear chat display
        self.chat_display.clear()
        
        # Add system message
        self.add_message("System", f"Connected to {username}")
    
    def show_settings(self):
        # Show settings dialog
        dialog = SettingsDialog(self.port, self.username, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update settings
            self.port = dialog.port
            self.username = dialog.username
            
            # Update window title
            self.setWindowTitle(f"Shadow Messenger - {self.username}")
            
            # Reinitialize network
            if self.network:
                self.network.cleanup()
            self.init_network()
    
    def closeEvent(self, event):
        # Clean up network resources
        if self.network:
            self.network.cleanup()
        event.accept()

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