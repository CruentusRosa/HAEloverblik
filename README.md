# Eloverblik Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

En Home Assistant custom component til at overvåge dit elforbrug fra [eloverblik.dk](https://eloverblik.dk).

## 📋 Oversigt

Denne integration henter elforbrugsdata fra Eloverblik og gør dem tilgængelige som sensorer i Home Assistant. Integrationen understøtter:

- Time-for-time elforbrug for de seneste 24 timer
- Samlet dagligt elforbrug
- Årligt elforbrug
- Tariffer og priser
- Langtidsstatistikker til brug i Energy Dashboard
- Måleraflæsninger

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

### Refresh Token og Målepunkt

For at bruge integrationen skal du have et refresh token og et målepunkt ID fra [eloverblik.dk](https://eloverblik.dk/customer/).

1. Log ind på [Eloverblik](https://eloverblik.dk/customer/overview/).
2. Find dit målepunkt ID (bruges som `ID` i Home Assistant).
3. Opret et refresh token:
   1. Klik på din bruger.
   2. Vælg **Data Sharing**.
   3. Klik **Create token** og gennemfør trinnene med dine præferencer.

## 📊 Sensorer og Attributter

### Energisensorer

Integrationen opretter sensorer for hver time i de seneste 24 timer:
- `sensor.eloverblik_energy_0_1` (time 0-1)
- `sensor.eloverblik_energy_1_2` (time 1-2)
- osv.

### Totalsensorer

- `sensor.eloverblik_energy_total` - Samlet dagligt elforbrug (kWh)
- `sensor.eloverblik_energy_total_year` - Samlet årligt elforbrug (kWh)

### Tarifsensor

- `sensor.eloverblik_tariff_sum` - Nuværende timepris (kr/kWh)
  - Attribut: `hourly` - Array med priser for alle 24 timer

### Måleraflæsning

- `sensor.eloverblik_meter_reading` - Seneste måleraflæsning (kWh)

### Statistiksensor

- `sensor.eloverblik_energy_statistic` - Langtidsstatistik til Energy Dashboard
  - **Bemærk**: Denne sensor vil altid vise `unknown` som værdi, men indeholder gyldige langtidsstatistikker.

Alle sensorer viser værdier i kWh (undtagen tarifsensoren som viser kr/kWh).

## 📈 Langtidsstatistik og Energy Dashboard

Integrationen understøtter langtidsstatistikker og kan bruges i Home Assistants Energy Dashboard.

Integrationen henter nuværende og sidste års data fra Eloverblik og indsætter dem i Home Assistants langtidsstatistikker.

> **Bemærk**: Data vil være forsinket med 1-3 dage afhængigt af din lokale netoperatør (DSO).

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
    pyeloverblik.eloverblik: debug
    custom_components.eloverblik: debug
```

Du kan også ændre logniveauet gennem UI via service calls.

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

## 📝 Licens

Dette projekt er licenseret under MIT licensen - se [LICENSE](LICENSE) filen for detaljer.

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

**Version**: 0.6.1
