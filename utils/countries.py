COUNTRIES = {
    'FR': 'France',
    'BE': 'Belgique',
    'CH': 'Suisse',
    'LU': 'Luxembourg',
    'MC': 'Monaco',
    'CA': 'Canada',
    'MA': 'Maroc',
    'TN': 'Tunisie',
    'DZ': 'Algérie',
    'SN': 'Sénégal',
    'CI': 'Côte d\'Ivoire',
    'CM': 'Cameroun',
    'MG': 'Madagascar',
    'ML': 'Mali',
    'NE': 'Niger',
    'BF': 'Burkina Faso',
    'TG': 'Togo',
    'BJ': 'Bénin',
    'GA': 'Gabon',
    'CG': 'Congo',
    'CD': 'RD Congo',
    'HT': 'Haïti',
    'MU': 'Maurice',
    'DE': 'Allemagne',
    'ES': 'Espagne',
    'IT': 'Italie',
    'PT': 'Portugal',
    'GB': 'Royaume-Uni',
    'US': 'États-Unis',
    'AE': 'Émirats Arabes Unis',
    'SA': 'Arabie Saoudite',
    'QA': 'Qatar',
    'KW': 'Koweït',
    'BH': 'Bahreïn',
    'OM': 'Oman',
    'JO': 'Jordanie',
    'LB': 'Liban',
    'EG': 'Égypte',
}


def get_all_countries():
    return [(code, name) for code, name in sorted(COUNTRIES.items(), key=lambda x: x[1])]


def get_country_name(code):
    return COUNTRIES.get(code, code)


def get_country_code(name):
    for code, country_name in COUNTRIES.items():
        if country_name.lower() == name.lower():
            return code
    return None
