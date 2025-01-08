from bs4 import BeautifulSoup
import requests
import cities
from datetime import datetime
import json
import db_handler
import PriceChange
import random
import re

SHOW_PRINTS = False

results =[]
data_dict = {}

def datetime_converter(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")

def extract_numbers(input_string):
    replace_string = input_string.replace(",", ".")
    # Verwende einen regulären Ausdruck, um Zahlen und Kommata zu extrahieren
    result = re.findall(r'[\d,]+', replace_string)
    
    # Verbinde alle gefundenen Teile zu einem String
    if result:
        return float(result[0])
    return None

def get_data(soup) -> dict:
    select_elements = soup.find_all('select', {'class': 'select'})

    for select_element in select_elements:
    
        if select_element:
            # Den Wert des Attributs 'data-options' extrahieren
            data_options = select_element.get('data-options')
        
            if data_options:
                # Den JSON-kompatiblen String in ein Python-Dict umwandeln
                data_dict = json.loads(data_options)
                return data_dict
                
            else:
                continue
    return None

def get_data_from_soup(soup) -> dict:
    data = {}

    tariff_wrappers = soup.find_all("article", class_ ="result-row")

    for tariff_wrapper in tariff_wrappers:
        provider_img = tariff_wrapper.find("img", class_ = "logo__img")
        if not provider_img: continue
        provider = provider_img.get("alt")
        tariff_div = tariff_wrapper.find("strong", class_ = "tariff-brand__tariff-name")

        if not tariff_div: continue
        tariff = tariff_div.text

        price_wrapper = tariff_wrapper.find("div", class_ ="result-row__priceCatcher")

        if not price_wrapper: continue
        price_tag = price_wrapper.find("strong")
        if not price_tag: continue
        price = price_tag.text
        price_cleaned = extract_numbers(price)

        if price_cleaned == None: continue

        if data.get(provider) == None:
            data[provider] = []
        
        data[provider].append(
            {
                "tariff" : tariff,
                "price" : price_cleaned,
            }
        )

    return data


def get_headers() -> str:
    user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 11; Pixel 4 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
    # Füge weitere User-Agents hinzu
    ]

    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1'
    }

    return headers

def get_prices(zipcode, city_to_add):
    global results, data_dict
    now = datetime.now().strftime("%Y-%m-%d")
    URL =f"https://www.check24.de/strom/vergleich/check24/?product_id=1&stats=yes&sortfield=popularity&sortorder=asc&zipcode={zipcode}&city={city_to_add}&totalconsumption=2500&pricing=month&setting=individual&commoncarrier=yes&customertype=private&energymix_type=all&tariffscore=0&contractperiod=12&consider_max_bonus_share=yes&cancellationperiod=30&contractextension=1&priceguarantee=fixed_price&priceguarantee_months=99&maxtariffs=2&companyevaluation_positive=yes&subscriptiononly=yes&guidelinematch=yes&packages=no&secondarytime_active=no&secondarytime=0&reference_provider_hash=drewag&reference_tariffversion_key=1278640-base&calculationparameter_id=1cbe3c84f1d5c154a174133c73c10fef&pagesize=120"

    headers = get_headers()
    source = requests.get(URL, headers = headers).text
    soup = BeautifulSoup(source, "html.parser")
    # with open("debug.html", "w", encoding="UTF-8") as file:
    #     file.write(soup.prettify())

    data = get_data_from_soup(soup)

    if data != None:
        for provider, tariffs in data.items():
            provider_tariff_sum = 0
            provider_tariff_count = 0
            if SHOW_PRINTS: print(provider)

            for tariff in tariffs:
                if SHOW_PRINTS: print("\tTarif:", tariff["tariff"])
                if SHOW_PRINTS: print("\tPreis kwh Netto:", tariff["price"])

                result = db_handler.get_latest_price_data_by_provider_tariff_from_sqlite_db(provider, tariff["tariff"], city_to_add)
                provider_tariff_count += 1
                provider_tariff_sum += tariff["price"]

                if result == None:
                    # Neuer Tariff in DB
                    if SHOW_PRINTS: print("\tNEW TARIFF")
                    pricechange_to_add = PriceChange.PriceChange(city_to_add, provider, tariff["tariff"], now, tariff["price"], 0, 0, "none")
                    db_handler.post_price_change_to_local_sqlite_db(pricechange_to_add)
                else:
                    # Check ob gleich:          33                          30
                    difference = float(result["price_old"]) - tariff["price"]
                    if difference == 0:
                        continue
                    else:
                        # PRICE CHANGE!
                        trend = "down"
                        if difference > 0:
                            trend = "up"
                        print(f"---- {city_to_add} {provider} PRICE CHANGE!! PriceOld", result['price_old'], "Price now:", tariff["price"], "difference:", difference, "trend:", trend, "\n")
                        pricechange_to_add = PriceChange.PriceChange(city_to_add, provider, tariff["tariff"], now, tariff["price"], result["price_old"], difference, trend)
                        db_handler.post_price_change_to_local_sqlite_db(pricechange_to_add)
                                
        

                # AVERAGE
            if provider_tariff_count != 0 and provider_tariff_sum != 0:
                average = provider_tariff_sum / provider_tariff_count
                result = db_handler.get_latest_price_data_by_provider_tariff_from_sqlite_db(provider, f"{provider}_AVERAGE", city_to_add)
                
                if result == None:
                    # Neuer Tariff in DB
                    if SHOW_PRINTS: print("   AVERAGE: NEW TARIFF\n")
                    pricechange_average_to_add = PriceChange.PriceChange(city_to_add, provider, f"{provider}_AVERAGE", now, average, 0, 0, "none")
                    db_handler.post_price_change_to_local_sqlite_db(pricechange_average_to_add)
                else:
                    # Check ob gleich:          33                          30
                    difference = float(result["price_old"]) - float(average)
                    if difference == 0:
                        continue
                    else:
                        # PRICE CHANGE!
                        trend = "down"
                        if difference > 0:
                            trend = "up"
                        print("     AVERAGE: PRICE CHANGE!! PriceOld", result['price_old'], "Price now:", average, "difference:", difference, "trend:", trend, "\n")
                        pricechange_average_to_add = PriceChange.PriceChange(city_to_add, provider, f"{provider}_AVERAGE", now, average, result["price_old"], difference, trend)
                        db_handler.post_price_change_to_local_sqlite_db(pricechange_average_to_add)
    else:
        print("Error, can't find data_dict (in HTML with parameter: data-options)")
        with open("debug.html", "w", encoding="UTF-8") as file:
            file.write(soup.prettify())
            print("HTML Code in debug.html")

def get_cities_data():
    count = 0
    for city_info in cities.cities_1:
        count += 1
        print(f"{city_info} \t\t {count} / {len(cities.cities_1)}")
        get_prices(zipcode=city_info[0], city_to_add=city_info[1])
get_cities_data()


