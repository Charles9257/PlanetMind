from typing import Dict, List, Tuple

from app.models import Intervention, RiskDomain, RiskSignal


DOMAIN_WEIGHTS: Dict[RiskDomain, Dict[str, float]] = {
    RiskDomain.climate: {
        "temperature_anomaly": 0.35,
        "rainfall_deficit": 0.30,
        "soil_moisture_drop": 0.20,
        "wildfire_index": 0.15,
    },
    RiskDomain.health: {
        "new_cases_growth": 0.40,
        "hospital_occupancy": 0.35,
        "vaccination_gap": 0.15,
        "mobility_spike": 0.10,
    },
    RiskDomain.cyber: {
        "malware_activity": 0.35,
        "phishing_rate": 0.25,
        "unpatched_assets": 0.25,
        "critical_alerts": 0.15,
    },
    RiskDomain.economic: {
        "inflation_pressure": 0.35,
        "unemployment_rise": 0.25,
        "supply_chain_delay": 0.20,
        "currency_volatility": 0.20,
    },
}


def _severity(score: float) -> str:
    if score >= 0.8:
        return "critical"
    if score >= 0.6:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def score_risk(domain: RiskDomain, signals: List[RiskSignal]) -> Tuple[float, Dict[str, float]]:
    domain_weights = DOMAIN_WEIGHTS[domain]
    signal_map = {signal.name: signal.value for signal in signals}

    weighted_sum = 0.0
    total_weight = 0.0
    contributors: Dict[str, float] = {}
    for name, weight in domain_weights.items():
        value = signal_map.get(name, 0.0)
        contribution = value * weight
        weighted_sum += contribution
        total_weight += weight
        contributors[name] = round(contribution, 4)

    if total_weight == 0:
        return 0.0, contributors

    score = round(min(max(weighted_sum / total_weight, 0.0), 1.0), 4)
    return score, contributors


def build_explanation(domain: RiskDomain, score: float, contributors: Dict[str, float]) -> str:
    dominant_signal = max(contributors, key=contributors.get)
    return (
        f"{domain.value.capitalize()} risk in the selected region is {_severity(score)} "
        f"(score={score:.2f}). The strongest contributor is '{dominant_signal}'."
    )


def simulate_interventions(baseline_score: float, interventions: List[Intervention]) -> Tuple[float, float]:
    reduction = sum(intervention.expected_reduction for intervention in interventions)
    reduction = min(max(reduction, 0.0), 0.95)
    projected_score = round(max(baseline_score * (1 - reduction), 0.0), 4)
    return projected_score, round(baseline_score - projected_score, 4)
