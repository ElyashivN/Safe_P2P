import bisect
import os
import socket
import threading
import time

import config
from dht import DHT
from FileHandler import FileHandler
from Peer import Peer, delete_file
from encryption import Encryption
import pickle


def find_index(names, target):
    """
    Function to find the index of the target in an ordered list.
    """
    index = bisect.bisect_left(names, target)
    if index < len(names) and names[index] == target:
        return index
    return -1


class Node(Peer):
    """
    Class that handles a node in the network.
    """
    NUMBER_TRIES_UPLOAD = 4
    SAFETY_CONSTANT = 1  # Number of tries to upload to a peer

    def __init__(self, port, peer_id, host='127.0.0.1', private_key=None, path=""):
        super().__init__(peer_id, host, port)
        if private_key is None:
            self.publicKey, self.privateKey = Encryption.generatePublicPrivateKeys()
        else:
            self.privateKey = private_key
            self.publicKey = private_key.public_key()
        self.DHT = DHT(port)
        self.fileHandler = FileHandler()
        self.host = host
        self.port = port
        self.path = path
        self.start_upload_download_thread()

    def store_Node(self, password, path=""):
        """
        Store the private key and DHT.
        """
        Encryption.store(password, self.privateKey, path=path)
        with open(os.path.join(path, 'dht.pickle'), 'wb') as handle:
            pickle.dump(self.DHT.get_dht(), handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(os.path.join(path, 'listfiles.pickle'), 'wb') as handle:
            pickle.dump(self.spacePIR.get_file_names(), handle, protocol=pickle.HIGHEST_PROTOCOL)

    def load_node(self, password, path=""):
        """
        Load the private key and DHT from storage.
        """
        self.privateKey = Encryption.load(password, path)
        self.publicKey = self.privateKey.public_key()
        with open(os.path.join(path, 'dht.pickle'), 'rb') as handle:
            dht = pickle.load(handle)
        self.DHT.add_DHT(dht)
        with open(os.path.join(path, 'listfiles.pickle'), 'rb') as handle:
            listfiles = pickle.load(handle)
        self.spacePIR.listfiles = listfiles

    def listfiles(self):
        """
        Return the list of files in spacePIR.
        """
        return self.spacePIR.listfiles()

    def download(self, name, n, k):
        """
        Download and reconstruct a file using subfiles from peers.
        """
        dht = self.DHT.get_dht()
        part_files = []
        for key in dht.keys():
            if len(part_files) >= k * Node.SAFETY_CONSTANT:
                success = self.fileHandler.combine(part_files, n, k, os.path.join(self.path, name))
                if success:
                    for file in part_files:
                        delete_file(file)
                    return True
                return False
            info = dht[key]
            port = info[config.PORT]
            host = info[config.HOST]
            file_name = self.download_from_peer(name, port, len(part_files), host)
            if file_name is not None:
                part_files.append(file_name)

        # If failed, delete all partial files
        for file in part_files:
            delete_file(file)
        return False

    def upload(self, file_path):
        """
        Upload a file to the network.
        """
        block_size = int(config.SUBFILE_SIZE)
        n = max(int((os.path.getsize(file_path) * 2) / block_size), 1)
        subfiles, k, _ = self.fileHandler.divide(file_path, self.peer_id, n=n, block_size=block_size)
        dht = self.DHT.get_dht()
        if len(dht) < n * Node.SAFETY_CONSTANT:
            raise ValueError(config.DHT_SMALL)
        i = 0
        for node in dht.values():
            if self.upload_to_peer(subfiles[i], node[config.PORT], node[config.HOST]):
                i += 1
            if i >= n:
                return True
        return False

    def upload_to_peer(self, file, port, host="127.0.0.1"):
        """
        Upload the file to a peer using a client socket.
        """
        print("uploading from ", str(self.peer_id), " to port: ", str(port))
        try:
            with socket.create_connection((host, port)) as sock:
                self.send_message(config.REQUEST_UPLOAD, sock)
                uploaded = self.is_uploaded_approved(sock)
                time.sleep(0.1)  # 100 ms to give the peer time to process the request

                i = 0
                while uploaded == -1 and i < Node.NUMBER_TRIES_UPLOAD:
                    time.sleep(0.1)  # 100 ms to give the peer time to process the request
                    uploaded = self.is_uploaded_approved(sock)
                    i += 1

                if uploaded == 0 or uploaded == -1:
                    return False

                # Send the file
                # self.send_message(file+",", sock)  # sending out file name todo if we change file handler to have name
                # in top of file this is redundunt
                self.send_file(file, sock)
                print("file has been sent")

                # Wait for success confirmation
                for i in range(Node.NUMBER_TRIES_UPLOAD):
                    success = self.is_uploaded_success(sock)
                    if success == 1:
                        return True
                    elif success == 0:
                        self.send_file(file, sock)
                return False
        except Exception as e:
            print(f"Error uploading to peer: {e}")
            return False

    def construct_list_from_bytes(self, list_bin):
        """
        Converts a byte stream representing a list of file names (separated by newlines) into a Python list.

        Args:
            list_bin (bytes): A byte stream containing file names separated by '\n'.

        Returns:
            list: A list of file names.
        """
        try:
            # Decode the byte stream into a string
            decoded_str = list_bin.decode('utf-8')

            # Split the string by newline characters to get the list of file names
            file_list = decoded_str.split('\n')

            # Filter out any empty strings that might result from trailing newlines
            file_list = [file_name for file_name in file_list if file_name]

            return file_list
        except Exception as e:
            print(f"Error constructing list from bytes: {e}")
            return []

    def download_from_peer(self, name, port, number, host="127.0.0.1"):
        """
        Download a file part from a peer.
        """
        try:
            with socket.create_connection((host, port)) as sock:
                self.send_message(config.REQUEST_FILE, sock)
                file_list = self.receive_obj(sock)
                file_list = self.construct_list_from_bytes(file_list)
                i = find_index(file_list, name)
                n = len(file_list)
                v = self.construct_vector(i, n)
                self.send_file('\n'.join(v), sock)
                obj = self.receive_obj(sock)

            if i == -1:
                return None

            print("downloaded object, processing it")
            decrypted_file = self.privateKey.decrypt(obj)
            file = decrypted_file.split(',')[1]
            filename = os.path.join(self.path, f"{name}_{number}")
            with open(filename, 'wb') as handle:
                handle.write(file)
            return filename
        except Exception as e:
            print(f"Error downloading from peer: {e}")
            return None

    def start_upload_download_thread(self):
        self._upload_thread = threading.Thread(target=self.upload_work)
        self._upload_thread.start()
        self._download_thread = threading.Thread(target=self.download_work)
        self._download_thread.start()

    def download_work(self):
        pass
        # while True:
        #     sock = self.download_work_list.get()  # Thread-safe pop equivalent for queue
        #     try:
        #         # Send the list of file names
        #         list_of_files = self.spacePIR.get_file_names()
        #         self.send_message('\n'.join(list_of_files), sock)
        #
        #         # Receive the vector
        #         vector = self.receive_obj(sock)
        #
        #         # Process the data and prepare the response (omitted for brevity)
        #         data = self.spacePIR.get(vector)
        #
        #         # Send the response
        #         self.send_file(data, sock)
        #     except Exception as e:
        #         print(f"Error handling get request: {e}")

    def upload_work(self):
        print("Uploading work")
        # while True:
        #     # Block until an item is available in the queue
        #     sock = self.upload_work_list.get()  # Automatically handles removing the item
        #     print("we actually have work debug")
        #     if self.spacePIR.is_allow_upload:
        #         with self._upload_lock:
        #             self.send_message(config.UPLOAD_APPROVED, sock)
        #             try:
        #                 file_name, _ = self.receive_file(sock)
        #                 if file_name:
        #                     self.spacePIR.add(file_name)
        #                     self.send_message(config.UPLOADED_SUCCESS, sock)
        #                 else:
        #                     self.send_message(config.UPLOADED_FAILED, sock)
        #             except Exception as e:
        #                 print(f"Error uploading file: {e}")
        #                 self.send_message(config.UPLOADED_FAILED, sock)
        #     else:
        #         self.send_message(config.UPLOAD_DENIED, sock)

    def add_DHT(self, other_DHT):
        return self.DHT.add_DHT(other_DHT)

    def construct_vector(self, i, n):
        """
        Constructs and encrypts a vector for secure retrieval.
        """
        vector = [0] * n
        if 0 <= i < n:
            vector[i] = 1
        print(self.privateKey)
        Encryption.encrypt(self.privateKey, 1)
        encrypted_vector = [self.privateKey.encrypt(value) for value in vector]
        print(encrypted_vector)
        return encrypted_vector
