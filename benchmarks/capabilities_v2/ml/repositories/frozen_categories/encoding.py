class Encoder:
    def fit(self, values):
        self.categories = sorted(set(values))
        return self

    def transform(self, values):
        if not hasattr(self, "categories"):
            raise ValueError("not fitted")
        return [
            [int(value == category) for category in self.categories] for value in values
        ]
