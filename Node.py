import bisect
import os.path

import config
from dht import DHT
from FileHandler import FileHandler
from Peer import Peer, delete_file
from encryption import Encryption
import pickle


def find_index(names, target):
    index = bisect.bisect_left(names, target)
    if index < len(names) and names[index] == target:
        return index
    return -1



class Node(Peer):
    NUMBER_TRIES_UPLOAD = 4 #number of tries to upload from peer, after which if still not working continue to next
    SAFETY_CONSTANT = 1.1

    def __init__(self, port, peer_id, host='127.0.0.1', private_key=None, path = ""):
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
        self.DHT.add_DHT(dht)
        with open(path + 'listfiles.pickle', 'rb') as handle:
            listfiles = pickle.load(handle)
        self.spacePIR.listfiles = listfiles

    def listfiles(self):
        return self.spacePIR.listfiles()

    def download(self, name, n, k):
        """
        get the name
        :param name:
        :return:
        """
        dht = self.DHT.get_dht()
        part_files = []
        for key in dht.keys():
            if len(part_files) >= k*Node.SAFETY_CONSTANT:
                # if we reached a number of files that is enough to construct the files
                return self.fileHandler.combine(part_files,n,k,self.path+name)
            info = dht[key]
            port = info[config.PORT]
            host = info[config.HOST]
            file_name = self.download_from_client(name, port,len(part_files), host)
            if file_name is not None:
                part_files.append(file_name)
        #if we failed delete everything
        for file in part_files:
            delete_file(file)
        return False


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
        dht = self.DHT.get_dht()
        if(len(dht)<n*Node.SAFETY_CONSTANT):
            raise ValueError(config.DHT_SMALL)
        i = 0
        for node in dht:
            if self.upload_to_client(subfiles[i], node[config.PORT]):
                i+=1
            if i >= n:
                # if we ended up sending all the subfiles.
                return True
        return False


    def upload_to_client(self, file, port, host="127.0.0.1"):
        """
        Upload the file to one client.
        """
        try:
            sock = self.connect(host, port)
            self.send_message(config.REQUEST_UPLOAD, sock)

            # Wait for approval
            uploaded = self.is_uploaded_approved(sock)
            i = 0
            while uploaded == -1 and i < Node.NUMBER_TRIES_UPLOAD:
                # Didn't get an approval or denial, try again
                uploaded = self.is_uploaded_approved(sock)
                i += 1

            if uploaded == 0 or uploaded == -1:
                sock.close()
                return False

            # Send the file
            self.send_file(file, sock)

            # Wait for success confirmation
            for i in range(Node.NUMBER_TRIES_UPLOAD):
                success = self.is_uploaded_success(sock)
                if success == 1:
                    sock.close()
                    return True
                elif success == 0 and i < Node.NUMBER_TRIES_UPLOAD - 1:
                    # Resend the file
                    self.send_file(file, sock)
                else:
                    break
            sock.close()
            return False
        except Exception as e:
            print(f"Error uploading to client: {e}")
            return False

    def download_from_client(self,name, port,number,host="127.0.0.1"):
        sock = self.connect(host,port)
        self.send(config.REQUEST_FILE, sock)
        list = self.recieve_obj(sock)# recieve list of all the file names
        i = find_index(list, name)
        n = len(list)
        v = self.construct_vector(i,n)
        self.send(v,sock)
        obj = self.recieve_obj(sock)
        if i == -1:
            #if we don't have the file in this peer DB we want to still do the same actions to peer but return False
            return None
        decrypted_file = self.privateKey.decrypt(obj)
        filename = self.path+name+str(number)
        with open(filename, 'wb') as handle:
            handle.write(decrypted_file)
        return filename

    def construct_vector(self, i, n):
        """
        Constructs and encrypts a vector of length n with a 1 at index i and 0 elsewhere.

        :param i: Index where the value should be 1
        :param n: Length of the vector
        :return: Encrypted vector
        """
        # Step 1: Create the vector of length n with 0s, set 1 at index i
        vector = [0] * n
        if 0 <= i < n:
            vector[i] = 1

        # Step 2: Encrypt each element in the vector using the node's public key
        encrypted_vector = [self.publicKey.encrypt(value) for value in vector]

        return encrypted_vector



