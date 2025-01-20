import json
import os
from datetime import datetime
from typing import Optional
from tqdm import tqdm
import numpy as np
import pandas as pd
import MetaTrader5 as mt5

# Function to import settings from settings.json
def get_project_settings(import_filepath):
    """
    Function to import settings from settings.json
    :param import_filepath: path to settings.json
    :return: settings as a dictionary object
    """
    # Test the filepath to make sure it exists
    if os.path.exists(import_filepath):
        # If yes, import the file
        f = open(import_filepath, "r")
        # Read the information
        settings = json.load(f)
        # Close the file
        f.close()
        # Return the project settings
        return settings
    # Notify user if settings.json doesn't exist
    else:
        raise ImportError("settings.json does not exist at provided location")

# Function to start up MT5
def initialize_mt5(project_settings):
    """
    Function to run through the process of starting up MT5 and initializing symbols
    :param project_settings: json object of project settings
    :return: Boolean.
    True for Startup successful.
    False for Error in starting up.
    """
    # Attempt to start MT5
    # Ensure that all variables are set to the correct type
    username = project_settings['mt5']['username']
    username = int(username)
    password = project_settings['mt5']['password']
    server = project_settings['mt5']['server']
    pathway = project_settings['mt5']['pathway']

    # Attempt to initialize MT5
    try:
        mt5_init = mt5.initialize(
            login=username,
            password=password,
            server=server,
            path=pathway
        )
    except Exception as e:
        print(f"Error initializing MetaTrader 5: {e}")
        # I cover more advanced error handling in other courses, which are useful for troubleshooting
        mt5_init = False

    # If MT5 initialized, attempt to log in to MT5
    mt5_login = False
    if mt5_init:
        try:
            mt5_login = mt5.login(
                login=username,
                password=password,
                server=server
            )
        except Exception as e:
            print(f"Error logging into MetaTrader 5: {e}")
            mt5_login = False

    # Return the outcome to the user
    if mt5_login:
        return True
    # Default fail condition of not logged in
    return False


# Function to enable all the symbols in settings.json. This means you can trade more than one currency pair!
def enable_all_symbols(project_settings):
    """
    MT5 requires symbols to be initialized before they can be queried.
    This function does that by enabling all symbols provided in settings.
    :param project_settings: Json object of project settings
    :return: Boolean.
    True if enabled, False if not.
    """

    # Get Symbols specified in Settings
    my_symbols = project_settings["mt5"]['symbols']

    # Get all symbols from MT5
    mt5_symbols = mt5.symbols_get()

    # Create a set of all MT5 symbols for quick lookup
    mt5_symbols_set = {symbol.name for symbol in mt5_symbols}

    # Iterate through my_symbols to check if they exist in mt5_symbols
    for symbol in my_symbols:
        if symbol in mt5_symbols_set:
            # Attempt to initialize/enable the symbol
            result = mt5.symbol_select(symbol, True)
            if not result:
                print(f"Failed to enable {symbol}.")
        else:
            print(f"{symbol} does not exist in MT5 symbols. Please update symbol name.")
            return False

    # Default to return True
    return True


# Function to convert a timeframe string into a MetaTrader 5 friendly format
def set_query_timeframe(timeframe):
    """
    Function to implement a pseudo switch statement.
    While Python 3.10 and above implement switch, this makes it
    a slightly backwards compatible
    :param timeframe: string of timeframe
    :return: MT5 compliant timeframe
    """
    if timeframe == "M1":
        return mt5.TIMEFRAME_M1, 1
    elif timeframe == "M2":
        return mt5.TIMEFRAME_M2, 2
    elif timeframe == "M3":
        return mt5.TIMEFRAME_M3, 3
    elif timeframe == "M4":
        return mt5.TIMEFRAME_M4, 4
    elif timeframe == "M5":
        return mt5.TIMEFRAME_M5, 5
    elif timeframe == "M6":
        return mt5.TIMEFRAME_M6, 6
    elif timeframe == "M10":
        return mt5.TIMEFRAME_M10, 10
    elif timeframe == "M12":
        return mt5.TIMEFRAME_M12, 12
    elif timeframe == "M15":
        return mt5.TIMEFRAME_M15, 15
    elif timeframe == "M20":
        return mt5.TIMEFRAME_M20, 20
    elif timeframe == "M30":
        return mt5.TIMEFRAME_M30, 30
    elif timeframe == "H1":
        return mt5.TIMEFRAME_H1, 60
    elif timeframe == "H2":
        return mt5.TIMEFRAME_H2, 120
    elif timeframe == "H3":
        return mt5.TIMEFRAME_H3, 180
    elif timeframe == "H4":
        return mt5.TIMEFRAME_H4, 240
    elif timeframe == "H6":
        return mt5.TIMEFRAME_H6, 360
    elif timeframe == "H8":
        return mt5.TIMEFRAME_H8, 480
    elif timeframe == "H12":
        return mt5.TIMEFRAME_H12, 720
    elif timeframe == "D1":
        return mt5.TIMEFRAME_D1, 1440
    elif timeframe == "W1":
        return mt5.TIMEFRAME_W1, 10080
    elif timeframe == "MN1":
        return mt5.TIMEFRAME_MN1, 43200
    else:
        print(f"Incorrect timeframe provided. {timeframe}")
        raise ValueError


