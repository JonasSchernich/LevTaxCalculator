import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime


def calculate_metrics(returns, portfolio_values):
    """Berechnet verschiedene Performance-Metriken"""
    # Jährliche Rendite
    years = len(returns) / 252  # Annahme: 252 Handelstage pro Jahr
    total_return = (portfolio_values[-1] / portfolio_values[0])
    annual_return = (total_return ** (1 / years) - 1) * 100

    # Volatilität (annualisiert)
    daily_vol = returns.std()
    annual_vol = daily_vol * np.sqrt(252) * 100

    # Maximum Drawdown
    peak = portfolio_values.expanding(min_periods=1).max()
    drawdown = (portfolio_values - peak) / peak
    max_drawdown = drawdown.min() * 100

    return {
        'Jährliche Rendite': f"{annual_return:.2f}%",
        'Volatilität': f"{annual_vol:.2f}%",
        'Max Drawdown': f"{max_drawdown:.2f}%"
    }


def analyze_portfolios():
    # Daten laden
    msci = yf.download("ACWI", start="1900-01-01")
    gold = yf.download("GC=F", start="1900-01-01")

    # DataFrame erstellen
    df = pd.DataFrame()
    df['MSCI'] = msci['Adj Close']
    df['Gold'] = gold['Adj Close']

    # NaN-Werte entfernen
    df = df.dropna()

    # Tägliche Returns berechnen
    df['MSCI_Return'] = df['MSCI'].pct_change()
    df['Gold_Return'] = df['Gold'].pct_change()

    # 50/50 Portfolio Return
    df['Mixed_Return'] = 0.5 * df['MSCI_Return'] + 0.5 * df['Gold_Return']

    # Gehebelte Returns
    # MSCI ACWI
    df['MSCI_2x'] = df['MSCI_Return'] * 2
    df['MSCI_3x'] = df['MSCI_Return'] * 3

    # Gold
    df['Gold_2x'] = df['Gold_Return'] * 2
    df['Gold_3x'] = df['Gold_Return'] * 3

    # Gemischtes Portfolio
    df['Mixed_2x'] = df['Mixed_Return'] * 2
    df['Mixed_3x'] = df['Mixed_Return'] * 3

    # Portfolio-Werte berechnen (startend bei 100)
    portfolios = {
        'MSCI': df['MSCI_Return'],
        'MSCI 2x': df['MSCI_2x'],
        'MSCI 3x': df['MSCI_3x'],
        'Gold': df['Gold_Return'],
        'Gold 2x': df['Gold_2x'],
        'Gold 3x': df['Gold_3x'],
        'Mixed': df['Mixed_Return'],
        'Mixed 2x': df['Mixed_2x'],
        'Mixed 3x': df['Mixed_3x']
    }

    # Portfolio-Werte berechnen
    for name, returns in portfolios.items():
        df[f'{name}_Portfolio'] = 100 * (1 + returns).cumprod()

    # Metriken berechnen
    results = {}
    for name, returns in portfolios.items():
        portfolio_values = df[f'{name}_Portfolio']
        results[name] = calculate_metrics(returns.dropna(), portfolio_values.dropna())

    return results, df


# Hauptprogramm
if __name__ == "__main__":
    results, df = analyze_portfolios()

    # Ergebnisse ausgeben
    print("\nPortfolio Analyse:")
    print("=" * 50)

    for portfolio, metrics in results.items():
        print(f"\n{portfolio}:")
        for metric, value in metrics.items():
            print(f"{metric}: {value}")

    # Zeitraum ausgeben
    print("\nAnalysezeitraum:")
    print(f"Start: {df.index[0].strftime('%Y-%m-%d')}")
    print(f"Ende: {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"Anzahl Handelstage: {len(df)}")