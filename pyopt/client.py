import requests
import pandas as pd
from typing import List, Dict
from datetime import date, datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from fake_useragent import UserAgent

class PriceHistory():
    """
    A Class to fetch historical stock price data from NASDAQ's API.
    """

    def __init__(self, symbols: List[str], user_agent: UserAgent) -> None:
        """
        Initializes the PriceHistory client.
        
        Args:
            symbols (List[str]): A list of stock ticker symbols to fetch historical data for.
            user_agent (UserAgent): A UserAgent object to mimic a browser request.
        """
        self._api_url = 'https://api.nasdaq.com/api/quote'
        self._api_service = 'historical'
        self._symbols = symbols
        self.user_agent = user_agent
        self.price_data_frame = self._build_data_frames()

    def _build_url(self, symbol: str) -> str:
        """Builds the full URL for API request."""
        return f"{self._api_url}/{symbol}/{self._api_service}"

    def _build_data_frames(self) -> pd.DataFrame:
        """Builds a DataFrame with historical stock price data for all symbols."""
        all_data = []
        to_date = date.today()
        from_date = to_date - relativedelta(months=12)

        for symbol in self._symbols:
            stock_data = self._grab_prices(symbol, from_date, to_date)
            all_data += stock_data
        
        if not all_data:
            print("No data was retrieved. Please check API or symbols.")
            return pd.DataFrame()  # Return empty DataFrame if no data

        price_data_frame = pd.DataFrame(all_data)
        price_data_frame['date'] = pd.to_datetime(price_data_frame['date'])
        return price_data_frame

    def _grab_prices(self, symbol: str, from_date: date, to_date: date) -> List[Dict]:
        """Fetches historical price data for a single stock symbol."""
        url = self._build_url(symbol)
        limit = (to_date - from_date).days
        params = {
            'fromdate': from_date.isoformat(),
            'todate': to_date.isoformat(),
            'assetclass': 'stocks',
            'limit': limit
        }
        headers = {'user-agent': self.user_agent.random}

        try:
            response = requests.get(url, params=params, headers=headers)

            if response.ok:
                try:
                    historical_data = response.json()
                    print(f"API Response for {symbol}: {historical_data}")  # Debug print

                    # Check if `historical_data` has the expected structure
                    if (
                        historical_data is not None and
                        'data' in historical_data and
                        'tradesTable' in historical_data['data'] and
                        'rows' in historical_data['data']['tradesTable']
                    ):
                        return self._clean_data(historical_data['data']['tradesTable']['rows'], symbol)
                    else:
                        print(f"Unexpected data structure for {symbol}. Full response: {historical_data}")
                        return []  # Return empty if structure is not as expected

                except ValueError:
                    print(f"Error parsing JSON response for {symbol}. Response content: {response.text}")
                    return []

            else:
                print(f"Failed to fetch data for {symbol}. HTTP Status: {response.status_code}")
                return []

        except requests.RequestException as e:
            print(f"Request failed for {symbol}: {e}")
            return []



    def _clean_data(self, raw_data: List[Dict], symbol: str) -> List[Dict]:
        """Cleans the raw data received from NASDAQ API."""
        cleaned_data = []
        for row in raw_data:
            try:
                cleaned_row = {
                    'symbol': symbol,
                    'date': row['date'],
                    'close': float(row.get('close', '0').replace('$', '')),
                    'volume': int(row.get('volume', '0').replace(',', '')),
                    'open': float(row.get('open', '0').replace('$', '')),
                    'high': float(row.get('high', '0').replace('$', '')),
                    'low': float(row.get('low', '0').replace('$', ''))
                }
                cleaned_data.append(cleaned_row)
            except (ValueError, AttributeError) as e:
                print(f"Error cleaning row for {symbol}: {row}, Error: {e}")
                continue
        return cleaned_data


    def get_returns(self, start_date: datetime, end_date: datetime, symbol: str) -> pd.Series:
        """
        Gets the percentage returns for a given symbol and date range.
        
        Args:
            start_date (datetime): Start date for historical data
            end_date (datetime): End date for historical data
            symbol (str): The stock symbol to get returns for
            
        Returns:
            pd.Series: A series of percentage returns indexed by date
        """
        # Get historical data
        raw_data = self._grab_prices(symbol, start_date, end_date)
        
        # If no data was retrieved, return an empty Series
        if not raw_data:
            print(f"No data available for {symbol}. Returning empty Series.")
            return pd.Series(dtype="float64")
        
        # Convert raw data into DataFrame
        df = pd.DataFrame(raw_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Calculate and return the percentage returns
        returns = 100 * df['Close'].pct_change().dropna()
        return returns


# if __name__ == "__main__":
#     # Example usage:
#     user_agent = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
#     portfolio = ['AAPL', 'AMZN', 'MA', 'TXRH', 'CRM', 'MCO', 'VICI', 'XOM', 'MO']
    
#     # Initialize the PriceHistory class with the UserAgent object
#     price_history_client = PriceHistory(symbols=portfolio, user_agent=user_agent)
    
#     # Print the data frame with stock prices.
#     print(price_history_client.price_data_frame)
