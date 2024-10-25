import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime


def calculate_trading_strategy(index='SPX', tax_rate=0.25, lev=1):
    # Dictionary mapping index names to their Yahoo Finance tickers
    index_tickers = {
        'DAX': '^GDAXI',
        'S&P 500': '^GSPC',
        'Dow Jones': '^DJI',
        'Nasdaq 100': '^NDX'
    }

    # Validate index input
    if index not in index_tickers:
        raise ValueError("Invalid index. Choose from: DAX, S&P 500, Dow Jones, Nasdaq 100")

    # Download historical data
    start_date = '1988-01-01'
    end_date = datetime.today().strftime('%Y-%m-%d')

    # Get index data
    index_data = yf.download(index_tickers[index], start=start_date, end=end_date)['Close']

    # Get gold data (GLD ETF as proxy)
    gold_data = yf.download('GC=F', start=start_date, end=end_date)['Close']

    # Create initial dataframe
    df = pd.DataFrame({
        'index_price': index_data,
        'gold_price': gold_data
    })

    # Calculate 200-day moving average for index
    df['ma_200'] = df['index_price'].rolling(window=200).mean()

    # Remove rows with NaN values in MA column
    df = df.dropna()

    # Calculate daily returns
    df['index_return'] = df['index_price'].pct_change()
    df['gold_return'] = df['gold_price'].pct_change()

    # Remove first row which will have NaN returns
    df = df.dropna()

    # Initialize portfolio value column
    df['portfolio_value'] = 100

    # Determine which asset to hold based on MA strategy
    df['position'] = np.where(df['index_price'].shift(1) < df['ma_200'], 'gold', 'index')

    # Initialize variables for tracking regime changes
    last_regime_change_idx = 0
    last_regime_change_value = 100

    # Calculate portfolio values
    for i in range(1, len(df)):
        # Get current position and previous position
        current_position = df['position'].iloc[i]
        prev_position = df['position'].iloc[i - 1]

        # Determine which return to use
        if current_position == 'gold':
            daily_return = df['gold_return'].iloc[i]
        else:
            daily_return = df['index_return'].iloc[i]

        # Calculate new portfolio value before tax consideration
        new_value = df['portfolio_value'].iloc[i - 1] * (1 + daily_return)

        # Check for regime change
        if current_position != prev_position:
            # Calculate gain since last regime change
            gain = new_value - last_regime_change_value

            # Apply tax if there's a positive gain
            if gain > 0:
                tax_amount = gain * tax_rate
                new_value -= tax_amount

            # Update regime change tracking variables
            last_regime_change_idx = i
            last_regime_change_value = new_value

        # Update portfolio value
        df.iloc[i, df.columns.get_loc('portfolio_value')] = new_value

    # Calculate average yearly return
    total_years = len(df) / 252  # Assuming 252 trading days per year
    total_return = (df['portfolio_value'].iloc[-1] / df['portfolio_value'].iloc[0]) - 1
    avg_yearly_return = (1 + total_return) ** (1 / total_years) - 1

    return avg_yearly_return


def main():
    # Example usage
    avg_yearly_return = calculate_trading_strategy(
        index='S&P 500',
        tax_rate=0,
        lev=1
    )
    print(f"Average yearly return: {avg_yearly_return:.2%}")


if __name__ == "__main__":
    main()