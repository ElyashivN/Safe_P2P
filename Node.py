import bisect
import os
import random
import secrets
import socket
import threading
import time
from typing import List

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
        self.DHT = DHT()
        self.fileHandler = FileHandler()
        self.host = host
        self.port = port
        self.path = path
        self.uploaded_files = list() #list of all uploaded files and their corresponding n, k

    def store_Node(self, password, path=""):
        """
        Store the private key and DHT.
        """
        Encryption.store(password, self.privateKey, path=path)
        with open(os.path.join(path, 'dht.pickle'), 'wb') as handle:
            pickle.dump(self.DHT.get_dht(), handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(os.path.join(path, 'listfiles.pickle'), 'wb') as handle:
            pickle.dump(self.spacePIR.get_file_names(), handle, protocol=pickle.HIGHEST_PROTOCOL)

    def get_uploaded_files(self):
        return self.uploaded_files
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
        SecurityRandom = 0  # a security random number for us to keep checking after we had already
        # received enough parts to reconstruct the message, in order to make MITM attacks not able to guess our
        # file based on when we stopped asking for new files for people
        if (n-k)//2 > 0:
            SecurityRandom = secrets.randbelow((n-k)//2)
        for key in dht.keys():
            try:
                if len(part_files) >= k + SecurityRandom:
                    print("downloaded enough, needs to reconstruct the message now")
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
                else:
                    raise ValueError("error in getting filename and downloading from one of the files")
            except Exception as e:
                print(f"error downloading {name} from {host}: {e}")
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
                self.uploaded_files.append((file_path, n, k))
                return n, k
        return 0, 0

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
    def vector_to_bytes(self, vector: List[bytes]) -> bytes:
        """
        make a vector into a bytes object.
        :param vector: a list of bytes
        :return: bytes object
        """


    def download_from_peer(self, name, port, number, host="127.0.0.1"):
        """
        Download a file part from a peer.
        """
        try:
            with socket.create_connection((host, port)) as sock:
                self.send_message(config.REQUEST_FILE, sock)
                file_list = self.receive_obj(sock)
                file_list = self.construct_list_from_string(file_list)
                i = find_index(file_list, name)
                n = len(file_list)
                v = self.construct_vector(i, n)
                self.send_message(v, sock)
                time.sleep(2) #debug wait for 2 seconds to recieve
                list_chunks = list()
                for i in range(config.SUBFILE_SIZE//config.BUFFER_SIZE):
                    obj = self.receive_obj(sock)
                    list_chunks.append(obj)


            if i == -1: #if we failed to send
                return None
            data = ""
            for chunk in list_chunks:
                decrypted_file = Encryption.decrypt(self.privateKey, obj)
                file_content_reverted = decrypted_file.decode()
                data+=file_content_reverted
            file = data.split(',')[1].encode()
            filename = os.path.join(self.path, f"{name}_{number}")
            with open(filename, 'wb') as handle:
                handle.write(file)
            print(f"filename has been recieved and it is :{filename}")
            return filename
        except Exception as e:
            print(f"Error downloading from peer: {e}")
            return None



    def add_DHT(self, other_DHT):
        return self.DHT.add_DHT(other_DHT)

    def add_node_to_DHT(self, port, node_id, host):
        return self.DHT.add_node(port, node_id, host)

    def construct_vector(self, i, n):
        """
        Constructs and encrypts a vector for secure retrieval.
        """
        vector = [0] * n
        if 0 <= i < n:
            vector[i] = 1
        # Encryption.encrypt(self.publicKey, 1)
        encrypted_vector = [Encryption.encrypt(self.publicKey, value) for value in vector]
        # n_bytes = pickle.dumps(self.publicKey)
        n_bytes = self.publicKey.n.to_bytes((self.publicKey.n.bit_length() + 7) // 8, byteorder='big')
        if len(n_bytes) < config.KEY_SIZE:
            # Pad with leading zeros if it's less than 768 bytes
            n_bytes = n_bytes.rjust(config.KEY_SIZE, b'\x00')
        encrypted_vector.append(n_bytes)

        binary_vector = b"".join(encrypted_vector)
        return binary_vector
