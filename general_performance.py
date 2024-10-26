import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime


def analyze_leveraged_portfolio(ticker_choice, signal_asset, leverage, position='over', direction='long'):
    if position.lower() not in ['over', 'under']:
        raise ValueError("Position muss 'over' oder 'under' sein")
    if direction.lower() not in ['long', 'short']:
        raise ValueError("Direction muss 'long' oder 'short' sein")

    # Dictionary für die Ticker-Symbole
    ticker_map = {
        "s&p 500": "^GSPC",
        "dax": "^GDAXI",
        "nasdaq 100": "^NDX",
        "dow jones": "^DJI",
        "gold": "GC=F",
        "bitcoin": "BTC-USD"
    }

    # Ticker-Symbole auswählen
    ticker = ticker_map.get(ticker_choice.lower())
    signal_ticker = ticker_map.get(signal_asset.lower())
    if not ticker:
        raise ValueError(
            "Ungültige Auswahl für Trading Asset. Bitte wählen Sie aus: S&P 500, DAX, NASDAQ 100, Dow Jones, Gold, Bitcoin")
    if not signal_ticker:
        raise ValueError(
            "Ungültige Auswahl für Signal Asset. Bitte wählen Sie aus: S&P 500, DAX, NASDAQ 100, Dow Jones, Gold, Bitcoin")

    # DataFrame für Signal Asset als Referenz erstellen
    df_ref = pd.DataFrame()
    signal_data = yf.download(signal_ticker, start="1900-01-01")
    df_ref['reference'] = signal_data['Close']

    # 200 Tage MA vom Signal Asset berechnen
    df_ref['ma200'] = df_ref['reference'].rolling(window=200).mean()

    # Erste 199 Zeilen löschen
    df_ref = df_ref.iloc[199:]

    # Regime-Spalte erstellen (True wenn über MA200)
    df_ref['regime'] = df_ref['reference'] > df_ref['ma200']

    # Gewählten Trading Index laden
    index_data = yf.download(ticker, start="1900-01-01")
    df_index = pd.DataFrame()
    df_index['price'] = index_data['Close']

    # DataFrames auf Basis der Daten mergen
    df = pd.merge(df_ref, df_index, left_index=True, right_index=True, how='left')

    # Zeilen mit NA im Index löschen
    df = df.dropna(subset=['price'])

    # Tägliche Returns berechnen
    df['daily_return'] = df['price'].pct_change()

    # Returns basierend auf Long/Short anpassen
    if direction.lower() == 'short':
        df['direction_return'] = -df['daily_return']
    else:  # 'long'
        df['direction_return'] = df['daily_return']

    # Gehebelte Returns berechnen
    df['leveraged_return'] = df['direction_return'] * leverage

    # Portfolio-Wert berechnen
    df['portfolio'] = 0.0  # Initialisieren
    df['portfolio'].iloc[0] = 100  # Startwert

    # Portfolio-Werte basierend auf Regime und Position berechnen
    for i in range(1, len(df)):
        prev_value = df['portfolio'].iloc[i - 1]
        if position.lower() == 'over':
            # Wenn "over", dann leveraged_return wenn über MA200, sonst 0
            return_today = df['leveraged_return'].iloc[i] if df['regime'].iloc[i - 1] else 0
        else:
            # Wenn "under", dann leveraged_return wenn unter MA200, sonst 0
            return_today = df['leveraged_return'].iloc[i] if not df['regime'].iloc[i - 1] else 0
        df['portfolio'].iloc[i] = prev_value * (1 + return_today)

    # Buy & Hold Portfolio zum Vergleich
    df['buy_hold'] = 100 * (1 + df['daily_return']).cumprod()
    df['buy_hold_leveraged'] = 100 * (1 + df['leveraged_return']).cumprod()

    # Jahre berechnen
    years = (df.index[-1] - df.index[0]).days / 365.25

    # Performance Metriken berechnen
    def calculate_annual_return(final_value, initial_value=100):
        return (final_value / initial_value) ** (1 / years) - 1

    results = {
        'Buy & Hold Portfolio': {
            'Finaler Wert': round(df['buy_hold'].iloc[-1], 2),
            'Jährliche Rendite': f'{round(calculate_annual_return(df["buy_hold"].iloc[-1]) * 100, 2)}%'
        },
        'Buy & Hold Leveraged': {
            'Finaler Wert': round(df['buy_hold_leveraged'].iloc[-1], 2),
            'Jährliche Rendite': f'{round(calculate_annual_return(df["buy_hold_leveraged"].iloc[-1]) * 100, 2)}%'
        },
        'Strategy Portfolio': {
            'Finaler Wert': round(df['portfolio'].iloc[-1], 2),
            'Jährliche Rendite': f'{round(calculate_annual_return(df["portfolio"].iloc[-1]) * 100, 2)}%'
        },
        'Analysezeitraum': f'{df.index[0].strftime("%Y-%m-%d")} bis {df.index[-1].strftime("%Y-%m-%d")}',
        'Strategie': f'{direction.upper()} Trading {ticker_choice} wenn {signal_asset} {"über" if position.lower() == "over" else "unter"} seiner MA200',
        'Hebel': leverage,
        'Signal Asset über MA200': f'{(df["regime"].sum() / len(df) * 100):.1f}%',
        'Signal Asset unter MA200': f'{((1 - df["regime"].sum() / len(df)) * 100):.1f}%'
    }

    return results, df

# Test
# Beispiel: SHORT Trading Bitcoin mit 3x Hebel wenn S&P 500 über MA200
results, data = analyze_leveraged_portfolio("bitcoin", "bitcoin", 1, "under", "short")
print(results)