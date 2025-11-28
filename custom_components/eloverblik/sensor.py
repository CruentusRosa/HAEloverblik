"""Platform for Eloverblik sensor integration."""
from datetime import datetime, timedelta
from typing import Optional
import logging
import pytz
import json
import os
from homeassistant.const import UnitOfEnergy
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    DOMAIN as RECORDER_DOMAIN,
    async_import_statistics,
    get_last_statistics,
)
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMetaData
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.util import Throttle
from .__init__ import HassEloverblik, MIN_TIME_BETWEEN_STATISTICS_UPDATES
from .const import DOMAIN, CURRENCY_KRONER_PER_KILO_WATT_HOUR
from .models import TimeSeries

_LOGGER = logging.getLogger(__name__)

# Version for logging
try:
    manifest_path = os.path.join(os.path.dirname(__file__), 'manifest.json')
    with open(manifest_path) as f:
        VERSION = json.load(f).get('version', 'unknown')
except Exception:
    VERSION = 'unknown'

async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, async_add_entities):
    """Set up the sensor platform."""
    eloverblik_clients = hass.data[DOMAIN][config.entry_id]
    
    # Support legacy single client format
    if not isinstance(eloverblik_clients, dict):
        eloverblik_clients = {eloverblik_clients.get_metering_point(): eloverblik_clients}

    sensors = []
    
    # Create sensors for each metering point
    for metering_point, eloverblik in eloverblik_clients.items():
        # Add metering point suffix to sensor names if multiple points
        suffix = f" {metering_point}" if len(eloverblik_clients) > 1 else ""
        
        sensors.append(EloverblikEnergy(f"Eloverblik Energy Total{suffix}", 'total', eloverblik))
        sensors.append(EloverblikEnergy(f"Eloverblik Energy Total (Year){suffix}", 'year_total', eloverblik))
        # Meter reading sensor removed - endpoint is deprecated
        for hour in range(1, 25):
            sensors.append(EloverblikEnergy(f"Eloverblik Energy {hour-1}-{hour}{suffix}", 'hour', eloverblik, hour))
        sensors.append(EloverblikTariff(f"Eloverblik Tariff Sum{suffix}", eloverblik))
        sensors.append(EloverblikStatistic(eloverblik, suffix))

    async_add_entities(sensors)

