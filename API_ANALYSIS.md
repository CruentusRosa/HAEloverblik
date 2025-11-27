# Eloverblik API Analyse og Data Oversigt

> **Note**: Se også [PYELOVERBLIK_COMPARISON.md](PYELOVERBLIK_COMPARISON.md) for sammenligning mellem pyeloverblik biblioteket og Swagger API.

## 📊 API Endpoints Oversigt

### Tilgængelige Endpoints

1. **`/customerapi/api/isalive`** (GET) ⭐
   - **Bruges til**: Tjekke om Eloverblik API servicen er oppe og kører normalt
   - **Returnerer**: Boolean (true/false)
   - **Authentication**: ❌ Ikke påkrævet (public endpoint)
   - **Status codes**: 
     - 200: Service er oppe
     - 503: Service er overbelastet eller nede
   - **Opdateringsfrekvens**: Status opdateres hver 60 sekunder
   - **Bruges i vores kode**: ❌ Nej (ikke implementeret)
   - **Anbefaling**: ⭐ **HØJ PRIORITET** - Brug dette til at tjekke service status før API calls

2. **`/customerapi/api/meterdata/gettimeseries/{dateFrom}/{dateTo}/{aggregation}`** (POST)
   - **Bruges til**: Henter timeseries data for elforbrug
   - **Aggregation muligheder**: `Actual`, `Quarter`, `Hour`, `Day`, `Month`, `Year`
   - **Begrænsning**: Max 730 dage per request
   - **Bruges i vores kode**: ✅ Ja (via `get_time_series()`)

2. **`/customerapi/api/meteringpoints/meteringpoint/getcharges`** (POST)
   - **Bruges til**: Henter charges, tariffs og fees
   - **Returnerer**: Subscriptions, tariffs (med time-for-time priser), fees
   - **Bruges i vores kode**: ✅ Ja (via `get_tariffs()`)

3. **`/customerapi/api/meteringpoints/meteringpoint/getdetails`** (POST)
   - **Bruges til**: Henter detaljerede metering point informationer
   - **Returnerer**: Master data, adresse, meter info, grid operator, etc.
   - **Bruges i vores kode**: ❌ Nej (ikke implementeret)

4. **`/customerapi/api/meterdata/getmeterreadings/{dateFrom}/{dateTo}`** (POST)
   - **Status**: ⚠️ **DEPRECATED** - No longer operational
   - **Bruges i vores kode**: ⚠️ Ja (via `get_meter_reading_latest()`) - **SKAL FJERNES**

5. **`/customerapi/api/meteringpoints/meteringpoints`** (GET)
   - **Bruges til**: Henter liste af metering points
   - **Bruges i vores kode**: ❌ Nej

6. **`/customerapi/api/token`** (GET)
   - **Bruges til**: Henter access token fra refresh token
   - **Token levetid**: 24 timer
   - **Bruges i vores kode**: ✅ Ja (håndteres af pyeloverblik biblioteket)

## 📥 Data vi henter og bruger

### 1. **Daglig Energidata** (`get_latest()`)
- **API Endpoint**: `/meterdata/gettimeseries` med `Hour` aggregation
- **Hvad vi henter**: Seneste dags time-for-time elforbrug (24 timer)
- **Bruges til**:
  - `sensor.eloverblik_energy_total` - Samlet dagligt forbrug
  - `sensor.eloverblik_energy_0_1` til `sensor.eloverblik_energy_23_24` - Time-for-time forbrug
- **Opdateringsfrekvens**: Hver time (60 min throttling)
- **Problemer**:
  - Data er typisk 1-3 dage forsinket, så "seneste dag" er faktisk for 1-3 dage siden
  - Henter kun én dag ad gangen

### 2. **Årlig Energidata** (`get_per_month()`)
- **API Endpoint**: `/meterdata/gettimeseries` med `Month` aggregation
- **Hvad vi henter**: Månedsvis elforbrug for året
- **Bruges til**:
  - `sensor.eloverblik_energy_total_year` - Samlet årligt forbrug
- **Opdateringsfrekvens**: Hver time (60 min throttling)
- **Problemer**:
  - Henter hele året hver gang, selvom kun den seneste måned er ny

### 3. **Tariffer** (`get_tariffs()`)
- **API Endpoint**: `/meteringpoints/meteringpoint/getcharges`
- **Hvad vi henter**: Alle charges (subscriptions, tariffs, fees)
- **Bruges til**:
  - `sensor.eloverblik_tariff_sum` - Nuværende timepris (kr/kWh)
  - Attribut: `hourly` - Array med priser for alle 24 timer
- **Opdateringsfrekvens**: Hver time (60 min throttling)
- **Problemer**:
  - Tariffer ændrer sig typisk kun månedligt, så hver time er for ofte

### 4. **Måleraflæsning** (`get_meter_reading_latest()`) ⚠️
- **API Endpoint**: `/meterdata/getmeterreadings` - **DEPRECATED**
- **Status**: ⚠️ Endpoint er ikke længere operational
- **Bruges til**:
  - `sensor.eloverblik_meter_reading` - Seneste måleraflæsning
- **Problemer**:
  - **DEPRECATED endpoint** - skal fjernes eller erstattes
  - Data er ikke længere tilgængelig efter 2021

### 5. **Historisk Data** (`get_time_series()`)
- **API Endpoint**: `/meterdata/gettimeseries` med `Hour` aggregation
- **Hvad vi henter**: Time-for-time data for historisk periode
- **Bruges til**:
  - `sensor.eloverblik_energy_statistic` - Langtidsstatistik til Energy Dashboard
- **Opdateringsfrekvens**: Dagligt (kun hvis der er mere end 1 dag siden sidste opdatering)
- **Problemer**:
  - Kan hente op til 730 dage ad gangen, men vi henter kun fra sidste statistik
  - Kunne optimeres til at hente flere dage ad gangen

