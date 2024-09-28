import os
import base64
import pickle

from encryption import Encryption


class SpacePIR:
    """
    SpacePIR handles the private storage and retrieval of files using a simplified cPIR approach.
    It encrypts file names and contents to ensure privacy during both addition and retrieval.
    """
    def __init__(self, key=None,space_capacity=200, storage_path='space_pir_storage.pkl'):
        """
        Initialize the SpacePIR instance.

        :param key: Optional. A 16-byte AES key. If not provided, a new key is generated.
        :param storage_path: Path to the file where encrypted data will be stored persistently.
        """
        self.is_allow_upload = True
        self.space_capacity = space_capacity
        self.key = key
        self.storage_path = storage_path
        self.files = {}  # Dictionary to store encrypted filenames and data
        self._load_storage()

    def change_capacity(self, capacity):
        if capacity > len(self.files):
            raise ValueError('Capacity must be less than the number of files, delete some')
        self.space_capacity = capacity



    def _load_storage(self):
        """
        Load the encrypted storage from the storage path.
        """
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'rb') as f:
                    self.files = pickle.load(f)
                print(f"SpacePIR storage loaded from {self.storage_path}.")
            except Exception as e:
                print(f"Error loading storage: {e}")
                self.files = {}
        else:
            print("No existing SpacePIR storage found. Starting fresh.")
            self.files = {}

    def _save_storage(self):
        """
        Save the encrypted storage to the storage path.
        """
        try:
            with open(self.storage_path, 'wb') as f:
                pickle.dump(self.files, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"SpacePIR storage saved to {self.storage_path}.")
        except Exception as e:
            print(f"Error saving storage: {e}")

    # --- Public Methods ---
    def add(self, filename,key, binary_data):
        """
        Add a file to the SpacePIR storage privately.

        :param filename: Name of the file (str).
        :param binary_data: Binary content of the file (bytes).
        """
        try:
            # Encrypt the filename and data
            encrypted_filename = Encryption.encrypt(key, filename.encode('utf-8'))
            encrypted_data = Encryption.encrypt(key, binary_data)

            # Store in the dictionary
            self.files[encrypted_filename] = encrypted_data
            if len(self.files) >= self.space_capacity:
                self.is_allow_upload = False

            # Persist the storage
            self._save_storage()

            print(f"File '{filename}' added privately.")
        except Exception as e:
            print(f"Error adding file '{filename}': {e}")

    def get(self, key, filename):
        """
        Retrieve a file from the SpacePIR storage privately.

        :param filename: Name of the file to retrieve (str).
        :return: Binary content of the file (bytes).
        :raises FileNotFoundError: If the file does not exist.
        """
        try:
            # Encrypt the filename to search
            encrypted_filename = Encryption.encrypt(key ,filename.encode('utf-8'))

            # Retrieve encrypted data
            encrypted_data = self.files.get(encrypted_filename, None)
            if not encrypted_data:
                raise FileNotFoundError(f"File '{filename}' not found.")

            # Decrypt the data
            binary_data = Encryption.decrypt(key, encrypted_data)

            print(f"File '{filename}' retrieved privately.")
            return binary_data
        except FileNotFoundError as fnf:
            print(fnf)
            raise
        except Exception as e:
            print(f"Error retrieving file '{filename}': {e}")
            raise

    def listfiles(self,key):
        """
        List all files in the SpacePIR storage.

        :return: List of filenames (str).
        """
        try:
            filenames = [Encryption.decrypt(key, base64.b64decode(enc_fname)).decode('utf-8')
                         for enc_fname in self.files.keys()]
            return filenames
        except Exception as e:
            print(f"Error listing files: {e}")
            return []

    def delete_file(self, key, filename):
        """
        Delete a file from the SpacePIR storage.

        :param key: key of the file to delete (str).
        :param filename: Name of the file to delete (str).
        """
        try:
            encrypted_filename = Encryption.encrypt(key, filename.encode('utf-8'))
            if encrypted_filename in self.files:
                del self.files[encrypted_filename]
                self._save_storage()
                print(f"File '{filename}' deleted successfully.")
            else:
                print(f"File '{filename}' does not exist.")
        except Exception as e:
            print(f"Error deleting file '{filename}': {e}")
