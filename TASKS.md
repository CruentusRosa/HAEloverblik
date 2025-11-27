# Opgaver og Forbedringer

Denne fil indeholder en liste over opgaver, forbedringer og kendte problemer der skal håndteres i projektet.

## 🔴 Høj Prioritet

### Kodekvalitet og Modernisering

- [x] **Opdater sensor klasser til moderne Home Assistant patterns**
  - [x] Konverter `EloverblikEnergy` fra `Entity` til `SensorEntity`
  - [x] Konverter `MeterReading` fra `Entity` til `SensorEntity`
  - [x] Konverter `EloverblikTariff` fra `Entity` til `SensorEntity`
  - [x] Opdater alle sensorer til at bruge `async_update()` i stedet for `update()`
  - [x] Tilføj korrekt `device_class` og `state_class` til alle sensorer

- [x] **Fjern forældede patterns**
  - [x] Fjern `CONNECTION_CLASS` fra `config_flow.py` (deprecated i nyere HA versioner)
  - [x] Opdater `async_setup()` funktionen hvis nødvendigt

- [x] **Ret logging problemer**
  - [x] Erstat alle `_LOGGER.warn()` med `_LOGGER.warning()` (3 steder i `__init__.py`)
  - [x] Forbedre exception handling - undgå bare `except:` klausuler
  - [x] Tilføj mere specifik exception handling

### Afhængigheder

- [x] **Opdater requirements.txt**
  - [x] Opdater Home Assistant version fra 2023.1.3 til nyere version
  - [x] Tjek om `pyeloverblik==0.4.4` er den seneste version ✅ (Seneste version, opdateret 26. januar 2025)
  - [x] Overvej at fjerne specifik HA version og bruge minimum version i stedet

