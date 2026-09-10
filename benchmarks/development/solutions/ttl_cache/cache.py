class Cache:
    def __init__(self, clock):
        self.clock = clock
        self.entries = {}

    def set(self, key, value, ttl):
        if ttl < 0:
            raise ValueError("negative ttl")
        self.entries[key] = (value, self.clock() + ttl)

    def get(self, key, default=None):
        if key not in self.entries:
            return default
        value, expiry = self.entries[key]
        if self.clock() >= expiry:
            return default
        return value
