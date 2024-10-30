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

    # Gemeinsame Zeiträume für alle drei Assets finden
    common_mask = (regimes['S&P 500'].notna() &
                   regimes['Gold'].notna() &
                   regimes['Bitcoin'].notna())

    if common_mask.any():
        total_common_days = common_mask.sum()

        # Analyse für gleiche Regime (über oder unter)
        all_same = ((regimes['S&P 500'][common_mask] == regimes['Gold'][common_mask]) &
                    (regimes['Gold'][common_mask] == regimes['Bitcoin'][common_mask]))
        all_same_pct = round(all_same.mean() * 100, 1)

        gold_btc_same = ((regimes['Gold'][common_mask] == regimes['Bitcoin'][common_mask]) &
                         (regimes['Gold'][common_mask] != regimes['S&P 500'][common_mask]))
        gold_btc_same_pct = round(gold_btc_same.mean() * 100, 1)

        sp_gold_same = ((regimes['S&P 500'][common_mask] == regimes['Gold'][common_mask]) &
                        (regimes['Gold'][common_mask] != regimes['Bitcoin'][common_mask]))
        sp_gold_same_pct = round(sp_gold_same.mean() * 100, 1)

        sp_btc_same = ((regimes['S&P 500'][common_mask] == regimes['Bitcoin'][common_mask]) &
                       (regimes['Bitcoin'][common_mask] != regimes['Gold'][common_mask]))
        sp_btc_same_pct = round(sp_btc_same.mean() * 100, 1)

        # Analyse speziell für "Unter MA" Szenarien
        all_under = ((~regimes['S&P 500'][common_mask]) &
                     (~regimes['Gold'][common_mask]) &
                     (~regimes['Bitcoin'][common_mask]))
        all_under_pct = round(all_under.mean() * 100, 1)

        gold_btc_under = ((~regimes['Gold'][common_mask]) &
                          (~regimes['Bitcoin'][common_mask]) &
                          (regimes['S&P 500'][common_mask]))
        gold_btc_under_pct = round(gold_btc_under.mean() * 100, 1)

        sp_gold_under = ((~regimes['S&P 500'][common_mask]) &
                         (~regimes['Gold'][common_mask]) &
                         (regimes['Bitcoin'][common_mask]))
        sp_gold_under_pct = round(sp_gold_under.mean() * 100, 1)

        sp_btc_under = ((~regimes['S&P 500'][common_mask]) &
                        (~regimes['Bitcoin'][common_mask]) &
                        (regimes['Gold'][common_mask]))
        sp_btc_under_pct = round(sp_btc_under.mean() * 100, 1)

        # Bedingte Wahrscheinlichkeiten berechnen
        # Gesamtanzahl Tage, an denen S&P 500 unter MA ist
        sp_under_days = (~regimes['S&P 500'][common_mask]).sum()

        if sp_under_days > 0:
            # Tage zählen, an denen S&P 500 UND Gold unter MA sind
            sp_and_gold_under = ((~regimes['S&P 500'][common_mask]) &
                                 (~regimes['Gold'][common_mask])).sum()

            # Tage zählen, an denen S&P 500 UND Bitcoin unter MA sind
            sp_and_btc_under = ((~regimes['S&P 500'][common_mask]) &
                                (~regimes['Bitcoin'][common_mask])).sum()

            # Tage zählen, an denen ALLE drei unter MA sind
            all_three_under = ((~regimes['S&P 500'][common_mask]) &
                               (~regimes['Gold'][common_mask]) &
                               (~regimes['Bitcoin'][common_mask])).sum()

            # Bedingte Wahrscheinlichkeiten berechnen
            gold_under_prob = sp_and_gold_under / sp_under_days
            btc_under_prob = sp_and_btc_under / sp_under_days
            both_under_prob = all_three_under / sp_under_days

            conditional_probabilities = {
                'Gegeben S&P 500 unter MA': {
                    'Gold auch unter MA': f"{round(gold_under_prob * 100, 1)}%",
                    'Bitcoin auch unter MA': f"{round(btc_under_prob * 100, 1)}%",
                    'Beide auch unter MA': f"{round(both_under_prob * 100, 1)}%",
                    'Anzahl Tage S&P unter MA': sp_under_days,
                    'Anteil Tage S&P unter MA': f"{round(sp_under_days / len(common_mask) * 100, 1)}%"
                }
            }
        else:
            conditional_probabilities = {
                'Fehler': 'Keine Tage gefunden, an denen S&P 500 unter MA war'
            }

        special_combinations = {
            'Gleiche Regime (über oder unter)': {
                'Alle drei gleich': f"{all_same_pct}%",
                'Gold & BTC gleich, S&P anders': f"{gold_btc_same_pct}%",
                'S&P & Gold gleich, BTC anders': f"{sp_gold_same_pct}%",
                'S&P & BTC gleich, Gold anders': f"{sp_btc_same_pct}%"
            },
            'Unter MA Szenarien': {
                'Alle drei unter MA': f"{all_under_pct}%",
                'Nur Gold & BTC unter MA': f"{gold_btc_under_pct}%",
                'Nur S&P & Gold unter MA': f"{sp_gold_under_pct}%",
                'Nur S&P & BTC unter MA': f"{sp_btc_under_pct}%"
            },
            'Bedingte Wahrscheinlichkeiten': conditional_probabilities,
            'Zeitraum': {
                'Gemeinsamer Zeitraum': f"{regimes[common_mask].index[0].strftime('%Y-%m-%d')} bis {regimes[common_mask].index[-1].strftime('%Y-%m-%d')}",
                'Anzahl gemeinsamer Tage': total_common_days
            }
        }
    else:
        special_combinations = {
            'Fehler': 'Keine gemeinsamen Daten für alle drei Assets gefunden'
        }

    return correlation_matrix, info, special_combinations


def print_results(ma_period=200):
    matrix, info, special = calculate_ma_correlation(ma_period)

    print(f"\nAnalyse für {ma_period}-Tage Moving Average")
    print("\nKorrelationsmatrix der MA-Signale:")
    print(matrix)

    print("\nZusätzliche Informationen je Asset:")
    for asset, details in info.items():
        print(f"\n{asset}:")
        for key, value in details.items():
            print(f"{key}: {value}")

    print("\nSpezielle Kombinationen:")
    for category, combinations in special.items():
        if isinstance(combinations, dict):
            print(f"\n{category}:")
            for key, value in combinations.items():
                if isinstance(value, dict):
                    print(f"\n{key}:")
                    for subkey, subvalue in value.items():
                        print(f"{subkey}: {subvalue}")
                else:
                    print(f"{key}: {value}")
        else:
            print(f"{category}: {combinations}")


# Beispielaufruf
if __name__ == "__main__":
    print_results(200)