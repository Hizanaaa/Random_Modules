from typing import Dict, List
import numpy as np


def detect_anomalies(
    values: np.ndarray,
    min_bound: float | None = None,
    max_bound: float | None = None
) -> Dict:

    #Validate Inputs
    # Input validation
    if not isinstance(values, np.ndarray):
        raise TypeError("values must be a numpy array")

    if values.ndim != 1:
        raise ValueError("values must be a 1D numpy array")

    if len(values) == 0:
        raise ValueError("values array cannot be empty")

    if np.isnan(values).any():
        raise ValueError("values contains NaN")

    if np.isinf(values).any():
        raise ValueError("values contains infinity")
    
    #Convert to float for calculations
    values = np.asarray(values, dtype=np.float64)

    #Validate bounds
    bounds_violations = []

    for idx, value in enumerate(values):

        if min_bound is not None and value < min_bound:
            bounds_violations.append(idx)

        elif max_bound is not None and value > max_bound:
            bounds_violations.append(idx)


    #Z-score outliers
    z_score_outliers = []

    mean = np.mean(values)
    std = np.std(values)

    if std != 0:

        z_scores = (values - mean) / std

        for idx, z in enumerate(z_scores):

            if abs(z) > 3:
                z_score_outliers.append(idx)

    #IQR Outliers
    iqr_outliers = []

    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)

    iqr = q3 - q1

    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    for idx, value in enumerate(values):

        if value < lower_bound or value > upper_bound:
            iqr_outliers.append(idx)

    #Drift Segments: Detect continuous directional drift.
    drift_segments = []
    drift_start = 0

    for i in range(1, len(values)):

        # Detect change in trend direction
        current_diff = values[i] - values[i - 1]

        previous_diff = values[i - 1] - values[i - 2] \
            if i > 1 else current_diff

        # Trend direction changed
        if np.sign(current_diff) != np.sign(previous_diff):

            if i - 1 > drift_start:

                drift_segments.append({
                    "from_idx": drift_start,
                    "to_idx": i - 1,
                    "delta": float(
                        values[i - 1] - values[drift_start]
                    )
                })

            drift_start = i - 1

    #Final drift segment
    if len(values) - 1 > drift_start:

        drift_segments.append({
            "from_idx": drift_start,
            "to_idx": len(values) - 1,
            "delta": float(
                values[-1] - values[drift_start]
            )
        })

    #Spikes: Detect sudden jumps
    spikes = []

    diffs = np.abs(np.diff(values))

    if len(diffs) > 0:

        diff_mean = np.mean(diffs)
        diff_std = np.std(diffs)

        spike_threshold = diff_mean + (3 * diff_std)

        for idx, diff in enumerate(diffs):

            if diff > spike_threshold:
                spikes.append(idx + 1)

    #Stuck Runs: Detect repeated constant values.
    stuck_runs = []

    run_start = 0
    run_length = 1

    for i in range(1, len(values)):

        if values[i] == values[i - 1]:

            run_length += 1

        else:

            if run_length >= 3:

                stuck_runs.append({
                    "start": run_start,
                    "length": run_length
                })

            run_start = i
            run_length = 1

    # Final stuck run
    if run_length >= 3:

        stuck_runs.append({
            "start": run_start,
            "length": run_length
        })

   
   #return all anomalies
    return {
        "bounds_violations": bounds_violations,
        "z_score_outliers": z_score_outliers,
        "iqr_outliers": iqr_outliers,
        "drift_segments": drift_segments,
        "spikes": spikes,
        "stuck_runs": stuck_runs
    }
