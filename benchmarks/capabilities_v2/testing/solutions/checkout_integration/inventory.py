def reserve(stock, sku, quantity):
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if sku not in stock:
        raise KeyError(sku)
    if stock[sku] < quantity:
        raise ValueError("insufficient stock")
    stock[sku] -= quantity
