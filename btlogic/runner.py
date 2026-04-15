from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from backtesting import Backtest, Strategy

from strategy.signals import position_size


@dataclass
class RiskConfig:
    risk_per_trade: float = 0.01
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.05


def _prepare_bt_frame(df: pd.DataFrame) -> pd.DataFrame:
    bt_df = pd.DataFrame({
        "Open": df["close"],
        "High": df["close"],
        "Low": df["close"],
        "Close": df["close"],
        "Volume": 1,
        "Signal": df["signal"].values,
    })
    bt_df.index = pd.DatetimeIndex(df["date"])
    return bt_df


def run_backtest(df_with_signals: pd.DataFrame, initial_capital: float = 100_000, risk: RiskConfig | None = None):
    risk = risk or RiskConfig()
    data = _prepare_bt_frame(df_with_signals)

    class SignalStrategy(Strategy):
        def init(self):  # noqa: D401
            pass

        def next(self):
            price = self.data.Close[-1]
            sig = self.data.Signal[-1]
            if sig == 1 and not self.position:
                size = position_size(self.equity, price, risk.risk_per_trade, risk.stop_loss_pct)
                if size > 0:
                    self.buy(size=size, sl=price * (1 - risk.stop_loss_pct), tp=price * (1 + risk.take_profit_pct))
            elif sig == -1 and self.position.is_long:
                self.position.close()

    bt = Backtest(data, SignalStrategy, cash=initial_capital, commission=0.0005)
    stats = bt.run()
    return stats, bt


def save_backtest_report(stats, path: str = "btlogic/report.json") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pd.Series(stats).to_json(path)
