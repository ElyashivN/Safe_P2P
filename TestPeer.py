import struct
import time
import unittest
from unittest.mock import MagicMock, patch, mock_open
import threading
import config
from Peer import Peer, delete_file

class TestPeer(unittest.TestCase):

    def setUp(self):
        """Set up a Peer instance for testing."""
        self.peer = Peer(peer_id="test_peer", host="127.0.0.1", port=5000)

        # Mock SpacePIR class inside the Peer class
        self.peer.spacePIR = MagicMock()

    def tearDown(self):
        """Clean up after each test."""
        self.peer.stop()  # Stop the Peer instance to ensure no threads are left running

    def test_initialization(self):
        """Test the initialization of the Peer class."""
        self.assertEqual(self.peer.peer_id, "test_peer")
        self.assertEqual(self.peer.host, "127.0.0.1")
        self.assertEqual(self.peer.port, 5000)
        # Check that the executor is a ThreadPoolExecutor
        from concurrent.futures import ThreadPoolExecutor
        self.assertIsInstance(self.peer.executor, ThreadPoolExecutor)
        # Verify that the stop event is not set initially
        self.assertFalse(self.peer._stop_event.is_set())

    def test_delete_file(self):
        """Test the delete_file function."""
        with patch('os.path.exists', return_value=True):
            with patch('os.remove') as mock_remove:
                delete_file("test_file.txt")
                mock_remove.assert_called_once_with("test_file.txt")

    @patch('socket.socket')
    def test_connect(self, mock_socket):
        """Test the connect method."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance

        # Attempt to connect to a mock host and port
        sock = self.peer.connect("127.0.0.1", 8000)
        mock_socket_instance.connect.assert_called_once_with(("127.0.0.1", 8000))
        self.assertEqual(sock, mock_socket_instance)

    def test_handle_upload_request(self):
        """Test the handle_upload_request method."""
        mock_sock = MagicMock()
        self.peer.spacePIR.is_allow_upload = True

        # Mock file handling behavior
        self.peer.receive_file = MagicMock(return_value=("mock_file_name", b"mock_file_content"))
        self.peer.send = MagicMock()

        self.peer.handle_upload_request(mock_sock)

        # Check if the file was received and stored
        self.peer.receive_file.assert_called_once_with(mock_sock)
        self.peer.spacePIR.add.assert_called_once_with("mock_file_name", b"mock_file_content")
        self.peer.send.assert_called_once_with(config.UPLOADED_SUCCESS, mock_sock)

    def test_handle_upload_request_denied(self):
        """Test the handle_upload_request method when upload is not allowed."""
        mock_sock = MagicMock()
        self.peer.spacePIR.is_allow_upload = False

        self.peer.handle_upload_request(mock_sock)
        mock_sock.send.assert_called_once_with(config.UPLOADED_DENIED)

    def test_handle_get_request(self):
        """Test the handle_get_request method."""
        mock_sock = MagicMock()
        self.peer.spacePIR.get_file_names.return_value = ["file1", "file2"]

        # Mock `recv` to return the requested file name and then a mock "polynomial"
        mock_sock.recv.side_effect = ["requested_file".encode(), b"mock_polynomial"]

        self.peer.send = MagicMock()

        self.peer.handle_get_request(mock_sock)

        # Check that the list of files was sent and file retrieval was attempted
        self.peer.send.assert_any_call(["file1", "file2"], mock_sock)

        # Ensure that `spacePIR.get()` is called with the correct file name ("requested_file")
        self.peer.spacePIR.get.assert_called_once_with("requested_file")

    def test_is_uploaded_approved(self):
        """Test the is_uploaded_approved method."""
        mock_sock = MagicMock()
        mock_sock.recv.return_value = config.UPLOAD_APPROVED

        result = self.peer.is_uploaded_approved(mock_sock)
        self.assertEqual(result, 1)

    def test_is_uploaded_success(self):
        """Test the is_uploaded_success method."""
        mock_sock = MagicMock()
        mock_sock.recv.return_value = config.UPLOADED_SUCCESS

        result = self.peer.is_uploaded_success(mock_sock)
        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()