class EloverblikEnergy(SensorEntity):
    """Representation of an energy sensor for Eloverblik.
    
    Can represent hourly energy consumption, daily total, or yearly total.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, name: str, sensor_type: str, client: HassEloverblik, hour: int = None):
        """Initialize the energy sensor.
        
        Args:
            name: Name of the sensor
            sensor_type: Type of sensor ('hour', 'total', or 'year_total')
            client: HassEloverblik client instance
            hour: Hour number (1-24) if sensor_type is 'hour'
        """
        self._attr_name = name
        self._data_date = None
        self._data = client
        self._hour = hour
        self._sensor_type = sensor_type

        if sensor_type == 'hour':
            self._attr_unique_id = f"{self._data.get_metering_point()}-{hour}"
        elif sensor_type == 'total':
            self._attr_unique_id = f"{self._data.get_metering_point()}-total"
        elif sensor_type == 'year_total':
            self._attr_unique_id = f"{self._data.get_metering_point()}-year-total"
        else:
            raise ValueError(f"Unexpected sensor_type: {sensor_type}.")

    @property
    def extra_state_attributes(self):
        """Return state attributes."""
        attributes = {
            'Metering date': self._data_date,
            'metering_date': self._data_date
        }
        
        # Add metering point information
        mp_info = self._data.get_metering_point_info()
        attributes.update(mp_info)
        
        return attributes

    async def async_update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        await self.hass.async_add_executor_job(self._data.update_energy)

        self._data_date = self._data.get_data_date()

        if self._sensor_type == 'hour':
            self._attr_native_value = self._data.get_usage_hour(self._hour)
        elif self._sensor_type == 'total':
            self._attr_native_value = self._data.get_total_day()
        elif self._sensor_type == 'year_total':
            self._attr_native_value = self._data.get_total_year()
        else:
            raise ValueError(f"Unexpected sensor_type: {self._sensor_type}.")

class EloverblikTariff(SensorEntity):
    """Representation of a tariff sensor.
    
    Shows the current electricity tariff (price per kWh) including all charges.
    """

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = CURRENCY_KRONER_PER_KILO_WATT_HOUR
    # No state_class for monetary sensors - they are instantaneous values

    def __init__(self, name: str, client: HassEloverblik):
        """Initialize the tariff sensor.
        
        Args:
            name: Name of the sensor
            client: HassEloverblik client instance
        """
        self._attr_name = name
        self._data = client
        self._data_hourly_tariff_sums = [0] * 24
        self._attr_unique_id = f"{self._data.get_metering_point()}-tariff-sum"

    @property
    def extra_state_attributes(self):
        """Return state attributes."""
        attributes = {
            "hourly": [self._data_hourly_tariff_sums[i] for i in range(24)]
        }
        return attributes

    async def async_update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        await self.hass.async_add_executor_job(self._data.update_tariffs)

        self._data_hourly_tariff_sums = [self._data.get_tariff_sum_hour(h) for h in range(1, 25)]
        self._attr_native_value = self._data_hourly_tariff_sums[datetime.now().hour]


class EloverblikStatistic(SensorEntity):
    """This class handles the total energy of the meter,
    and imports it as long term statistics from Eloverblik.
    
    This sensor provides cumulative energy consumption data that can be used
    in Home Assistant's Energy Dashboard and for creating energy consumption curves.
    The data is automatically imported into long-term statistics for historical tracking.
    """

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, hass_eloverblik: HassEloverblik, suffix: str = ""):
        self._attr_name = f"Eloverblik Energy Statistic{suffix}"
        self._attr_unique_id = f"{hass_eloverblik.get_metering_point()}-statistic"
        self._hass_eloverblik = hass_eloverblik
        self._last_total: Optional[float] = None

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup callback to remove statistics when deleting entity"""
        await get_instance(self.hass).async_clear_statistics([self.entity_id])

    @Throttle(MIN_TIME_BETWEEN_STATISTICS_UPDATES)  # Update every 6 hours
    async def _async_update_statistics(self):
        """Continually update history with improved frequency"""
        last_stat = await self._get_last_stat(self.hass)

        if last_stat is not None:
            # Check if we need to update - data is typically 1-3 days delayed
            # Update if more than 6 hours since last update
            last_update_time = pytz.utc.localize(datetime.utcfromtimestamp(last_stat["start"]))
            time_since_update = pytz.utc.localize(datetime.now()) - last_update_time
            
            if time_since_update < timedelta(hours=6):
                # Don't update too frequently - data is delayed anyway
                return

        self.hass.async_create_task(self._update_data(last_stat))
    
    async def async_update(self):
        """Update the sensor - triggers statistics update if needed."""
        # Call the throttled statistics update (will only run if throttling allows)
        await self._async_update_statistics()
        
        # Always update sensor value from last statistic for real-time display
        last_stat = await self._get_last_stat(self.hass)
        if last_stat is not None:
            self._last_total = last_stat["sum"]
            self._attr_native_value = self._last_total
        elif self._last_total is not None:
            # Keep showing last known value if statistics exist but query failed
            self._attr_native_value = self._last_total

    async def _update_data(self, last_stat: StatisticData):
        """Update statistics data from Eloverblik.
        
        Fetches data from the last recorded point up to now (minus 2 days delay).
        """
        if last_stat is None:
            # If no previous data, import from start of last year
            from_date = datetime(datetime.today().year - 1, 1, 1)
        else:
            # Start from the hour after the last recorded statistic
            # Add 1 hour to avoid duplicates
            from_date = pytz.utc.localize(datetime.utcfromtimestamp(last_stat["start"])) + timedelta(hours=1)

        # Data is typically 1-3 days delayed, so only fetch up to 2 days ago
        # Convert to naive datetime for API call (API expects dates, not datetimes with timezone)
        if from_date.tzinfo is not None:
            from_date = from_date.replace(tzinfo=None)
        
        # Use UTC midnight to avoid timezone issues
        to_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
        
        # Don't fetch if from_date is too recent
        if from_date >= to_date:
            _LOGGER.debug(f"[v{VERSION}] No new data available yet (data is delayed by 1-3 days)")
            return

        _LOGGER.debug(f"[v{VERSION}] Fetching hourly data from {from_date} to {to_date}")
        
        data = await self.hass.async_add_executor_job(
            self._hass_eloverblik.get_hourly_data,
            from_date,
            to_date)

        if data is not None and len(data) > 0:
            await self._insert_statistics(data, last_stat)
            _LOGGER.info(f"[v{VERSION}] Imported {len(data)} time series periods to statistics")
        else:
            _LOGGER.debug(f"[v{VERSION}] No data was returned from Eloverblik")

    async def _insert_statistics(
        self,
        data: dict[datetime, TimeSeries],
        last_stat: StatisticData):

        statistics : list[StatisticData] = []

        if last_stat is not None:
            total = last_stat["sum"]
        else:
            total = 0

        # Sort time series to ensure correct insertion
        sorted_time_series = sorted(data.values(), key = lambda timeseries : timeseries.data_date)

        for time_series in sorted_time_series:
            if time_series._metering_data is not None:
                number_of_hours = len(time_series._metering_data)

                # data_date returned is end of the time series
                date = time_series.data_date - timedelta(hours=number_of_hours)

                for hour in range(0, number_of_hours):
                    start = date + timedelta(hours=hour)

                    total += time_series.get_metering_data(hour+1)

                    statistics.append(
                        StatisticData(
                            start=start,
                            sum=total
                        ))

        metadata = StatisticMetaData(
            name=self._attr_name,
            source=RECORDER_DOMAIN,
            statistic_id=self.entity_id,
            unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            has_mean=False,
            has_sum=True,
        )

        if len(statistics) > 0:
            async_import_statistics(self.hass, metadata, statistics)
            # Update sensor value to latest total for real-time display
            if statistics:
                self._last_total = statistics[-1]["sum"]
                self._attr_native_value = self._last_total

    async def _get_last_stat(self, hass: HomeAssistant) -> StatisticData:
        last_stats = await get_instance(hass).async_add_executor_job(
            get_last_statistics, hass, 1, self.entity_id, True, {"sum"}
        )

        if self.entity_id in last_stats and len(last_stats[self.entity_id]) > 0:
            return last_stats[self.entity_id][0]
        else:
            return None
