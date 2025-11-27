# Eloverblik Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

En Home Assistant custom component til at overvåge dit elforbrug fra [eloverblik.dk](https://eloverblik.dk).

## 📋 Oversigt

Denne integration henter elforbrugsdata fra Eloverblik og gør dem tilgængelige som sensorer i Home Assistant. 

### ✨ Hovedfunktioner

- **🔍 Automatisk målepunkt detection** - Vælg fra dine tilgængelige målepunkter
- **⚡ Native API implementation** - Ingen eksterne afhængigheder ud over Home Assistant
- **📊 Energy Dashboard support** - Fuld integration med Home Assistant's Energy Dashboard
- **🔄 Smart caching** - Intelligent caching reducerer API calls
- **🛡️ Robust fejlhåndtering** - Automatisk retry med exponential backoff
- **📈 Forbedret langtidsstatistikker** - Opdateres hver 6. time for bedre kurver

### 📊 Data Typer

- Time-for-time elforbrug for de seneste 24 timer
- Samlet dagligt elforbrug
- Årligt elforbrug
- Tariffer og priser (med time-for-time priser)
- Langtidsstatistikker til brug i Energy Dashboard og kurver

## ⚠️ Vigtig Information

**Projektstatus**: Dette projekt er en fork/opdateret version af det oprindelige projekt. Den oprindelige udvikler vedligeholder ikke længere aktivt projektet, men der arbejdes på at opdatere og forbedre integrationen.

Bemærk at Eloverblik API kan være ustabilt og langsomt - dette er uden for vores kontrol.

## 🚀 Installation

### Installation via HACS (Anbefalet)

1. Sørg for at [HACS](https://hacs.xyz/) er installeret.
2. Søg efter og installer `eloverblik` integrationen gennem HACS.
   * Eller brug denne genvej:  
   [![Open your Home Assistant instance and open a the Eloverblik repository inside the Home Assistant Community Store](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=CruentusRosa&repository=HAEloverblik&category=integration)
3. Genstart Home Assistant (Settings → ⋮ → Restart Home Assistant → Restart).
4. [Konfigurer](#konfiguration) Eloverblik gennem Settings → Devices & Services → Add Integration.
   * Eller brug denne genvej:  
   [![Open your Home Assistant instance and start setting up a Eloverblik](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=eloverblik)

### Manuel Installation

1. Kopiér `eloverblik` mappen ind i din `custom_components` mappe i din Home Assistant konfigurationsmappe.
2. Genstart Home Assistant (Settings → ⋮ → Restart Home Assistant → Restart).
3. [Konfigurer](#konfiguration) Eloverblik gennem Settings → Devices & Services → Add Integration.
   * Eller brug denne genvej:  
   [![Open your Home Assistant instance and start setting up a Eloverblik](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=eloverblik)

## ⚙️ Konfiguration

### Refresh Token

For at bruge integrationen skal du have et refresh token fra [eloverblik.dk](https://eloverblik.dk/customer/).

1. Log ind på [Eloverblik](https://eloverblik.dk/customer/overview/).
2. Opret et refresh token:
   1. Klik på din bruger.
   2. Vælg **Data Sharing**.
   3. Klik **Create token** og gennemfør trinnene med dine præferencer.

### Konfiguration i Home Assistant

1. Gå til **Settings** → **Devices & Services** → **Add Integration**.
2. Søg efter **Eloverblik**.
3. Indtast dit **Refresh Token**.
4. Integrationen henter automatisk dine tilgængelige målepunkter.
5. Vælg det målepunkt du vil overvåge fra dropdown listen.

> **Bemærk**: Integrationen henter automatisk alle dine målepunkter fra Eloverblik API, så du ikke behøver at kende målepunkt ID'et på forhånd.

## 📊 Sensorer og Attributter

### Energisensorer

Integrationen opretter sensorer for hver time i de seneste 24 timer:
- `sensor.eloverblik_energy_0_1` (time 0-1)
- `sensor.eloverblik_energy_1_2` (time 1-2)
- ... (op til 24 timer)

**Attributes**: Alle energisensorer inkluderer metering point information (adresse, type, grid operator, etc.)

### Totalsensorer

- `sensor.eloverblik_energy_total` - Samlet dagligt elforbrug (kWh)
  - Opdateres hver time
  - Viser data fra i går (data er 1-3 dage forsinket)
  
- `sensor.eloverblik_energy_total_year` - Samlet årligt elforbrug (kWh)
  - Opdateres dagligt
  - Viser månedsvis aggregering

### Tarifsensor

- `sensor.eloverblik_tariff_sum` - Nuværende timepris (kr/kWh)
  - **Opdatering**: Dagligt (med 24 timer cache)
  - **Attributes**: 
    - `hourly` - Array med priser for alle 24 timer
    - Metering point information

### Statistiksensor

- `sensor.eloverblik_energy_statistic` - Langtidsstatistik til Energy Dashboard
  - **State Class**: `total_increasing` - Kumulativt totalt forbrug over tid
  - **Opdatering**: Hver 6. time for bedre kurver
  - **Bruges til**: Energy Dashboard, historiske kurver, og langtidsanalyse
  - Viser kumulativt totalt forbrug og importerer time-for-time data til long-term statistics
  - **Note**: Sensoren kan vise "unknown" som værdi, men indeholder stadig gyldige langtidsstatistikker

Alle sensorer viser værdier i kWh (undtagen tarifsensoren som viser kr/kWh).

## 📈 Langtidsstatistik og Energy Dashboard

Integrationen understøtter langtidsstatistikker og kan bruges i Home Assistants Energy Dashboard.

### 🚀 Forbedringer i v0.7.0

- **⚡ Opdatering hver 6. time**: Langtidsstatistikker opdateres nu hver 6. time i stedet for dagligt, hvilket giver bedre kurver og mere opdateret data.
- **📊 Kontinuerlig tracking**: Data importeres time-for-time, så du får glatte kurver over tid.
- **✅ Energy Dashboard ready**: Sensoren bruger `total_increasing` state class, hvilket gør den perfekt til Energy Dashboard.
- **🔄 Smart data håndtering**: Integrationen henter kun nye data og håndterer automatisk data delay.

### 📥 Hvordan det virker

Integrationen henter automatisk historiske data fra sidste år og opdaterer løbende med nye data. Data importeres time-for-time til Home Assistant's recorder, så du kan se detaljerede kurver over dit elforbrug.

> **Bemærk**: Data vil være forsinket med 1-3 dage afhængigt af din lokale netoperatør (DSO). Integrationen håndterer dette automatisk ved kun at hente data op til 2 dage siden.

### Eksempel: Gårs forbrug

```yaml
type: statistic
name: Elforbrug i går
entity: sensor.eloverblik_energy_statistic
period:
  calendar:
    period: day
    offset: -1
stat_type: change
icon: mdi:lightning-bolt
```

### Eksempel: Sidste 7 dages forbrug (ApexCharts)

```yaml
type: custom:apexcharts-card
graph_span: 7d
header:
  show: true
  title: Sidste 7 dages elforbrug
span:
  end: day
  offset: '-1d'
series:
  - entity: sensor.eloverblik_energy_statistic
    type: column
    statistics:
      type: sum
      period: hour
    group_by:
      func: diff
      start_with_last: true
      duration: 1d
```

## 🔍 Debugging

For at aktivere debug-logging af rådata fra eloverblik.dk API, tilføj følgende til din `configuration.yaml`:

```yaml
logger: 
  default: info
  logs: 
    custom_components.eloverblik: debug
```

Du kan også ændre logniveauet gennem UI via service calls.

> **Note**: Integrationen bruger nu native API implementation, så der er ingen `pyeloverblik` logging længere.

## 🛠️ Troubleshooting

### Integrationen kan ikke forbinde

- **Tjek dit refresh token**: Sørg for at dit refresh token er gyldigt og ikke er udløbet. Generer et nyt token i Eloverblik portalen hvis nødvendigt.
- **Tjek internetforbindelse**: Integrationen skal kunne tilgå `api.eloverblik.dk`.
- **Tjek service status**: Integrationen tjekker automatisk om Eloverblik servicen er oppe før API calls.

### Data vises ikke eller er for gamle

- **Data forsinkelse**: Eloverblik data er typisk 1-3 dage forsinket. Dette er normalt og afhænger af din lokale netoperatør (DSO).
- **Ingen data for i dag**: Dette er forventet - data er altid forsinket. Brug data fra i går eller tidligere.
- **Statistics sensor viser "unknown"**: Dette er normalt. Sensoren indeholder stadig gyldige langtidsstatistikker selvom værdien vises som "unknown".

### API fejl (429, 503)

- **429 (Too Many Requests)**: Integrationen håndterer dette automatisk med exponential backoff. Vent et øjeblik og prøv igen.
- **503 (Service Unavailable)**: Eloverblik servicen kan være overbelastet eller nede. Integrationen prøver automatisk igen med exponential backoff.

### Målepunkt ikke fundet

- **Sørg for at målepunktet er linket**: Gå til Eloverblik portalen og sørg for at målepunktet er linket til din konto.
- **Brug automatisk detection**: Integrationen henter automatisk alle dine målepunkter - vælg fra listen i stedet for at indtaste manuelt.

## ❓ FAQ

### Hvor ofte opdateres dataene?

- **Daglig data**: Hver time (60 minutter throttling)
- **Årlig data**: Dagligt (24 timer throttling)
- **Tariffer**: Dagligt (24 timer throttling, med cache)
- **Statistics**: Hver 6. time

### Hvorfor er data forsinket?

Eloverblik modtager data fra din lokale netoperatør (DSO), som typisk sender data med 1-3 dages forsinkelse. Dette er normalt og kan ikke ændres.

### Kan jeg bruge integrationen med flere målepunkter?

Ja, du kan tilføje integrationen flere gange med forskellige målepunkter. Hver integration er uafhængig.

### Hvad betyder "unknown" i statistics sensoren?

Dette er normalt. Statistics sensoren viser "unknown" som værdi, men indeholder stadig gyldige langtidsstatistikker der kan bruges i Energy Dashboard og kurver.

### Hvordan ved jeg om min refresh token er gyldig?

Hvis integrationen ikke kan forbinde, kan det være fordi dit refresh token er udløbet. Generer et nyt token i Eloverblik portalen under Data Sharing.

## 💡 Eksempler

### Dagligt gennemsnit og gauge

Dette eksempel viser dagligt gennemsnit og en gauge der indikerer højt forbrug.

**Krav:**
- Recorder component med minimum det antal dage gennemsnittet skal dække
- [Lovelace Config Template Card](https://github.com/iantrich/config-template-card)

**Statistik sensor:**

```yaml
sensor:
  - platform: statistics
    entity_id: sensor.eloverblik_energy_total
    name: Eloverblik Monthly Statistics
    sampling_size: 50
    state_characteristic: mean
    max_age:
      days: 30
```

**Lovelace:**

```yaml
type: vertical-stack
cards:
  - card:
      entity: sensor.eloverblik_energy_total
      max: 20
      min: 0
      name: >-
        ${'Strømforbrug d. ' +
        states['sensor.eloverblik_energy_total'].attributes.metering_date }
      severity:
        green: 0
        red: '${states[''sensor.eloverblik_monthly_statistics''].state * 1.25}'
        yellow: '${states[''sensor.eloverblik_monthly_statistics''].state * 1.10}'
      type: gauge
    entities:
      - sensor.eloverblik_energy_total
      - sensor.eloverblik_monthly_statistics
    type: 'custom:config-template-card'
  - type: entity
    entity: sensor.eloverblik_monthly_statistics
    name: Daglig gennemsnit
```

### Prognose for total kWh pris med Nordpool integration

Hvis du har [Nordpool](https://github.com/custom-components/nordpool) installeret, kan du beregne den nuværende elpris og prognosticere prisen for i dag og i morgen time-for-time. Disse priser inkluderer alle tariffer der gælder, som justeres efter spidsbelastningstider og sæson, da de hentes fra Eloverblik.

**Template sensor:**

```yaml
template:
  - sensor:
    - name: "Electricity Cost"
      unique_id: electricity_cost
      device_class: monetary
      unit_of_measurement: "kr/kWh"
      state: >
        {{ 1.25 * (float(states('sensor.eloverblik_tariff_sum')) + float(states('sensor.nordpool'))) }}
      attributes:
        today: >
          {% if state_attr('sensor.eloverblik_tariff_sum', 'hourly') and state_attr('sensor.nordpool', 'today') %}
            {% set ns = namespace (prices=[]) %}
            {% for h in range(24) %}
              {% set ns.prices = ns.prices + [(1.25 * (float(state_attr('sensor.eloverblik_tariff_sum', 'hourly')[h]) + float(state_attr('sensor.nordpool', 'today')[h]))) | round(5)] %}
            {% endfor %}
            {{ ns.prices }}
          {% endif %}
        tomorrow: >
          {% if state_attr('sensor.eloverblik_tariff_sum', 'hourly') and state_attr('sensor.nordpool', 'tomorrow') %}
            {% set ns = namespace (prices=[]) %}
            {% for h in range(24) %}
              {% set ns.prices = ns.prices + [(1.25 * (float(state_attr('sensor.eloverblik_tariff_sum', 'hourly')[h]) + float(state_attr('sensor.nordpool', 'tomorrow')[h]))) | round(5)] %}
            {% endfor %}
            {{ ns.prices }}
          {% endif %}
```

> **Bemærk**: Skift `nordpool` med navnet på din Nordpool sensor. Template antager at din Nordpool integration er konfigureret til IKKE at inkludere moms.

## 🛠️ Udvikling

Pull requests er velkomne! Se [TASKS.md](TASKS.md) for en liste over kendte opgaver og forbedringer.

### API Begrænsninger og Rate Limits

Integrationen håndterer automatisk følgende API begrænsninger:

- **Rate Limiting**: Hvis du modtager 429 (Too Many Requests), venter integrationen automatisk med exponential backoff
- **Service Unavailable**: Hvis servicen er nede (503), prøver integrationen automatisk igen
- **Data Delay**: Data er typisk 1-3 dage forsinket - integrationen håndterer dette automatisk
- **Max Request Size**: Time series requests er begrænset til 730 dage per request
- **Token Expiry**: Access tokens udløber efter 24 timer - integrationen fornyer automatisk

Integrationen bruger throttling og caching for at minimere API calls og overholde rate limits.

## 📝 Licens

Dette projekt er licenseret under Apache 2.0 licensen - se [LICENSE](LICENSE) filen for detaljer.

## 📚 API Dokumentation

En OpenAPI/Swagger specifikation for Eloverblik API er inkluderet i projektet som `eloverblik.swagger.json`. Denne fil kan bruges til at forstå API'et bedre eller generere klientkode.

## 🔗 Links

- [Eloverblik.dk](https://eloverblik.dk)
- [Home Assistant](https://www.home-assistant.io/)
- [HACS](https://hacs.xyz/)
- [Originalt projekt](https://github.com/JonasPed/homeassistant-eloverblik)

## 👥 Bidragydere

- **Original udvikler**: [JonasPed](https://github.com/JonasPed) - [homeassistant-eloverblik](https://github.com/JonasPed/homeassistant-eloverblik)
- Dette projekt er baseret på og bygger videre på det oprindelige arbejde

## 🙏 Credits

Dette projekt er baseret på det oprindelige [homeassistant-eloverblik](https://github.com/JonasPed/homeassistant-eloverblik) projekt udviklet af [JonasPed](https://github.com/JonasPed). Vi takker for det oprindelige arbejde og bidrager med opdateringer og forbedringer.

---

**Version**: 0.7.0

### Hvad er nyt i 0.7.0?

#### 🎉 Store Forbedringer
- ✅ **Native API implementation** - Fjernet afhængighed til `pyeloverblik` biblioteket. Nu 100% native implementation!
- ✅ **Automatisk målepunkt detection** - Vælg fra dine målepunkter i stedet for manuel indtastning
- ✅ **Forbedret energy tracking** - Opdatering hver 6. time for bedre kurver og Energy Dashboard support
- ✅ **Smart caching** - Cache for tariffer og årlig data reducerer unødvendige API calls
- ✅ **Intelligent throttling** - Forskellige opdateringsintervaller for forskellige data typer

#### 🔧 Forbedringer
- ✅ **IsAlive check** - Tjekker service status før API calls med 503 håndtering
- ✅ **Retry logik** - Exponential backoff for 429 og 503 fejl (op til 3 forsøg)
- ✅ **Bedre fejlhåndtering** - Specifikke exceptions, bedre fejlbeskeder og validering
- ✅ **Metering point details** - Viser adresse, type, grid operator i sensor attributes
- ✅ **Validering** - Tjekker refresh token og målepunkt ID format
- ✅ **Fjernet deprecated endpoint** - Meter reading endpoint er fjernet (var allerede deprecated)
- ✅ **Opdateret oversættelser** - Alle sprog (en, da, nb) opdateret

#### 📚 Dokumentation
- ✅ **Troubleshooting guide** - Løsninger på almindelige problemer
- ✅ **FAQ sektion** - Svar på almindelige spørgsmål
- ✅ **API begrænsninger** - Dokumentation af rate limits og begrænsninger
