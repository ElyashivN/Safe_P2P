import bisect
import os.path
import random

import config
from dht import DHT
from FileHandler import FileHandler
from spacePIR import SpacePIR
from Peer import Peer
from encryption import Encryption
import pickle
import sympy as sp


def find_index(names, target):
    index = bisect.bisect_left(names, target)
    if index < len(names) and names[index] == target:
        return index
    return -1


def construct_polynomial(target_index, n, target_value):
    """
    Constructs a polynomial P(x) such that:
    P(target_index) = target_value and
    P(j) = 0 for all j in {0, 1, ..., n-1} where j != target_index.

    Parameters:
    - target_index: the index `i` where the polynomial should evaluate to `target_value`.
    - n: total number of indices.
    - target_value: the value `r` that the polynomial should take at `target_index`.

    Returns:
    - The constructed polynomial P(x).
    """
    # Create a symbolic variable x
    x = sp.symbols('x')

    # Construct the Lagrange basis polynomial L_i(x)
    L_i = 1
    for j in range(n):
        if j != target_index:
            L_i *= (x - j) / (target_index - j)

    # Construct P(x) = r * L_i(x)
    P_x = target_value * L_i

    return sp.expand(P_x)


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
        with open(path + 'listfiles.pickle', 'wb') as handle:
            pickle.dump(self.spacePIR.get_file_names(), handle, protocol=pickle.HIGHEST_PROTOCOL)

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
        with open(path + 'listfiles.pickle', 'rb') as handle:
            listfiles = pickle.load(handle)
        self.spacePIR.listfiles = listfiles

    def listfiles(self):
        return self.spacePIR.listfiles()

    def download(self, name):
        """
        get the name
        :param name:
        :return:
        """
        dht = self.DHT.get_dht()
        for key in dht.keys():
            info = dht[key]
            port = info[config.PORT]
            host = info[config.HOST]
            self.download_from_client(name, port, host)

    def add_DHT(self, DHT):
        return self.DHT.add_DHT(DHT)

    def upload(self, file_path):
        """
        upload the file
        :param file_path: file path
        :return:
        """
        k = config.SUBFILE_SIZE
        n = (os.path.getsize(file_path) * 2) / k
        subfiles, original_size, _ = self.fileHandler.divide(file_path,self.peer_id,n,k)
        for i, node in enumerate(self.DHT.get_dht()):
            self.ask_upload(subfiles[i], node[config.PORT])
            #wait then if self.recieve_uploaded_succes(node[config.PORT])) continue else more
            if i >= n:
                # if we ended up sending all the subfiles.
                break


    def upload_to_client(self,file, port,host="127.0.0.1"):
        sock = self.connect(host,port)
        self.send(config.REQUEST_UPLOAD, sock)
        if not self.is_uploaded_approved(sock):
            return False
        self.send(file,sock)
        self.is_uploaded_success(sock)
        return True

    def download_from_client(self,name, port,host="127.0.0.1"):
        sock = self.connect(host,port)
        self.send(config.REQUEST_FILE, sock)
        list = self.recieve_obj(sock)# recieve list of all the file names
        i = find_index(list, name)
        n = len(list)
        rand = random.randint(0, n)
        poly = construct_polynomial(i,n, rand)
        self.send(poly,sock)
        obj = self.recieve_obj(sock)
        self.privateKey.decrypt(obj)


