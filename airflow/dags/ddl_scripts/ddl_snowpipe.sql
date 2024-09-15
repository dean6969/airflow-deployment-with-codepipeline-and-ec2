USE DATABASE binance_database_dev;

USE SCHEMA RAW;

CREATE OR REPLACE PIPE BINANCE_DATABASE_DEV.RAW.CURRENT_PRICE_PIPE 
AUTO_INGEST = TRUE
AS
COPY INTO BINANCE_DATABASE_DEV.RAW.landing_current_price 
FROM (
    SELECT PARSE_JSON($1), CURRENT_TIMESTAMP()
    FROM @s3_json_stage/landing_file/current_price
)
FILE_FORMAT = (TYPE = 'JSON');

CREATE or REPLACE pipe BINANCE_DATABASE_DEV.RAW.PRICE_LINE_ITEM_PIPE
AUTO_INGEST = TRUE
AS
COPY INTO BINANCE_DATABASE_DEV.RAW.landing_price_line_item 
FROM (
    SELECT PARSE_JSON($1), CURRENT_TIMESTAMP()
    FROM @s3_json_stage/landing_file/price_line_item
)
FILE_FORMAT = (TYPE = 'JSON');