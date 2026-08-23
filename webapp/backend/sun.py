"""Estimation de l'exposition au soleil du capteur de température.

Le capteur DFRobot Lark n'est pas ventilé activement et n'est pas protégé du
rayonnement solaire direct (contrairement à un abri Stevenson). En plein
soleil, il chauffe plus vite que l'air ambiant et surestime la température
réelle ; la nuit ou par ciel couvert, il n'y a pas ce biais.

On n'a pas de capteur de luminosité/nébulosité sur la station : on ne peut
donc pas savoir s'il fait vraiment soleil. Ce module calcule seulement la
hauteur du soleil au-dessus de l'horizon (position astronomique, fonction du
lieu et de l'heure) et l'utilise comme *proxy* du risque de biais — c'est un
majorant "ciel dégagé", pas une mesure du biais réel.
"""

import math
import os

# Coordonnées approximatives de la station (Lauzès, Lot, France).
# À corriger via les variables d'environnement STATION_LAT / STATION_LON si
# la position réelle est différente : la précision du calcul de hauteur
# solaire (et donc du seuil jour/nuit) en dépend directement.
STATION_LAT = float(os.environ.get('STATION_LAT', '44.598'))
STATION_LON = float(os.environ.get('STATION_LON', '1.483'))

# Biais radiatif maximal estimé, en plein soleil à la mi-journée (°C).
MAX_RADIATIVE_BIAS_C = 3.5


def solar_elevation_deg(timestamp_utc, lat=STATION_LAT, lon=STATION_LON):
    """Hauteur angulaire approximative du soleil au-dessus de l'horizon (°).

    Formule NOAA simplifiée (sans "equation of time"), précise à quelques
    degrés/minutes près : largement suffisant pour classer une lecture en
    "nuit / soleil bas / soleil haut", pas pour un calcul astronomique exact.
    """
    day_of_year = timestamp_utc.timetuple().tm_yday
    declination = math.radians(23.45) * math.sin(math.radians(360 / 365 * (day_of_year - 81)))

    solar_time = timestamp_utc.hour + timestamp_utc.minute / 60 + lon / 15
    hour_angle = math.radians(15 * (solar_time - 12))

    lat_rad = math.radians(lat)
    elevation_rad = math.asin(
        math.sin(lat_rad) * math.sin(declination)
        + math.cos(lat_rad) * math.cos(declination) * math.cos(hour_angle)
    )
    return math.degrees(elevation_rad)


def classify_exposure(timestamp_utc):
    """Retourne ('none' | 'low' | 'high', hauteur_soleil_deg)."""
    elevation = solar_elevation_deg(timestamp_utc)
    if elevation <= 0:
        risk = 'none'
    elif elevation <= 15:
        risk = 'low'
    else:
        risk = 'high'
    return risk, elevation


def _radiative_bias(elevation):
    if elevation <= 0:
        return 0.0
    if elevation <= 15:
        return MAX_RADIATIVE_BIAS_C * (elevation / 15) * 0.4
    # Le biais croît avec la hauteur du soleil puis plafonne : un soleil
    # déjà haut dans le ciel ne "brûle" pas beaucoup plus le capteur.
    return MAX_RADIATIVE_BIAS_C * min(1.0, elevation / 45)


def sun_bias_estimate(temperature, timestamp_utc):
    """Diagnostic + température 'corrigée' estimée pour une lecture.

    ATTENTION : la correction suppose un ciel dégagé. Par temps couvert le
    biais réel est plus faible (voire nul) ; `temperature_corrected` est donc
    une estimation de pire cas, pas une mesure fiable.
    """
    risk, elevation = classify_exposure(timestamp_utc)
    if temperature is None:
        return {"sun_elevation_deg": round(elevation, 1), "exposure_risk": risk, "temperature_corrected": None}

    bias = _radiative_bias(elevation)
    corrected = round(temperature - bias, 1) if bias > 0 else temperature

    return {
        "sun_elevation_deg": round(elevation, 1),
        "exposure_risk": risk,
        "temperature_corrected": corrected,
    }
