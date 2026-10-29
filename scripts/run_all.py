"""Run the whole pipeline in order: python scripts/run_all.py"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["01_data_quality_report.py", "02_clean_transform.py", "03_etl_star_schema.py",
         "04_timeseries_forecast.py", "05_gradient_descent_trend.py", "06_eda_charts.py",
         "07_cv_evaluation.py", "08_diagnostics_forecast.py", "09_segment_forecasts.py",
         "10_business_analytics.py", "11_data_engineering_extras.py"]

for s in STEPS:
    print(f"\n===== {s} =====", flush=True)
    r = subprocess.run([sys.executable, str(HERE / s)], cwd=HERE.parent)
    if r.returncode != 0:
        sys.exit(f"FAILED at {s} (exit code {r.returncode})")
print("\nAll steps finished OK. See reports/ and data/ folders.")
