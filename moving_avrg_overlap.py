import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime


def calculate_ma_correlation(ma_period=200):
    # Dictionary für die Ticker-Symbole
    ticker_map = {
        "S&P 500": "^GSPC",
        "DAX": "^GDAXI",
        "NASDAQ 100": "^NDX",
        "Gold": "GC=F",
        "Bitcoin": "BTC-USD"
    }

    # DataFrame für die Regime-Daten erstellen
    regimes = pd.DataFrame()

    # Für jedes Asset Moving Average und Regime berechnen
    for name, ticker in ticker_map.items():
        # Daten laden
        data = yf.download(ticker, start="1900-01-01")

        # Moving Average berechnen
        data['MA'] = data['Close'].rolling(window=ma_period).mean()

        # Regime bestimmen (True wenn über MA)
        data['Regime'] = data['Close'] > data['MA']

        # Zum Regime DataFrame hinzufügen
        regimes[name] = data['Regime']

    # Leere Matrix für die Ergebnisse erstellen
    assets = list(ticker_map.keys())
    n_assets = len(assets)
    correlation_matrix = pd.DataFrame(np.zeros((n_assets, n_assets)),
                                      columns=assets,
                                      index=assets)

    # Matrix füllen
    for i in range(n_assets):
        for j in range(n_assets):
            # Gemeinsame Zeiträume finden
            mask = regimes[assets[i]].notna() & regimes[assets[j]].notna()

            if i == j:
                correlation_matrix.iloc[i, j] = 1.0
            else:
                # Berechne den Anteil der Zeit, wo beide Assets im gleichen Regime sind
                same_regime = (regimes[assets[i]][mask] == regimes[assets[j]][mask])
                correlation = same_regime.mean()
                correlation_matrix.iloc[i, j] = round(correlation, 3)

    # Zusätzliche Informationen berechnen
    info = {}
    for asset in assets:
        mask = regimes[asset].notna()
        if mask.any():
            total_days = mask.sum()
            days_above = regimes[asset][mask].sum()
            days_below = total_days - days_above

            info[asset] = {
                'Zeitraum': f"{regimes[asset][mask].index[0].strftime('%Y-%m-%d')} bis {regimes[asset][mask].index[-1].strftime('%Y-%m-%d')}",
                'Tage über MA': f"{(days_above / total_days * 100):.1f}%",
                'Tage unter MA': f"{(days_below / total_days * 100):.1f}%",
                'Gesamte Tage': total_days
            }

    return correlation_matrix, info

# Beispielaufruf
matrix, info = calculate_ma_correlation(200)
print("\nKorrelationsmatrix der MA-Signale:")
print(matrix)
print("\nZusätzliche Informationen:")
for asset, details in info.items():
    print(f"\n{asset}:")
    for key, value in details.items():
        print(f"{key}: {value}")