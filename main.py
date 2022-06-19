import sys
import json
import requests
import pandas as pd
import datetime as dt
from crypto_algorithms import run_predictions
from utils import adjust_year_and_format_datetime, adjust_months_and_format_datetime

API_KEY = "C83FD246-BBED-4D3D-8A94-C3190A1371C5"
READ_FROM_CSV = True
WRITE_TO_CSV = True


def run():
    print("Starting crypto algorithm...")
    coin_abbreviation: str = sys.argv[1]
    csv_file_name = "{0} History.csv".format(coin_abbreviation)
    try:
        predict_hours_in_advance = int(sys.argv[2])
    except IndexError as error:
        print("No hours in advance to predict provided. Using default of - 1 - hour")
        predict_hours_in_advance = 1

    if READ_FROM_CSV:
        print("Reading from .csv file: {0}".format(READ_FROM_CSV))
        coin_data: pd.DataFrame = read_data_from_csv(csv_file_name)
        # print(coin_data)

        # coin_data.drop(["End Time", "Open Time", "Close Time", "Price Close"], axis="columns", inplace=True)
        coin_prices_open = [coin_value for coin_value in coin_data["Price Open"].values.tolist()]
        most_recent_time: str = coin_data["Start Time"].values.tolist()[-1].split("+")[0]
        # print(coin_prices_open)

        coin_prices_hourly_differences = [coin_prices_open[i] - coin_prices_open[i + 1] for i in range(len(coin_prices_open) - 1)]
        # print(coin_prices_hourly_differences)
        # print("{0:.8f}".format(coin_prices_hourly_differences[0]))

        run_predictions(coin_abbreviation, coin_prices_open, predict_hours_in_advance, most_recent_time)

    else:
        # Supported periods: https://docs.coinapi.io/#list-all-periods-get
        period_timing = "1HRS"
        today = dt.datetime.now()
        # datetime_start = adjust_year_and_format_datetime(today, 1)
        # datetime_end = adjust_year_and_format_datetime(today, 0)
        datetime_start = adjust_months_and_format_datetime(today, 6)
        datetime_end = adjust_months_and_format_datetime(today, 0)
        limit = "100000"
        url = "https://rest.coinapi.io/v1/ohlcv/{0}/USD/history?period_id={1}&time_start={2}&time_end={3}&limit={4}".format(
            coin_abbreviation, period_timing, datetime_start, datetime_end, limit
        )
        print(url)
        headers = {"X-CoinAPI-Key": API_KEY}
        response = requests.get(url, headers=headers)

        if response.status_code == 429:
            # API response
            print("Too many requests.")

        else:
            coin_data = json.loads(response.text)
            if len(coin_data) == 0:
                print("No data to work with")
                return

            coin_data_frame = pd.DataFrame(coin_data)
            # print(coin_data_frame)
            coin_data_frame.rename(columns={
                "time_period_start": "Start Time",
                "time_period_end": "End Time",
                "time_open": "Open Time",
                "time_close": "Close Time",
                "price_open": "Price Open",
                "price_high": "Price High",
                "price_low": "Price Low",
                "price_close": "Price Close",
                "volume_traded": "Volume Traded",
                "trades_count": "Trade Count"
            }, inplace=True)

            coin_data_frame["Start Time"] = pd.to_datetime(coin_data_frame["Start Time"])
            coin_data_frame["Day of the Week"] = coin_data_frame["Start Time"].dt.dayofweek
            coin_data_frame["Day of the Week"] = coin_data_frame["Day of the Week"].apply(number_to_day)
            # coin_data_frame.drop(["End Time", "Open Time", "Close Time", "Price Close"], axis="columns", inplace=True)

            coin_data_column_reorder = [
                "Day of the Week", "Start Time", "End Time", "Open Time", "Close Time",
                "Price Open", "Price Close", "Price High", "Price Low", "Volume Traded", "Trade Count"
            ]
            coin_data_frame = coin_data_frame.reindex(columns=coin_data_column_reorder)

            # print(coin_data_frame)

            if WRITE_TO_CSV:
                coin_data_frame.to_csv(csv_file_name, index=False)


def read_data_from_csv(filename):
    return pd.read_csv(filename)


def number_to_day(number):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[number]


run()
