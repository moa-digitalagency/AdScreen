import os
import json
import logging
import threading
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CACHE_FILE = '/tmp/exchange_rates_cache.json'
CACHE_DURATION_HOURS = 24

ECB_API_URL = 'https://open.er-api.com/v6/latest/EUR'

DEFAULT_RATES = {
    'EUR': 1.0,
    'USD': 1.09,
    'GBP': 0.86,
    'CHF': 0.95,
    'MAD': 10.85,
    'TND': 3.40,
    'XOF': 655.96,
    'XAF': 655.96,
    'DZD': 147.50,
    'EGP': 33.50,
    'SAR': 4.09,
    'AED': 4.00,
    'CAD': 1.47,
    'AUD': 1.65,
    'JPY': 162.50,
    'CNY': 7.85,
    'INR': 90.50,
    'BRL': 5.35,
    'MXN': 18.80,
    'ZAR': 20.50,
    'NGN': 850.00,
    'KES': 165.00,
    'GHS': 13.50,
    'TRY': 31.50,
    'RUB': 98.00,
    'PLN': 4.35,
    'CZK': 25.20,
    'HUF': 385.00,
    'RON': 4.97,
    'SEK': 11.35,
    'NOK': 11.60,
    'DKK': 7.46,
}


def _load_from_cache_file():
    """Load raw cache data from file."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading exchange rate cache: {e}")
    return None


def _save_cache(rates):
    """Save exchange rates to cache file."""
    try:
        cache_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'rates': rates
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except Exception as e:
        logger.warning(f"Error saving exchange rate cache: {e}")


def _fetch_rates_from_api():
    """Fetch exchange rates from the API."""
    try:
        headers = {'User-Agent': 'ShabakaAdScreen/1.0'}
        response = requests.get(ECB_API_URL, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get('result') == 'success':
            rates = data.get('rates', {})
            _save_cache(rates)
            logger.info("Successfully fetched exchange rates from API")
            return rates
    except requests.RequestException as e:
        logger.warning(f"Error fetching exchange rates from API: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error fetching exchange rates: {e}")
    return None


def get_exchange_rates():
    """
    Get current exchange rates with EUR as base currency.
    First tries cache, then API (in background if stale), fallback to default rates.
    
    Returns:
        dict: Dictionary of currency codes to exchange rates
    """
    cache_data = _load_from_cache_file()

    if cache_data:
        try:
            timestamp = datetime.fromisoformat(cache_data.get('timestamp', '2000-01-01'))
            rates = cache_data.get('rates', {})

            # Check if cache is valid
            if datetime.utcnow() - timestamp < timedelta(hours=CACHE_DURATION_HOURS):
                return rates

            # Cache expired - return stale data but refresh in background
            logger.info("Exchange rate cache expired. Refreshing in background.")
            threading.Thread(target=_fetch_rates_from_api, daemon=True).start()
            return rates

        except Exception as e:
            logger.warning(f"Error parsing cache data: {e}")
    
    # Cache missing or invalid - fetch in background and return defaults to avoid blocking
    logger.info("Exchange rate cache missing. Fetching in background, returning defaults.")
    threading.Thread(target=_fetch_rates_from_api, daemon=True).start()
    
    return DEFAULT_RATES.copy()


def convert_currency(amount, from_currency, to_currency):
    """
    Convert an amount from one currency to another.
    
    Args:
        amount: The amount to convert
        from_currency: Source currency code (e.g., 'USD')
        to_currency: Target currency code (e.g., 'EUR')
    
    Returns:
        float: Converted amount
    """
    if from_currency == to_currency:
        return amount
    
    if amount == 0:
        return 0.0
    
    rates = get_exchange_rates()
    
    from_rate = rates.get(from_currency, 1.0)
    to_rate = rates.get(to_currency, 1.0)
    
    amount_in_eur = amount / from_rate
    result = amount_in_eur * to_rate
    
    return round(result, 2)


def convert_to_base_currency(amount, from_currency, base_currency='EUR'):
    """
    Convert an amount to the base currency (default EUR).
    
    Args:
        amount: The amount to convert
        from_currency: Source currency code
        base_currency: Target base currency (default: EUR)
    
    Returns:
        float: Amount in base currency
    """
    return convert_currency(amount, from_currency, base_currency)


def get_conversion_rate(from_currency, to_currency):
    """
    Get the conversion rate between two currencies.
    
    Args:
        from_currency: Source currency code
        to_currency: Target currency code
    
    Returns:
        float: Conversion rate
    """
    if from_currency == to_currency:
        return 1.0
    
    rates = get_exchange_rates()
    from_rate = rates.get(from_currency, 1.0)
    to_rate = rates.get(to_currency, 1.0)
    
    return round(to_rate / from_rate, 6)


def format_currency(amount, currency_code, include_symbol=True):
    """
    Format an amount with the appropriate currency symbol.
    
    Args:
        amount: The amount to format
        currency_code: Currency code
        include_symbol: Whether to include the currency symbol
    
    Returns:
        str: Formatted currency string
    """
    from utils.currencies import get_currency_by_code
    
    currency_info = get_currency_by_code(currency_code)
    symbol = currency_info.get('symbol', currency_code)
    
    if currency_code in ['JPY', 'KRW', 'VND', 'IDR', 'XOF', 'XAF']:
        formatted_amount = f"{int(amount):,}"
    else:
        formatted_amount = f"{amount:,.2f}"
    
    if include_symbol:
        if currency_code in ['EUR', 'GBP', 'JPY', 'CNY', 'INR', 'KRW']:
            return f"{symbol}{formatted_amount}"
        else:
            return f"{formatted_amount} {symbol}"
    
    return formatted_amount


def get_rates_last_updated():
    """Get the timestamp of when rates were last updated."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                return cache_data.get('timestamp')
    except Exception:
        pass
    return None