# Function to retrieve data from MT5
def fetch_data(symbol, timeframe,
               start_date: Optional[str] = None, end_date: Optional[str] = None,
               start_pos: Optional[int] = None, end_pos: Optional[int] = None):
    """
        Function to fetch historic data from MetaTrader 5
        :param symbol: string of the symbol to query
        :param timeframe: string of the timeframe to query
        :param start_date: string of starting date in a range
        :param end_date: string of ending date in a range
        :param start_pos: int of starting position
        :param end_pos: int of ending position
        :return: dataframe of the queried data
        """
    # Convert the timeframe into MT5 friendly format
    mt5_timeframe, time_delta = set_query_timeframe(timeframe=timeframe)

    # Convert dates to datetime objects
    start = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
    end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

    # Get Candles
    if start and end:
        rates = mt5.copy_rates_range(symbol, mt5_timeframe, start, end)
    else:
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, start_pos or 0, end_pos or 100)

    # Verify that rates contain data
    if rates is None or len(rates) == 0:
        raise ValueError(f"No data fetched for symbol {symbol} within the specified range.")

    # Convert to a dataframe
    dataframe = pd.DataFrame(rates)

    # Verify that the expected 'time' field is in the dataframe
    if 'time' not in dataframe:
        raise KeyError("'time' column is missing in the fetched data.")

    # Convert Datetime to be human-readable
    dataframe['datetime'] = pd.to_datetime(dataframe['time'], unit='s')
    # Set Index of the dataframe
    dataframe.set_index('datetime', inplace=True)
    # Delete unwanted columns
    dataframe = dataframe[["open", "high", "low", "close", "tick_volume"]]

    return dataframe


def find_timestamp_extremum(df, df_lower_timeframe):
    """
    :param: df_lowest_timeframe
    :return: self._data with three new columns: Low_time (TimeStamp), High_time (TimeStamp), High_first (Boolean)
    """
    df = df.copy()
    df = df.loc[df_lower_timeframe.index[0]:]

    # Set new columns
    df["low_time"] = np.nan
    df["high_time"] = np.nan

    # Loop to find out which of the high or low appears first
    for i in tqdm(range(len(df) - 1)):

        # Extract values from the lowest timeframe dataframe
        start = df.iloc[i:i + 1].index[0]
        end = df.iloc[i + 1:i + 2].index[0]
        row_lowest_timeframe = df_lower_timeframe.loc[start:end].iloc[:-1]

        # Extract Timestamp of the max and min over the period (highest timeframe)
        try:
            high = row_lowest_timeframe["high"].idxmax()
            low = row_lowest_timeframe["low"].idxmin()

            df.loc[start, "low_time"] = low
            df.loc[start, "high_time"] = high

        except Exception as e:
            print(e)
            df.loc[start, "low_time"] = None
            df.loc[start, "high_time"] = None

    # Verify the number of row without both TP and SL on same time
    percentage_good_row = len(df.dropna()) / len(df) * 100
    percentage_garbage_row = 100 - percentage_good_row

    # if percentage_garbage_row<95:
    print(f"WARNINGS: Garbage row: {'%.2f' % percentage_garbage_row} %")

    df = df.iloc[:-1]

    return df

def merge_symbols(symbols, trading_timeframe, start_date, end_date):
    data = pd.DataFrame()

    for symbol in symbols:
        df = fetch_data(symbol, trading_timeframe, start_date, end_date)

        # Ensure the DataFrame has a "close" column and a datetime index
        if "close" not in df.columns:
            raise ValueError(f"DataFrame for {symbol} does not have a 'close' column.")

        if data.empty:
            # Initialize the merged DataFrame with the first symbol's data
            data = df[["close"]].rename(columns={"close": symbol})
        else:
            # Merge on the index, renaming "close" to the symbol name
            data = data.join(df[["close"]].rename(columns={"close": symbol}), how="outer")

    data.to_csv("merged_data.csv")

    return data