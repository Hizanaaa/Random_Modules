from typing import Dict

def compose_risk_score(
    bound_distance: float,
    drift_direction: float,
    recent_anomaly_count: float,
    stability: float
) -> Dict:
   
    #helper function to clamp values between 0 and 25
    def clamp(value: float) -> int:
        return int(max(0, min(25, round(value))))

    components = {
        "bound_distance": clamp(bound_distance),
        "drift_direction": clamp(drift_direction),
        "recent_anomaly_count": clamp(recent_anomaly_count),
        "stability": clamp(stability),
    }

    total = sum(components.values())

    #Risk level thresholds
    if total < 25:
        label = "low"
    elif total < 50:
        label = "moderate"
    elif total < 75:
        label = "high"
    else:
        label = "critical"

    return {
        "total": total,
        "components": components,
        "label": label,
    }



if __name__ == "__main__":
    result = compose_risk_score(
        bound_distance=18,
        drift_direction=12,
        recent_anomaly_count=20,
        stability=10
    )

    print(result)