from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

# Import from our local modules
from inflation_modules.ingest import ensure_dir, fetch_fred, fred_series
from inflation_modules.transform import transform_data
from inflation_modules.model_steps import (
    ensure_output_dir,
    load_data,
    prepare_data,
    select_features_lasso,
    scale_features,
    train_mlr,
    train_random_forest,
    train_svr,
    evaluate_mlr,
    evaluate_random_forest,
    evaluate_svr,
    serialize_model_info
)

with DAG(
    'inflation_forecasting',
    start_date=datetime(2025, 5, 10),
    schedule_interval='@monthly',
    catchup=False,
    tags=['inflation', 'ingest', 'transform', 'model'],
) as dag:
    # Task to ensure data directory exists
    t0 = PythonOperator(
        task_id='ensure_data_dir',
        python_callable=ensure_dir,
    )

    # Create tasks for each FRED series
    fetch_tasks = []
    for task_id, (series, fname) in fred_series.items():
        task = PythonOperator(
            task_id=task_id,
            python_callable=fetch_fred,
            op_kwargs={
                'series_id': series,
                'filename': fname,
                'start_date': '1900-01-01'  # Fetch all available historical data
            },
        )
        task.set_upstream(t0)
        fetch_tasks.append(task)

    # Task to transform the data
    transform_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
    )

    # Set dependencies: transform runs after all fetch tasks
    for task in fetch_tasks:
        transform_task.set_upstream(task)

    # Task to ensure model output directory exists
    ensure_output_dir_task = PythonOperator(
        task_id='ensure_output_dir',
        python_callable=ensure_output_dir,
    )
    ensure_output_dir_task.set_upstream(transform_task)

    # Task to load the transformed data
    load_data_task = PythonOperator(
        task_id='load_data',
        python_callable=load_data,
    )
    load_data_task.set_upstream(ensure_output_dir_task)

    # Task to prepare the data for modeling
    prepare_data_task = PythonOperator(
        task_id='prepare_data',
        python_callable=prepare_data,
    )
    prepare_data_task.set_upstream(load_data_task)

    # Task to select features using LassoCV
    select_features_task = PythonOperator(
        task_id='select_features',
        python_callable=select_features_lasso,
        op_kwargs={
            'data_path': "{{ ti.xcom_pull(task_ids='prepare_data') }}"
        }
    )
    select_features_task.set_upstream(prepare_data_task)

    # Task to scale the selected features
    scale_features_task = PythonOperator(
        task_id='scale_features',
        python_callable=scale_features,
        op_kwargs={
            'selected_features_path': "{{ ti.xcom_pull(task_ids='select_features') }}"
        }
    )
    scale_features_task.set_upstream(select_features_task)

    # Task to train the MLR model
    train_mlr_task = PythonOperator(
        task_id='train_mlr',
        python_callable=train_mlr,
        op_kwargs={
            'selected_features_path': "{{ ti.xcom_pull(task_ids='scale_features') }}",
            'train_test_data_path': "{{ ti.xcom_pull(task_ids='prepare_data') }}"
        }
    )
    train_mlr_task.set_upstream(scale_features_task)

    # Task to train the Random Forest model
    train_rf_task = PythonOperator(
        task_id='train_random_forest',
        python_callable=train_random_forest,
        op_kwargs={
            'selected_features_path': "{{ ti.xcom_pull(task_ids='scale_features') }}",
            'train_test_data_path': "{{ ti.xcom_pull(task_ids='prepare_data') }}"
        }
    )
    train_rf_task.set_upstream(scale_features_task)

    # Task to train the SVR model
    train_svr_task = PythonOperator(
        task_id='train_svr',
        python_callable=train_svr,
        op_kwargs={
            'selected_features_path': "{{ ti.xcom_pull(task_ids='scale_features') }}",
            'train_test_data_path': "{{ ti.xcom_pull(task_ids='prepare_data') }}"
        }
    )
    train_svr_task.set_upstream(scale_features_task)

    # Task to evaluate the MLR model
    evaluate_mlr_task = PythonOperator(
        task_id='evaluate_mlr',
        python_callable=evaluate_mlr,
        op_kwargs={
            'model_path': "{{ ti.xcom_pull(task_ids='train_mlr') }}",
            'selected_features_path': "{{ ti.xcom_pull(task_ids='scale_features') }}",
            'train_test_data_path': "{{ ti.xcom_pull(task_ids='prepare_data') }}"
        }
    )
    evaluate_mlr_task.set_upstream(train_mlr_task)

    # Task to evaluate the Random Forest model
    evaluate_rf_task = PythonOperator(
        task_id='evaluate_random_forest',
        python_callable=evaluate_random_forest,
        op_kwargs={
            'model_path': "{{ ti.xcom_pull(task_ids='train_random_forest') }}",
            'selected_features_path': "{{ ti.xcom_pull(task_ids='scale_features') }}",
            'train_test_data_path': "{{ ti.xcom_pull(task_ids='prepare_data') }}"
        }
    )
    evaluate_rf_task.set_upstream(train_rf_task)

    # Task to evaluate the SVR model
    evaluate_svr_task = PythonOperator(
        task_id='evaluate_svr',
        python_callable=evaluate_svr,
        op_kwargs={
            'model_path': "{{ ti.xcom_pull(task_ids='train_svr') }}",
            'selected_features_path': "{{ ti.xcom_pull(task_ids='scale_features') }}",
            'train_test_data_path': "{{ ti.xcom_pull(task_ids='prepare_data') }}"
        }
    )
    evaluate_svr_task.set_upstream(train_svr_task)

    # Task to serialize model information
    serialize_model_info_task = PythonOperator(
        task_id='serialize_model_info',
        python_callable=serialize_model_info,
        op_kwargs={
            'mlr_metrics_path': "{{ ti.xcom_pull(task_ids='evaluate_mlr') }}",
            'rf_metrics_path': "{{ ti.xcom_pull(task_ids='evaluate_random_forest') }}",
            'svr_metrics_path': "{{ ti.xcom_pull(task_ids='evaluate_svr') }}",
            'train_test_data_path': "{{ ti.xcom_pull(task_ids='prepare_data') }}"
        }
    )
    serialize_model_info_task.set_upstream([evaluate_mlr_task, evaluate_rf_task, evaluate_svr_task])
