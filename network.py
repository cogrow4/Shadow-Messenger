import zmq
import threading
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import base64
import json
import os
import shutil
import socket
from PyQt6.QtCore import QObject, pyqtSignal
from encryption import RSAEncryption

class MessengerNetwork(QObject):
    message_received = pyqtSignal(str)
    message_sent = pyqtSignal(bool, str)
    key_exchange_complete = pyqtSignal(str)
    connection_request = pyqtSignal(str, str, int)  # username, ip, port
    connection_status = pyqtSignal(str, bool)  # username, success

    def __init__(self, listen_port=5555, message_callback=None, username="Anonymous"):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{listen_port}")
        self.message_callback = message_callback
        self.username = username
        self.listen_port = listen_port
        
        # Get the actual IP address
        self.local_ip = self._get_local_ip()
        print(f"Local IP address: {self.local_ip}")
        
        # Initialize encryption
        self.encryption = RSAEncryption()
        self.encryption.generate_keys()
        print("Keys generated and loaded successfully")
        
        # Store peer public keys
        self.peer_public_keys = {}
        
        # Store pending connection requests
        self.pending_connections = {}
        
        # Store connected peers
        self.connected_peers = {}
        
        # Store connection state
        self.connection_state = {}  # Tracks the state of each connection attempt
        
        # Start receiving thread
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.receive_thread.start()

    def _get_local_ip(self):
        """Get the local IP address of this machine"""
        try:
            # Create a socket to get the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Doesn't actually connect, just gets the local IP
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            # Fallback to localhost if we can't determine the IP
            return "127.0.0.1"

    def cleanup(self):
        """Clean up network resources"""
        try:
            # Stop the receive thread gracefully
            self.running = False
            if hasattr(self, 'receive_thread') and self.receive_thread and self.receive_thread.is_alive():
                try:
                    self.receive_thread.join(timeout=2)
                except Exception as e:
                    print(f"Error stopping receive thread: {str(e)}")

            # Close all connections first
            for peer_username in list(self.connected_peers.keys()):
                try:
                    peer_info = self.connected_peers[peer_username]
                    self.disconnect_from_peer(peer_info["ip"], peer_info["port"])
                except Exception as e:
                    print(f"Error disconnecting from {peer_username}: {str(e)}")

            # Close the socket gracefully
            if hasattr(self, 'socket') and self.socket:
                try:
                    self.socket.close(linger=0)
                except Exception as e:
                    print(f"Error closing socket: {str(e)}")

            # Clear all peer information
            self.connected_peers.clear()
            self.pending_connections.clear()
            self.peer_public_keys.clear()
            self.connection_state.clear()

            # Close the context last
            if hasattr(self, 'context') and self.context:
                try:
                    self.context.term()
                except Exception as e:
                    print(f"Error terminating context: {str(e)}")

        except Exception as e:
            print(f"Error during network cleanup: {str(e)}")
        finally:
            # Ensure the keys directory is cleaned up
            try:
                if os.path.exists("keys"):
                    shutil.rmtree("keys")
                    print("Keys directory deleted")
            except Exception as e:
                print(f"Error cleaning up keys directory: {str(e)}")

    def get_public_key_pem(self):
        """Get the public key in PEM format"""
        return self.encryption.get_public_key_pem()

    def encrypt_message(self, message, recipient_username=None):
        """Encrypt a message using the appropriate public key"""
        try:
            if recipient_username and recipient_username in self.peer_public_keys:
                # Use recipient's public key if available
                print(f"Using public key for {recipient_username}")
                return self.encryption.encrypt_message(message, self.peer_public_keys[recipient_username])
            else:
                # If no recipient key available, return unencrypted message
                print(f"Warning: No public key available for {recipient_username}, sending unencrypted message")
                return message
        except Exception as e:
            print(f"Encryption error: {e}")
            return message

    def decrypt_message(self, encrypted_message):
        """Decrypt a message using our private key"""
        try:
            # First try to decrypt
            decrypted = self.encryption.decrypt_message(encrypted_message)
            print(f"Decryption result: {decrypted[:50] if decrypted else 'None'}")
            return decrypted
        except Exception as e:
            print(f"Decryption error: {e}")
            # If decryption fails, return the original message
            return encrypted_message

    def initiate_connection(self, peer_ip, peer_port, peer_username):
        """Initiate a connection request to a peer"""
        # Check if already connected
        if peer_username in self.connected_peers:
            print(f"Already connected to {peer_username}")
            self.connection_status.emit(peer_username, True)
            return True
            
        try:
            # Set connection state
            self.connection_state[peer_username] = "connecting"
            
            # Create a temporary socket for connection request
            conn_socket = self.context.socket(zmq.REQ)
            conn_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            conn_socket.connect(f"tcp://{peer_ip}:{peer_port}")
            
            # Send connection request
            conn_request = {
                "type": "connection_request",
                "username": self.username,
                "port": self.listen_port,
                "ip": self.local_ip
            }
            conn_socket.send_json(conn_request)
            
            # Wait for response
            response = conn_socket.recv_json()
            conn_socket.close()
            
            if response["type"] == "connection_accepted":
                # Connection accepted, proceed with key exchange
                print(f"Connection accepted by {peer_username}")
                self.connection_state[peer_username] = "key_exchange"
                self.initiate_key_exchange(peer_ip, peer_port, peer_username)
                return True
            else:
                # Connection refused
                print(f"Connection refused by {peer_username}")
                self.connection_state[peer_username] = "failed"
                self.connection_status.emit(peer_username, False)
                return False
                
        except zmq.error.Again:
            # Timeout error
            print(f"Connection request to {peer_username} timed out")
            self.connection_state[peer_username] = "failed"
            self.connection_status.emit(peer_username, False)
            return False
        except Exception as e:
            print(f"Connection request failed: {str(e)}")
            self.connection_state[peer_username] = "failed"
            self.connection_status.emit(peer_username, False)
            return False

    def _key_exchange_thread(self, peer_ip, peer_port, peer_username):
        """Thread function for key exchange"""
        # Check if already connected
        if peer_username in self.connected_peers:
            print(f"Already connected to {peer_username}, skipping key exchange")
            return
            
        try:
            # Create a temporary socket for key exchange
            exchange_socket = self.context.socket(zmq.REQ)
            exchange_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            exchange_socket.connect(f"tcp://{peer_ip}:{peer_port}")
            
            # Send our public key
            key_exchange_msg = {
                "type": "key_exchange",
                "username": self.username,
                "public_key": self.get_public_key_pem()
            }
            exchange_socket.send_json(key_exchange_msg)
            
            # Receive peer's public key
            response = exchange_socket.recv_json()
            if response["type"] == "key_exchange":
                # Store the peer's public key
                self.peer_public_keys[peer_username] = response["public_key"]
                print(f"Key exchange completed with {peer_username}")
                
                # Move from pending to connected
                if peer_username in self.pending_connections:
                    self.connected_peers[peer_username] = self.pending_connections[peer_username]
                    del self.pending_connections[peer_username]
                
                self.connection_state[peer_username] = "connected"
                self.key_exchange_complete.emit(peer_username)
                self.connection_status.emit(peer_username, True)
            else:
                print("Invalid key exchange response")
                self.connection_state[peer_username] = "failed"
                self.connection_status.emit(peer_username, False)
            
            exchange_socket.close()
        except zmq.error.Again:
            # Timeout error
            print(f"Key exchange with {peer_username} timed out")
            self.connection_state[peer_username] = "failed"
            self.connection_status.emit(peer_username, False)
        except Exception as e:
            print(f"Key exchange failed: {str(e)}")
            self.connection_state[peer_username] = "failed"
            self.connection_status.emit(peer_username, False)

    def accept_connection(self, peer_ip, peer_port, peer_username):
        """Accept a connection request and exchange keys"""
        # Check if already connected
        if peer_username in self.connected_peers:
            print(f"Already connected to {peer_username}")
            self.connection_status.emit(peer_username, True)
            return True
            
        try:
            # Set connection state
            self.connection_state[peer_username] = "accepting"
            
            # Store the connection info for later use
            self.pending_connections[peer_username] = {
                "ip": peer_ip,
                "port": peer_port
            }
            
            # Create a new socket for this connection request
            accept_socket = self.context.socket(zmq.REQ)
            accept_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            accept_socket.connect(f"tcp://{peer_ip}:{peer_port}")
            
            # Send acceptance response with our connection info
            response = {
                "type": "connection_accepted",
                "username": self.username,
                "port": self.listen_port,
                "ip": self.local_ip
            }
            accept_socket.send_json(response)
            
            # Wait for acknowledgment
            try:
                ack = accept_socket.recv_json(timeout=5000)
                print(f"Received acknowledgment: {ack}")
            except Exception as e:
                print(f"Error receiving acknowledgment: {e}")
            
            accept_socket.close()
            
            # Start key exchange in a separate thread
            threading.Thread(target=self._key_exchange_thread, 
                           args=(peer_ip, peer_port, peer_username),
                           daemon=True).start()
            
            return True
        except Exception as e:
            print(f"Error accepting connection: {str(e)}")
            self.connection_state[peer_username] = "failed"
            return False

    def _connect_back_thread(self, peer_ip, peer_port, peer_username):
        """Thread function to connect back to the peer"""
        # Check if already connected
        if peer_username in self.connected_peers:
            print(f"Already connected to {peer_username}, skipping connect back")
            return
            
        try:
            # Create a temporary socket for connection request
            conn_socket = self.context.socket(zmq.REQ)
            conn_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            conn_socket.connect(f"tcp://{peer_ip}:{peer_port}")
            
            # Send connection request
            conn_request = {
                "type": "connection_request",
                "username": self.username,
                "port": self.listen_port,
                "ip": self.local_ip
            }
            conn_socket.send_json(conn_request)
            
            # Wait for response
            response = conn_socket.recv_json()
            conn_socket.close()
            
            if response["type"] == "connection_accepted":
                # Connection accepted, proceed with key exchange
                print(f"Mutual connection established with {peer_username}")
                self.connection_state[peer_username] = "connected"
                self.connection_status.emit(peer_username, True)
            else:
                # Connection refused
                print(f"Mutual connection refused by {peer_username}")
                self.connection_state[peer_username] = "failed"
                self.connection_status.emit(peer_username, False)
                
        except zmq.error.Again:
            # Timeout error
            print(f"Mutual connection request to {peer_username} timed out")
            self.connection_state[peer_username] = "failed"
            self.connection_status.emit(peer_username, False)
        except Exception as e:
            print(f"Mutual connection request failed: {str(e)}")
            self.connection_state[peer_username] = "failed"
            self.connection_status.emit(peer_username, False)

    def refuse_connection(self, peer_ip, peer_port, peer_username):
        """Refuse a connection request"""
        try:
            # Create a new socket for this connection request
            refuse_socket = self.context.socket(zmq.REQ)
            refuse_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            refuse_socket.connect(f"tcp://{peer_ip}:{peer_port}")
            
            # Send refusal response
            response = {
                "type": "connection_refused",
                "username": self.username,
                "reason": "Connection refused by user"
            }
            refuse_socket.send_json(response)
            
            # Wait for acknowledgment
            try:
                ack = refuse_socket.recv_json(timeout=5000)
                print(f"Received acknowledgment: {ack}")
            except Exception as e:
                print(f"Error receiving acknowledgment: {e}")
            
            refuse_socket.close()
            
            # Clean up connection state
            if peer_username in self.connection_state:
                del self.connection_state[peer_username]
            if peer_username in self.pending_connections:
                del self.pending_connections[peer_username]
                
            return True
        except Exception as e:
            print(f"Error refusing connection: {str(e)}")
            return False

    def initiate_key_exchange(self, peer_ip, peer_port, peer_username):
        """Initiate key exchange with a peer"""
        try:
            # Create a temporary socket for key exchange
            exchange_socket = self.context.socket(zmq.REQ)
            exchange_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            exchange_socket.connect(f"tcp://{peer_ip}:{peer_port}")
            
            # Send our public key
            key_exchange_msg = {
                "type": "key_exchange",
                "username": self.username,
                "public_key": self.get_public_key_pem()
            }
            exchange_socket.send_json(key_exchange_msg)
            
            # Receive peer's public key
            response = exchange_socket.recv_json()
            if response["type"] == "key_exchange":
                self.peer_public_keys[peer_username] = response["public_key"]
                print(f"Key exchange completed with {peer_username}")
                self.key_exchange_complete.emit(peer_username)
                self.connection_status.emit(peer_username, True)
                
                # Update connection state
                if peer_username in self.pending_connections:
                    self.connected_peers[peer_username] = self.pending_connections[peer_username]
            else:
                print("Invalid key exchange response")
                self.connection_status.emit(peer_username, False)
            
            exchange_socket.close()
        except zmq.error.Again:
            # Timeout error
            print(f"Key exchange with {peer_username} timed out")
            self.connection_status.emit(peer_username, False)
        except Exception as e:
            print(f"Key exchange failed: {str(e)}")
            self.connection_status.emit(peer_username, False)

    def send_message(self, receiver_ip, port, message, recipient_username):
        """Send a message to a receiver"""
        def _send_message_thread():
            try:
                # Create a temporary socket for sending
                send_socket = self.context.socket(zmq.REQ)
                send_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
                send_socket.connect(f"tcp://{receiver_ip}:{port}")
                
                # First create the JSON message
                message_data = {
                    "type": "message",
                    "username": self.username,
                    "content": message
                }
                json_message = json.dumps(message_data)
                
                # Then encrypt if we have the recipient's public key
                if recipient_username in self.peer_public_keys:
                    try:
                        print(f"Encrypting message for {recipient_username}")
                        encrypted_message = self.encrypt_message(json_message, recipient_username)
                        send_socket.send_string(encrypted_message)
                    except Exception as e:
                        print(f"Encryption failed: {e}")
                        self.message_sent.emit(False, f"Encryption failed: {str(e)}")
                        return
                else:
                    print(f"No public key for {recipient_username}, sending unencrypted")
                    send_socket.send_string(json_message)
                
                # Wait for acknowledgment
                response = send_socket.recv_string()
                if response == "OK":
                    self.message_sent.emit(True, "")
                else:
                    self.message_sent.emit(False, "Failed to send message")
                
                send_socket.close()
            except Exception as e:
                print(f"Error sending message: {e}")
                self.message_sent.emit(False, str(e))
        
        # Start sending in a separate thread
        threading.Thread(target=_send_message_thread, daemon=True).start()

    def receive_loop(self):
        """Continuously receive messages"""
        while self.running:
            try:
                # Set a timeout for receiving messages
                if self.socket.poll(timeout=1000) == 0:  # 1 second timeout
                    continue
                
                # Receive message
                message = self.socket.recv_string()
                print(f"Raw message received: {message[:100]}...")
                
                # First try to decrypt if it's encrypted
                try:
                    decrypted = self.decrypt_message(message)
                    print(f"Decrypted message: {decrypted[:100]}...")
                    # If decryption succeeded, try to parse as JSON
                    try:
                        message_data = json.loads(decrypted)
                        print(f"Parsed JSON from decrypted message: {message_data.get('type', 'unknown')}")
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error after decryption: {e}")
                        # If not JSON, treat as plain text
                        self.message_received.emit(decrypted)
                        self.socket.send_string("OK")
                        continue
                except Exception as e:
                    print(f"Decryption failed: {e}")
                    # If decryption failed, try to parse as JSON directly
                    try:
                        message_data = json.loads(message)
                        print(f"Parsed JSON from raw message: {message_data.get('type', 'unknown')}")
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error on raw message: {e}")
                        # If neither decryption nor JSON parsing worked, treat as plain text
                        self.message_received.emit(message)
                        self.socket.send_string("OK")
                        continue
                
                # Handle different message types
                if message_data["type"] == "connection_request":
                    # Only emit if we're not already connected or connecting
                    peer_username = message_data["username"]
                    print(f"Connection request from {peer_username}")
                    if (peer_username not in self.connected_peers and 
                        peer_username not in self.pending_connections and
                        self.connection_state.get(peer_username) != "connecting"):
                        print(f"Emitting connection request for {peer_username}")
                        # Store the connection info for later use
                        self.pending_connections[peer_username] = {
                            "ip": message_data["ip"],
                            "port": message_data["port"]
                        }
                        # Emit the connection request to the UI
                        self.connection_request.emit(
                            message_data["username"],
                            message_data["ip"],
                            message_data["port"]
                        )
                        # Don't send a response yet - wait for user decision
                        # The UI will call accept_connection or refuse_connection
                    else:
                        print(f"Ignoring connection request from {peer_username} - already connected or connecting")
                        # Send a response for duplicate requests
                        self.socket.send_json({"type": "connection_accepted", "username": self.username})
                elif message_data["type"] == "connection_accepted":
                    print(f"Connection accepted by {message_data['username']}")
                    if message_data["username"] not in self.connected_peers:
                        self.connection_status.emit(message_data["username"], True)
                elif message_data["type"] == "connection_refused":
                    print(f"Connection refused by {message_data['username']}")
                    self.connection_status.emit(message_data["username"], False)
                elif message_data["type"] == "key_exchange":
                    print(f"Key exchange from {message_data['username']}")
                    self._handle_key_exchange(message_data)
                elif message_data["type"] == "key_exchange_complete":
                    print(f"Key exchange complete with {message_data['username']}")
                    if message_data["username"] not in self.connected_peers:
                        self.key_exchange_complete.emit(message_data["username"])
                elif message_data["type"] == "disconnect":
                    peer_username = message_data["username"]
                    print(f"Disconnect request from {peer_username}")
                    if peer_username in self.connected_peers:
                        del self.connected_peers[peer_username]
                        if peer_username in self.peer_public_keys:
                            del self.peer_public_keys[peer_username]
                        print(f"Peer {peer_username} disconnected")
                        self.connection_status.emit(peer_username, False)
                    self.socket.send_json({"type": "disconnect_ack"})
                elif message_data["type"] == "disconnect_ack":
                    print("Disconnect acknowledged")
                elif message_data["type"] == "message":
                    print(f"Message from {message_data.get('username', 'unknown')}")
                    self.message_received.emit(message)
                elif message_data["type"] == "file":
                    print(f"File from {message_data.get('username', 'unknown')}")
                    self.message_received.emit(message)
                else:
                    print(f"Received unknown message type: {message_data.get('type', 'unknown')}")
                    self.message_received.emit(message)
                
                # Send acknowledgment for all message types except connection_request
                # (which is handled separately)
                if message_data["type"] != "connection_request":
                    self.socket.send_string("OK")
            except zmq.error.Again:
                continue
            except Exception as e:
                print(f"Error in receive loop: {e}")
                continue

    def _handle_key_exchange(self, message_data):
        """Handle key exchange message"""
        try:
            # Extract peer information
            peer_username = message_data["username"]
            peer_public_key = message_data["public_key"]
            
            # Check if we already have this peer's key
            if peer_username in self.peer_public_keys:
                print(f"Already have key for {peer_username}")
                # Send acknowledgment
                self.socket.send_json({
                    "type": "key_exchange_ack",
                    "username": self.username
                })
                return
            
            # Store the peer's public key
            self.peer_public_keys[peer_username] = peer_public_key
            print(f"Stored public key for {peer_username}")
            
            # Send our public key in response
            response = {
                "type": "key_exchange",
                "username": self.username,
                "public_key": self.get_public_key_pem()
            }
            self.socket.send_json(response)
            print(f"Sent our public key to {peer_username}")
            
            # Update connection state
            if peer_username in self.pending_connections:
                if peer_username not in self.connected_peers:
                    print(f"Moving {peer_username} from pending to connected")
                    self.connected_peers[peer_username] = self.pending_connections[peer_username]
                    self.connection_state[peer_username] = "connected"
                    self.key_exchange_complete.emit(peer_username)
                    self.connection_status.emit(peer_username, True)
                
        except Exception as e:
            print(f"Error handling key exchange: {str(e)}")
            # Send error response
            error_response = {
                "type": "error",
                "error": f"Key exchange failed: {str(e)}"
            }
            self.socket.send_json(error_response)

    def disconnect_from_peer(self, peer_ip, peer_port):
        """Disconnect from a peer"""
        try:
            # Create a temporary socket for disconnect request
            disconnect_socket = self.context.socket(zmq.REQ)
            disconnect_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            disconnect_socket.connect(f"tcp://{peer_ip}:{peer_port}")
            
            # Send disconnect request
            disconnect_request = {
                "type": "disconnect",
                "username": self.username
            }
            disconnect_socket.send_json(disconnect_request)
            
            # Wait for response
            try:
                response = disconnect_socket.recv_json()
                print(f"Disconnect response: {response}")
            except zmq.error.Again:
                print("Disconnect request timed out")
            except Exception as e:
                print(f"Error receiving disconnect response: {str(e)}")
                
            disconnect_socket.close()
            
            # Remove from connected peers
            for peer_username, peer_info in list(self.connected_peers.items()):
                if peer_info["ip"] == peer_ip and peer_info["port"] == peer_port:
                    del self.connected_peers[peer_username]
                    if peer_username in self.peer_public_keys:
                        del self.peer_public_keys[peer_username]
                    print(f"Disconnected from {peer_username}")
                    return True
                    
            return False
        except Exception as e:
            print(f"Error disconnecting from peer: {str(e)}")
            return False