import unittest
import threading
import os
import config
from Node import Node
from time import sleep


class TestNodeMessaging(unittest.TestCase):

    def setUp(self):
        # Setup nodes with different ports and IDs
        self.node1 = Node(5001, peer_id=1)
        self.node2 = Node(5002, peer_id=2)
        self.node3 = Node(5003, peer_id=3)


        # Create a DHT with references to both nodes
        self.node1.add_DHT({3: {config.PORT: 5003, config.HOST: '127.0.0.1'},
                            2: {config.PORT: 5002, config.HOST: '127.0.0.1'}})
        self.node2.add_DHT({1: {config.PORT: 5001, config.HOST: '127.0.0.1'},
                            3: {config.PORT: 5003, config.HOST: '127.0.0.1'}})
        self.node3.add_DHT({1: {config.PORT: 5001, config.HOST: '127.0.0.1'},
                            2: {config.PORT: 5002, config.HOST: '127.0.0.1'}})

        # Start a simple server on each node to listen for incoming messages
        print("Starting node listeners...")
        threading.Thread(target=self.node1.start_listening, daemon=True).start()
        threading.Thread(target=self.node2.start_listening, daemon=True).start()
        threading.Thread(target=self.node3.start_listening, daemon=True).start()

        # Allow more time for the servers to start
        sleep(3)  # Increase this value if nodes take longer to initialize
        print("Nodes are set up and listening.")

        # Send a simple message to verify the connection
        sock = self.node1.connect('127.0.0.1', 5002)
        print("Sending test message from Node1 to Node2...")
        self.node1.send_message("Hello from Node1", sock)
        response = sock.recv(1024).decode().strip()
        print(f"Node2 received: {response}")
        sock.close()

    def test_message_exchange(self):
        """
        Simple test to verify communication between nodes.
        """
        print("Testing basic message exchange...")

        # Connect to Node2 from Node1
        sock = self.node1.connect('127.0.0.1', 5002)
        print("Sending message from Node1 to Node2...")
        test_message = "Hello from Node1"
        self.node1.send_message(test_message, sock)
        # Receive the echoed message on Node1
        try:
            response = sock.recv(1024).decode().strip()
            while response == "":
                self.node1.send_message(test_message, sock)
                response = sock.recv(1024).decode().strip()
            print(f"Node1 received: {response}")
        except Exception as e:
            print(f"Error receiving message: {e}")
            response = ""

        # Check if the response matches the sent message
        self.assertEqual(response, test_message, f"Expected '{test_message}', but got '{response}'")

        # Close the socket
        sock.close()

    def test_send_recieve(self):
        test_message = b"Hello from Node1, testing recieving function Nodes"
        sock = self.node1.connect('127.0.0.1', 5002)
        self.node1.send_message(test_message, sock)
        try:
            response = self.node2.receive_obj(sock)
            while response == "":
                self.node1.send_message(config.REQUEST_FILE, sock)
                response = self.node2.receive_obj(sock)
            print(f"Node2 received: {response}")
        except Exception as e:
            print(f"Error receiving message: {e}")
            response = ""

        # Check if the response matches the sent message
        self.assertEqual(response, test_message, f"Expected '{test_message}', but got '{response}'")

        # Close the socket
        sock.close()


    def test_upload_download(self):
        # Test uploading a file from node1 to node2
        file_path = "testfile.txt"
        print(file_path)
        with open(file_path, "w") as f:
            f.write("This is a test file.")

        # Upload the file from node1 to node2
        result, _ = self.node1.upload(file_path)
        print(result)
        self.assertTrue(result != 0, "File upload failed")

        # Attempt to download the file back from node2
        download_success = self.node1.download("testfile.txt", 2, 1)
        self.assertTrue(download_success, "File download failed")

        # Cleanup created test file
        if os.path.exists(file_path):
            os.remove(file_path)

    def tearDown(self):
        # Clean up resources or shutdown any running server threads
        self.node1.stop()
        self.node2.stop()

    def test_upload_download_large_file(self):
        """
        Test uploading and downloading a large file (1 MB) between nodes.
        """
        file_path = "large_testfile_1mb.txt"
        print(file_path)

        # Create a 1 MB test file
        with open(file_path, "wb") as f:
            f.write(os.urandom(1024 * 1024))  # 1 MB of random data

        # Upload the file from node1 to node2
        result, _ = self.node1.upload(file_path)
        print(result)
        self.assertTrue(result != 0, "Large file upload failed")

        # Attempt to download the file back from node2
        download_success = self.node1.download("large_testfile_1mb.txt", 2, 1)
        self.assertTrue(download_success, "Large file download failed")

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_multiple_peers(self):
        """
        Test setup with more than 10 peers for communication and upload/download.
        """
        num_peers = 12
        peers = [Node(5000 + i, peer_id=i) for i in range(1, num_peers + 1)]

        # Start listening on all peers
        for peer in peers:
            threading.Thread(target=peer.start_listening, daemon=True).start()

        sleep(3)  # Ensure all peers are listening

        # Perform a simple message exchange between node1 and each other node
        for i, peer in enumerate(peers[1:], start=2):  # Skip node1 (already initialized)
            sock = self.node1.connect('127.0.0.1', 5000 + i)
            test_message = f"Hello from Node1 to Node {i}"
            self.node1.send_message(test_message.encode(), sock)
            response = sock.recv(1024).decode().strip()
            self.assertEqual(response, test_message, f"Message exchange with Node {i} failed")
            sock.close()

    def test_multiple_peers_with_large_file(self):
        """
        Test upload and download of a large file (1 MB) with multiple peers (more than 10).
        """
        num_peers = 12
        peers = [Node(5000 + i, peer_id=i) for i in range(1, num_peers + 1)]

        # Start listening on all peers
        for peer in peers:
            threading.Thread(target=peer.start_listening, daemon=True).start()

        sleep(3)  # Ensure all peers are listening

        # Create and upload a 1 MB file
        file_path = "large_testfile_1mb_multi_peer.txt"
        with open(file_path, "wb") as f:
            f.write(os.urandom(1024 * 1024))  # 1 MB of random data

        # Upload the file from node1 to a random peer
        local_host = '127.0.0.1'
        for peer in peers:
            self.node1.add_node_to_DHT(peer.port,peer.peer_id, local_host)
        result, _ = self.node1.upload(file_path)
        self.assertTrue(result != 0, "File upload failed in multi-peer test")

        # Download the file from another random peer
        download_success = self.node1.download("large_testfile_1mb_multi_peer.txt", 2, 1)
        self.assertTrue(download_success, "File download failed in multi-peer test")

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_upload_download_very_large_file(self):
        """
        Test uploading and downloading a very large file (>3 MB).
        """
        file_path = "very_large_testfile.txt"
        print(file_path)

        # Create a 3 MB test file
        with open(file_path, "wb") as f:
            f.write(os.urandom(3 * 1024 * 1024))  # 3 MB of random data

        # Upload the file from node1 to node2
        result, _ = self.node1.upload(file_path)
        self.assertTrue(result != 0, "Very large file upload failed")

        # Attempt to download the file back from node2
        download_success = self.node1.download("very_large_testfile.txt", 2, 1)
        self.assertTrue(download_success, "Very large file download failed")

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)


if __name__ == '__main__':
    unittest.main()
