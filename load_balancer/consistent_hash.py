class ConsistentHashMap:
    """A consistent hashing ring used to map requests to server replicas.

    Each server is placed at `num_virtual` positions (virtual nodes) on a
    ring of `num_slots` slots, so load spreads more evenly than one slot
    per server would, and adding/removing a server only remaps requests
    that fall in its immediate vicinity on the ring.
    """

    def __init__(self, num_slots: int = 512, num_virtual: int = 9) -> None:
        """Initialize the consistent hash ring map.

        Args:
            num_slots (int): Total number of slots (M) on the hash ring. Default is 512.
            num_virtual (int): Number of virtual nodes (K) per server. Default is 9.
        """
        self.num_slots: int = num_slots        # M = 512
        self.num_virtual: int = num_virtual    # K = 9
        self.hash_map: list = [None] * num_slots  # the ring


    def request_hash(self, req_id: int) -> int:
        """Hash a request ID to a specific slot on the consistent hashing ring.

        Uses the quadratic hash function formula: H(i) = (i^2 + 2i + 17) % M.

        Args:
            req_id (int): The unique integer ID of the incoming request.

        Returns:
            int: The calculated slot index on the ring (0 <= index < num_slots).
        """
        return (req_id**2 + 2*req_id + 17) % self.num_slots


    def server_hash(self, server_id, virtual_id):
        """Phi(i, j) = i^2 + j^2 + 2j + 25 -- maps a (server, virtual node)
        pair to a ring slot."""
        i, j = server_id, virtual_id
        return (i**2 + j**2 + 2*j + 25) % self.num_slots

    def add_server(self, server_id):
        """Place all of a server's virtual nodes on the ring, resolving
        any slot collisions via linear probing to the next free slot."""
        for j in range(self.num_virtual):
            slot = self.server_hash(server_id, j)
            while self.hash_map[slot] is not None:
                slot = (slot + 1) % self.num_slots
            self.hash_map[slot] = server_id

    def remove_server(self, server_id):
        """Clear every slot occupied by this server's virtual nodes."""
        for slot in range(self.num_slots):
            if self.hash_map[slot] == server_id:
                self.hash_map[slot] = None

    def get_server(self, req_id):
        """Hash the request onto the ring, then walk clockwise to the
        nearest occupied slot - that slot's server handles the request."""
        slot = self.request_hash(req_id)
        for i in range(self.num_slots):
            candidate = self.hash_map[(slot + i) % self.num_slots]
            if candidate is not None:
                return candidate
        return None  # no servers at all