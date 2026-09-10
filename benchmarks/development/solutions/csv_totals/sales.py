import csv
import io


def totals(text):
    result = {}
    for row in csv.DictReader(io.StringIO(text, newline="")):
        product = row["product"]
        result[product] = result.get(product, 0) + int(row["quantity"])
    return result
