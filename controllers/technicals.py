import ta
from config.setup import *

# Basic Indicators functions
# Moving Average
def moving_average(df, ma_type, col, period):
    if ma_type == 'sma':
        df[f"SMA_{period}"] = ta.trend.SMAIndicator(df[col], int(period)).sma_indicator()
    if ma_type == 'ema':
        df[f"EMA_{period}"] = ta.trend.EMAIndicator(df[col], int(period)).ema_indicator()
    if ma_type == 'wma':
        df[f"WMA_{period}"] = ta.trend.WMAIndicator(df[col], int(period)).wma()
    return df

def rsi(df, col, period):
    df[f"RSI"] = ta.momentum.RSIIndicator(df[col], int(period)).rsi()
    return df

def williams_percent(df, period):
    df["WPR"] = ta.momentum.williams_r(df.high, df.low, df.close, int(period))
    return df

def atr(df, period):
    df['ATR'] = ta.volatility.AverageTrueRange(df.high, df.low, df.close, window=period, fillna=False).average_true_range()
    return df

def ma_trend_signal(df, fastMa, slowMA):
    """
    This function analyzes the TREND UP signal using WMA (12) and WMA (144) along with Williams %R (6)
    """
    # Calculate WMA
    df['Fast_LWMA'] = ta.trend.WMAIndicator(df['close'], int(fastMa)).wma()
    df['Slow_LWMA'] = ta.trend.WMAIndicator(df['close'], int(slowMA)).wma()

    # Calculate Williams %R
    df['Williams %R'] = ta.momentum.williams_r(df.high, df.low, df.close, int(6))

    # Create Signal column based on previous row's values including crossover logic
    df['Signal'] = 0

    for i in range(1, len(df)):
        # Buy signal
        df.loc[(df['close'].shift(i+1) > df['Fast_LWMA'].shift(i+1))
           & (df['close'].shift(i+1) > df['Slow_LWMA'].shift(i+1))
           & (df['Williams %R'].shift(i+1) > -20)
           & (df['Williams %R'].shift(i+2) <= -20), 'Signal'] = 1

        # Sell signal
        df.loc[(df['close'].shift(i+1) < df['Fast_LWMA'].shift(i+1))
           & (df['close'].shift(i+1) < df['Slow_LWMA'].shift(i+1))
           & (df['Williams %R'].shift(i+1) < -80)
           & (df['Williams %R'].shift(i+2) >= -80), 'Signal'] = -1

        return df

def live_ma_trend_signal(df, fastMa, slowMA):
    """
    This function analyzes the TREND UP signal using WMA (12) and WMA (144) along with Williams %R (6)
    """
    # Calculate WMA
    df['Fast_LWMA'] = ta.trend.WMAIndicator(df['close'], int(fastMa)).wma()
    df['Slow_LWMA'] = ta.trend.WMAIndicator(df['close'], int(slowMA)).wma()

    # Calculate Williams %R
    df['Williams %R'] = ta.momentum.williams_r(df.high, df.low, df.close, int(6))

    # Create Signal column based on previous row's values including crossover logic
    df['Signal'] = 0
    # Buy signal
    df.loc[(df['close'].shift(1) > df['Fast_LWMA'].shift(1))
           & (df['close'].shift(1) > df['Slow_LWMA'].shift(1))
           & (df['Williams %R'].shift(1) > -20)
           & (df['Williams %R'].shift(2) <= -20), 'Signal'] = 1
    # Sell signal
    df.loc[(df['close'].shift(1) < df['Fast_LWMA'].shift(1))
           & (df['close'].shift(1) < df['Slow_LWMA'].shift(1))
           & (df['Williams %R'].shift(1) < -80)
           & (df['Williams %R'].shift(2) >= -80), 'Signal'] = -1

    last_signal = df['Signal'].iloc[-1]

    if last_signal == 1:
        return "buy"
    elif last_signal == -1:
        return "sell"
    else:
        return "neutral"

def williamsPCT_signal(df, symbolName):
    """
    This function gets the momentum signal based on the Williams %R (6)
    """

    # Calculate Williams %R
    df['Williams %R'] = ta.momentum.williams_r(df.high, df.low, df.close, int(6))

    # Create Signal column based on previous row's values including crossover logic
    df['Signal'] = 0

    df.loc[(df['Williams %R'].shift(1) > -20) & (df['Williams %R'].shift(2) <= -20), 'Signal'] = 1 # Buy signal
    df.loc[(df['Williams %R'].shift(1) < -80) & (df['Williams %R'].shift(2) >= -80), 'Signal'] = -1 # Sell signal
    last_signal = df['Signal'].iloc[-1]

    if last_signal == 1:
        return f"{symbolName} Buy"
    elif last_signal == -1:
        return f"{symbolName} Sell"
    else:
        return "Neutral"

def swing_line(df):
    """
            Identify swing direction by tracking highs and lows.
            """
    df["upswing"] = 0
    highest_high = df["high"].iloc[0]
    lowest_low = df["low"].iloc[0]

    for i in range(1, len(df)):
        current_high = df["high"].iloc[i]
        current_low = df["low"].iloc[i]

        if upswing == 1:  # Uptrend
            if current_high > highest_high:
                highest_high = current_high
            if current_low > highest_low:
                highest_low = current_low
            if current_high < highest_low:  # Swing change to downtrend
                upswing = -1
                lowest_low = current_low
                lowest_high = current_high
        else:  # Downtrend
            if current_low < lowest_low:
                lowest_low = current_low
            if current_high < lowest_high:
                lowest_high = current_high
            if current_low > lowest_high:  # Swing change to uptrend
                upswing = 1
                highest_high = current_high
                highest_low = current_low

        df.at[df.index[i], "upswing"] = upswing
    return df


