from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64
import os
import json

class RSAEncryption:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.keys_dir = "keys"
        
        # Create keys directory if it doesn't exist
        if not os.path.exists(self.keys_dir):
            os.makedirs(self.keys_dir)

    def generate_keys(self):
        """Generate a new RSA key pair"""
        # Generate private key
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Get public key
        self.public_key = self.private_key.public_key()
        
        # Save keys to files
        self._save_keys()

    def _save_keys(self):
        """Save the generated keys to files"""
        # Save private key
        with open(f"{self.keys_dir}/private_key.pem", "wb") as f:
            f.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save public key
        with open(f"{self.keys_dir}/public_key.pem", "wb") as f:
            f.write(self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

    def get_public_key_pem(self):
        """Get the public key in PEM format"""
        if not self.public_key:
            return None
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def encrypt_message(self, message, public_key_pem=None):
        """Encrypt a message using RSA"""
        try:
            # If a public key is provided, use it; otherwise use our own public key
            if public_key_pem:
                print(f"Loading public key from PEM: {public_key_pem[:50]}...")
                public_key = serialization.load_pem_public_key(public_key_pem.encode())
            else:
                print("Using own public key")
                public_key = self.public_key
            
            # Encrypt the message
            print(f"Encrypting message: {message[:50]}...")
            encrypted = public_key.encrypt(
                message.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            result = base64.b64encode(encrypted).decode()
            print(f"Encryption result: {result[:50]}...")
            return result
        except Exception as e:
            print(f"Encryption error: {e}")
            return message

    def decrypt_message(self, encrypted_message):
        """Decrypt a message using RSA"""
        try:
            # Check if the message is already a JSON string
            try:
                # Try to parse it as JSON to see if it's already a JSON string
                json.loads(encrypted_message)
                # If we get here, it's already a JSON string, no need to decrypt
                return encrypted_message
            except json.JSONDecodeError:
                # Not a JSON string, proceed with decryption
                pass
                
            # Decode from base64
            print(f"Decoding from base64: {encrypted_message[:50]}...")
            encrypted = base64.b64decode(encrypted_message)
            
            # Decrypt using private key
            print("Decrypting with private key")
            decrypted = self.private_key.decrypt(
                encrypted,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Decode from bytes to string
            decrypted_str = decrypted.decode('utf-8')
            print(f"Decryption result: {decrypted_str[:50]}...")
            return decrypted_str
        except Exception as e:
            print(f"Decryption error: {e}")
            # If decryption fails, return the original message
            return encrypted_message


if __name__ == "__main__":
    generate_rsa_keys()

    from cryptography.hazmat.primitives.asymmetric import dh


    def generate_dh_keys():
        """Generates ephemeral Diffie-Hellman keys"""
        parameters = dh.generate_parameters(generator=2, key_size=2048)
        private_key = parameters.generate_private_key()
        public_key = private_key.public_key()
        return private_key, public_key