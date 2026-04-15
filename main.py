import argparse
from datetime import datetime

import pandas as pd
import schedule

from data.ticker_fetcher import fetch_nse_tickers
from data.downloader import download_history
from features.engineer import run_feature_engineering, load_combined_dataset
from training.dataset import prepare_dataset
from training.trainer import train_all_models, evaluate_models
from training.retrain_scheduler import retrain_symbols
from models.multi_strategy import save_multi_strategy, train_multi_strategy_for_symbol
from backtest.dual_engine_alpha import run_alpha_engine
from strategy.signals import ensemble_predict
from btlogic.runner import run_backtest, save_backtest_report
from utils.logger import get_logger

logger = get_logger(__name__)


def pipeline_download_and_features(years: int = 15, limit: int | None = None) -> None:
    tickers = fetch_nse_tickers()
    if limit:
        tickers = tickers[:limit]
        logger.info("Limiting tickers to first %d for this run", limit)
    if not tickers:
        logger.error("No tickers fetched; aborting pipeline")
        return
    download_history(tickers, years=years)
    run_feature_engineering()


def pipeline_training():
    df = load_combined_dataset()
    if df.empty:
        logger.error("No processed data to train on")
        return None, None
    dataset = prepare_dataset(df)
    models = train_all_models(dataset)
    metrics = evaluate_models(models, dataset)
    logger.info("Training complete. AUC: %.3f", metrics["auc"])
    return models, df


def pipeline_backtest(models, df, symbol: str | None = None):
    if df is None or models is None:
        logger.error("Training output missing; cannot backtest")
        return
    symbol = symbol or df['stock_symbol'].iloc[0]
    df_sym = df[df['stock_symbol'] == symbol].copy()
    df_with_signals = ensemble_predict(df_sym, models)
    stats, bt = run_backtest(df_with_signals)
    save_backtest_report(stats)
    logger.info("Backtest done for %s", symbol)
    logger.info("Backtest metrics: %s", stats)
    return stats, bt


def daily_job(years: int = 15):
    logger.info("Running daily retrain job at %s", datetime.utcnow())
    pipeline_download_and_features(years=years)
    models, df = pipeline_training()
    if models is not None:
        models.save("models")
        pipeline_backtest(models, df)
    logger.info("Daily job finished")


def schedule_daily(hour: str = "18:00"):
    schedule.every().day.at(hour).do(daily_job)
    logger.info("Scheduled daily job at %s", hour)
    while True:
        schedule.run_pending()


def parse_args():
    parser = argparse.ArgumentParser(description="NSE ML trading system")
    parser.add_argument("command", choices=["full", "download", "train", "backtest", "daily", "multi-train", "multi-retrain", "dual-engine"], help="Pipeline stage")
    parser.add_argument("--symbol", dest="symbol", default=None, help="Symbol for backtest (Yahoo format)")
    parser.add_argument("--years", dest="years", type=int, default=15, help="Years of history")
    parser.add_argument("--schedule", dest="schedule_time", default="18:00", help="Daily schedule time HH:MM")
    parser.add_argument("--limit", dest="limit", type=int, default=None, help="Limit number of tickers (for faster dev runs)")
    parser.add_argument("--cadence", dest="cadence", default="weekly", choices=["weekly", "monthly"], help="Retraining cadence")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.command == "download":
        pipeline_download_and_features(years=args.years, limit=args.limit)
    elif args.command == "train":
        _, _ = pipeline_training()
    elif args.command == "backtest":
        models, df = pipeline_training()
        pipeline_backtest(models, df, symbol=args.symbol)
    elif args.command == "daily":
        schedule_daily(args.schedule_time)
    elif args.command == "multi-train":
        if not args.symbol:
            logger.error("Please provide --symbol for multi-train")
            return
        bundle = train_multi_strategy_for_symbol(args.symbol)
        path = save_multi_strategy(bundle, args.symbol)
        logger.info("Multi-strategy model saved at %s", path)
    elif args.command == "multi-retrain":
        result = retrain_symbols(fetch_nse_tickers()[:20], cadence=args.cadence)
        logger.info("Retrain result: %s", result)
    elif args.command == "dual-engine":
        result = run_alpha_engine()
        logger.info("Dual-engine reports generated: %s", result.get("combined_report", {}))
    elif args.command == "full":
        pipeline_download_and_features(years=args.years, limit=args.limit)
        models, df = pipeline_training()
        if models is not None:
            models.save("models")
            pipeline_backtest(models, df, symbol=args.symbol)


if __name__ == "__main__":
    main()
