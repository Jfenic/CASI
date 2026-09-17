from inventory import reserve


def checkout(stock, prices, sku, quantity):
    price = prices[sku]
    reserve(stock, sku, quantity)
    return price * quantity
