"""Prévision courte échéance par tendance de pression + analogues historiques.

Principe (volontairement simple et explicable, pas un modèle météo) :
1. On mesure de combien la pression a varié sur les 3 dernières heures.
2. On cherche dans l'historique de LA STATION des moments passés survenus à
   une période comparable de l'année (+/- 15 jours) où la pression évoluait
   de façon similaire.
3. On regarde ce qui s'est effectivement passé, en moyenne, 6h après ces
   moments-là (température montée/descendue/stable).

C'est une climatologie locale auto-calibrée plutôt qu'une formule importée
(type Zambretti) : on ne connaît pas l'altitude exacte de la station donc on
n'a pas de pression ramenée au niveau de la mer, ce qui rendrait une table
météo standard peu fiable. Travailler en relatif (tendance + analogues
propres à la station) contourne ce problème.

Limites assumées : une seule station, un an de données au démarrage (peu
d'exemples, pas de vraie variabilité inter-annuelle), pas de données
régionales (radar/satellite). Utile à l'échelle de quelques heures, pas
au-delà. Voir `limitations` dans la réponse.
"""

import bisect
from datetime import timedelta

from models import db, SensorReading

MIN_ANALOGS = 15
DAY_WINDOW = 15
TREND_TOLERANCE_HPA = 1.0
TREND_WINDOW_HOURS = 3
OUTCOME_WINDOW_HOURS = 6

LIMITATIONS = [
    "Basé sur un an de données d'une seule station : peu d'années, donc pas de vraie moyenne climatique.",
    "Aucune donnée régionale (pas de radar, pas de satellite, pas de systèmes météo entrants).",
    "Le capteur de température peut être biaisé par le soleil en journée (voir l'indicateur d'exposition solaire).",
    "Fiable seulement à l'échelle de quelques heures, pas au-delà.",
]


def _day_of_year_distance(doy_a, doy_b, year_length=365):
    diff = abs(doy_a - doy_b)
    return min(diff, year_length - diff)


def _nearest_reading(readings, timestamps, target_time, tolerance_minutes):
    idx = bisect.bisect_left(timestamps, target_time)
    tol = timedelta(minutes=tolerance_minutes)
    best, best_diff = None, None
    for i in (idx - 1, idx):
        if 0 <= i < len(readings):
            r = readings[i]
            diff = abs(r.timestamp - target_time)
            if diff <= tol and (best_diff is None or diff < best_diff):
                best, best_diff = r, diff
    return best


def _pressure_trend(readings, timestamps, at_time, hours=TREND_WINDOW_HOURS):
    now_r = _nearest_reading(readings, timestamps, at_time, tolerance_minutes=15)
    past_r = _nearest_reading(readings, timestamps, at_time - timedelta(hours=hours), tolerance_minutes=30)
    if not now_r or not past_r or now_r.pressure is None or past_r.pressure is None:
        return None
    return round(now_r.pressure - past_r.pressure, 1)


def build_forecast(device_id, now):
    readings = (
        db.session.query(SensorReading.timestamp, SensorReading.pressure, SensorReading.temperature)
        .filter(SensorReading.device_id == device_id, SensorReading.pressure.isnot(None))
        .order_by(SensorReading.timestamp.asc())
        .all()
    )
    if not readings:
        return {"available": False, "reason": "no_data"}

    timestamps = [r.timestamp for r in readings]

    current_trend = _pressure_trend(readings, timestamps, now)
    if current_trend is None:
        return {"available": False, "reason": "no_recent_data"}

    latest = readings[-1]
    doy_now = now.timetuple().tm_yday
    cutoff = now - timedelta(hours=24)  # on exclut la situation actuelle elle-même

    analogs = []
    for r in readings:
        if r.timestamp > cutoff:
            break  # liste triée par date croissante : tout le reste est trop récent
        if _day_of_year_distance(r.timestamp.timetuple().tm_yday, doy_now) > DAY_WINDOW:
            continue

        trend = _pressure_trend(readings, timestamps, r.timestamp)
        if trend is None or abs(trend - current_trend) > TREND_TOLERANCE_HPA:
            continue

        future = _nearest_reading(readings, timestamps, r.timestamp + timedelta(hours=OUTCOME_WINDOW_HOURS), tolerance_minutes=45)
        if not future or future.temperature is None or r.temperature is None:
            continue

        analogs.append(future.temperature - r.temperature)

    if len(analogs) < MIN_ANALOGS:
        return {
            "available": False,
            "reason": "not_enough_analogs",
            "analog_count": len(analogs),
            "current_pressure": latest.pressure,
            "pressure_trend_3h_hpa": current_trend,
        }

    n = len(analogs)
    avg_change = sum(analogs) / n
    rising = sum(1 for t in analogs if t > 0.3)
    falling = sum(1 for t in analogs if t < -0.3)
    stable = n - rising - falling

    outcome = {
        "avg_temp_change_6h": round(avg_change, 1),
        "rising_pct": round(100 * rising / n),
        "falling_pct": round(100 * falling / n),
        "stable_pct": round(100 * stable / n),
    }

    return {
        "available": True,
        "current_pressure": latest.pressure,
        "pressure_trend_3h_hpa": current_trend,
        "analog_count": n,
        "outcome": outcome,
        "forecast_text": _forecast_text(current_trend, outcome),
        "confidence": _confidence(n, outcome),
        "method": (
            "Comparaison de la tendance de pression des 3 dernières heures avec des situations "
            "similaires (même tendance, +/- 15 jours autour de la même date) survenues dans "
            "l'historique de cette station, puis observation de ce qu'il s'est passé 6h plus tard."
        ),
        "limitations": LIMITATIONS,
    }


def _forecast_text(trend, outcome):
    if trend <= -1.5:
        trend_desc = "La pression chute nettement"
    elif trend <= -0.5:
        trend_desc = "La pression baisse doucement"
    elif trend >= 1.5:
        trend_desc = "La pression monte nettement"
    elif trend >= 0.5:
        trend_desc = "La pression remonte doucement"
    else:
        trend_desc = "La pression est stable"

    dominant = max(outcome["rising_pct"], outcome["falling_pct"], outcome["stable_pct"])
    if dominant == outcome["falling_pct"] and dominant >= 50:
        outlook = f"un refroidissement a suivi {outcome['falling_pct']}% du temps"
    elif dominant == outcome["rising_pct"] and dominant >= 50:
        outlook = f"un réchauffement a suivi {outcome['rising_pct']}% du temps"
    else:
        outlook = "l'évolution qui a suivi était trop partagée pour dégager une tendance nette"

    return (
        f"{trend_desc} ({trend:+.1f} hPa / 3h). Dans des situations similaires par le passé, "
        f"{outlook} dans les 6h suivantes (variation moyenne : {outcome['avg_temp_change_6h']:+.1f}°C)."
    )


def _confidence(analog_count, outcome):
    dominant = max(outcome["rising_pct"], outcome["falling_pct"], outcome["stable_pct"])
    if analog_count >= 40 and dominant >= 60:
        return "moyenne"
    return "faible"
