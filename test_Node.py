import json
import pickle
import socket
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

        # Create a DHT with references to both nodes
        self.node1.add_DHT({1: {config.PORT: 5001, config.HOST: '127.0.0.1'},
                            2: {config.PORT: 5002, config.HOST: '127.0.0.1'}})
        self.node2.add_DHT({1: {config.PORT: 5001, config.HOST: '127.0.0.1'},
                            2: {config.PORT: 5002, config.HOST: '127.0.0.1'}})

        # Start a simple server on each node to listen for incoming messages
        print("Starting node listeners...")
        threading.Thread(target=self.node1.start_listening, daemon=True).start()
        threading.Thread(target=self.node2.start_listening, daemon=True).start()

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

    def test_mock_download(self):
        test_message = b"Hello from Node1, testing recieving function Nodes"
        sock = self.node1.connect('127.0.0.1', 5002)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.node1.send_message(config.REQUEST_FILE, sock)
        list_files = ["mock"]
        try:
            get_request = self.node2.receive_obj(sock)
            while get_request is None:
                self.node1.send_message(config.REQUEST_FILE, sock)
                get_request = self.node2.receive_obj(sock)
            if get_request == config.REQUEST_FILE:
                print("request_file achieved")
                binary_list = json.dumps(list_files).encode('utf-8')
                self.node2.send_message(binary_list, sock)
                get_list = self.node1.receive_obj(sock)
                while get_list is None:
                    self.node2.send_message(binary_list, sock)
                    get_list = self.node1.receive_obj(sock)
                if get_list == binary_list:
                    print("list files acheived")
                    vector = [1]
                    binary_vector = pickle.dumps(vector)
                    self.node1.send_message(binary_vector, sock)
                    get_vector = self.node2.receive_obj(sock)
                    while get_vector == "":
                        self.node1.send_message(binary_vector, sock)
                        get_vector = self.node2.receive_obj(sock)
                    if get_vector == binary_vector:
                        print(f"Node1 received vector: {get_vector}")
                        self.node2.send_message(test_message, sock)
                        response = self.node1.receive_obj(sock)
                        while response == "":
                            self.node2.send_message(test_message, sock)
                            response = self.node1.receive_obj(sock)

                        # Check if the response matches the sent message
                        self.assertEqual(response, test_message, f"Expected '{test_message}', but got '{response}'")

                        # Close the socket
                        sock.close()



        except Exception as e:
            print(f"Error receiving message: {e}")
            response = ""

        # # Check if the response matches the sent message
        # self.assertEqual(response, test_message, f"Expected '{test_message}', but got '{response}'")
        #
        # # Close the socket
        # sock.close()

    def test_upload_download(self):
        # Test uploading a file from node1 to node2
        file_path = "testfile.txt"
        print(file_path)
        with open(file_path, "w") as f:
            f.write("This is a test file.")

        # Upload the file from node1 to node2
        result = self.node1.upload(file_path)
        print(result)
        self.assertTrue(result, "File upload failed")

        # Attempt to download the file back from node2
        download_success = self.node2.download("testfile.txt", 2, 1)
        self.assertTrue(download_success, "File download failed")

        # Cleanup created test file
        if os.path.exists(file_path):
            os.remove(file_path)

    def tearDown(self):
        # Clean up resources or shutdown any running server threads
        self.node1.stop()
        self.node2.stop()


if __name__ == '__main__':
    unittest.main()
