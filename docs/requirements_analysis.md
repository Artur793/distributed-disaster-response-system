# Anforderungsanalyse für Praktikas 1-4

## Praktikum 1:

--> Leitstelle: HTTP Server - Produce Websites

--> Leitstelle: HTTP Server - Endpunkte

--> Map (Dashboard)

--> Funktionale und nicht funktionale Tests


## Praktikum 2:

- [ ] Mindestens zwei rollen  — Einsatzdrohnen, Reparaturfahrzeuge oder Versorgungs-fahrzeuge.
- [ ] Fahrzeug sollen sich unterscheiden 
- [ ] Durch Leitstelle wird’s Einsätze per RPC zugewiesen
- [ ] Apache Thrift oder Google RPC (gRPC) d¨ urfen verwendet werden.
- [ ] IDL - RPC- Schnittstelle , 
- [ ] Einsatz-ID, einen Typ, eine Zielposition und eine Priorität 
- [ ] Registration (aufgabe1)
- [ ] Einsatz vergabe soll von Ereignistyp abhängen
- [ ] Rollenzuordnung - 
- [ ] Rückmeldung - Bestätigung , simuliert Anfahrt und Bearbeitung , meldet Abschluss oder Fehler
- [ ] Zustände - idle , assighned , busy , error
- [ ] Dashboard   - Arbeitsfortschritt über REST 


## Praktikum 3:

- [ ] Middleware - Broker(Mos-quitto, HiveMQ und EMQX) und clients 
- [ ] Pub/sub - Kameras und Sensoren publizieren Ereignisse; Fahrzeuge publizieren Telemetrie wie Position, Fortschritt und Fehler.
- [ ] Ereignisverarbeitung -
- [ ] Topics und QoS - 
- [ ] Ereignisdefinition - water level cm > 80 erzeugt water level alert oder supply level percent < 20 erzeugt resupply required.
- [ ] Nchrichten format - json muss klar definiert und dokumentiert werden
- [ ] REST-Integration: Die Endpunkte GET /map und GET /status sollen weiterhin verfügbar sein, ihre Datenbasis soll nun jedoch primär aus den MQTT-Nachrichten stammen.
- [ ] Fehlerszenarien - testen Ausfall / Neustart einzelner publisher und das broker



## Praktikum 4:

- [ ] Leitstelle nicht mehr Zentral 
- [ ] Drei Fahrzeuge koordinieren sich durch request und reply gemäß das Algorithmus
- [ ] Zugriff auf Ladestationen 
- [ ] Ordnung: Die Reihenfolge konkurrierender Zugri!e muss über logische Zeit mit Totalordnung nachvollziehbar sein. 
- [ ] Passendes Kommunikationsweg wählen , begründen
- [ ] Safety - kein Fahrzeug nutzt das  Ressource gleichzeitig
- [ ] Liveness - nach Abschluss / Fehler - muss weiter arbeiten
- [ ] Fehlerbetrachtung - Nachrichtenausfall, Prozessabsturz oder nicht-FIFO-Kommunikation passiert.