def find_swing_direction(data):
    """
    Identifies swing direction and updates swing variables.

    :param data: DataFrame with 'high' and 'low' columns.
    :return: DataFrame with updated swing direction (upswing) and swing variables.
    """
    # Initialize swing variables
    highest_high = data['high'].iloc[0]
    lowest_low = data['low'].iloc[0]
    lowest_high = data['high'].iloc[0]
    highest_low = data['low'].iloc[0]
    upswing = 0  # 0 for downtrend, 1 for uptrend

    # Initialize swing columns
    data['upswing'] = -1
    data['highest_high'] = highest_high
    data['lowest_low'] = lowest_low
    data['lowest_high'] = lowest_high
    data['highest_low'] = highest_low

    # Iteratively update swing variables
    for i in range(1, len(data)):
        current_high = data['high'].iloc[i]
        current_low = data['low'].iloc[i]

        if upswing == 1:  # Uptrend
            if current_high > highest_high:
                highest_high = current_high
            if current_low > highest_low:
                highest_low = current_low
            if current_high < highest_low:  # Swing change to downtrend
                upswing = -1
                lowest_low = current_low
                lowest_high = current_high

        elif upswing == -1:  # Downtrend
            if current_low < lowest_low:
                lowest_low = current_low
            if current_high < lowest_high:
                lowest_high = current_high
            if current_low > lowest_high:  # Swing change to uptrend
                upswing = 1
                highest_high = current_high
                highest_low = current_low

        # Update DataFrame with swing variables
        data.at[data.index[i], 'upswing'] = upswing
        data.at[data.index[i], 'highest_high'] = highest_high
        data.at[data.index[i], 'lowest_low'] = lowest_low
        data.at[data.index[i], 'lowest_high'] = lowest_high
        data.at[data.index[i], 'highest_low'] = highest_low

    return data


def calculate_currency_strength(pair_symbols, timeframe, strength_lookback, strength_rsi, strength_loc):
    data = pd.DataFrame()
    for symbol in pair_symbols:
        df = fetch_data(symbol, timeframe, start_pos=0, end_pos=strength_lookback)
        df = rsi(df, 'close', strength_rsi)
        data[symbol] = df['RSI']

    strength = pd.DataFrame()
    strength["USD"] = 1 / 7 * ((100 - data.EURUSD) + (100 - data.GBPUSD) + data.USDCAD + data.USDJPY + (100 - data.NZDUSD) + (100 - data.AUDUSD) + data.USDCHF)
    strength["EUR"] = 1 / 7 * (data.EURUSD + data.EURGBP + data.EURAUD + data.EURNZD + data.EURCHF + data.EURCAD)
    strength["GBP"] = 1 / 7 * (data.GBPUSD + data.GBPJPY + data.GBPAUD + data.GBPNZD + data.GBPCAD + data.GBPCHF + (100 - data.EURGBP))
    strength["CHF"] = 1 / 7 * ((100 - data.EURCHF) + (100 - data.GBPCHF) + (100 - data.NZDCHF) + (100 - data.AUDCHF) + (100 - data.CADCHF) +  data.CHFJPY + (100 - data.USDCHF))
    strength["JPY"] = 1 / 7 * ((100 - data.EURJPY) + (100 - data.GBPJPY) + (100 - data.USDJPY) + (100 - data.CHFJPY) + (100 - data.CADJPY) + (100 - data.NZDJPY) + (100 - data.AUDJPY))
    strength["AUD"] = 1 / 7 * ((100 - data.EURAUD) + (100 - data.GBPAUD) + (100 - data.AUDJPY) + data.AUDNZD + data.AUDCAD + data.AUDCHF + data.AUDUSD)
    strength["CAD"] = 1 / 7 * ((100 - data.EURCAD) + (100 - data.GBPCAD) + (100 - data.USDCAD) + data.CADJPY + (100 - data.AUDCAD) + (100 - data.NZDCAD) + data.CADCHF)
    strength["NZD"] = 1 / 7 * ((100 - data.EURNZD) + (100 - data.GBPNZD) + data.NZDJPY + data.NZDUSD + data.NZDCAD + data.NZDCHF + (100 - data.AUDNZD))
    strength_df = strength.iloc[-strength_loc].apply(lambda x: x - 50).round(2).sort_values(ascending=False)
    return strength_df


def evaluate_live_signal(signal):
    """
    Evaluates a buy/sell signal based on currency strength differences.

    Parameters:
        signal (str): The trading signal in the format 'EURUSD Buy' or 'EURUSD Sell'.
        currency_strengths (dict): A dictionary with currency codes as keys and their strengths as values.

    Returns:
        str: 'Valid' if the signal meets the criteria, 'Excluded' otherwise.
    """
    try:
        # Parse the signal
        pair, action = signal.split()
        base_currency = pair[:3]
        quote_currency = pair[3:]

        currency_strengths = calculate_currency_strength(symbols, timeframe=trading_timeframe,
                                                    strength_lookback=strength_lookback_period, strength_rsi=rsi_period,
                                                    strength_loc=2)

        # Get strengths for the base and quote currencies
        base_strength = currency_strengths[base_currency]
        quote_strength = currency_strengths[quote_currency]

        if base_strength is None or quote_strength is None:
            return "Excluded: Invalid currency pair or missing strength data"

        # Calculate strength difference
        strength_diff = abs(base_strength - quote_strength)

        # Check criteria
        if (
                strength_diff > 10
                and ((base_strength > 0 > quote_strength) if action == "Buy" else (quote_strength > 0 > base_strength))
        ):
            return "Valid"
        else:
            return "Excluded: Strength criteria not met"
    except Exception as e:
        return f"Error: {str(e)}"

