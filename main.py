import os
import logging
from dotenv import load_dotenv
from app.config.settings import setup_logging
from app.dashboard.app import create_app
from app.live_trading.executor import LiveTrader

# Load environment variables
load_dotenv()

def main():
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting HaruTrader...")

    try:
        # Initialize the live trading system
        trader = LiveTrader()
        
        # Create and run the dashboard
        app = create_app()
        
        # Start the trading system
        trader.start()
        
        # Run the dashboard
        app.run(
            host=os.getenv("DASHBOARD_HOST", "0.0.0.0"),
            port=int(os.getenv("DASHBOARD_PORT", 5000))
        )
    
    except Exception as e:
        logger.error(f"Error starting HaruTrader: {e}")
        raise

if __name__ == "__main__":
    main() 