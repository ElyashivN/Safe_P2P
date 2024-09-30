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
            with open(file_obj, 'rb') as f:
                while True:
                    chunk = f.read(config.BUFFER_SIZE)
                    if not chunk:
                        break
                    sock.sendall(chunk)
        except Exception as e:
            print(f"Error sending file: {e}")
        # finally:
        #     sock.close()

    def send_message(self, message, sock):
        """
        Send a simple message over the socket.
        """
        try:
            if isinstance(message, str):
                message = message.encode()
            sock.sendall(message)
        except Exception as e:
            print(f"Error sending message: {e}")

    def is_uploaded_approved(self, sock):
        """
        Receive a message for upload approval.
        """
        try:
            # Receive the message
            message = sock.recv(1024).decode().strip()
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
            message = message.decode().strip()
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
            file_name_size = struct.unpack('I', client_sock.recv(4))[0]
            file_name = client_sock.recv(file_name_size).decode()

            total_received = 0
            with open(file_name, 'wb') as f:
                while True:
                    chunk = client_sock.recv(config.BUFFER_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    total_received += len(chunk)
            return file_name, total_received
        except Exception as e:
            print(f"Error receiving file: {e}")
            return None, None
        finally:
            client_sock.close()

    def receive_obj(self, sock):
        """
        Receive an object stored in RAM.
        """
        try:
            data = b''
            while True:
                chunk = sock.recv(config.BUFFER_SIZE)
                if not chunk:
                    break
                data += chunk
            return data
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
        Create a socket connection to the given host and port.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return sock

    def handle_peer(self, client_sock):
        """
        Handle incoming connections from peers.
        """
        try:
            # First, receive the message type
            message_type = client_sock.recv(1024).decode().strip()
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
        Handle an upload request and send appropriate messages.
        """
        if self.spacePIR.is_allow_upload:
            with self._upload_lock:
                self.send_message(config.UPLOAD_APPROVED, sock)
                try:
                    file_name, _ = self.receive_file(sock)
                    if file_name:
                        self.spacePIR.add(file_name)
                        self.send_message(config.UPLOADED_SUCCESS, sock)
                    else:
                        self.send_message(config.UPLOADED_FAILED, sock)
                except Exception as e:
                    print(f"Error uploading file: {e}")
                    self.send_message(config.UPLOADED_FAILED, sock)
        else:
            self.send_message(config.UPLOAD_DENIED, sock)

    def handle_get_request(self, sock):
        """
        Handle request to send a file to the peer.
        """
        try:
            # Send the list of file names
            list_of_files = self.spacePIR.get_file_names()
            self.send_message('\n'.join(list_of_files), sock)

            # Receive the polynomial (or vector)
            data = self.receive_obj(sock)
            # Process the data and prepare the response (omitted for brevity)

            # Send the response
            # self.send_file(response_file, sock)
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
