from datetime import datetime
from cosmos import ProjectConfig, ProfileConfig, ExecutionConfig, DbtTaskGroup
from cosmos.profiles import SnowflakeUserPasswordProfileMapping
from airflow import settings
from airflow.models import Connection
from airflow.operators.python import PythonOperator
# from airflow import DAG
from airflow.decorators import dag
import boto3
from botocore.exceptions import ClientError
import ast

import boto3
from botocore.exceptions import ClientError



def get_secret():

    secret_name = "snowflake_credential"
    region_name = "ap-southeast-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = ast.literal_eval(get_secret_value_response['SecretString'])

    return secret


secret = get_secret()

print(secret)

# Define the profile configurations for raw, staging, and silver stages
profile_config_raw = ProfileConfig(profile_name="dbtvault_snowflake_demo",
                                    target_name="dev",
                                    profile_mapping=SnowflakeUserPasswordProfileMapping(conn_id="sf_test",
                                    profile_args={
                                        "database": "binance_database_dev",
                                        "schema": "RAW",
                                        },
                                    ))

profile_config_stg = ProfileConfig(profile_name="dbtvault_snowflake_demo",
                                    target_name="dev",
                                    profile_mapping=SnowflakeUserPasswordProfileMapping(conn_id="sf_test",
                                    profile_args={
                                        "database": "binance_database_dev",
                                        "schema": "STAGING",
                                        },
                                    ))

profile_config_silver = ProfileConfig(profile_name="dbtvault_snowflake_demo",
                                    target_name="dev",
                                    profile_mapping=SnowflakeUserPasswordProfileMapping(conn_id="sf_test",
                                    profile_args={
                                        "database": "binance_database_dev",
                                        "schema": "SILVER",
                                        },
                                    ))


# Define the function to set up the Snowflake connection
def setup_snowflake_connection():
    # Check if the connection already exists
    conn_id = "sf_test"
    session = settings.Session()
    existing_conn = session.query(Connection).filter(Connection.conn_id == conn_id).first()

    if not existing_conn:
        # If the connection does not exist, create it
        conn = Connection(
            conn_id=conn_id,
            conn_type=secret['conn_type'],
            login=secret['login'],
            password=secret['password'],
            extra={"account": secret['account'], "role": secret['role']}
        )
        session.add(conn)
        session.commit()
        print(f"Connection '{conn_id}' created successfully.")
    else:
        print(f"Connection '{conn_id}' already exists.")
    session.close()


@dag(
    schedule_interval="* 10 * * 1-5",
    start_date=datetime(2023, 1, 1),
    catchup=False,
    dag_id="ETL_PIPELINE_DATA_MODELING"
)
def basic_cosmos_task_group() -> None:
    # Task to set up Snowflake connection
    setup_connection_task = PythonOperator(
        task_id='setup_snowflake_connection',
        python_callable=setup_snowflake_connection
    )

    dbt_snowflake_dag_raw_stage = DbtTaskGroup(
        group_id="Raw_stage",
        project_config=ProjectConfig("/opt/airflow/dags/dbt/raw"),
        execution_config=ExecutionConfig(dbt_executable_path="./dbt_venv/bin/dbt",),
        operator_args={"install_deps": True},
        profile_config=profile_config_raw,
    )

    dbt_snowflake_dag_staging_stage = DbtTaskGroup(
        group_id="Staging_stage",
        project_config=ProjectConfig("/opt/airflow/dags/dbt/staging"),
        execution_config=ExecutionConfig(dbt_executable_path="./dbt_venv/bin/dbt",),
        operator_args={"install_deps": True},
        profile_config=profile_config_stg,
    )

    dbt_snowflake_dag_silver_stage = DbtTaskGroup(
        group_id="Silver_stage",
        project_config=ProjectConfig("/opt/airflow/dags/dbt/silver"),
        execution_config=ExecutionConfig(dbt_executable_path="./dbt_venv/bin/dbt",),
        operator_args={"install_deps": True},
        profile_config=profile_config_silver,
    )

    setup_connection_task >> dbt_snowflake_dag_raw_stage >> dbt_snowflake_dag_staging_stage

    dbt_snowflake_dag_staging_stage >> dbt_snowflake_dag_silver_stage


basic_cosmos_task_group()
