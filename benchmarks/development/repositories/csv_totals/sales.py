def totals(text):
    result = {}
    for line in text.splitlines()[1:]:
        if not line:
            continue
        product, quantity = line.split(",")
        result[product] = int(quantity)
    return result
