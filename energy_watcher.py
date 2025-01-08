from bs4 import BeautifulSoup
import requests
import cities
from datetime import datetime
import re

import json

headers = {'user-agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 12_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 105.0.0.11.118 (iPhone11,8; iOS 12_3_1; en_US; en-US; scale=2.00; 828x1792; 165586599)'}

results =[]

def datetime_converter(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")

def extract_numbers_and_commas(input_string):
    result = re.sub(r'[^0-9,]', '', input_string)
    try:
        return float(result.replace(",", "."))
    except Exception as e:
        print("Error converting price:", e)
    return None

def get_prices(zipcode, city):
    global results
    now = datetime.now()
    URL =f"https://www.check24.de/strom/vergleich/check24/?product_id=1&stats=yes&sortfield=popularity&sortorder=asc&zipcode={zipcode}&city={city}&totalconsumption=2500&pricing=month&setting=individual&commoncarrier=yes&customertype=private&energymix_type=all&tariffscore=0&contractperiod=12&consider_max_bonus_share=yes&cancellationperiod=30&contractextension=1&priceguarantee=fixed_price&priceguarantee_months=99&maxtariffs=2&companyevaluation_positive=yes&subscriptiononly=yes&guidelinematch=yes&packages=no&secondarytime_active=no&secondarytime=0&reference_provider_hash=drewag&reference_tariffversion_key=1278640-base&calculationparameter_id=1cbe3c84f1d5c154a174133c73c10fef&pagesize=120"


    source = requests.get(URL, headers = headers).text
    soup = BeautifulSoup(source, "html.parser")
    result_wrappers = soup.find_all("article", class_ = "result-row")

    for result_wrapper in result_wrappers:

        has_data = result_wrapper.find_all("section")
        if has_data == False:
            continue

        provider_img = result_wrapper.find("img", class_ ="logo__img")
        if provider_img:
            provider = provider_img.get("alt")
        else:
            continue

        tariff_name_div = result_wrapper.find("div", class_ = "result-rowTarifName")
        if tariff_name_div:
            tariff_name = tariff_name_div.text.strip()
        else:
            continue
        
        price_kwh_div = result_wrapper.find("div", class_="result-row__priceCatcher")
        if price_kwh_div:
            price_per_kwh_in_cent = price_kwh_div.text
            price_per_kwh_in_cent = extract_numbers_and_commas(price_per_kwh_in_cent)
            if price_per_kwh_in_cent is None:
                continue
        else:
            continue
        
        results.append({
            "city": city,
            "zipcode" : zipcode,
            "provider" : provider, 
            "tariff_name" : tariff_name, 
            "price_per_kwh_in_cent" : price_per_kwh_in_cent,
            "date": now
        })
        
def save_to_json():
    global results
    output = json.dumps(results, indent=4, default=datetime_converter)

    with open("data.json", "w", encoding="UTF-8") as json_file:
        json_file.write(output)
        print("Erfolgreich gespeichert")

def get_cities_data():
    count = 0
    for city_info in cities.cities:
        count += 1
        print(f"{city_info} \t\t {count} / {len(cities.cities)}")
        get_prices(zipcode=city_info[0], city=city_info[1])

get_cities_data()
print(len(results))

save_to_json()

