def invoice_total(lines):
    return f"{sum(float(price) * quantity for price, quantity in lines):.2f}"
