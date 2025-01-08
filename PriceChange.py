class PriceChange:
    def __init__(self, city, provider, tariff, date, price, price_before, difference, trend):
        self.city = city
        self.date = date
        self.provider = provider
        self.tariff = tariff
        self.price = price
        self.price_before = price_before
        self.difference = difference
        self.trend = trend
