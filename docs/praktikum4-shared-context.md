# Aufgabe 4 - Shared Context: Ricart/Agrawala

## Ziel

In Aufgabe 4 koordinieren die Fahrzeuge den exklusiven Zugriff auf eine knappe Ressource selbst. Die Leitstelle darf den Zugriff nicht vergeben, sondern nur beobachten und visualisieren.

Wir verwenden den Ricart/Agrawala-Algorithmus fuer gegenseitigen Ausschluss.

## Kritische Ressource

Es wird genau ein Ladeplatz koordiniert:

```json
{
  "resource_id": "charging-station-1-slot-1",
  "type": "charging_slot",
  "station_id": "charging-station-1",
  "capacity": 1,
  "position": { "x": 9, "y": 6 }
}
```

Die Position `(9, 6)` existiert bereits als `CHARGING_STATION` in der aktuellen Karte. Die zweite vorhandene Ladestation bei `(15, 15)` bleibt vorerst unkoordiniert.

## Teilnehmer

Wir verwenden die aktuell vorhandenen drei Fahrzeuge:

```text
drone-1
rover-1
boat-1
```

Alle drei Fahrzeuge implementieren dieselbe Ricart/Agrawala-Logik. Es werden keine neuen Fahrzeugtypen nur fuer Aufgabe 4 benoetigt.

## Kommunikationsweg

Ricart/Agrawala-Nachrichten laufen ueber den bestehenden Mosquitto-Broker aus Aufgabe 3.

Wichtig fuer die Abnahme:

```text
Der Broker transportiert nur Nachrichten.
Die Leitstelle entscheidet nicht ueber den Zugriff.
Die Zugriffentscheidung entsteht nur in den Fahrzeugen.
```

RPC bleibt fuer die Einsatzvergabe aus Aufgabe 2 bestehen. Aufgabe 4 nutzt MQTT fuer dezentrale Fahrzeug-zu-Fahrzeug-Koordination.

## Ricart/Agrawala-Zustaende

Die normalen Fahrzeugzustaende bleiben unveraendert:

```text
IDLE, ASSIGNED, BUSY, COMPLETED, ERROR, CHARGING
```

Zusaetzlich bekommt jedes Fahrzeug einen separaten RA-Zustand:

```text
RELEASED - Fahrzeug moechte den Ladeplatz nicht nutzen
WANTED   - Fahrzeug wartet auf REPLYs
HELD     - Fahrzeug nutzt den Ladeplatz gerade
```

`HELD` ist der kritische Abschnitt. Fuer dieselbe `resource_id` darf nie mehr als ein Fahrzeug gleichzeitig `HELD` sein.

## Batterie und Ladesimulation

Ein Fahrzeug fordert den Ladeplatz an, wenn seine Batterie unter den Schwellwert faellt:

```text
battery_percent < 20
```

Die Ladesimulation soll kurz bleiben:

```text
+10 Prozent Batterie pro Sekunde
```

Beispiel: Ein Fahrzeug mit 20 Prozent braucht etwa 8 Sekunden bis 100 Prozent.

## Lamport-Ordnung

Jedes Fahrzeug fuehrt eine lokale Lamport-Uhr.

Regeln:

```text
1. Vor dem Senden von REQUEST oder REPLY wird die Uhr erhoeht.
2. Beim Empfangen wird gesetzt: local_clock = max(local_clock, received_lamport) + 1.
3. Konkurrierende Requests werden nach (lamport, vehicle_id) sortiert.
```

Kleinere Lamport-Zeit gewinnt. Bei gleicher Lamport-Zeit gewinnt die lexikographisch kleinere `vehicle_id`.

## MQTT Topics und QoS

```text
REQUEST: island/coordination/charging/request
REPLY:   island/coordination/charging/reply/{target_vehicle_id}
STATUS:  island/coordination/charging/status
```

QoS:

```text
REQUEST QoS 1
REPLY   QoS 1
STATUS  QoS 1
```

Retained messages sollen fuer diese Topics nicht verwendet werden.

## Nachrichtenformat

Alle Nachrichten verwenden JSON und snake_case.

Gemeinsame Felder:

```json
{
  "message_id": "drone-1-1781366709123-1",
  "type": "REQUEST | REPLY | STATUS",
  "resource_id": "charging-station-1-slot-1",
  "sender_id": "drone-1",
  "lamport": 12,
  "sent_at": "2026-06-23T10:15:00Z"
}
```

`message_id` folgt dem Stil aus Aufgabe 3:

```text
{sender_id}-{timestamp_ms}-{counter}
```

### REQUEST

```json
{
  "message_id": "drone-1-1781366709123-1",
  "type": "REQUEST",
  "resource_id": "charging-station-1-slot-1",
  "sender_id": "drone-1",
  "lamport": 12,
  "request_id": "drone-1-12",
  "battery_percent": 14,
  "reason": "LOW_BATTERY",
  "sent_at": "2026-06-23T10:15:00Z"
}
```

### REPLY

