import asyncio
import logging
import yfinance as yf
from typing import List, Dict, Any
from backend.pipeline.notebook_client import notebook_client

logger = logging.getLogger(__name__)

class PortfolioMonitor:
    def __init__(self):
        self.is_running = False

    async def start_monitoring(self, interval_seconds: int = 3600):
        """
        Starts the background monitoring loop.
        """
        if self.is_running:
            return
        
        self.is_running = True
        logger.info(f"--- [LAYER 7] Starting Portfolio Performance Monitor (Interval: {interval_seconds}s) ---")
        
        while self.is_running:
            try:
                await self.update_portfolio_performance()
            except Exception as e:
                logger.error(f"Error in portfolio monitor loop: {e}")
            
            await asyncio.sleep(interval_seconds)

    async def update_portfolio_performance(self):
        """
        Updates the current prices and ROI for all active signals.
        """
        logger.info("--- [LAYER 7] Updating Portfolio Performance Metrics ---")
        
        signals = await notebook_client.get_portfolio_signals()
        active_signals = [s for s in signals if s['status'] == 'ACTIVE']
        
        if not active_signals:
            logger.info("No active signals to update.")
            return

        updates = []
        for signal in active_signals:
            ticker = signal['ticker']
            try:
                # Fetch current price via yfinance
                ticker_data = yf.Ticker(ticker)
                # Use fast_info to get the latest price without a full download
                current_price = ticker_data.fast_info.get('last_price')
                
                if not current_price:
                    # Fallback to history if fast_info fails
                    hist = ticker_data.history(period="1d")
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                
                if current_price:
                    entry_price = signal['entry_price']
                    action = signal['action']
                    
                    # Calculate ROI based on action
                    if action == 'BUY':
                        roi = ((current_price - entry_price) / entry_price) * 100
                    elif action == 'SELL':
                        roi = ((entry_price - current_price) / entry_price) * 100
                    else:
                        roi = 0.0
                    
                    updates.append({
                        "signal_id": signal['signal_id'],
                        "current_price": float(current_price),
                        "roi": float(roi)
                    })
                    logger.info(f"Updated {ticker}: Price ${current_price:.2f}, ROI {roi:.2f}%")
            except Exception as e:
                logger.error(f"Failed to update price for {ticker}: {e}")

        if updates:
            await notebook_client.update_signal_prices(updates)

portfolio_monitor = PortfolioMonitor()
