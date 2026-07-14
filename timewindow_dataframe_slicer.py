import numpy as np
import pandas as pd


def slice_window(df: pd.DataFrame, ts_col: str, start: str, end: str, max_samples: int = None) -> pd.DataFrame:
    
    #check if timestamp column exists
    if ts_col not in df.columns:
        raise KeyError(f"Timestamp column '{ts_col}' not found in DataFrame")

    #convert timestamp column to datetime objects
    timestamps = pd.to_datetime(df[ts_col])
    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end)

    #Filtering row based on timestamp range
    mask = (timestamps >= start_ts) & (timestamps <= end_ts)
    sliced = df.loc[mask].copy()

    if max_samples is None or max_samples >= len(sliced) or len(sliced) == 0:
        return sliced
    
    #downsampling
    indices = np.linspace(0, len(sliced) - 1, max_samples, dtype=int)
    return sliced.iloc[indices]

if __name__ == "__main__":
    data = {
        "time": [
            "2026-05-18 10:00",
            "2026-05-18 10:01",
            "2026-05-18 10:02"
        ],
        "value": [1, 2, 3]
    }

    df = pd.DataFrame(data)

    result = slice_window(
        df,
        "time",
        "2026-05-18 10:00",
        "2026-05-18 10:02"
    )

    print(result)