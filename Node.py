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
        self.spacePIR = SpacePIR()
        self.fileHandler = FileHandler()
        self.host = host
        self.port = port

    def store(self, password, path=""):
        Encryption.store(password, self.privateKey, path=path)
        with open('dht.pickle', 'wb') as handle:
            pickle.dump(self.DHT.get_dht(), handle, protocol=pickle.HIGHEST_PROTOCOL)

    def load(self, password, path=""):
        self.privateKey = Encryption.load(password, path)
        self.publicKey = self.privateKey.public_key()
        with open(path + 'dht.pickle', 'rb') as handle:
            dht = pickle.load(handle)
        self.DHT._add(dht)

    def get(self, name):
        dht = self.DHT.get_dht()
        for key in dht.keys():
            self.ask(dht[key], name)

    def ask(self, info, name):
        port = info[config.PORT]
        socket = info[config.SOCKET]

