from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from models.multi_strategy import save_multi_strategy, train_multi_strategy_for_symbol


def needs_retrain(last_trained_at: datetime | None, cadence: str = "weekly") -> bool:
    if last_trained_at is None:
        return True
    now = datetime.utcnow()
    if cadence == "monthly":
        return now - last_trained_at >= timedelta(days=30)
    return now - last_trained_at >= timedelta(days=7)


def retrain_symbols(symbols: Iterable[str], cadence: str = "weekly") -> dict:
    trained = []
    skipped = []
    for sym in symbols:
        marker = Path(f"models/.last_trained_{sym.upper()}.txt")
        last = None
        if marker.exists():
            try:
                last = datetime.fromisoformat(marker.read_text().strip())
            except Exception:
                last = None

        if not needs_retrain(last, cadence=cadence):
            skipped.append(sym)
            continue

        bundle = train_multi_strategy_for_symbol(sym)
        save_multi_strategy(bundle, sym)
        marker.write_text(datetime.utcnow().isoformat())
        trained.append(sym)

    return {"trained": trained, "skipped": skipped, "cadence": cadence}
