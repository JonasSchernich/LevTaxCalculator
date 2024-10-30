import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime


def simulate_regime_portfolio():
    # Daten laden
    sp500 = yf.download("^GSPC", start="1900-01-01")
    gold = yf.download("GC=F", start="1900-01-01")

    # DataFrame für die Analyse erstellen
    df = pd.DataFrame()

    # 200 Tage MA für beide Assets berechnen
    df['SP500'] = sp500['Close']
    df['SP500_MA200'] = sp500['Close'].rolling(window=200).mean()
    df['Gold'] = gold['Close']
    df['Gold_MA200'] = gold['Close'].rolling(window=200).mean()

    # Regime bestimmen (True wenn über MA)
    df['SP500_above_MA'] = df['SP500'] > df['SP500_MA200']
    df['Gold_above_MA'] = df['Gold'] > df['Gold_MA200']

    # Returns berechnen
    df['SP500_return'] = df['SP500'].pct_change()
    df['Gold_return'] = df['Gold'].pct_change()

    # Gehebelte Returns
    df['SP500_4x'] = df['SP500_return'] * 3
    df['SP500_2x'] = df['SP500_return'] * 2
    df['Gold_3x'] = df['Gold_return'] * 3
    df['Gold_2x'] = df['Gold_return'] * 2

    # Erste 200 Tage und Tage mit NaN entfernen
    df = df.iloc[200:].dropna()

    # Portfolio Return berechnen
    df['Portfolio_return'] = 0.0
    df['Regime'] = 'Initial'
    current_regime = 'Initial'

    # Konstante tägliche Rendite
    CASH_RETURN = 0.00012  # 0.012%

    for i in range(1, len(df)):
        # Aktuelle und gestrige Bedingungen prüfen
        sp500_above_today = df['SP500_above_MA'].iloc[i]
        gold_above_today = df['Gold_above_MA'].iloc[i]
        sp500_above_yesterday = df['SP500_above_MA'].iloc[i - 1]
        gold_above_yesterday = df['Gold_above_MA'].iloc[i - 1]

        # Regime bestimmen
        new_regime = current_regime

        # Prüfen ob Regimewechsel nötig ist
        if sp500_above_today == sp500_above_yesterday and gold_above_today == gold_above_yesterday:
            if sp500_above_today and gold_above_today:
                new_regime = 'Both_Above'
            elif sp500_above_today and not gold_above_today:
                new_regime = 'SP500_Above_Only'
            elif not sp500_above_today and gold_above_today:
                new_regime = 'Gold_Above_Only'
            else:
                new_regime = 'Both_Below'

        # Returns basierend auf aktuellem Regime berechnen
        if current_regime == 'Both_Above':
            portfolio_return = 0.9 * df['SP500_4x'].iloc[i] + 0.2 * df['Gold_3x'].iloc[i]
        elif current_regime == 'SP500_Above_Only':
            portfolio_return = 1.1 * df['SP500_4x'].iloc[i]
        elif current_regime == 'Both_Below':
            portfolio_return = CASH_RETURN
        elif current_regime == 'Gold_Above_Only':
            portfolio_return = 0.5 * df['Gold_2x'].iloc[i] + 0.5 * CASH_RETURN
        else:  # Initial regime
            portfolio_return = 0

        df['Portfolio_return'].iloc[i] = portfolio_return
        df['Regime'].iloc[i] = current_regime
        current_regime = new_regime

    # Portfolio-Wert berechnen
    df['Portfolio_value'] = 100 * (1 + df['Portfolio_return']).cumprod()

    # Performance Metriken berechnen
    years = (df.index[-1] - df.index[0]).days / 365.25
    final_value = df['Portfolio_value'].iloc[-1]
    annual_return = (final_value / 100) ** (1 / years) - 1

    # Regime-Statistiken berechnen
    regime_stats = df['Regime'].value_counts()
    regime_percentages = regime_stats / len(df) * 100

    results = {
        'Performance': {
            'Finaler Portfolio-Wert': round(final_value, 2),
            'Jährliche Rendite': f"{round(annual_return * 100, 2)}%",
            'Analysezeitraum': f"{df.index[0].strftime('%Y-%m-%d')} bis {df.index[-1].strftime('%Y-%m-%d')}",
            'Anzahl Tage': len(df)
        },
        'Regime-Verteilung': {
            regime: f"{percentage:.1f}%"
            for regime, percentage in regime_percentages.items()
        }
    }

    return results, df


# Beispielaufruf
if __name__ == "__main__":
    results, df = simulate_regime_portfolio()

    print("\nPortfolio Performance:")
    for key, value in results['Performance'].items():
        print(f"{key}: {value}")

    print("\nRegime-Verteilung:")
    for regime, percentage in results['Regime-Verteilung'].items():
        print(f"{regime}: {percentage}")