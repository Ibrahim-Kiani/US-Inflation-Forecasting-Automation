import os
from pathlib import Path
from dags.inflation_modules.model import model_inflation

def main():
    # Define paths for local execution
    base_dir = Path.cwd()  # Current working directory
    data_dir = base_dir / 'data'
    output_dir = data_dir / 'model_output'
    
    # Run modeling
    print(f"Running inflation modeling with data from {data_dir}")
    model_results = model_inflation(data_dir, output_dir)
    
    # Print results
    print("\nModel Comparison:")
    for result in model_results:
        print(f"{result['model_name']} - RMSE: {result['rmse']:.4f}, MAE: {result['mae']:.4f}, R²: {result['r2']:.4f}")

if __name__ == "__main__":
    main()
