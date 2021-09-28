from pathlib import Path
from random import choices, sample
import progressbar
from datetime import datetime
from api.binanceApi import client
import numpy as np
import argparse
from enum import Enum


class DatasetType(Enum):
    LATEST = "latest"
    RANDOM = "random"

    def __str__(self):
        return self.value


class Downloader:
    def _download_dataset(self, i):
        full_ticker = self.args.from_ticker + self.args.to_ticker
        raw_klines = client.get_historical_klines(
            full_ticker,
            self.args.interval,
            f"{str((i+1)*3*500)} minutes ago UTC",
            end_str=f"{str((i)*3*500)} minutes ago UTC",
        )
        klines = np.array(raw_klines).astype(float)
        times = np.array([datetime.fromtimestamp(int(t) // 1000) for t in klines[:, 0]])
        return [times, klines]

    def _prepare_last_datasets(self):
        datasets = []
        for i in progressbar.progressbar(range(self.args.size)):
            datasets.append(self._download_dataset(i))
        return datasets

    def _prepare_random_datasets(self):
        start, end = self.args.sample_scope
        datasets = []
        days = sample(range(start, end), self.args.size)
        for day in progressbar.progressbar(days):
            datasets.append(self._download_dataset(day))
        return datasets

    def _get_file_name(self):
        now = datetime.now().strftime("%y-%m-%d_%H-%M")
        return Path(
            self.args.output_dir,
            f"{self.args.from_ticker}-{self.args.to_ticker}-{self.args.interval}-{self.args.dataset_type}-{self.args.size}_{now}",
        )

    def _save_to_file(self, datasets):
        datasets = np.array(datasets, dtype=object)
        np.save(self._get_file_name(), datasets)

    def _run_downloader(self):
        if self.args.dataset_type.value == DatasetType.LATEST.value:
            datasets = self._prepare_last_datasets()
        elif self.args.dataset_type.value == DatasetType.RANDOM.value:
            datasets = self._prepare_random_datasets()

        self._save_to_file(datasets)

    def cli(self):
        parser = argparse.ArgumentParser(
            description="Download data from binance and save it to numpy files."
        )
        parser.add_argument("from_ticker", type=str, help="example: BTC, ETH, DOGE")
        parser.add_argument("to_ticker", type=str, help="example: BUSD, USDT")
        parser.add_argument(
            "interval",
            type=str,
            choices=[
                "1m",
                "3m",
                "5m",
                "15m",
                "30m",
                "1h",
                "2h",
                "4h",
                "6h",
                "8h",
                "12h",
                "1d",
                "3d",
                "1w",
                "1M",
            ],
        )
        parser.add_argument("size", type=int)
        parser.add_argument("dataset_type", type=DatasetType, choices=list(DatasetType))
        parser.add_argument("--output_dir", type=str, default="datasets/")
        parser.add_argument(
            "--sample_scope",
            nargs=2,
            type=int,
            default=[1, 100],
            help="when supplying RANDOM dataset type, select the scope of latest days to sample from",
        )

        self.args = parser.parse_args()
        self._run_downloader()


if __name__ == "__main__":
    Downloader().cli()
