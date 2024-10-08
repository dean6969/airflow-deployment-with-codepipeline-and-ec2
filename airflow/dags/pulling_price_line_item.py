import json
import uuid
from datetime import datetime, timedelta
import logging
import boto3
from botocore.exceptions import ClientError
from binance.client import Client
import ast
from time import sleep, time


def pull_data_price_line_item():
    # AWS Secrets Manager configuration
    secret_name = "binace_api"
    region_name = "ap-southeast-2"

    # kinesis data stream
    stream_name = "stream_binance"
    kinesis = boto3.client('kinesis', region_name='ap-southeast-2')

    # Create a Secrets Manager client
    session = boto3.session.Session()
    secrets_client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # Fetch API key and secret from Secrets Manager
    try:
        get_secret_value_response = secrets_client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = ast.literal_eval(get_secret_value_response['SecretString'])

    # Binance API credentials
    api_key = secret['api_key']
    api_secret = secret['api_secret']

    # Initialize Binance client
    client = Client(api_key, api_secret)

    # Configure logging
    logging.basicConfig(filename='binance_logs.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Fetch exchange information (symbols and assets)
    exchange_info = client.get_exchange_info()
    symbols = [symbol['symbol'] for symbol in exchange_info['symbols']]

    count = 0
    # Loop over symbols and fetch kline data for each
    for symbol in symbols:
        # Fetch the most recent 1-minute kline for the symbol
        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1DAY, limit=1)

        for kline in klines:  # Process each kline entry
            kline_info = {
                'id': str(uuid.uuid4()),
                "symbol": symbol,
                "open_time": datetime.fromtimestamp(kline[0] / 1000).isoformat(),
                "open_price": kline[1],
                "high_price": kline[2],
                "low_price": kline[3],
                "close_price": kline[4],
                "volume": kline[5],
                "close_time": datetime.fromtimestamp(kline[6] / 1000).isoformat(),
                "quote_asset_volume": kline[7],
                "number_of_trades": kline[8],
                "taker_buy_base_asset_volume": kline[9],
                "taker_buy_quote_asset_volume": kline[10],
            }

            params = {
                'Data': json.dumps(kline_info),
                'PartitionKey': 'price_line_item',
                'StreamName': stream_name
            }

            try:
                response = kinesis.put_record(**params)
                print(response)
            except Exception as e:
                print(e)

            sleep(1)

        count += 1
        print(count)

        if count == 10:
            break
