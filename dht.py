from datetime import datetime

import config


class DHT:
    def __init__(self):
        """
        Initialize the DHT class, which represents a Distributed Hash Table. The DHT allows nodes
        to be added, retrieved, and removed. It also handles server operations using Kademlia.
        Args:
            port (int): The port number on which the Kademlia server listens..
        """
        # try:
        #     self.loop = asyncio.get_running_loop()  # Get the current running event loop, if available
        # except RuntimeError:
        #     self.loop = asyncio.new_event_loop()  # Create a new event loop if none is running
        #     asyncio.set_event_loop(self.loop)
        #
        # self.server = Server()  # Initialize the Kademlia server
        #
        # # Start the server asynchronously if the loop is running, or block until the server starts
        # if self.loop.is_running():
        #     asyncio.ensure_future(self.server.listen(port))  # Schedule server to start asynchronously
        # else:
        #     self.loop.run_until_complete(self.server.listen(port))  # Block and start listening on the port

        self._dht = {}  # Dictionary to keep track of local node information

    async def get_and_add_node(self, port, node_id, host):
        """
        Add a node to the DHT, but do not overwrite existing nodes with the same ID. If the node already exists,
        return the current DHT without changes.

        Args:
            port (int): The port number of the node.
            node_id (str): The unique identifier for the node.
            socket (str): The socket address (IP and port) of the node.

        Returns:
            dict: A copy of the updated DHT.
        """
        if node_id in self._dht:
            return self.get_dht()  # Return the current DHT without adding the node if it already exists
        await self.add_node(port, node_id, host)  # Add the node if it does not exist
        return self.get_dht()  # Return the updated DHT

    def add_node(self, port, node_id, host):
        """
        Add a new node to the DHT.

        :param port: The port of the new node.
        :param node_id: The unique identifier of the new node.
        :param host: The host/IP address of the new node.
        :return: True if added successfully, False if node already exists.
        """
        if node_id not in self._dht:
            self._dht[node_id] = {config.PORT: port, config.HOST: host}
            return True
        return False  # Node already exists

    def get_dht(self):
        """
        Return a copy of the current DHT, ensuring that the original DHT remains immutable.

        Returns:
            dict: A copy of the current DHT.
        """
        return self._dht.copy()  # Return a shallow copy of the DHT to prevent external modifications

    async def get_node_data(self, node_id):
        """
        Retrieve node data from the Kademlia DHT. This method deserializes the data before returning it.

        Args:
            node_id (str): The unique identifier of the node to retrieve.

        Returns:
            dict: The node data, or None if the node does not exist.
        """
        # serialized_data = await self.server.get(node_id)  # Retrieve the serialized node data from Kademlia
        return self._dht[node_id]

    def add_DHT(self, other_dht):
        """
        Add all nodes from another DHT instance to this DHT. This is useful for merging DHTs
        from multiple sources without overwriting existing nodes in the current DHT.
        """
        for node_id, node_data in other_dht.items():
            if node_id not in self._dht:
                self._dht[node_id] = node_data  # Add the node if it doesn't already exist in the current DHT
            else:  # todo if we have more time we will override by signature of the node (public key) and timestamp.
                print(f"Node with ID {node_id} already in dht")

    async def _remove_node(self, node_id):
        """
        Remove a node from both the local DHT and the Kademlia network. This ensures the node is no longer
        accessible.

        Args:
            node_id (str): The unique identifier of the node to be removed.
        """
        if node_id in self._dht:
            del self._dht[node_id]  # Remove the node from the local DHT
            # await self.server.set(node_id, None)  # Remove the node from the Kademlia DHT

    # def shutdown(self):
    #     """
    #     Gracefully shut down the DHT and Kademlia server. This method cancels all pending tasks and ensures
    #     that resources such as the event loop and the Kademlia server are cleaned up properly.
    #     """
    #     if self.server:
    #         self.server.stop()  # Stop the Kademlia server
    #
    #     # Gather and cancel all pending tasks in the event loop
    #     pending_tasks = asyncio.all_tasks(self.loop)
    #     for task in pending_tasks:
    #         task.cancel()
    #
    #     if self.loop.is_running():
    #         # Schedule task cleanup asynchronously if the loop is running
    #         asyncio.ensure_future(self._cleanup_tasks(pending_tasks))
    #     else:
    #         # Clean up synchronously if the loop is not running
    #         try:
    #             self.loop.run_until_complete(self._cleanup_tasks(pending_tasks))
    #             self.loop.run_until_complete(self.loop.shutdown_asyncgens())
    #         except RuntimeError:
    #             pass  # Ignore if there's no running event loop
    #
    #     # Only close the event loop if it's not running and hasn't been closed
    #     if not self.loop.is_running() and not self.loop.is_closed():
    #         self.loop.close()

    # async def _cleanup_tasks(self, tasks):
    #     """
    #     Helper method to await all pending tasks and handle task cancellation during the shutdown process.
    #
    #     Args:
    #         tasks (set): A set of tasks to be awaited and cleaned up.
    #     """
    #     results = await asyncio.gather(*tasks, return_exceptions=True)  # Await all tasks and handle exceptions
    #     for result in results:
    #         if isinstance(result, asyncio.CancelledError):
    #             continue  # Handle any cancelled tasks during cleanup