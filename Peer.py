import os
import socket
import struct
import threading
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
    master class that is responsible for all communication related tasks
    """

    def __init__(self, peer_id, host='127.0.0.1', port=5000):
        """
        initiate the Peer class
        :param peer_id: id for the peer
        :param host: host of the peer(IP)
        :param port: the port of the peer to listen to
        """
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
        send the file
        :param file_obj: path to the file
        :param sock: target port
        :return: nothing
        """
        try:

            # Send file content in chunks
            with file_obj as f:
                while True:
                    chunk = f.read(config.BUFFER_SIZE)
                    if not chunk:
                        break
                    sock.sendall(chunk)

        except Exception as e:
            print(f"Error sending file: {e}")
        finally:
            sock.close()

    def is_uploaded_approved(self, sock):
        """
        recieve a message for uploaded success
        :param sock: the sock of the client
        :return: true if the message was approved, false if client denied, raise error if didnt get any message
        """
        # establish a socket with the port
        suc = sock.recv(struct.calcsize('256sQ'))
        if suc == config.UPLOAD_APPROVED:
            return 1
        if suc == config.UPLOADED_DENIED:
            return 0
        else:
            return -1

    def is_uploaded_success(self, sock):
        """
        recieve a message for uploaded success
        :param sock: the sock of the client
        :return: true if the message was approved, false if client denied, raise error if didnt get any message
        """
        # establish a socket with the port
        suc = sock.recv(struct.calcsize('256sQ'))
        if suc == config.UPLOADED_SUCCESS:
            return 1
        if suc == config.UPLOADED_FAILED:
            return 0
        else:
            return -1

    def receive_file(self, client_sock):
        """
        recieve a file
        :param client_sock: client socket object
        :return: nothing
        """
        try:
            # Read file metadata
            file_name = client_sock.recv(struct.calcsize('256sQ'))
            file_name = file_name.decode().strip('\x00')
            # file_name = f"{self.peer_id}_received_{file_name}"
            total_received = 0

            with open(file_name, 'wb') as f:
                while total_received < config.SUBFILE_SIZE:
                    chunk = client_sock.recv(config.BUFFER_SIZE)
                    if not chunk:
                        print("file is smaller than 1MB")
                        break
                    f.write(chunk)
                    total_received += len(chunk)
            client_sock.close()
            return file_name, total_received

        except Exception as e:
            print(f"Error receiving file: {e}")
            client_sock.close()
            return None, None

    def recieve_obj(self, sock):
        """
        recieve an object. as opposed to recieve_file, stored in RAM
        :param sock: the sock to recieve from
        :return: file
        """
        total_received = 0
        file = ""
        while total_received < config.SUBFILE_SIZE:
            chunk = sock.recv(config.BUFFER_SIZE)
            if not chunk:
                print("file is smaller than 1MB")
                break
            file += chunk
            total_received += len(chunk)
        return file

    def start_listening(self):
        """
        start a listener thread
        :return: nothing
        """
        # Start the listener thread without creating a socket here
        self._listener_thread = threading.Thread(target=self._listen_for_connections)
        self._listener_thread.start()

    def _listen_for_connections(self):
        """
        a function for the listener thread representing a listener
        :return: nothing
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(5)
            print(f"Peer {self.peer_id} listening on {self.host}:{self.port}...")
            while not self._stop_event.is_set():
                s.settimeout(1)
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=self.handle_peer, args=(conn,)).start()
                except socket.timeout:
                    continue
            print(f"Peer {self.peer_id} stopped listening.")

    def connect(self, host, port):
        """
        a simple function creating a socket to connect us to
        :param host: the host of the peer(IP)
        :param port: the port
        :return: sock
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return sock

    def handle_peer(self, client_sock):
        """
        handle peers (either asks or recieve a file)
        :param client_sock: client socket object
        :return: nothing
        """
        try:
            # First, receive the message type
            message_type = client_sock.recv(10).decode().strip()
            if message_type == config.REQUEST_UPLOAD:
                self.handle_upload_request(client_sock)
            elif message_type == config.REQUEST_FILE:
                self.handle_get_request(client_sock)
            else:
                print(f"Unknown message type: {message_type}")

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_sock.close()

    def handle_upload_request(self, sock):
        """
        handle an upload request and send appropriate messages
        :param sock: the sock
        :return:
        """
        if self.spacePIR.is_allow_upload:
            with self._upload_lock:
                sock.send(config.UPLOAD_APPROVED)
                try:
                    # stop uploading before reaching to recieve file
                    file_name, file = self.receive_file(sock)
                    self.spacePIR.add(file_name, file)
                    self.send(config.UPLOADED_SUCCESS, sock)
                except Exception as e:
                    print(f"Error uploading file: {e}")
                    self.send(config.UPLOADED_FAILED, sock)
        else:
            sock.send(config.UPLOADED_DENIED)

    def handle_get_request(self, sock):
        """
        handle request to send a file to the peer.
        :param sock: the client sock
        :return: nothing
        """
        try:
            # Receive the requested file polynom for the inner product homomorphic function
            list_of_files = self.spacePIR.get_file_names()
            self.send(list_of_files, sock)  # send the list of the file so that the node can create the correct poly
            poly = sock.recv(256).decode().strip('\x00').strip()
            file_obj = self.spacePIR.get(poly)
            self.send(file_obj, sock)
        except Exception as e:
            print(f"Error handling get: {e}")

    def send(self, file_obj, sock):
        """
        send a file through the thread pool
        :param file_obj: path to the file
        :param sock: target port
        :return: nothing
        """
        self.executor.submit(self.send_file, file_obj, sock)

    def stop(self):
        """
        safely stop the listener thread and the senders threadpool
        :return: nothing
        """
        self._stop_event.set()
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join()
        self.executor.shutdown(wait=True)
        print(f"Peer {self.peer_id} stopped.")