```json
{
  "message_id": "rover-1-1781366712123-2",
  "type": "REPLY",
  "resource_id": "charging-station-1-slot-1",
  "sender_id": "rover-1",
  "target_vehicle_id": "drone-1",
  "lamport": 15,
  "request_id": "drone-1-12",
  "sent_at": "2026-06-23T10:15:03Z"
}
```

### STATUS

```json
{
  "message_id": "drone-1-1781366713123-3",
  "type": "STATUS",
  "resource_id": "charging-station-1-slot-1",
  "sender_id": "drone-1",
  "vehicle_id": "drone-1",
  "vehicle_state": "BUSY",
  "ra_state": "WANTED",
  "lamport": 12,
  "waiting_for": ["rover-1", "boat-1"],
  "deferred_replies": [],
  "battery_percent": 14,
  "sent_at": "2026-06-23T10:15:01Z"
}
```

## Algorithmusregeln

Wenn ein Fahrzeug laden will:

```text
1. Wechsel nach WANTED.
2. Lamport-Uhr erhoehen.
3. Eigenen Request speichern: (lamport, vehicle_id).
4. REQUEST an alle Fahrzeuge senden.
5. Auf REPLY von allen anderen Teilnehmern warten.
6. Erst danach nach HELD wechseln und laden.
```

Wenn ein Fahrzeug einen REQUEST empfaengt:

```text
- Ist der eigene Zustand HELD, wird die REPLY zurueckgestellt.
- Ist der eigene Zustand WANTED und der eigene Request hat Prioritaet, wird die REPLY zurueckgestellt.
- Sonst wird sofort REPLY gesendet.
```

Nach dem Laden:

```text
1. Wechsel nach RELEASED.
2. Zurueckgestellte REPLYs senden.
3. STATUS publizieren.
```

## Deduplizierung

Wegen QoS 1 koennen Nachrichten mehrfach ankommen.

Jedes Fahrzeug speichert verarbeitete IDs:

```text
seen_message_ids
seen_request_ids
```

Regeln:

```text
- Eine message_id wird nur einmal verarbeitet.
- Alte oder abgeschlossene request_id-Werte werden ignoriert.
- Eine REPLY fuer einen nicht mehr offenen Request wird ignoriert.
```

## Leitstelle und Dashboard

Die Leitstelle abonniert nur STATUS-Nachrichten und erweitert daraus `/status` und das Dashboard.

Erlaubt:

```text
- aktuellen RA-Zustand anzeigen
- current_holder anzeigen
- waiting_vehicles anzeigen
- Lamport-Werte anzeigen
- Safety-Verletzungen loggen
```

Nicht erlaubt:

```text
- Ladeplatz vergeben
- REQUESTs priorisieren
- REPLYs erzeugen
- zentrale Warteschlange verwalten
```

## Aufgabenverteilung

### Person A - Fahrzeuglogik und Ricart/Agrawala

Verantwortlich fuer:

```text
- Batterie-Schwellwert battery_percent < 20
- Ladesimulation mit +10 Prozent pro Sekunde
- RA-Zustaende RELEASED, WANTED, HELD in den Fahrzeugen
- Lamport-Uhr pro Fahrzeug
- REQUEST publishen
- REQUEST empfangen und Prioritaet bewerten
- REPLY publishen
- REPLY empfangen und waiting_for aktualisieren
- deferred_replies verwalten
- Eintritt in HELD erst nach allen REPLYs
- Verlassen von HELD und Senden zurueckgestellter REPLYs
- Deduplizierung in den Fahrzeugen
- Fahrzeuglogs fuer REQUEST, REPLY, HELD, RELEASED
```

### Person B - Leitstelle, Dashboard, Beobachtung und Tests

Verantwortlich fuer:

```text
- Leitstelle abonniert island/coordination/charging/status
- STATUS JSON parsen und speichern
- GET /status um charging_coordination erweitern
- Dashboard-Anzeige fuer Ladeplatzstatus
- Anzeige von current_holder, waiting_vehicles und Teilnehmerzustaenden
- Safety-Verletzungen erkennen und loggen
- MQTT Explorer Nachweise vorbereiten
- Testprotokoll fuer Aufgabe 4 spaeter ergaenzen
- Fehlerfaelle spaeter dokumentieren: Broker-Ausfall, Fahrzeugabsturz, Duplikate
```

### Gemeinsam

```text
- Pruefen, dass alle drei Fahrzeuge dieselbe Teilnehmerliste nutzen
- Pruefen, dass alle dieselbe resource_id nutzen
- Safety-Test: nie zwei Fahrzeuge gleichzeitig HELD
- Liveness-Test: wartende Fahrzeuge kommen nach Freigabe weiter
- Abnahme-Erklaerung gemeinsam vorbereiten
```

## Noch offen

Die konkrete Testausloesung wird spaeter entschieden.

Moegliche Varianten:

```text
- Env-Variable pro Fahrzeugcontainer
- Startparameter
- manueller Testmodus im Code
```
