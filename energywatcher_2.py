from bs4 import BeautifulSoup
import requests
import cities
from datetime import datetime
import json
import db_handler
import PriceChange
import random


SHOW_PRINTS = False

results =[]
data_dict = {}

def datetime_converter(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")

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

    data_dict = get_data(soup)
    if data_dict != None:
        for provider, value in data_dict.items():
                provider_tariff_sum = 0
                provider_tariff_count = 0
                if SHOW_PRINTS: print(provider)
                try:
                    for id, tariff_info in value.items():
                        if tariff_info["name"] == "Anderer Tarif des Anbieters *"  : continue
                        provider_tariff_count += 1
                        if SHOW_PRINTS: print("\tTarif:", tariff_info["name"])
                        if SHOW_PRINTS: print("\tPreis kwh Netto:", tariff_info["unitfee"])
                        
                        result = db_handler.get_latest_price_data_by_provider_tariff_from_sqlite_db(provider, tariff_info["name"], city_to_add)
                        provider_tariff_sum += tariff_info["unitfee"]

                        if result == None:
                            # Neuer Tariff in DB
                            if SHOW_PRINTS: print("\t  NEW TARIFF\n")
                            pricechange_to_add = PriceChange.PriceChange(city_to_add, provider, tariff_info["name"], now, tariff_info["unitfee"], 0, 0, "none")
                            db_handler.post_price_change_to_local_sqlite_db(pricechange_to_add)
                        else:
                            # Check ob gleich:          33                          30
                            difference = float(result["price_old"]) - float(tariff_info["unitfee"])
                            if difference == 0:
                                continue
                            else:
                                # PRICE CHANGE!
                                trend = "down"
                                if difference > 0:
                                    trend = "up"
                                print(f"---- {city_to_add} {provider} PRICE CHANGE!! PriceOld", result['price_old'], "Price now:", tariff_info["unitfee"], "difference:", difference, "trend:", trend, "\n")
                                pricechange_to_add = PriceChange.PriceChange(city_to_add, provider, tariff_info["name"], now, tariff_info["unitfee"], result["price_old"], difference, trend)
                                db_handler.post_price_change_to_local_sqlite_db(pricechange_to_add)
                                
                except Exception as e:
                    print("Error etting data:", e)
                    print("data:", tariff_info)
                    print("\n\n")


                # AVERAGE
                if provider_tariff_count != 0 and provider_tariff_sum != 0:
                    average = provider_tariff_sum / provider_tariff_count
                    result = db_handler.get_latest_price_data_by_provider_tariff_from_sqlite_db(provider, f"{provider}_AVERAGE", city_to_add)
                    
                    if result == None:
                        # Neuer Tariff in DB
                        print("\t AVERAGE: NEW TARIFF\n")
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
    for city_info in cities.cities_2:
        count += 1
        if SHOW_PRINTS: print(f"{city_info} \t\t {count} / {len(cities.cities_2)}")
        get_prices(zipcode=city_info[0], city_to_add=city_info[1])

get_cities_data()


