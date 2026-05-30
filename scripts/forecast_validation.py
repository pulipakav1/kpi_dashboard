"""
Walk-forward backtesting for the three revenue forecast methods defined in forecast.sql.
Trains on months 1-24, evaluates on months 25-36, reports MAPE and RMSE per method.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


def load_revenue(path='dashboard_data/csv/monthly_revenue.csv') -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=['month'])
    df = df.sort_values('month').reset_index(drop=True)
    return df[['month', 'revenue']]


def mape(actual, forecast):
    mask = actual != 0
    return np.mean(np.abs((actual[mask] - forecast[mask]) / actual[mask])) * 100


def rmse(actual, forecast):
    return np.sqrt(np.mean((actual - forecast) ** 2))


def forecast_moving_average(history: pd.Series, horizon: int, window: int = 3) -> np.ndarray:
    base = history.iloc[-window:].mean()
    return np.full(horizon, base)


def forecast_linear(history: pd.Series, horizon: int, lookback: int = 6) -> np.ndarray:
    recent = history.iloc[-lookback:]
    avg_growth = recent.diff().dropna().mean()
    last = history.iloc[-1]
    return np.array([last + avg_growth * (i + 1) for i in range(horizon)])


def forecast_combined(history: pd.Series, horizon: int) -> np.ndarray:
    ma = forecast_moving_average(history, horizon)
    lin = forecast_linear(history, horizon)
    return (ma + lin) / 2


def walk_forward_backtest(df: pd.DataFrame, train_months: int = 24, horizon: int = 3):
    results = []
    max_start = len(df) - train_months - horizon + 1

    for i in range(max_start):
        train = df['revenue'].iloc[i: i + train_months]
        actual = df['revenue'].iloc[i + train_months: i + train_months + horizon].values

        forecasts = {
            'moving_average': forecast_moving_average(train, horizon),
            'linear_trend':   forecast_linear(train, horizon),
            'combined':       forecast_combined(train, horizon),
        }

        for method, pred in forecasts.items():
            results.append({
                'fold': i,
                'method': method,
                'mape': mape(actual, pred),
                'rmse': rmse(actual, pred),
            })

    return pd.DataFrame(results)


def main():
    df = load_revenue()

    if len(df) < 27:
        print(f"Only {len(df)} months of data — need at least 27 for backtesting. Skipping.")
        return

    results = walk_forward_backtest(df, train_months=24, horizon=3)

    summary = results.groupby('method')[['mape', 'rmse']].mean().round(2)
    summary.columns = ['Mean MAPE (%)', 'Mean RMSE ($)']
    summary = summary.sort_values('Mean MAPE (%)')

    print("\n--- Forecast Method Comparison (walk-forward backtesting) ---")
    print(summary.to_string())

    best = summary.index[0]
    print(f"\nBest method: {best} (MAPE {summary.loc[best, 'Mean MAPE (%)']:.2f}%)")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle('Forecast Method Backtesting — Walk-Forward Validation', fontsize=12, fontweight='bold')

    colors = {'moving_average': '#4472C4', 'linear_trend': '#E05C5C', 'combined': '#2ecc71'}

    for method, grp in results.groupby('method'):
        axes[0].plot(grp['fold'], grp['mape'], label=method, color=colors.get(method), linewidth=1.5, alpha=0.8)
        axes[1].plot(grp['fold'], grp['rmse'], label=method, color=colors.get(method), linewidth=1.5, alpha=0.8)

    for ax, metric in zip(axes, ['MAPE (%)', 'RMSE ($)']):
        ax.set_xlabel('Fold')
        ax.set_ylabel(metric)
        ax.set_title(f'{metric} by Fold')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('reports/forecast_validation.png', dpi=150, bbox_inches='tight')
    print("Saved reports/forecast_validation.png")


if __name__ == '__main__':
    main()
