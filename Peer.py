import os
import socket
import struct
import threading
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

# Constants for the peer-to-peer system
BUFFER_SIZE = 1024

def delete_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File '{file_path}' deleted successfully.")
        else:
            print(f"File '{file_path}' does not exist.")
    except Exception as e:
        print(f"Error deleting file: {e}")

class Peer:
    def __init__(self, peer_id, host='127.0.0.1', port=5000):
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self._stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._listener_thread = None

    def send_file(self, file_path, target_port):
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, target_port))

            # Send file metadata
            sock.sendall(struct.pack('256sQ', file_name.encode(), file_size))

            # Send file content in chunks
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    sock.sendall(chunk)

        except Exception as e:
            print(f"Error sending file: {e}")
        finally:
            sock.close()

    def receive_file(self, client_sock):
        try:
            packed_file_info = client_sock.recv(struct.calcsize('256sQ'))
            file_name, file_size = struct.unpack('256sQ', packed_file_info)
            file_name = file_name.decode().strip('\x00')
            file_name = f"{self.peer_id}_received_{file_name}"
            with open(file_name, 'wb') as f:
                total_received = 0
                while total_received < file_size:
                    chunk = client_sock.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    total_received += len(chunk)

            if total_received != file_size:
                print(f"Warning: File size mismatch for '{file_name}'")

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
        # Start the listener thread without creating a socket here
        self._listener_thread = threading.Thread(target=self._listen_for_connections)
        self._listener_thread.start()

    def _listen_for_connections(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(5)
            print(f"Peer {self.peer_id} listening on {self.host}:{self.port}...")
            while not self._stop_event.is_set():
                s.settimeout(1)
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=self.receive_file, args=(conn,)).start()
                except socket.timeout:
                    continue
            print(f"Peer {self.peer_id} stopped listening.")

    def send(self, file_path, target_port):
        self.executor.submit(self.send_file, file_path, target_port)

    def stop(self):
        self._stop_event.set()
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join()
        self.executor.shutdown(wait=True)
        print(f"Peer {self.peer_id} stopped.")
