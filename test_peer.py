import struct
import unittest
import os
import time
import threading
import socket
from Peer import Peer, delete_file

BUFFER_SIZE = 528

def generate_random_file(file_path, size_mb):
    with open(file_path, 'wb') as f:
        f.write(os.urandom(size_mb * 1024 * 1024))  # Write random bytes

class TestPeerFileTransfer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_file_1 = "test_file_1"
        cls.test_file_2 = "test_file_2"
        cls.large_test_file = "large_test_file"
        generate_random_file(cls.test_file_1, 1)  # 1 MB
        generate_random_file(cls.test_file_2, 2)  # 2 MB
        generate_random_file(cls.large_test_file, 10)  # 10 MB

    @classmethod
    def tearDownClass(cls):
        # Stop any running peers
        try:
            cls.peer1.stop()
        except AttributeError:
            pass
        try:
            cls.peer2.stop()
        except AttributeError:
            pass
        # Ensure files are not locked before attempting to remove
        time.sleep(1)
        for file in [cls.test_file_1, cls.test_file_2, cls.large_test_file]:
            if os.path.exists(file):
                os.remove(file)

    def setUp(self):
        # Recreate test files if necessary
        if not os.path.exists(self.test_file_1):
            generate_random_file(self.test_file_1, 1)  # 1 MB
        if not os.path.exists(self.test_file_2):
            generate_random_file(self.test_file_2, 2)  # 2 MB
        if not os.path.exists(self.large_test_file):
            generate_random_file(self.large_test_file, 10)  # 10 MB

    def run_peer(self, peer_id, port):
        peer = Peer(peer_id=peer_id, port=port)
        peer.start_listening()  # Ensure this starts the listener thread
        time.sleep(1)  # Ensure peer is ready
        return peer

    def test_single_transfer(self):
        received_file = f"2_received_{self.test_file_1}"
        try:
            # Ensure 'test_file_1' exists
            if not os.path.exists(self.test_file_1):
                generate_random_file(self.test_file_1, 1)  # 1 MB

            self.peer1 = self.run_peer(1, 5000)
            self.peer2 = self.run_peer(2, 5001)
            self.peer1.send(self.test_file_1, 5001)
            time.sleep(2)  # Wait for transfer to complete

            # Verify the file was received
            self.assertTrue(os.path.exists(received_file), f"{received_file} should exist after transfer")
        finally:
            # Cleanup peers and received file
            self.peer1.stop()
            self.peer2.stop()
            if os.path.exists(received_file):
                os.remove(received_file)

    def test_simultaneous_transfers(self):
        self.peer1 = self.run_peer(1, 5000)
        self.peer2 = self.run_peer(2, 5001)

        def run_peer_test(peer_id, port, target_port, file_to_send, times=1):
            peer = Peer(peer_id=peer_id, port=port)
            peer.start_listening()
            time.sleep(1)  # Ensure peer is ready
            for _ in range(times):
                peer.send(file_to_send, target_port)
            peer.stop()

        threads = []
        for _ in range(5):
            t = threading.Thread(target=run_peer_test, args=(1, 5000, 5001, self.test_file_1, 10))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        # Verify file was received multiple times
        received_file = f"2_received_{self.test_file_1}"
        self.assertTrue(os.path.exists(received_file), f"{received_file} should exist after transfer")
        self.peer1.stop()
        self.peer2.stop()
        if os.path.exists(received_file):
            os.remove(received_file)

    def test_large_file_transfer(self):
        self.peer1 = self.run_peer(1, 5000)
        self.peer2 = self.run_peer(2, 5001)
        self.peer1.send(self.large_test_file, 5001)
        time.sleep(10)  # Wait for transfer to complete

        # Verify the large file was received
        received_file = f"2_received_{self.large_test_file}"
        self.assertTrue(os.path.exists(received_file), f"{received_file} should exist after transfer")

        # Cleanup peers and received file
        self.peer1.stop()
        self.peer2.stop()
        if os.path.exists(received_file):
            os.remove(received_file)

    def test_end_cases(self):
        try:
            self.peer1 = self.run_peer(1, 5000)
            self.peer2 = self.run_peer(2, 5001)

            # Test interrupted transfer
            def interrupted_transfer():
                self.peer1.send(self.test_file_1, 5001)
                time.sleep(1)  # Interrupt the transfer by deleting the file
                delete_file(self.test_file_1)

            t = threading.Thread(target=interrupted_transfer)
            t.start()
            t.join()

            # Ensure file was deleted
            self.assertFalse(os.path.exists(self.test_file_1), f"File '{self.test_file_1}' should be deleted.")

            # Ensure file was deleted
            self.assertFalse(os.path.exists(self.test_file_1), f"File '{self.test_file_1}' should be deleted.")
        finally:
            # Recreate 'test_file_1' for other tests
            if not os.path.exists(self.test_file_1):
                generate_random_file(self.test_file_1, 1)  # 1 MB

            # Cleanup peers
            self.peer1.stop()
            self.peer2.stop()

    def test_corrupted_receive(self):
        try:
            # Ensure 'test_file_1' exists
            if not os.path.exists(self.test_file_1):
                generate_random_file(self.test_file_1, 1)  # 1 MB

            self.peer1 = self.run_peer(1, 5000)
            self.peer2 = self.run_peer(2, 5001)

            # Test receiving a corrupted file
            def corrupted_receive(peer, file_path):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((peer.host, peer.port))
                    file_size = os.path.getsize(file_path)
                    sock.sendall(struct.pack('256sQ', file_path.encode(), file_size))
                    with open(file_path, 'rb') as f:
                        chunk = f.read(BUFFER_SIZE // 2)  # Send only part of the file
                        sock.sendall(chunk)
                    sock.close()
                except Exception as e:
                    self.fail(f"Error in corrupted receive test: {e}")

            corrupted_receive(self.peer2, self.test_file_1)
            time.sleep(2)

            # Clean up received file
            received_file = f"{self.peer2.peer_id}_received_{self.test_file_1}"
            if os.path.exists(received_file):
                os.remove(received_file)
        finally:
            # Cleanup peers
            self.peer1.stop()
            self.peer2.stop()


if __name__ == "__main__":
    unittest.main()
