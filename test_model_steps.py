import os
from pathlib import Path
from dags.inflation_modules.model_steps import (
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

def main():
    # Define paths for local execution
    base_dir = Path.cwd()  # Current working directory

    # Override global variables in model_steps.py
    import dags.inflation_modules.model_steps as model_steps
    model_steps.DATA_DIR = str(base_dir / 'data')
    model_steps.OUTPUT_DIR = str(base_dir / 'data' / 'model_output')
    model_steps.TRANSFORMED_DATA_PATH = os.path.join(model_steps.DATA_DIR, 'transformed_data.csv')
    model_steps.SELECTED_FEATURES_PATH = os.path.join(model_steps.OUTPUT_DIR, 'selected_features.pkl')
    model_steps.TRAIN_TEST_DATA_PATH = os.path.join(model_steps.OUTPUT_DIR, 'train_test_data.pkl')
    model_steps.SCALER_PATH = os.path.join(model_steps.OUTPUT_DIR, 'Scaler.pkl')
    model_steps.MLR_MODEL_PATH = os.path.join(model_steps.OUTPUT_DIR, 'MLR.pkl')
    model_steps.RF_MODEL_PATH = os.path.join(model_steps.OUTPUT_DIR, 'RandomForest.pkl')
    model_steps.SVR_MODEL_PATH = os.path.join(model_steps.OUTPUT_DIR, 'SVR.pkl')
    model_steps.MODEL_COMPARISON_PATH = os.path.join(model_steps.OUTPUT_DIR, 'model_comparison.csv')
    model_steps.MODEL_PREDICTIONS_PATH = os.path.join(model_steps.OUTPUT_DIR, 'model_predictions.csv')
    model_steps.MODEL_COMPARISON_JSON_PATH = os.path.join(model_steps.OUTPUT_DIR, 'model_comparison.json')

    print(f"Running inflation modeling with data from {model_steps.DATA_DIR}")
    print(f"Output will be saved to {model_steps.OUTPUT_DIR}")

    # Run each step in sequence
    print("\n1. Ensuring output directory exists...")
    ensure_output_dir()

    print("\n2. Loading data...")
    df = load_data()

    print("\n3. Preparing data...")
    train_test_data_path = prepare_data(df)

    print("\n4. Selecting features with LassoCV...")
    selected_features_path = select_features_lasso(train_test_data_path)

    print("\n5. Scaling features...")
    scaled_features_path = scale_features(selected_features_path)

    print("\n6. Training MLR model...")
    mlr_model_path = train_mlr(scaled_features_path, train_test_data_path)

    print("\n7. Training Random Forest model...")
    rf_model_path = train_random_forest(scaled_features_path, train_test_data_path)

    print("\n8. Training SVR model...")
    svr_model_path = train_svr(scaled_features_path, train_test_data_path)

    print("\n9. Evaluating MLR model...")
    mlr_metrics_path = evaluate_mlr(mlr_model_path, scaled_features_path, train_test_data_path)

    print("\n10. Evaluating Random Forest model...")
    rf_metrics_path = evaluate_random_forest(rf_model_path, scaled_features_path, train_test_data_path)

    print("\n11. Evaluating SVR model...")
    svr_metrics_path = evaluate_svr(svr_model_path, scaled_features_path, train_test_data_path)

    print("\n12. Serializing model information...")
    model_comparison_path = serialize_model_info(mlr_metrics_path, rf_metrics_path, svr_metrics_path, train_test_data_path)

    # Load the model comparison data
    import pandas as pd
    comparison_df = pd.read_csv(model_comparison_path)

    print("\nModel Comparison:")
    for _, row in comparison_df.iterrows():
        print(f"{row['Model']} - RMSE: {row['RMSE']:.4f}, MAE: {row['MAE']:.4f}, R²: {row['R_squared']:.4f}")

if __name__ == "__main__":
    main()
