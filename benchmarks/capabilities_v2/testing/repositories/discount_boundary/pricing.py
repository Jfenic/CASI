def discounted_total(amount, member):
    if amount < 0:
        raise ValueError("negative amount")
    if member and amount >= 100:
        return amount * 0.9
    return amount
