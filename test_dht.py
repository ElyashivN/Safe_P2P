import socket
import unittest
import asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime
from dht import DHT


class TestDHT(unittest.TestCase):
    """
    Unit tests for the DHT class, which verifies the behavior of various Distributed Hash Table operations,
    including adding nodes, retrieving node data, removing nodes, and handling multiple DHT instances.
    """

    def setUp(self):
        """
        Set up the test environment by initializing a DHT instance with a random port.
        Uses a socket bound to port 0 to automatically assign a free port.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('localhost', 0))
            port = s.getsockname()[1]

        # Initialize the DHT with the randomly selected port
        self.dht = DHT(port=port)

    def tearDown(self):
        """
        Tear down the test environment by shutting down the DHT instance and closing the event loop.
        Ensures proper cleanup after each test to avoid resource leaks.
        """
        self.dht.shutdown()
        if not self.dht.loop.is_closed():
            self.dht.loop.close()

    def test_add_node(self):
        """
        Test that adding a node to the DHT works as expected.
        This ensures that a node can be added and properly stored in the DHT.
        """
        with patch.object(self.dht, 'server', new_callable=AsyncMock):
            self.dht.server.set = AsyncMock()

            async def run_test():
                # Add a node with port 8080 and a socket address
                await self.dht.get_and_add_node(8080, "node1", "192.168.1.1:8080")
                # Retrieve the DHT and verify the node exists
                result = self.dht.get_dht()
                self.assertIn("node1", result)
                self.assertEqual(result["node1"]["port"], 8080)
                self.assertEqual(result["node1"]["socket"], "192.168.1.1:8080")

            asyncio.run(run_test())

    def test_get_node_data(self):
        """
        Test that retrieving data for a node works as expected.
        This uses a mocked Kademlia server to simulate retrieving node data from the DHT.
        """
        with patch.object(self.dht, 'server', new_callable=AsyncMock):
            self.dht.server.set = AsyncMock()
            self.dht.server.get = AsyncMock()

            # Simulate Kademlia returning node information as a JSON string
            self.dht.server.get.return_value = '{"port": 8080, "socket": "192.168.1.1:8080", "upload_time": "2024-01-01T12:00:00", "last_get": "2024-01-01T12:00:00"}'

            async def run_test():
                # Add a node and then retrieve its data
                await self.dht.get_and_add_node(8080, "node1", "192.168.1.1:8080")
                node_data = await self.dht.get_node_data("node1")
                # Verify that the retrieved data matches the added node
                self.assertIsNotNone(node_data)
                self.assertEqual(node_data["port"], 8080)
                self.assertEqual(node_data["socket"], "192.168.1.1:8080")

            asyncio.run(run_test())

    def test_remove_node(self):
        """
        Test that a node can be removed from the DHT.
        Verifies that the node is no longer in the DHT after being removed.
        """
        with patch.object(self.dht, 'server', new_callable=AsyncMock):
            self.dht.server.set = AsyncMock()

            async def run_test():
                # Add a node and then remove it
                await self.dht.get_and_add_node(8080, "node1", "192.168.1.1:8080")
                await self.dht._remove_node("node1")
                # Ensure the node is no longer in the DHT
                result = self.dht.get_dht()
                self.assertNotIn("node1", result)

            asyncio.run(run_test())

    def test_add_multiple_nodes(self):
        """
        Test that multiple nodes can be added to the DHT and stored correctly.
        Verifies that all added nodes are present in the DHT.
        """
        with patch.object(self.dht, 'server', new_callable=AsyncMock):
            self.dht.server.set = AsyncMock()

            async def run_test():
                # Add three different nodes to the DHT
                await self.dht.get_and_add_node(8080, "node1", "192.168.1.1:8080")
                await self.dht.get_and_add_node(8081, "node2", "192.168.1.2:8081")
                await self.dht.get_and_add_node(8082, "node3", "192.168.1.3:8082")
                # Verify that all nodes are added
                result = self.dht.get_dht()
                self.assertIn("node1", result)
                self.assertIn("node2", result)
                self.assertIn("node3", result)

            asyncio.run(run_test())

    def test_get_nonexistent_node(self):
        """
        Test retrieving a nonexistent node from the DHT.
        This should return None when the node does not exist in the DHT.
        """
        with patch.object(self.dht, 'server', new_callable=AsyncMock):
            self.dht.server.get = AsyncMock()
            # Simulate a None result for a nonexistent node
            self.dht.server.get.return_value = None

            async def run_test():
                # Try retrieving a node that doesn't exist
                node_data = await self.dht.get_node_data("nonexistent_node")
                # Ensure that the result is None
                self.assertIsNone(node_data)

            asyncio.run(run_test())

    def test_timestamps(self):
        """
        Test that the upload_time and last_get timestamps are set correctly when a node is added to the DHT.
        This ensures that timestamps are properly initialized and match the expected values.
        """
        with patch.object(self.dht, 'server', new_callable=AsyncMock):
            self.dht.server.set = AsyncMock()

            async def run_test():
                # Mock the current datetime to control the timestamps
                with patch('dht.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)

                    # Add a node and verify timestamps
                    await self.dht.get_and_add_node(8080, "node1", "192.168.1.1:8080")

                # Check that the timestamps are set correctly
                result = self.dht.get_dht()
                self.assertEqual(result["node1"]["upload_time"], "2024-01-01T12:00:00")
                self.assertEqual(result["node1"]["last_get"], "2024-01-01T12:00:00")

            asyncio.run(run_test())

    def test_add_same_node_id_twice(self):
        """
        Test that adding the same node ID twice does not overwrite the original node's details.
        Ensures that duplicate IDs do not replace existing entries in the DHT.
        """
        with patch.object(self.dht, 'server', new_callable=AsyncMock):
            self.dht.server.set = AsyncMock()

            async def run_test():
                # Add a node with ID "node1"
                await self.dht.get_and_add_node(8080, "node1", "192.168.1.1:8080")
                # Attempt to add another node with the same ID but different details
                await self.dht.get_and_add_node(9090, "node1", "192.168.1.2:9090")

                # Retrieve the DHT and verify that the original node details were not overwritten
                result = self.dht.get_dht()
                self.assertIn("node1", result)
                self.assertEqual(result["node1"]["port"], 8080)
                self.assertEqual(result["node1"]["socket"], "192.168.1.1:8080")

            asyncio.run(run_test())

    def test_add_dht(self):
        """
        Test merging nodes from one DHT instance into another.
        Ensures that nodes from the second DHT are correctly added to the first DHT without overwriting existing nodes.
        """
        with patch.object(self.dht, 'server', new_callable=AsyncMock):
            self.dht.server.set = AsyncMock()
            self.dht.server.protocol = AsyncMock()
            self.dht.server.protocol.router = AsyncMock()

            async def run_test():
                # Create a second DHT instance with a randomly assigned port
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.bind(('localhost', 0))
                    second_port = s.getsockname()[1]

                second_dht = DHT(port=second_port)

                # Mock the server on second_dht
                second_dht.server.set = AsyncMock()
                second_dht.server.protocol = AsyncMock()
                second_dht.server.protocol.router = AsyncMock()

                # Add nodes to dht1
                await self.dht.get_and_add_node(8080, "node1", "192.168.1.1:8080")
                await self.dht.get_and_add_node(8081, "node2", "192.168.1.2:8081")

                # Add different nodes to second_dht
                await second_dht.get_and_add_node(9090, "node3", "192.168.1.3:9090")
                await second_dht.get_and_add_node(9091, "node4", "192.168.1.4:9091")

                # Assert that dht1 does not have node3 and node4 before calling _add
                result_before_add = self.dht.get_dht()
                self.assertNotIn("node3", result_before_add)
                self.assertNotIn("node4", result_before_add)

                # Call the _add method to merge nodes from second_dht into dht1
                self.dht._add(second_dht)

                # Assert that dht1 now contains all nodes from second_dht as well
                result_after_add = self.dht.get_dht()
                self.assertIn("node1", result_after_add)
                self.assertIn("node2", result_after_add)
                self.assertIn("node3", result_after_add)
                self.assertIn("node4", result_after_add)

                # Cleanup second_dht (without manually closing the loop)
                second_dht.shutdown()

            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(run_test())
            except asyncio.CancelledError:
                pass  # Handle the cancelled tasks gracefully


if __name__ == '__main__':
    unittest.main()
