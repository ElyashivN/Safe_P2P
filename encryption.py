import os
import pickle

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, modes, algorithms
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from phe import paillier
import base64


class Encryption:
    def __init__(self):
        pass

    @staticmethod
    def generatePublicPrivateKeys():
        """
        Generate Paillier public and private keys for homomorphic encryption.
        """
        public_key, private_key = paillier.generate_paillier_keypair()
        return public_key, private_key

    @staticmethod
    def encrypt(public_key, data):
        """
        Encrypt data using Paillier homomorphic encryption.

        :param public_key: Paillier public key.
        :param data: Integer data to encrypt (must be an integer).
        :return: Encrypted data (as a base64-encoded string).
        """
        if not isinstance(data, int):
            raise ValueError("Paillier encryption only works with integers.")

        encrypted_data = public_key.encrypt(data)
        encrypted_data_bytes = encrypted_data.ciphertext(True).to_bytes(
        (encrypted_data.ciphertext(True).bit_length() + 7) // 8, byteorder='big')

        # Return base64 encoded encrypted data
        return base64.b64encode(encrypted_data_bytes).decode('utf-8')
        # return encrypted_data_bytes.decode('utf-8')

    @staticmethod
    def decrypt(private_key, encrypted_data):
        """
        Decrypt data using Paillier homomorphic encryption.

        :param private_key: Paillier private key.
        :param encrypted_data: Encrypted data (base64-encoded string).
        :return: Decrypted integer.
        """
        # number 1 problem: reach too big, and overflow the decrypt -> need to solve
        # number 2 problem: the decryption works but provides uncoherent data.
        # Decode base64 encrypted data
        encrypted_data_bytes = base64.b64decode(encrypted_data)
        ciphertext_int = int.from_bytes(encrypted_data_bytes, byteorder='big')
        cipher_result = paillier.EncryptedNumber(private_key.public_key, ciphertext_int)
        # Decrypt the ciphertext
        decrypted_data = private_key.decrypt(cipher_result)
        return decrypted_data


    # Store Paillier Private Key with Password-Based Encryption
    @staticmethod
    def store(password, private_key, path=""):
        """
        Store the Paillier private key securely with password-based encryption.

        :param password: Password for encrypting the private key.
        :param private_key: Paillier private key to store.
        :param path: File path for storage.
        """
        # Derive AES key from password
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        aes_key = kdf.derive(password.encode())

        # Serialize the Paillier private key with pickle
        private_key_bytes = pickle.dumps(private_key)

        # Encrypt the serialized private key with AES in GCM mode
        iv = os.urandom(12)  # GCM requires a 12-byte nonce
        encryptor = Cipher(algorithms.AES(aes_key), modes.GCM(iv), backend=default_backend()).encryptor()
        encrypted_key = encryptor.update(private_key_bytes) + encryptor.finalize()

        # Store salt, IV, tag, and encrypted key in a single binary file
        with open(path + 'encrypted_paillier_key.bin', 'wb') as f:
            f.write(salt + iv + encryptor.tag + encrypted_key)

    # Load Paillier Private Key with Password-Based Decryption
    @staticmethod
    def load(password, path=""):
        """
        Load the Paillier private key securely with password-based decryption.

        :param password: Password for decrypting the private key.
        :param path: File path for loading.
        :return: Decrypted Paillier private key.
        """
        with open(path + 'encrypted_paillier_key.bin', 'rb') as f:
            # Read salt, IV, tag, and encrypted data
            salt = f.read(16)
            iv = f.read(12)
            tag = f.read(16)
            encrypted_key = f.read()

        # Derive AES key from password
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        aes_key = kdf.derive(password.encode())

        # Decrypt the private key
        decryptor = Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag), backend=default_backend()).decryptor()
        private_key_bytes = decryptor.update(encrypted_key) + decryptor.finalize()

        # Deserialize the Paillier private key
        private_key = pickle.loads(private_key_bytes)
        return private_key