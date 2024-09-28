import os.path

import config
from dht import DHT
from FileHandler import FileHandler
from spacePIR import SpacePIR
from Peer import Peer
from encryption import Encryption
import pickle


class Node(Peer):

    def __init__(self, port, peer_id, host='127.0.0.1', private_key=None):
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

    def store_Node(self, password, path=""):
        """
        store the privatekey and the dht (private key is always stored with a passsword
        :param password: the password to encrypt the key
        :param path: the path to store the key and the dht
        :return: nothing
        """
        Encryption.store(password, self.privateKey, path=path)
        with open(path + 'dht.pickle', 'wb') as handle:
            pickle.dump(self.DHT.get_dht(), handle, protocol=pickle.HIGHEST_PROTOCOL)

    def load_node(self, password, path=""):
        """
        load the private key and decript it, and loads the dht
        :param password: the password for the private key encryption
        :param path: the path to the key
        :return: None
        """
        self.privateKey = Encryption.load(password, path)
        self.publicKey = self.privateKey.public_key()
        with open(path + 'dht.pickle', 'rb') as handle:
            dht = pickle.load(handle)
        self.DHT._add(dht)

    def listfiles(self):
        return self.spacePIR.listfiles()

    def get(self, name):
        """
        get the name
        :param name:
        :return:
        """
        dht = self.DHT.get_dht()
        for key in dht.keys():
            self.ask(dht[key], name)

    def add_DHT(self, DHT):
        return self.DHT.add_DHT(DHT)

    def upload(self, file_path):
        k = config.SUBFILE_SIZE
        n = (os.path.getsize(file_path) * 2) / k
        subfiles, original_size, _ = self.fileHandler.divide(file_path,self.peer_id,n,k)
        for i, node in enumerate(self.DHT.get_dht()):
            self.ask_upload(subfiles[i], node[config.PORT])
            #wait then if self.recieve_uploaded_succes(node[config.PORT])) continue else more
            if i >= n:
                # if we ended up sending all the subfiles.
                break


    def ask(self, info, name):
        port = info[config.PORT]
        socket = info[config.SOCKET]
