import os
import pickle
from phe import PaillierPublicKey
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import config
from spacePIR import SpacePIR
def delete_file(file_path):
    """
    Delete the file at the given path.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File '{file_path}' deleted successfully.")
        else:
            print(f"File '{file_path}' does not exist.")
    except Exception as e:
        print(f"Error deleting file: {e}")
class Peer:
    """
    Master class responsible for all communication-related tasks.
    """
    def __init__(self, peer_id, host='127.0.0.1', port=5000):
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self._stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._listener_thread = None
        self.spacePIR = SpacePIR()
        self._upload_lock = threading.Lock()  # Specific lock for SpacePIR uploads to prevent concurrent uploads



    def send_file(self, file_obj, sock):
        """
        Send the file over the socket.
        """
        try:
            # Send file content in chunks
            print("file sending...")
            with open(file_obj, 'rb') as f:
                print("file opened")
                while True:
                    chunk = f.read(config.BUFFER_SIZE)
                    if not chunk:
                        break
                    print(chunk)
                    sock.sendall(chunk)
                print("file sent successfully.")
        except Exception as e:
            print(f"Error sending file: {e}")


    def send_message(self, message, sock):
        """
        Send a simple message over the socket.
        """
        try:
            if isinstance(message, str):
                message = message.encode('UTF-8')
            sock.sendall(message)
        except Exception as e:
            print(f"Error sending message: {e}")

    def is_uploaded_approved(self, sock):
        """
        Receive a message for upload approval.
        """
        try:
            # Receive the message
            message = sock.recv(1024).strip()
            if message == config.UPLOAD_APPROVED:
                return 1
            elif message == config.UPLOAD_DENIED:
                return 0
            else:
                return -1
        except Exception as e:
            print(f"Error in is_uploaded_approved: {e}")
            return -1

    def is_uploaded_success(self, sock):
        """
        Receive a message for upload success.
        """
        try:
            # Receive the message
            message = sock.recv(1024)
            message = message.strip()
            print(message)
            if message == config.UPLOADED_SUCCESS:
                return 1
            elif message == config.UPLOADED_FAILED:
                return 0
            else:
                return -1
        except Exception as e:
            print(f"Error in is_uploaded_success: {e}")
            return -1

    def receive_file(self, client_sock):
        """
        Receive a file from the client socket.
        """
        try:
            # Read file metadata
            # file_name_size = struct.unpack('I', client_sock.recv(4))[0]
            data = client_sock.recv(256)
            # with open(file_name, 'wb') as f:
            #     f.write(data.encode())
            # total_received = 0
            # with open(file_name, 'wb') as f:
            #     while True:
            #         chunk = client_sock.recv(config.BUFFER_SIZE)
            #         if not chunk:
            #             break
            #         f.write(chunk)
            #         total_received += len(chunk)
            return data

        except Exception as e:
            print(f"Error receiving file: {e}")
            return None

    def receive_obj(self, sock):
        """
        Receive an object stored in RAM.
        """
        try:
            data = b''
            sock.settimeout(10)
            while data == b'':
                chunk = sock.recv(config.BUFFER_SIZE)
                if not chunk:
                    continue
                data += chunk
            return data
        except socket.timeout:
            print("didnt recieve any object")
            return None
        except Exception as e:
            print(f"Error receiving object: {e}")
            return None

    def start_listening(self):
        """
        Start a listener thread.
        """
        self._listener_thread = threading.Thread(target=self._listen_for_connections)
        self._listener_thread.start()

    def _listen_for_connections(self):
        """
        Listener thread function representing a listener.
        """
        print(f"Peer {self.peer_id} entering listener function...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(5)
            print(f"Peer {self.peer_id} listening on {self.host}:{self.port}...")

            while not self._stop_event.is_set():
                s.settimeout(10)  # Set a small timeout to allow regular checking
                try:
                    print(f"Peer {self.peer_id} waiting for connections...")
                    conn, addr = s.accept()  # Accept a new connection
                    print(f"Peer {self.peer_id} accepted connection from {addr}")
                    threading.Thread(target=self.handle_peer, args=(conn,)).start()
                except socket.timeout:
                    # Timeout indicates no incoming connections; continue listening
                    print("socket timeout")
                    continue
                except Exception as e:
                    print(f"Error in listener for Peer {self.peer_id}: {e}")
                    break
            print(f"Peer {self.peer_id} stopped listening.")

    def connect(self, host, port):
        """
        Create a socket connection to the given host and port.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return sock

    def handle_peer(self, sock):
        """
        Handle incoming connections from peers.
        """
        try:
            # First, receive the message type
            message_type = sock.recv(1024).strip()
            if message_type == config.REQUEST_UPLOAD or message_type == "request_upload":
                print("Upload has been requested from node ",str(self.peer_id),"by port ",str(sock.getpeername()[1]))
                self.handle_upload_request(sock)
            elif message_type == config.REQUEST_FILE:
                print("download has been requested from node ",str(self.peer_id),"by port ",str(sock.getpeername()[1]))
                self.handle_get_request(sock)
            elif message_type == "":
                print(f"Error in handle_peer: for some reason is empty ")
            else:
                self.send_message(message_type,sock)
                print(f"Unknown message type: {message_type}")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            time.sleep(5)
            print(f"Peer {self.peer_id} stopped listening.")
            if sock.fileno() != -1:  # Check if socket is still open
                sock.close()

    def handle_upload_request(self, sock):
        print("handle upload request debug")  # This prints, so we know we reach here

        print("Attempting to acquire upload lock...")  # Add this print
        with self._upload_lock:
            print("Lock acquired")  # Add this print to check if we acquire the lock

            print(f"spacePIR.is_allow_upload: {self.spacePIR.is_allow_upload}")  # This prints True
            if self.spacePIR.is_allow_upload:
                print("uploading debug")  # This is what we expect but are not seeing
                self.send_message(config.UPLOAD_APPROVED, sock)
                print("message has been sent debug")
                try:
                    print("going to try to recieve debug")
                    time.sleep(2) #wait a bit before recieving
                    print("checking")
                    data = self.receive_file(sock)
                    # file_name = f"{file_name}_rport_{sock.getpeername()[1]}"
                    if self.spacePIR.add(data):
                        print("file has been added to spacePIR")
                        print("list of files in spacePIR is ",self.spacePIR.get_file_names(), " on peer ",self.peer_id)
                        self.send_message(config.UPLOADED_SUCCESS, sock)
                    else:
                        self.send_message(config.UPLOADED_FAILED, sock)
                except Exception as e:
                    print(f"Error uploading file: {e}")
                    self.send_message(config.UPLOADED_FAILED, sock)
            else:
                print("npooooooooo sdebug")  # This should print if upload is denied
                self.send_message(config.UPLOAD_DENIED, sock)
    def construct_list_from_string(self, list_bin):
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
            file_list = decoded_str.split('\n')# todo what if \n in one of the numbers encypted to us


            # Filter out any empty strings that might result from trailing newlines
            file_list = [file_name for file_name in file_list if file_name]

            return file_list
        except Exception as e:
            print(f"Error constructing list from bytes: {e}")
            return []

    def construct_list_from_bytes(self, list_bin):
        """
        construct a list from bytes. each element is exactly Pailier_keysize in bytes/2,
         and the last element is the Public Key n
        :param list_bin: list in binary format
        :return: the list elements and the public key it sends
        """
        vector = []
        i = 0
        while i < len(list_bin)-config.KEY_SIZE:
            vector.append(list_bin[i:i+config.PAILIER_KEY_SIZE//4])
            i += config.PAILIER_KEY_SIZE//4
        n_reconstructed = int.from_bytes(list_bin[i:],byteorder="big")
        reconstructed_public_key = PaillierPublicKey(n=n_reconstructed)
        return vector, reconstructed_public_key


    def handle_get_request(self, sock):
        """
        Handle request to send a file to the peer.
        """
        try:
            # Send the list of file names
            list_of_files = self.spacePIR.get_file_names()
            self.send_message('\n'.join(list_of_files), sock)

            # Receive the vector
            time.sleep(2)
            vector = self.receive_obj(sock)
            vector, public_key = self.construct_list_from_bytes(vector)
            # Process the data and prepare the response (omitted for brevity)
            response_vector = self.spacePIR.get(vector, public_key)

            # Send the response
            for chunk in response_vector:
                self.send_message(chunk, sock) #todo check for using send file
            print(f'response for download has been sent from node {self.peer_id} to peer {sock.getpeername()[1]}')
            # For simplicity, assuming response_file is prepared
        except Exception as e:
            print(f"Error handling get request: {e}")

    def stop(self):
        """
        Safely stop the listener thread and the senders thread pool.
        """
        self._stop_event.set()
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join()
        self.executor.shutdown(wait=True)
        print(f"Peer {self.peer_id} stopped.")
