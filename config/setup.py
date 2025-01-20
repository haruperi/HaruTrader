from datetime import timedelta
from controllers.data import *

# Config data
settings_filepath = "../config/settings.json"

# Data variables
interval_minutes = 5
time_shift=-3
trading_timeframe = f'M{interval_minutes}'
core_timeframe = "D1"
start_core=0
end_core=60
start_pos=0
end_pos=1440
range_start = datetime.now().strftime("%Y-%m-%d")
range_end = (datetime.now() - timedelta(days=end_core)).strftime("%Y-%m-%d")
start_date = "2023-12-01"
end_date = "2024-12-22"
test_symbol = "XAUUSD"

# Risk Variables
stop_adr_ratio = 3
max_risk_per_trade = 5
risk_base_amount = 1024

# Financial variables
correlation_period = 20  # Correlation period (Num of days for a rolling window)
volatility_period = 10  # Volatility period (Num of days for a rolling window)
confidence_level = 0.95
risk_threshold = 0.10  # Risk threshold for accepting new positions (10%)

# Technicals
fast_ma = 15
slow_ma = 60
ma_type = "wma"
df_col = "close"
rsi_period = 12
willpct_period = 6
adr_period = 10
strength_lookback_period = 144


# GLOBAL INIT
project_settings = get_project_settings(settings_filepath)     # Import settings
init_mt5 = initialize_mt5(project_settings)                    # Start MT5
init_symbols = enable_all_symbols(project_settings)            # Initialize Symbols
symbols = project_settings["mt5"]["symbols"]                        # Get symbol names
