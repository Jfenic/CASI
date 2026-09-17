class Centerer:
    def fit(self, rows):
        if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
            raise ValueError("nonempty rectangular training data required")
        means = []
        for column in zip(*rows, strict=True):
            values = [value for value in column if value is not None]
            means.append(sum(values) / len(values) if values else 0.0)
        self.means = means
        return self

    def transform(self, rows):
        if not hasattr(self, "means"):
            raise ValueError("not fitted")
        if any(len(row) != len(self.means) for row in rows):
            raise ValueError("wrong width")
        return [
            [
                0.0 if value is None else value - mean
                for value, mean in zip(row, self.means, strict=True)
            ]
            for row in rows
        ]
