# Finanzanalyse

**Persönliche Finanzdaten verstehen – mit Python und Datenanalyse.**

Die Finanzanalyse ist eine Python-Anwendung zur Auswertung und Visualisierung persönlicher Finanztransaktionen. Sie importiert Bankumsätze aus CSV-Dateien, speichert die Daten in einer SQLite-Datenbank und stellt sie über ein interaktives Streamlit-Dashboard zur Verfügung.

Das Projekt verbindet Datenverarbeitung, Datenbankverwaltung und Webentwicklung zu einem praktischen Werkzeug für die persönliche Finanzübersicht.

## Ziele des Projekts

- Persönliche Finanztransaktionen strukturiert erfassen und auswerten
- Einnahmen und Ausgaben nachvollziehbar analysieren
- Finanzdaten übersichtlich visualisieren
- Eine lokal ausführbare Anwendung mit Python entwickeln

## Funktionen

- **CSV-Import:** Bankumsätze aus CSV-Dateien einlesen
- **Datenbank:** Transaktionen mit SQLite speichern
- **Datenanalyse:** Finanzdaten mit pandas verarbeiten und auswerten
- **Dashboard:** Ergebnisse mit Streamlit interaktiv darstellen
- **Kategorien:** Kategorien individuell an die eigenen Anforderungen anpassen
- **Lokale Nutzung:** Die Anwendung auf dem eigenen Rechner ausführen

## Technologien

- Python 3.12+
- pandas – Datenverarbeitung und Analyse
- SQLite – lokale Datenspeicherung
- Streamlit – interaktives Dashboard
- uv – Verwaltung von Python-Umgebung und Abhängigkeiten


## Projektstatus

Persönliches Lern- und Demonstrationsprojekt, das praktische Datenanalyse mit der Entwicklung einer vollständigen Python-Anwendung verbindet.
Das Projekt wird schrittweise weiterentwickelt. Rückmeldungen und Anregungen sind willkommen.

## Einblick in das Dashboard

Die Anwendung stellt die Finanzdaten übersichtlich dar.

![Finanzanalyse-Dashboard](screenshots/dashboard.png)

---


## Voraussetzungen

- Python 3.12 oder neuer
- [uv – Python-Paket- und Projektverwaltung](https://docs.astral.sh/uv/)

Falls `uv` noch nicht installiert ist, kann es unter Linux mit folgendem Befehl installiert werden:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Weitere Installationsmöglichkeiten findest du in der offiziellen Dokumentation:

https://docs.astral.sh/uv/getting-started/installation

Danach gegebenenfalls ein neues Terminal öffnen und mit `uv --version` prüfen, ob die Installation funktioniert hat.

## Projekt entpacken

Die heruntergeladene ZIP-Datei zunächst entpacken. Unter Linux geht das per Rechtsklick → „Hier entpacken“ oder im Terminal mit:

```bash
unzip Finanzanalyse.zip
```
Anschließend in das Projektverzeichnis wechseln und mit der Installation fortfahren.

## Installation

Ins Projektverzeichnis wechseln und die Abhängigkeiten mit folgendem Befehl installieren:

```bash
uv sync
```

uv erstellt dabei die virtuelle Umgebung `.venv` und installiert die benötigten Pakete anhand der Projektkonfiguration und der Lockdatei.

## Datenimport

Die Umsatzdaten werden aus CSV-Dateien in die Datenbank importiert.
Die Datei `Beispielumsatz_2026.csv` im Hauptverzeichnis des Projekts enthält fiktive Umsatzdaten und steht zum Testen der Anwendung zur Verfügung. Zum Import die Datei in den Rohdatenordner `data/raw/` verschieben.

## Anwendung starten

Das Dashboard mit folgendem Befehl im Projektverzeichnis starten:

```bash
uv run streamlit run src/finanzanalyse/dashboard.py
```

Streamlit zeigt nach dem Start die erreichbaren Adressen im Terminal an, zum Beispiel:

```text
Local URL:   http://localhost:8501
Network URL: http://192.168.0.19:8501
```

- **Local URL:** Zugriff auf dem eigenen Rechner.
- **Network URL:** Zugriff von anderen Geräten im selben Netzwerk, beispielsweise einem Smartphone.


### Ablauf

1. Die CSV-Dateien manuell im Rohdatenordner `data/raw/` ablegen.
2. Anwendung starten. Die Dateien werden beim Start eingelesen.
3. Die eingelesenen Dateien werden anschließend automatisch nach `data/imported/` verschoben.

Damit bleiben die ursprünglichen Importdateien von den bereits verarbeiteten Dateien getrennt.

### Datenbank konfigurieren

Der Name der Datenbank kann in `src/database.py` angepasst werden. Dazu folgende Zeile bearbeiten:

```python
DB_FILE = DATA_DIR / "beispiel.db"
```

`beispiel.db` durch den gewünschten Datenbanknamen ersetzen.

## Kategorien

Die Kategorien lassen sich individuell anpassen.

Dazu das Dictionary `KATEGORIEN` in `src/kategorien.py` bearbeiten. Hier können die Kategorien entsprechend den persönlichen Anforderungen an die Finanzanalyse definiert werden.

## Hinweis zur Nutzung und Haftung

Diese Software ist ein privates Lern- und Demonstrationsprojekt zur Analyse von Finanztransaktionen. Sie wird kostenlos und ohne Zusicherung bestimmter Eigenschaften bereitgestellt.

Die Auswertungen dienen ausschließlich der Information und stellen keine Finanz-, Steuer- oder Anlageberatung dar. Trotz sorgfältiger Entwicklung können Fehler auftreten. Ergebnisse und Berechnungen sollten vor einer Verwendung für finanzielle Entscheidungen eigenständig überprüft werden.

Die Nutzung erfolgt im Rahmen der geltenden gesetzlichen Bestimmungen. Eine Haftung wird ausgeschlossen, soweit dies gesetzlich zulässig ist. Zwingende gesetzliche Haftung bleibt unberührt.

## Lizenz

Der Quellcode dieses Projekts steht unter der MIT-Lizenz. Einzelheiten sind der Datei `LICENSE` zu entnehmen.

Verwendete Drittanbieterbibliotheken unterliegen ihren jeweiligen Lizenzbedingungen.
