import pandas as pd
import requests

# Eurostat House Price Index (HPI) dataset
API_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hpi_a"
)

# EU-27 + EFTA countries
countries = [
    "AT",
    "BE",
    "BG",
    "HR",
    "CY",
    "CZ",
    "DK",
    "EE",
    "FI",
    "FR",
    "DE",
    "EL",
    "HU",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SK",
    "SI",
    "ES",
    "SE",
    "CH",
    "NO",
    "IS",
]

# Request total dwelling purchases, HPI with 2015=100, for 2015-2025
params = [
    ("purchase", "TOTAL"),
    ("unit", "I15_A_AVG"),
    ("sinceTimePeriod", "2015"),
    ("untilTimePeriod", "2025"),
]

# Eurostat accepts repeated geo parameters for multiple countries
for country in countries:
    params.append(("geo", country))


response = requests.get(API_URL, params=params, timeout=30)
response.raise_for_status()
data = response.json()


# Validate the JSON-stat structure expected by the transformation logic
expected_dimensions = ["freq", "purchase", "unit", "geo", "time"]

if data["id"] != expected_dimensions:
    raise ValueError(f"Unexpected dimension order: {data['id']}")

if data["size"][:3] != [1, 1, 1]:
    raise ValueError(
        f"Expected freq, purchase and unit dimensions to have size 1, "
        f"but received: {data['size']}"
    )

# Extract country/year metadata from the JSON-stat response
country_codes = list(data["dimension"]["geo"]["category"]["index"].keys())
country_labels = data["dimension"]["geo"]["category"]["label"]
years = list(data["dimension"]["time"]["category"]["index"].keys())

# Convert flattened JSON-stat values into country-year observations
rows = []

for country_position, country_code in enumerate(country_codes):
    for year_index, year in enumerate(years):

        position = country_position * len(years) + year_index
        value = data["value"].get(str(position))

        rows.append(
            {
                "country_code": country_code,
                "country_name": country_labels[country_code],
                "year": int(year),
                "house_price_index": value,
            }
        )

df = pd.DataFrame(rows)

# Basic extraction quality checks
print(f"Extracted {len(df)} rows")
print(f"Missing HPI values: {df['house_price_index'].isna().sum()}")

# Preserve the extracted data as the raw layer
df.to_csv("data/raw/house_price_index.csv", index=False)
print("Saved data/raw/house_price_index.csv")
