import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import config
from Node import Node
from dht import DHT
from encryption import Encryption
from FileHandler import FileHandler
import rsa

class TestNode(unittest.TestCase):
    def setUp(self):
        """
        Setup for Node testing.
        """
        self.node = Node(port=5001, peer_id="Node1", host="127.0.0.1", path="test_path/")
        # Mocking RSA encryption and decryption methods
        self.node.publicKey = MagicMock()
        self.node.privateKey = MagicMock()

    @patch("Node.Encryption")
    @patch("Node.pickle.dump")
    @patch("builtins.open", new_callable=mock_open)
    def test_store_Node(self, mock_open_file, mock_pickle, mock_encryption):
        password = "test_password"
        self.node.store_Node(password, path="test_path/")
        mock_encryption.store.assert_called_once_with(password, self.node.privateKey, path="test_path/")
        self.assertTrue(mock_open_file.called)
        self.assertTrue(mock_pickle.called)

    @patch("Node.Encryption")
    @patch("Node.pickle.load")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_Node(self, mock_open_file, mock_pickle, mock_encryption):
        password = "test_password"
        mock_encryption.load.return_value = MagicMock()
        self.node.load_node(password, path="test_path/")
        mock_encryption.load.assert_called_once_with(password, path="test_path/")
        self.assertTrue(mock_open_file.called)
        self.assertTrue(mock_pickle.called)

    @patch("Node.socket.create_connection")
    @patch("Node.Node.is_uploaded_approved", return_value=1)
    @patch("Node.Node.is_uploaded_success", return_value=1)
    @patch("Node.Node.send_file")
    def test_upload_to_peer_success(self, mock_send_file, mock_is_uploaded_success, mock_is_uploaded_approved, mock_socket):
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        file_path = "test_file"
        result = self.node.upload_to_peer(file=file_path, port=5001)
        self.assertTrue(result)
        mock_send_file.assert_called_once_with(file_path, mock_sock_instance)

    @patch("Node.socket.create_connection", side_effect=Exception("Connection Error"))
    def test_upload_to_peer_failure(self, mock_socket):
        file_path = "test_file"
        result = self.node.upload_to_peer(file=file_path, port=5001)
        self.assertFalse(result)

    @patch("Node.Node.send_message")
    @patch("Node.Node.receive_obj", return_value=["file1", "file2"])
    @patch("Node.socket.create_connection")
    def test_download_from_peer_success(self, mock_socket, mock_receive_obj, mock_send_message):
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        self.node.privateKey.decrypt.return_value = b"decrypted_data"
        result = self.node.download_from_peer(name="file1", port=5001, number=0)
        self.assertIsNotNone(result)

    @patch("os.path.getsize", return_value=100)
    @patch("Node.FileHandler.divide", return_value=(["subfile1", "subfile2"], 2, None))
    @patch("Node.Node.upload_to_peer", return_value=True)
    def test_upload_success(self, mock_upload_to_peer, mock_divide, mock_getsize):
        self.node.DHT.add_DHT({
            "peer1": {config.PORT: 5001, config.HOST: "127.0.0.1"},
            "peer2": {config.PORT: 5002, config.HOST: "127.0.0.1"}
        })
        result = self.node.upload(file_path="test_path/testfile")
        self.assertTrue(result)

    @patch("os.path.getsize", return_value=100)
    @patch("Node.FileHandler.divide", return_value=(["subfile1", "subfile2"], 2, None))
    @patch("Node.Node.upload_to_peer", return_value=False)
    def test_upload_failure(self, mock_upload_to_peer, mock_divide, mock_getsize):
        self.node.DHT.add_DHT({
            "peer1": {config.PORT: 5001, config.HOST: "127.0.0.1"},
            "peer2": {config.PORT: 5002, config.HOST: "127.0.0.1"}
        })
        result = self.node.upload(file_path="test_path/testfile")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
