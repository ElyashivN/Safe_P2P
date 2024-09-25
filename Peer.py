import os
import socket
import struct
import threading
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

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
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self._stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._listener_thread = None
        self.spacePIR = SpacePIR()
    def send_file(self, file_path, target_port):
        """
        send the file
        :param file_path: path to the file
        :param target_port: target port
        :return: nothing
        """
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, target_port))

            # Send message type
            sock.sendall('SEND_FILE'.ljust(10).encode())

            # Send file metadata
            sock.sendall(struct.pack('256sQ', file_name.encode(), file_size))

            # Send file content in chunks
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(config.BUFFER_SIZE)
                    if not chunk:
                        break
                    sock.sendall(chunk)

            print(f"File '{file_name}' sent to peer on port {target_port}.")

        except Exception as e:
            print(f"Error sending file: {e}")
        finally:
            sock.close()

    def receive_file(self, client_sock):
        """
        recieve a file
        :param client_sock: client socket object
        :return: nothing
        """
        try:
            # Read file metadata
            packed_file_info = client_sock.recv(struct.calcsize('256sQ'))
            file_name, file_size = struct.unpack('256sQ', packed_file_info)
            file_name = file_name.decode().strip('\x00')
            file_name = f"{self.peer_id}_received_{file_name}"
            self.spacePIR.add_subfile(file_name, file_size)
            total_received = 0

            with open(file_name, 'wb') as f:
                while total_received < file_size:
                    chunk = client_sock.recv(config.BUFFER_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    total_received += len(chunk)

            if total_received != file_size:
                print(f"Warning: File size mismatch for '{file_name}'")

            print(f"File '{file_name}' received successfully.")

            # For debug purposes (optional)
            if file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                try:
                    image = Image.open(file_name)
                    image.show()
                except Exception as e:
                    print(f"Error opening image file: {e}")

        except Exception as e:
            print(f"Error receiving file: {e}")
        finally:
            client_sock.close()

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
                    threading.Thread(target=self.handle_client, args=(conn,)).start()
                except socket.timeout:
                    continue
            print(f"Peer {self.peer_id} stopped listening.")

    def handle_client(self, client_sock):
        """
        handle clients (either asks or recieve a file)
        :param client_sock: client socket object
        :return: nothing
        """
        try:
            # First, receive the message type
            message_type = client_sock.recv(10).decode().strip()

            if message_type == config.REQUEST_UPLOAD:
                if self.spacePIR.allow_upload:
                    self.receive_file(client_sock)
                    client_sock.send(config.UPLOADED_SUCCESS)
                else:
                    client_sock.send(config.ERROR_UPLOAD)

            elif message_type == config.REQUEST_FILE:
                self.handle_request(client_sock)
            else:
                print(f"Unknown message type: {message_type}")
                client_sock.close()
        except Exception as e:
            print(f"Error handling client: {e}")
            client_sock.close()

    # def handle_upload(self, client_sock):
    #     if self.spacePIR.allow_upload:
    #         self.receive_file(client_sock)

    def handle_request(self, client_sock):
        """
        handle request to send a file to the peer.
        :param client_sock: the client sock
        :return: nothing
        """
        try:
            # Receive the requested file name
            requested_file_name = client_sock.recv(256).decode().strip('\x00').strip()
            # Retrieve the file using SpacePIR
            file_obj, file_size = self.spacePIR.get(requested_file_name)
            client_sock.sendall(config.SEND_FILE.ljust(10).encode())

            # Send file metadata
            file_name = os.path.basename(requested_file_name)
            client_sock.sendall(struct.pack('256sQ', file_name.encode(), file_size))

            # Send file content
            with file_obj as f:
                while True:
                    chunk = f.read(config.BUFFER_SIZE)
                    if not chunk:
                        break
                    client_sock.sendall(chunk)
            print(f"File sent in response to request.")
        except Exception as e:
            print(f"Error handling file request: {e}")
        finally:
            client_sock.close()
    def send(self, file_path, target_port):
        """
        send a file through the thread pool
        :param file_path: path to the file
        :param target_port: target port
        :return: nothing
        """
        self.executor.submit(self.send_file, file_path, target_port)

    def ask_download(self, file_name, target_port):
        """
        ask for a filename and target port
        :param file_name: the file name
        :param target_port: the target port
        :return:nothing
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, target_port))

            # Send message type
            sock.sendall(config.REQUEST_FILE.ljust(10).encode())

            # Send the requested file name
            sock.sendall(file_name.ljust(256).encode())

        except Exception as e:
            print(f"Error requesting file: {e}")
            sock.close()
    def ask_upload(self, file_name, target_port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, target_port))

            # Send message type
            sock.sendall(config.REQUEST_UPLOAD.ljust(10).encode())

            # Send the requested file name
            sock.sendall(file_name.ljust(256).encode())

        except Exception as e:
            print(f"Error requesting file: {e}")
            sock.close()

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
