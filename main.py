import sys
import argparse
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox
from ui import ChatApp
from encryption import RSAEncryption

def get_port_from_user(app):
    """Ask the user to select a port number"""
    port, ok = QInputDialog.getInt(
        None, 
        'Port Selection', 
        'Enter the port number to use (1024-65535):',
        5555,  # Default value
        1024,  # Minimum value
        65535, # Maximum value
        1      # Step
    )
    
    if ok:
        return port
    else:
        # If user cancels, use default port
        return 5555

if __name__ == "__main__":
    # Create QApplication first
    app = QApplication(sys.argv)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Secure Messenger')
    parser.add_argument('--port', type=int, help='Port to use for the messenger')
    args = parser.parse_args()
    
    # Initialize encryption
    encryption = RSAEncryption()
    encryption.generate_keys()
    print("RSA keys generated successfully.")
    
    # If port is provided via command line, use it; otherwise ask the user
    port = args.port if args.port else get_port_from_user(app)
    
    # Create and show the main window
    window = ChatApp(port=port)
    window.show()
    
    sys.exit(app.exec())
