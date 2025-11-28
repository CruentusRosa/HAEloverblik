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

### Installation via HACS (Anbefalet) ⭐

**Dette er den nemmeste og anbefalede metode til at installere integrationen.**

1.ration → Søg efter "Eloverblik"

ne

## ⚙️ Konfiguration

### Refresh Token

For at bruge integrationen skal du have et refresh token fra [eloverblik.dk](https://eloverblik.dk/customer/).

1. Log ind på [Eloverblik](https://eloverblik.dk/customer/overview/).
2. Opret et refresh token:
   1. Klik på din bruger.
   2. Vælg **Data Sharing**.
   3. Klik **Create token** og gennemfør trinnene med dine præferencer.
 Sørg for at [HACS](https://hacs.xyz/) er installeret.
2. Installer integrationen gennem HACS:
   * **HACS Link** (virker kun hvis du har Home Assistant Companion app installeret):  
   [![Open your Home Assistant instance and open a the Eloverblik repository inside the Home Assistant Community Store](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=CruentusRosa&repository=HAEloverblik&category=integration)
   * **Manuel metode**: 
     - Gå til **HACS** → **Integrations**
     - Klik på **⋮** (tre prikker) → **Custom repositories**
     - Indtast `CruentusRosa/HAEloverblik` i Repository URL
     - Vælg `Integration` i Category
     - Klik **Add**
     - Find "Eloverblik" i HACS → Integrations og klik **Download**
3. Genstart Home Assistant (Settings → ⋮ → Restart Home Assistant → Restart).
4. [Konfigurer](#konfiguration) Eloverblik gennem Settings → Devices & Services → Add Integration.
   * **Config Flow Link** (virker kun hvis du har Home Assistant Companion app installeret):  
   [![Open your Home Assistant instance and start setting up a Eloverblik](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=eloverblik)
   * **Manuel metode**: Gå til Settings → Devices & Services → Add Integ
### Konfiguration i Home Assistant

1. Gå til **Settings** → **Devices & Services** → **Add Integration**.
2. Søg efter **Eloverblik**.
3. Indtast dit **Refresh Token** fra eloverblik.dk.
4. Integrationen henter automatisk alle dine målepunkter og opretter sensorer for hvert målepunkt.

> **Bemærk**: 
> - Integrationen opretter automatisk sensorer for **alle** målepunkter du har en aktiv relation til.
> - Hvis du har flere målepunkter, får hver sensor et suffix med målepunkt ID for at skelne dem.
> - Hvis du ser en fejl om at integrationen ikke understøtter konfiguration via brugerfladen, skal du:
>   1. Genstarte Home Assistant
>   2. Slette integrationen hvis den allerede er installeret og prøve igen
>   3. Tjekke at du har den nyeste version (0.8.4)

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

### Integrationen viser stadig målepunkt ID felt i første step

Hvis du stadig ser et målepunkt ID felt i første step (i stedet for kun refresh token):

- **Genstart Home Assistant**: Home Assistant cacher config flows. Genstart for at rydde cache.
- **Slet eksisterende integration**: Hvis du har en gammel integration fra version 1, slet den og opret en ny.
- **Tjek version**: Sørg for at du har version 0.7.0 eller nyere installeret.
- **Efter genstart**: Gå til Settings → Devices & Services → Add Integration → Eloverblik. Du skulle nu kun se "Refresh Token" feltet i første step.

### "Denne integration understøtter ikke konfiguration via brugerfladen" eller "Invalid handler specified"

Hvis du ser disse fejl:

- **Slet __pycache__**: Slet `custom_components/eloverblik/__pycache__` mappen og genstart Home Assistant (dette rydder cached Python filer). Dette er oftest løsningen!
- **Genstart Home Assistant**: Dette er oftest nødvendigt efter opdatering af integrationen.
- **HACS reinstall**: Hvis du bruger HACS:
  1. Gå til HACS → Integrations
  2. Find Eloverblik og klik på ⋮ → Delete
  3. Genstart Home Assistant
  4. Installer integrationen igen gennem HACS
  5. Genstart igen
- **Tjek filstruktur**: Sørg for at `config_flow.py` findes i `custom_components/eloverblik/` mappen.
- **Tjek manifest.json**: Sørg for at `"config_flow": true` er sat i `manifest.json`.
- **Tjek logs**: Se Home Assistant logs for fejlmeddelelser (Settings → System → Logs). Se efter Python tracebacks eller import fejl.
- **Slet og geninstaller**: Hvis problemet fortsætter, slet integrationen og installer den igen.
- **Brug manuel metode**: Hvis links ikke virker, gå manuelt til Settings → Devices & Services → Add Integration → Søg efter "Eloverblik"

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

## 💡 Eksempler og Use Cases

### Energy Dashboard Setup

Integrationen understøtter automatisk Home Assistant's Energy Dashboard. Tilføj `sensor.eloverblik_energy_statistic` til dit Energy Dashboard:

1. Gå til **Settings** → **Dashboards** → **Energy**
2. Under **Electricity grid** → **Add consumption**
3. Vælg `sensor.eloverblik_energy_statistic`
4. Vælg målepunktet (hvis du har flere)

Sensoren importerer automatisk historiske data og opdaterer løbende med nye data hver 6. time.

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

### Daglig og månedlig elpris beregning

Beregn den samlede pris for dit daglige og månedlige elforbrug:

```yaml
template:
  - sensor:
    # Daglig pris
    - name: "Eloverblik Daily Cost"
      unique_id: eloverblik_daily_cost
      device_class: monetary
      unit_of_measurement: "kr"
      state: >
        {{ (states('sensor.eloverblik_energy_total') | float(0)) * 
           (states('sensor.eloverblik_tariff_sum') | float(0)) | round(2) }}
      icon: mdi:currency-usd
    
    # Månedlig pris (baseret på årlig data)
    - name: "Eloverblik Monthly Cost"
      unique_id: eloverblik_monthly_cost
      device_class: monetary
      unit_of_measurement: "kr"
      state: >
        {% set year_total = states('sensor.eloverblik_energy_total_year') | float(0) %}
        {% set current_month = now().month %}
        {% set monthly_avg = year_total / 12 %}
        {% set avg_tariff = state_attr('sensor.eloverblik_tariff_sum', 'hourly') | 
                            default([0]) | sum / 24 if state_attr('sensor.eloverblik_tariff_sum', 'hourly') else 0 %}
        {{ (monthly_avg * avg_tariff) | round(2) }}
      icon: mdi:currency-usd
```

### Automatisering: Notifikation ved højt dagligt forbrug

Send en notifikation hvis dit daglige forbrug overstiger et bestemt niveau:

```yaml
automation:
  - alias: "Højt elforbrug notifikation"
    trigger:
      - platform: numeric_state
        entity_id: sensor.eloverblik_energy_total
        above: 25  # kWh
    condition:
      - condition: time
        after: "08:00:00"
        before: "22:00:00"
    action:
      - service: notify.mobile_app_din_telefon
        data:
          message: >
            Dit elforbrug i dag er {{ states('sensor.eloverblik_energy_total') }} kWh,
            hvilket er over dit normale niveau.
          title: "Højt elforbrug"
```

### Automatisering: Billigste tidspunkt at bruge strøm

Automatiser opvaskemaskine, vaskemaskine eller opladere til at køre når strømmen er billigst:

```yaml
template:
  - sensor:
    - name: "Cheapest Hour Today"
      unique_id: cheapest_hour_today
      state: >
        {% set hourly = state_attr('sensor.eloverblik_tariff_sum', 'hourly') | default([]) %}
        {% if hourly | length > 0 %}
          {{ hourly | map('float') | list | min | string }}
        {% else %}
          unknown
        {% endif %}
      attributes:
        cheapest_hour_index: >
          {% set hourly = state_attr('sensor.eloverblik_tariff_sum', 'hourly') | default([]) %}
          {% if hourly | length > 0 %}
            {{ hourly | map('float') | list | 
               index(hourly | map('float') | list | min) }}
          {% else %}
            -1
          {% endif %}

automation:
  - alias: "Start vaskemaskine ved billigste tidspunkt"
    trigger:
      - platform: time
        at: "{{ state_attr('sensor.cheapest_hour_today', 'cheapest_hour_index') | int }}:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.vaskemaskine_klar
        state: "on"
    action:
      - service: switch.turn_on
        entity_id: switch.vaskemaskine
```

### Sammenligning med tidligere måneder

Opret en sensor der sammenligner dit nuværende månedlige forbrug med tidligere måneder:

```yaml
template:
  - sensor:
    - name: "Eloverblik Monthly Comparison"
      unique_id: eloverblik_monthly_comparison
      state: >
        {% set current = states('sensor.eloverblik_energy_total') | float(0) %}
        {% set year_total = states('sensor.eloverblik_energy_total_year') | float(0) %}
        {% set monthly_avg = year_total / 12 %}
        {% if monthly_avg > 0 %}
          {{ ((current / monthly_avg - 1) * 100) | round(1) }}
        {% else %}
          0
        {% endif %}
      unit_of_measurement: "%"
      icon: mdi:chart-line-variant
      attributes:
        current_month: "{{ states('sensor.eloverblik_energy_total') }}"
        monthly_average: "{{ (states('sensor.eloverblik_energy_total_year') | float(0) / 12) | round(2) }}"
```

### Dashboard Card: Time-for-time forbrug og pris

Vis både forbrug og pris time-for-time i en graf:

```yaml
type: history-graph
title: "Elforbrug og Pris"
entities:
  - entity: sensor.eloverblik_energy_total
    name: "Forbrug (kWh)"
  - entity: sensor.eloverblik_tariff_sum
    name: "Pris (kr/kWh)"
hours_to_show: 24
refresh: 60
```

### Automatisering: Opdatering når nye data er tilgængelig

Send en notifikation når nye data er tilgængelig fra Eloverblik:

```yaml
automation:
  - alias: "Nyt elforbrug data tilgængelig"
    trigger:
      - platform: state
        entity_id: sensor.eloverblik_energy_total
        # Trigger når sensoren opdateres (hver time)
    condition:
      - condition: template
        value_template: >
          {{ state_attr('sensor.eloverblik_energy_total', 'metering_date') != 
             state_attr('sensor.eloverblik_energy_total', 'metering_date') }}
    action:
      - service: persistent_notification.create
        data:
          title: "Nyt elforbrug data"
          message: >
            Nye data tilgængelig for {{ state_attr('sensor.eloverblik_energy_total', 'metering_date') }}.
            Forbrug: {{ states('sensor.eloverblik_energy_total') }} kWh
```

### Template: Time-for-time pris med moms

Beregn den samlede pris inkl. moms for hver time:

```yaml
template:
  - sensor:
    - name: "Eloverblik Price with VAT"
      unique_id: eloverblik_price_vat
      device_class: monetary
      unit_of_measurement: "kr/kWh"
      state: >
        {{ (states('sensor.eloverblik_tariff_sum') | float(0) * 1.25) | round(4) }}
      attributes:
        hourly_with_vat: >
          {% set hourly = state_attr('sensor.eloverblik_tariff_sum', 'hourly') | default([]) %}
          {% if hourly | length > 0 %}
            {{ hourly | map('float') | map('multiply', 1.25) | map('round', 4) | list }}
          {% else %}
            []
          {% endif %}
```

### Automatisering: Ugentlig elforbrug rapport

Send en ugentlig rapport med dit elforbrug:

```yaml
automation:
  - alias: "Ugentlig elforbrug rapport"
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: time
        weekday:
          - mon
    action:
      - service: notify.mobile_app_din_telefon
        data:
          title: "Ugentlig elforbrug rapport"
          message: >
            📊 Elforbrug rapport for sidste uge:
            
            📅 Dagligt gennemsnit: {{ states('sensor.eloverblik_monthly_statistics') }} kWh
            💰 Gennemsnitlig pris: {{ states('sensor.eloverblik_tariff_sum') }} kr/kWh
            📈 Årligt total: {{ states('sensor.eloverblik_energy_total_year') }} kWh
```

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

**Version**: 0.8.4

### Hvad er nyt i 0.8.4?

- **Forbedret data parsing** - Støtter nu både `MyEnergyData_MarketDocument` og `MyEnergyDataMarketDocument` strukturer
- **Bedre debug logging** - Viser nu response struktur når data ikke kan parses, for nemmere debugging
- **Forbedret fejlhåndtering** - Bedre håndtering af forskellige API response formater

### Hvad er nyt i 0.8.3?

- **Version tracking forbedret** - Sikrer at versionen altid vises korrekt i logger
- **Forbedret API validering** - Alle metering point ID'er valideres nu korrekt (18 alphanumeriske tegn)
- **Bedre fejlbeskeder** - Detaljerede fejlbeskeder fra API'en inkluderer nu errorCode, errorText og detail
- **Forbedret dato-validering** - Håndterer korrekt at dateFrom != dateTo (API fejlkode 30002)
- **Robust fejlhåndtering** - Integrationen hopper over ugyldige metering points i stedet for at fejle

### Hvad er nyt i 0.8.2?

- **Forbedret API validering** - Alle metering point ID'er valideres nu korrekt (18 alphanumeriske tegn)
- **Bedre fejlbeskeder** - Detaljerede fejlbeskeder fra API'en inkluderer nu errorCode, errorText og detail
- **Forbedret dato-validering** - Håndterer korrekt at dateFrom != dateTo (API fejlkode 30002)
- **Robust fejlhåndtering** - Integrationen hopper over ugyldige metering points i stedet for at fejle

### Hvad er nyt i 0.8.1?

- **Forbedret logging** - Alle logger-statements inkluderer nu version nummer for nemmere debugging
- **Forbedret dato-validering** - Bedre håndtering af forkert systemtid og datoer
- **Forbedret fejlhåndtering** - Bedre validering af datoer til API kald

### Hvad er nyt i 0.8.0?

#### 🎉 Store Forbedringer
- ✅ **Simplificeret konfiguration** - Nu kun ét step! Indtast kun refresh token, og integrationen opretter automatisk sensorer for alle dine målepunkter.
- ✅ **Automatisk multi-målepunkt support** - Opretter sensorer for alle målepunkter du har en aktiv relation til, uden manuel valg.

### Hvad var nyt i 0.7.0?

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
