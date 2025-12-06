"""
Countries utilities - Uses comprehensive world data
"""

from utils.world_data import WORLD_COUNTRIES, WORLD_CITIES


def get_all_countries():
    """Get all countries sorted alphabetically by name"""
    return [(code, data["name"]) for code, data in sorted(WORLD_COUNTRIES.items(), key=lambda x: x[1]["name"])]


def get_country_name(code):
    """Get country name from ISO code"""
    if code in WORLD_COUNTRIES:
        return WORLD_COUNTRIES[code]["name"]
    return code


def get_country_code(name):
    """Get ISO code from country name"""
    for code, data in WORLD_COUNTRIES.items():
        if data["name"].lower() == name.lower():
            return code
    return None


def get_country_info(code):
    """Get full country info (name, flag, continent, currency)"""
    return WORLD_COUNTRIES.get(code, {})


def get_country_flag(code):
    """Get country flag emoji"""
    if code in WORLD_COUNTRIES:
        return WORLD_COUNTRIES[code].get("flag", "")
    return ""


def get_cities_by_country(country_code):
    """Get list of cities for a given country code"""
    return WORLD_CITIES.get(country_code, [])


def get_all_countries_with_flags():
    """Get all countries with their flags, sorted alphabetically"""
    return [(code, f"{data.get('flag', '')} {data['name']}") for code, data in sorted(WORLD_COUNTRIES.items(), key=lambda x: x[1]["name"])]


def search_countries(query):
    """Search countries by name (partial match)"""
    query = query.lower()
    results = []
    for code, data in WORLD_COUNTRIES.items():
        if query in data["name"].lower():
            results.append((code, data["name"]))
    return sorted(results, key=lambda x: x[1])


def get_countries_by_continent(continent):
    """Get all countries in a given continent"""
    results = []
    for code, data in WORLD_COUNTRIES.items():
        if data.get("continent", "").lower() == continent.lower():
            results.append((code, data["name"]))
    return sorted(results, key=lambda x: x[1])
