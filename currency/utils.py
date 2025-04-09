import xml.etree.ElementTree as ET
import requests

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


def fetch_exchange_rates():
    response = requests.get(ECB_URL, timeout=10)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    namespaces = {
        "gesmes": "http://www.gesmes.org/xml/2002-08-01",
        "eurofxref": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref",
    }

    actual_date = root.find(".//eurofxref:Cube[@time]", namespaces).attrib["time"]
    return root, namespaces, actual_date


def fetch_exchange_rates_cmd():
    root, namespaces, actual_date = fetch_exchange_rates()

    rates = []
    for cube in root.findall(".//eurofxref:Cube[@currency]", namespaces):
        currency = cube.attrib["currency"]
        rate = cube.attrib["rate"]
        rates.append({currency: rate})

    rates.append(actual_date)

    return rates


def fetch_exchange_rates_for_db():
    root, namespaces, actual_date = fetch_exchange_rates()

    rates = []
    for cube in enumerate(
        root.findall(".//eurofxref:Cube[@currency]", namespaces), start=1
    ):
        id = cube[0]
        currency = cube[1].attrib["currency"]
        rate = float(cube[1].attrib["rate"])
        rates.append(
            {
                "currency_name": currency,
                "rate": rate,
                "actual_date": actual_date,
                "is_modified": False,
            }
        )

    return rates