## ⚠️ Problemer og Forbedringsmuligheder

### Kritiske Problemer

1. **⚠️ Bruger DEPRECATED endpoint**
   - `get_meter_reading_latest()` bruger et endpoint der ikke længere virker
   - **Løsning**: Fjern sensor eller find alternativ metode

2. **⭐ Mangler IsAlive check**
   - Vi tjekker ikke om servicen er oppe før vi laver API calls
   - Kunne undgå unødvendige calls og give bedre fejlbeskeder
   - **Løsning**: Implementér `/isalive` check før API calls

3. **For ofte opdateringer**
   - Henter data hver time (60 min throttling)
   - Tariffer ændrer sig typisk kun månedligt
   - Årlig data ændrer sig kun månedligt
   - **Løsning**: Forskellige throttling intervaller for forskellige data typer

3. **Ineffektiv datahentning**
   - Henter hele året hver gang for årlig data
   - Henter kun én dag ad gangen for daglig data
   - **Løsning**: Cache data bedre, hent kun nye data

### API Begrænsninger vi skal respektere

- **Max 120 calls per minut per IP** - Vi er under dette med 60 min throttling
- **Max 730 dage per request** - Vi respekterer dette
- **Token levetid 24 timer** - Håndteres af pyeloverblik
- **Data forsinkelse 1-3 dage** - Vi kan ikke gøre noget ved dette

### Anbefalinger fra API dokumentation

> "Bundle requests for 10 metering points at a time"
> "Spread out multiple requests over a longer period"
> "Don't request data for periods of several years repeatedly"
> "If you get an error 429 or 503, wait 1min. before retrying"

**Vores nuværende implementering:**
- ✅ Respekterer throttling (60 min)
- ✅ Henter kun for ét metering point
- ⚠️ Henter årlig data hver time (kunne optimeres)
- ❌ Har ikke retry logik for 429/503 errors

## 🔧 Foreslåede Forbedringer

### 1. Implementér IsAlive Check ⭐
```python
# Tjek service status før API calls
def check_service_available(self) -> bool:
    """Check if Eloverblik API service is available."""
    try:
        response = self._client.check_isalive()  # Skal implementeres i pyeloverblik
        return response.status == 200 and response.body == "true"
    except:
        return False

# Brug før hver API call:
if not self.check_service_available():
    _LOGGER.warning("Eloverblik service is unavailable, skipping update")
    return
```

**Fordele:**
- Undgå unødvendige API calls hvis servicen er nede
- Bedre fejlbeskeder til brugere
- Kan håndtere 503 errors proaktivt

### 2. Fjern Deprecated Endpoint
```python
# Fjern eller deaktiver meter reading sensor
# Endpoint er deprecated og virker ikke længere
```

### 2. Optimér Opdateringsfrekvens
```python
# Forskellige throttling intervaller:
MIN_TIME_BETWEEN_ENERGY_UPDATES = timedelta(hours=1)  # Daglig data
MIN_TIME_BETWEEN_TARIFF_UPDATES = timedelta(hours=24)  # Tariffer ændrer sig sjældent
MIN_TIME_BETWEEN_YEAR_UPDATES = timedelta(days=1)  # Årlig data ændrer sig månedligt
```

### 3. Forbedr Cache Strategi
- Cache tariffer indtil de faktisk ændrer sig
- Cache årlig data og hent kun nye måneder
- Cache daglig data bedre

### 4. Tilføj Retry Logik
```python
# Håndter 429 (Too Many Requests) og 503 (Service Unavailable)
# Vent 1 minut før retry som anbefalet i API dokumentation
```

### 5. Brug Bedre Aggregation
- For daglig data: Brug `Hour` aggregation (gør vi allerede)
- For årlig data: Brug `Month` aggregation (gør vi allerede)
- Overvej `Day` aggregation for bedre historisk data

### 6. Implementér Metering Point Details
- Kunne give mere information om metering point
- Kunne bruges til at validere metering point ID
- Kunne give bedre fejlbeskeder

## 📋 Data Flow Diagram

```
User Input (refresh_token, metering_point)
    ↓
pyeloverblik.Eloverblik
    ↓
Get Access Token (24h levetid, cached)
    ↓
┌─────────────────────────────────────┐
│  Hver time (60 min throttling):     │
│  ├─ get_latest() → Daglig data      │
│  ├─ get_per_month() → Årlig data    │
│  └─ get_tariffs() → Tariffer        │
│                                     │
│  Hver time (deprecated):            │
│  └─ get_meter_reading_latest()      │
│                                     │
│  Dagligt (hvis >1 dag siden):      │
│  └─ get_time_series() → Historisk   │
└─────────────────────────────────────┘
    ↓
Sensors i Home Assistant
```

## 🎯 Konklusion

**Hvad vi gør godt:**
- ✅ Respekterer API throttling
- ✅ Bruger korrekte endpoints (undtagen deprecated)
- ✅ Håndterer errors grundlæggende
- ✅ Bruger korrekt aggregation levels

**Hvad vi skal forbedre:**
- ⚠️ Fjern deprecated endpoint
- ⚠️ Optimér opdateringsfrekvens
- ⚠️ Forbedr cache strategi
- ⚠️ Tilføj retry logik for 429/503
- ⚠️ Overvej at hente metering point details

**Prioritering:**
1. **Høj**: Implementér IsAlive check ⭐
2. **Høj**: Fjern deprecated endpoint
3. **Medium**: Optimér opdateringsfrekvens
4. **Medium**: Tilføj retry logik
5. **Lav**: Implementér metering point details
6. **Lav**: Forbedr cache strategi

