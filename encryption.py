import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.algorithms import AES


class Encryption:
    def __init__(self):
        pass

    @staticmethod
    def encrypt(key, data):
        """
        Encrypt data using AES-GCM.

        :param data: Data to encrypt (bytes).
        :return: Encrypted data encoded in base64 (str).
        """
        data = bin(data)
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        encrypted = cipher.nonce + tag + ciphertext
        return base64.b64encode(encrypted).decode('utf-8')

    @staticmethod
    def decrypt(key, encrypted_data):
        """
        Decrypt data using AES-GCM.

        :param encrypted_data: Encrypted data encoded in base64 (str).
        :return: Decrypted data (bytes).
        """
        raw_data = base64.b64decode(encrypted_data)
        nonce, tag, ciphertext = raw_data[:16], raw_data[16:32], raw_data[32:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        try:
            return cipher.decrypt_and_verify(ciphertext, tag)
        except ValueError:
            raise ValueError("Incorrect decryption")
    @staticmethod
    def generatePublicPrivateKeys():
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # # Serialize the private key
        # pem_private_key = private_key.private_bytes(
        #     encoding=serialization.Encoding.PEM,
        #     format=serialization.PrivateFormat.PKCS8,
        # )

        # Generate public key from the private key
        public_key = private_key.public_key()

        # # Serialize the public key
        # pem_public_key = public_key.public_bytes(
        #     encoding=serialization.Encoding.PEM,
        #     format=serialization.PublicFormat.SubjectPublicKeyInfo,
        # )

        return public_key, private_key

    @staticmethod
    def store(password, private_key,path=""):
        encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
        # encrypt the file in the computer
        # Serialize the private key
        pem_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm,
        )

        with open(path+'private_key.pem', 'wb') as f:
            f.write(pem_private_key)
    @staticmethod
    def load(password, path=""):
        # Load the private key
        with open(path+'private_key.pem', 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=password,  # Use the same password used during encryption
            )
        return private_key