- [x] **Opdater manifest.json**
  - [x] Opdater documentation og issue_tracker links til nyt repo (https://github.com/CruentusRosa/HAEloverblik)
  - [x] Opdater codeowners til nye maintainers (@CruentusRosa)
  - [x] **FJERNET pyeloverblik afhængighed - nu native implementation**
  - [ ] Opdater version nummer når ændringer er implementeret
  - [x] Tjek om alle dependencies er korrekte (kun homeassistant nu)

## 🟡 Medium Prioritet

### API Optimering (se API_ANALYSIS.md)

- [x] **Implementér IsAlive check** ⭐
  - [x] Tilføj metode til at tjekke `/isalive` endpoint
  - [x] Brug før API calls for at undgå unødvendige requests
  - [ ] Håndter 503 status proaktivt
  - [x] Tilføj bedre fejlbeskeder når servicen er nede
  - [ ] Overvej at tilføje binary sensor for service status

- [x] **Fjern deprecated endpoint**
  - [x] Fjern eller deaktiver `get_meter_reading_latest()` (endpoint er deprecated)
  - [x] Fjern `MeterReading` sensor
  - [ ] Opdater dokumentation

- [ ] **Optimér opdateringsfrekvens**
  - [ ] Implementér forskellige throttling intervaller for forskellige data typer
  - [ ] Tariffer: Opdater kun dagligt (ændrer sig sjældent)
  - [ ] Årlig data: Opdater kun dagligt (ændrer sig månedligt)
  - [ ] Daglig data: Behold hver time (men data er 1-3 dage forsinket)

- [ ] **Forbedr cache strategi**
  - [ ] Cache tariffer indtil de faktisk ændrer sig
  - [ ] Cache årlig data og hent kun nye måneder
  - [ ] Cache daglig data bedre

- [x] **Tilføj retry logik**
  - [x] Token refresh ved 401 fejl
  - [ ] Håndter 429 (Too Many Requests) - vent 1 minut
  - [ ] Håndter 503 (Service Unavailable) - vent 1 minut
  - [ ] Implementér exponential backoff

- [ ] **Implementér metering point details**
  - [ ] Hent metering point details ved setup
  - [ ] Brug til validering af metering point ID
  - [ ] Vis mere information i sensor attributes

### Fejlhåndtering

- [ ] **Forbedret fejlhåndtering**
  - [ ] Tilføj bedre fejlbeskeder til brugere
  - [ ] Håndter API timeout bedre
  - [ ] Tilføj retry logik for ustabile API calls
  - [ ] Forbedr håndtering af manglende data

- [ ] **Validering**
  - [ ] Tilføj validering af refresh token format
  - [ ] Tilføj validering af målepunkt ID format
  - [ ] Bedre fejlbeskeder ved validering

### Dokumentation

- [ ] **Opdater README**
  - [x] Opret ny README med bedre struktur
  - [ ] Tilføj screenshots af integration i Home Assistant
  - [ ] Tilføj troubleshooting sektion
  - [ ] Tilføj FAQ sektion
  - [ ] Opdater eksempler med nyere Home Assistant syntax

- [ ] **Kodedokumentation**
  - [x] Tilføj docstrings til alle klasser og funktioner
  - [x] Tilføj type hints hvor de mangler
  - [ ] Dokumenter API begrænsninger og rate limits

### Testing

- [ ] **Tilføj tests**
  - [ ] Unit tests for sensor klasser
  - [ ] Integration tests for API calls
  - [ ] Mock tests for Eloverblik API
  - [ ] Test error handling

## 🟢 Lav Prioritet

### Features

- [ ] **Nye features**
  - [ ] Tilføj support for flere målepunkter i samme integration
  - [ ] Tilføj konfigurerbare opdateringsintervaller
  - [ ] Tilføj support for push notifikationer ved højt forbrug
  - [ ] Tilføj automatisk genoprettelse ved API fejl

- [ ] **Forbedringer**
  - [ ] Optimér API calls (reducer antal calls)
  - [ ] Cache data bedre
  - [ ] Forbedr performance ved store datasæt
  - [ ] Tilføj support for historiske data eksport

### UI/UX

- [ ] **Forbedringer**
  - [ ] Tilføj bedre entity names og descriptions
  - [ ] Tilføj device information
  - [ ] Forbedr sensor icons
  - [ ] Tilføj danske oversættelser (se nedenfor)

### Oversættelser

- [ ] **Oversættelser**
  - [ ] Gennemgå eksisterende oversættelser (da.json, en.json, nb.json)
  - [ ] Opdater oversættelser med nye strings
  - [ ] Tilføj manglende oversættelser
  - [ ] Tjek for konsistens mellem sprog

## 🐛 Kendte Problemer

- [ ] **API Stabilitet**
  - [ ] Dokumenter kendte problemer med Eloverblik API
  - [ ] Tilføj workarounds for API begrænsninger
  - [ ] Overvej at tilføje fallback mekanismer

- [ ] **Data Forsinkelse**
  - [ ] Dokumenter at data er 1-3 dage forsinket
  - [ ] Overvej at tilføje indikator for data alder
  - [ ] Tilføj advarsel i UI hvis data er for gamle

## 📋 Code Review Checklist

Før en PR merges, skal følgende tjekkes:

- [ ] Koden følger Home Assistant coding standards
- [ ] Alle sensorer bruger moderne patterns (`SensorEntity`, `async_update`)
- [ ] Exception handling er specifik (ingen bare `except:`)
- [ ] Logging bruger korrekt niveau (`warning` ikke `warn`)
- [ ] Type hints er tilføjet hvor relevant
- [ ] Docstrings er tilføjet til nye funktioner
- [ ] Tests er tilføjet for nye features
- [ ] README er opdateret hvis nødvendigt
- [ ] Manifest version er opdateret
- [ ] Ingen breaking changes uden version bump

## 🔄 Vedligeholdelse

### Regelmæssige opgaver

- [ ] **Månedligt**
  - [x] Tjek for opdateringer til `pyeloverblik` biblioteket ✅ (0.4.4 er seneste, opdateret jan 2025)
  - [ ] Tjek for Home Assistant breaking changes
  - [ ] Gennemgå issues på GitHub

- [ ] **Ved hver release**
  - [ ] Opdater version i manifest.json
  - [ ] Opdater CHANGELOG.md (hvis den eksisterer)
  - [ ] Test integrationen med nyeste Home Assistant version
  - [ ] Opdater README med nye features

## 📝 Noter

- Eloverblik API er kendt for at være ustabilt og langsomt - dette er uden for vores kontrol
- Data fra Eloverblik er typisk 1-3 dage forsinket afhængigt af DSO
- Integrationen bruger throttling (60 minutter) for at undgå for mange API calls

---

**Sidst opdateret**: 2024

