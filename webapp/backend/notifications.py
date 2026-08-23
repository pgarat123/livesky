"""Alertes push via ntfy.sh (https://ntfy.sh) — pas de notifications web natives
(Web Push) car ça demanderait du HTTPS + un service worker + des clés VAPID pour
un gain minime ici. ntfy fait la même chose avec une simple requête HTTP côté
serveur et une appli gratuite côté téléphone.

Aucune nouvelle dépendance : un simple POST JSON via `urllib` (stdlib).
"""

import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta

from models import db, NotificationSubscriber, AlertState, SensorReading
from sun import sun_bias_estimate

NTFY_URL = "https://ntfy.sh/"

# Seuils volontairement simples (pas de vrais niveaux de vigilance
# météorologique) : un seuil absolu par type d'alerte, cohérent avec les
# indicateurs déjà affichés sur le site.
FROST_THRESHOLD_C = 2
HEATWAVE_THRESHOLD_C = 35
HIGH_WIND_THRESHOLD_KMH = 50
OFFLINE_AFTER_MIN = 120

ALERT_META = {
    'frost': {'title': 'Risque de gel', 'tags': ['snowflake'], 'priority': 4},
    'heatwave': {'title': 'Chaleur intense', 'tags': ['fire'], 'priority': 4},
    'high_wind': {'title': 'Vent fort', 'tags': ['dash'], 'priority': 3},
    'offline': {'title': 'Station injoignable', 'tags': ['warning'], 'priority': 4},
}

ALERT_ENABLED_FIELD = {
    'frost': NotificationSubscriber.frost_enabled,
    'heatwave': NotificationSubscriber.heatwave_enabled,
    'high_wind': NotificationSubscriber.high_wind_enabled,
    'offline': NotificationSubscriber.offline_enabled,
}


def send_ntfy(topic, title, message, tags=None, priority=3):
    """Publie une notification sur un topic ntfy.sh. Retourne False (sans lever
    d'exception) si l'envoi échoue, pour ne jamais faire planter une requête
    /api/data à cause d'un problème réseau ou d'un topic invalide."""
    payload = {"topic": topic, "title": title, "message": message, "priority": priority}
    if tags:
        payload["tags"] = tags

    req = urllib.request.Request(
        NTFY_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"Erreur envoi notification ntfy (topic={topic}): {e}")
        return False


def _subscribers_for(device_id, alert_type):
    column = ALERT_ENABLED_FIELD[alert_type]
    return NotificationSubscriber.query.filter(
        NotificationSubscriber.device_id == device_id,
        column.is_(True),
    ).all()


def _get_or_create_state(device_id, alert_type):
    state = AlertState.query.filter_by(device_id=device_id, alert_type=alert_type).first()
    if not state:
        state = AlertState(device_id=device_id, alert_type=alert_type, active=False)
        db.session.add(state)
    return state


def _transition(device_id, alert_type, is_triggered, start_message, clear_message=None):
    """Envoie une notification uniquement au changement d'état (déclenchement
    ou fin d'alerte), jamais en continu tant que la condition reste vraie."""
    state = _get_or_create_state(device_id, alert_type)
    meta = ALERT_META[alert_type]

    if is_triggered and not state.active:
        state.active = True
        state.since = datetime.utcnow()
        for sub in _subscribers_for(device_id, alert_type):
            send_ntfy(sub.ntfy_topic, meta['title'], start_message, tags=meta['tags'], priority=meta['priority'])
    elif not is_triggered and state.active:
        state.active = False
        state.since = None
        if clear_message:
            for sub in _subscribers_for(device_id, alert_type):
                send_ntfy(sub.ntfy_topic, f"{meta['title']} - terminé", clear_message, tags=['white_check_mark'], priority=2)

    db.session.commit()


def check_reading_alerts(reading):
    """A appeler après l'enregistrement d'une nouvelle lecture (POST /api/data)."""
    device_id = reading.device_id

    if reading.temperature is not None:
        _transition(
            device_id, 'frost',
            reading.temperature <= FROST_THRESHOLD_C,
            f"Température actuelle : {reading.temperature}°C.",
            f"La température est remontée au-dessus de {FROST_THRESHOLD_C}°C.",
        )

        # Le seuil canicule se base sur la température estimée après correction
        # du biais solaire, pas la valeur brute : sinon une simple mesure
        # surexposée au soleil déclencherait une fausse alerte.
        sun = sun_bias_estimate(reading.temperature, reading.timestamp)
        effective_temp = sun['temperature_corrected'] if sun['temperature_corrected'] is not None else reading.temperature
        _transition(
            device_id, 'heatwave',
            effective_temp >= HEATWAVE_THRESHOLD_C,
            f"Température estimée : {effective_temp}°C (mesure brute {reading.temperature}°C).",
            f"La température est repassée sous {HEATWAVE_THRESHOLD_C}°C.",
        )

    if reading.wind_speed is not None:
        _transition(
            device_id, 'high_wind',
            reading.wind_speed >= HIGH_WIND_THRESHOLD_KMH,
            f"Vitesse du vent : {reading.wind_speed} km/h.",
            "Le vent est retombé.",
        )


def check_offline_alerts():
    """A appeler périodiquement (thread de fond) : contrairement aux autres
    alertes, celle-ci détecte une ABSENCE de lecture, donc rien ne la
    déclenche automatiquement côté /api/data."""
    device_ids = [row[0] for row in db.session.query(SensorReading.device_id).distinct().all()]
    cutoff = datetime.utcnow() - timedelta(minutes=OFFLINE_AFTER_MIN)

    for device_id in device_ids:
        latest = (SensorReading.query
                  .filter_by(device_id=device_id)
                  .order_by(SensorReading.timestamp.desc())
                  .first())
        if not latest:
            continue
        _transition(
            device_id, 'offline',
            latest.timestamp < cutoff,
            f"Dernière mesure reçue le {latest.timestamp.strftime('%d/%m %H:%M')} UTC.",
            "La station envoie de nouveau des données.",
        )