def refresh_rates():
    """
    Force refresh exchange rates from API.
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'rates_count': int (if success)
        }
    """
    try:
        rates = _fetch_rates_from_api()
        if rates:
            return {
                'success': True,
                'message': 'Exchange rates updated successfully',
                'rates_count': len(rates)
            }
        else:
            return {
                'success': False,
                'message': 'Failed to fetch rates from API, using cached or default rates'
            }
    except Exception as e:
        logger.error(f"Error refreshing rates: {e}")
        return {
            'success': False,
            'message': f'Error refreshing rates: {str(e)}'
        }


def calculate_revenue_in_base_currency(revenues_by_currency, base_currency='EUR'):
    """
    Calculate total revenue in base currency from revenues in multiple currencies.
    
    Args:
        revenues_by_currency: Dict of {currency_code: amount}
        base_currency: Target currency for totals
    
    Returns:
        dict: {
            'total': total in base currency,
            'by_currency': list of currency breakdowns,
            'base_currency': the base currency used
        }
    """
    from utils.currencies import get_currency_by_code
    
    total = 0.0
    currency_breakdown = []
    
    for currency_code, amount in revenues_by_currency.items():
        if amount is None or amount == 0:
            continue
            
        converted = convert_to_base_currency(amount, currency_code, base_currency)
        rate = get_conversion_rate(currency_code, base_currency)
        
        currency_info = get_currency_by_code(currency_code)
        
        currency_breakdown.append({
            'code': currency_code,
            'name': currency_info.get('name', currency_code),
            'symbol': currency_info.get('symbol', currency_code),
            'flag': currency_info.get('flag', ''),
            'original_amount': amount,
            'converted_amount': converted,
            'rate': rate
        })
        
        total += converted
    
    base_info = get_currency_by_code(base_currency)
    
    return {
        'total': round(total, 2),
        'by_currency': currency_breakdown,
        'base_currency': {
            'code': base_currency,
            'symbol': base_info.get('symbol', base_currency),
            'name': base_info.get('name', base_currency)
        }
    }
