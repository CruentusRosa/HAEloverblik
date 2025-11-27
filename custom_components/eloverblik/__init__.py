"""The Eloverblik integration.""" 
import asyncio
import logging
from datetime import timedelta, datetime
from typing import Optional, Dict, Any
import voluptuous as vol
from homeassistant.util import Throttle
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .api_client import EloverblikAPI, EloverblikAPIError, EloverblikAuthError
from .models import TimeSeries, ChargesData, DayData, YearData

# Module-level cache for tariffs and year data
# Format: metering_point: (data, timestamp)
_TARIFF_CACHE: Dict[str, tuple] = {}
_YEAR_DATA_CACHE: Dict[str, tuple] = {}

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["sensor"]

# Different throttling intervals for different data types
MIN_TIME_BETWEEN_ENERGY_UPDATES = timedelta(minutes=60)  # Hourly for daily data
MIN_TIME_BETWEEN_TARIFF_UPDATES = timedelta(hours=24)  # Daily for tariffs (rarely change)
MIN_TIME_BETWEEN_YEAR_UPDATES = timedelta(hours=24)  # Daily for yearly data (monthly changes)
MIN_TIME_BETWEEN_STATISTICS_UPDATES = timedelta(hours=6)  # Every 6 hours for statistics


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Eloverblik component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Eloverblik from a config entry."""
    refresh_token = entry.data.get('refresh_token')
    metering_point = entry.data.get('metering_point')
    
    if not refresh_token or not metering_point:
        _LOGGER.error("Missing required config data: refresh_token or metering_point")
        return False
    
    # Create client and fetch metering point details
    client = HassEloverblik(refresh_token, metering_point)
    
    # Fetch metering point details for additional information
    try:
        await hass.async_add_executor_job(client._fetch_metering_point_details)
    except Exception as e:
        _LOGGER.warning(f"Could not fetch metering point details: {e}. Continuing without details.")
    
    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

class HassEloverblik:
    """Wrapper class for Eloverblik API client."""

    def __init__(self, refresh_token: str, metering_point: str):
        """Initialize the Eloverblik client."""
        self._api = EloverblikAPI(refresh_token)
        self._metering_point = metering_point

        self._day_data: Optional[DayData] = None
        self._year_data: Optional[YearData] = None
        self._tariff_data: Optional[ChargesData] = None
        self._metering_point_details: Optional[Dict[str, Any]] = None

    def _fetch_metering_point_details(self):
        """Fetch metering point details from API."""
        try:
            details_response = self._api.get_metering_point_details(self._metering_point)
            if details_response and "result" in details_response:
                result_list = details_response["result"]
                if result_list and len(result_list) > 0:
                    result_item = result_list[0]
                    if "result" in result_item:
                        self._metering_point_details = result_item["result"]
                        _LOGGER.debug(f"Fetched metering point details for {self._metering_point}")
        except Exception as e:
            _LOGGER.debug(f"Could not fetch metering point details: {e}")

    def get_metering_point_info(self) -> Dict[str, Any]:
        """Get metering point information for attributes.
        
        Returns:
            Dictionary with metering point information
        """
        info = {
            "metering_point_id": self._metering_point
        }
        
        if self._metering_point_details:
            details = self._metering_point_details
            if isinstance(details, list) and len(details) > 0:
                details = details[0]
            
            # Extract useful information
            if isinstance(details, dict):
                info.update({
                    "type": details.get("typeOfMP", "Unknown"),
                    "address": self._format_address(details),
                    "grid_operator": details.get("gridOperatorName", "Unknown"),
                    "balance_supplier": details.get("balanceSupplierName", "Unknown"),
                    "measurement_unit": details.get("energyTimeSeriesMeasureUnit", "kWh"),
                })
        
        return info

    def _format_address(self, details: Dict[str, Any]) -> str:
        """Format address from metering point details."""
        parts = []
        if details.get("streetName"):
            street = details.get("streetName", "")
            if details.get("buildingNumber"):
                street += f" {details.get('buildingNumber')}"
            parts.append(street)
        if details.get("postcode") and details.get("cityName"):
            parts.append(f"{details.get('postcode')} {details.get('cityName')}")
        return ", ".join(parts) if parts else "Unknown"

    def get_total_day(self) -> Optional[float]:
        """Get total energy consumption for the day."""
        if self._day_data is not None:
            return round(self._day_data.get_total_metering_data(), 3)
        return None
    
    def get_total_year(self) -> Optional[float]:
        """Get total energy consumption for the year."""
        if self._year_data is not None:
            return round(self._year_data.get_total_metering_data(), 3)
        return None

    def get_usage_hour(self, hour: int) -> Optional[float]:
        """Get energy usage for a specific hour."""
        if self._day_data is not None:
            try:
                return round(self._day_data.get_metering_data(hour), 3)
            except IndexError:
                self._day_data.get_metering_data(23)
                _LOGGER.info(f"Unable to get data for hour {hour}. If switch to daylight saving day this is not an error.")
                return 0
        return None

    @Throttle(MIN_TIME_BETWEEN_STATISTICS_UPDATES)
    def get_hourly_data(self, from_date: datetime, to_date: datetime) -> Optional[Dict[datetime, TimeSeries]]:
        """Get hourly data for a meter between two dates."""
        try:
            # Check if service is alive first
            if not self._api.check_isalive():
                _LOGGER.warning("Eloverblik service is not available")
                return None
                
            raw_data = self._api.get_time_series(
                self._metering_point,
                from_date,
                to_date,
                aggregation="Hour"
            )
            
            if raw_data:
                # Parse response into TimeSeries objects
                return self._parse_time_series_response(raw_data)
                
        except EloverblikAuthError as e:
            _LOGGER.warning(f"Authentication error: {e}")
        except EloverblikAPIError as e:
            _LOGGER.warning(f"API error while getting historic data: {e}")
        except Exception as e:
            _LOGGER.warning(f"Unexpected exception while getting historic data: {e}", exc_info=True)
        return None

    def get_data_date(self) -> Optional[str]:
        """Get the date of the current data."""
        if self._day_data is not None:
            return self._day_data.data_date.date().strftime('%Y-%m-%d')
        return None

    def get_metering_point(self) -> str:
        """Get the metering point ID."""
        return self._metering_point

    def get_tariff_sum_hour(self, hour: int) -> Optional[float]:
        """Get the sum of all tariffs for a specific hour."""
        if self._tariff_data is not None:
            tariff_sum = 0.0
            for tariff in self._tariff_data.charges.values():
                if isinstance(tariff, list):
                    if len(tariff) == 24:
                        tariff_sum += tariff[hour - 1]
                    else:
                        _LOGGER.warning(f"Unexpected length of tariff array ({len(tariff)}), expected 24 entries.")
                else:
                    tariff_sum += float(tariff)
            return tariff_sum
        return None

    @Throttle(MIN_TIME_BETWEEN_ENERGY_UPDATES)
    def update_energy(self):
        """Update energy data from Eloverblik API."""
        _LOGGER.debug("Fetching energy data from Eloverblik")

        try:
            # Check if service is alive first
            if not self._api.check_isalive():
                _LOGGER.warning("Eloverblik service is not available, skipping energy update")
                return

            # Get latest day data (yesterday, as data is 1-3 days delayed)
            yesterday = datetime.now() - timedelta(days=1)
            day_data_response = self._api.get_time_series(
                self._metering_point,
                yesterday,
                yesterday,
                aggregation="Hour"
            )
            
            if day_data_response:
                time_series_dict = self._parse_time_series_response(day_data_response)
                if time_series_dict:
                    # Get the first (and should be only) time series
                    time_series = next(iter(time_series_dict.values()))
                    self._day_data = DayData(time_series)
                    _LOGGER.debug("Successfully updated day data")
                else:
                    _LOGGER.warning("No day data parsed from response. Data may not be available yet (typically 1-3 days delayed).")
                    # Keep existing data if available
            else:
                _LOGGER.warning("Failed to get day data from Eloverblik. Data may not be available yet (typically 1-3 days delayed).")
                # Keep existing data if available

            # Get year data (monthly aggregation) - only fetch new months
            cache_key = self._metering_point
            year_start = datetime(datetime.now().year, 1, 1)
            
            # Check cache for year data
            if cache_key in _YEAR_DATA_CACHE:
                cached_data, cache_time = _YEAR_DATA_CACHE[cache_key]
                # If cache is less than 24 hours old, use it
                if datetime.now() - cache_time < timedelta(hours=24):
                    _LOGGER.debug("Using cached year data")
                    self._year_data = cached_data
                else:
                    # Only fetch new months (from last cached month)
                    # For simplicity, we'll still fetch full year but cache it
                    pass
            else:
                # First time, fetch from start of year
                pass
            
            year_data_response = self._api.get_time_series(
                self._metering_point,
                year_start,
                datetime.now(),
                aggregation="Month"
            )
            
            if year_data_response:
                time_series_dict = self._parse_time_series_response(year_data_response)
                if time_series_dict:
                    # For year data, combine all monthly values
                    # Create a combined TimeSeries with all monthly values
                    all_monthly_values = []
                    for ts in sorted(time_series_dict.values(), key=lambda x: x.data_date if x.data_date else datetime.min):
                        if ts._metering_data:
                            all_monthly_values.extend(ts._metering_data)
                    
                    if all_monthly_values:
                        # Create a combined TimeSeries
                        from .models import TimeSeries
                        # Use the latest date
                        latest_date = max(ts.data_date for ts in time_series_dict.values() if ts.data_date)
                        fake_response = {
                            "result": [{
                                "success": True,
                                "MyEnergyData_MarketDocument": {
                                    "TimeSeries": [{
                                        "Period": [{
                                            "timeInterval": {"end": latest_date.isoformat()},
                                            "Point": [{"position": str(i+1), "out_Quantity": {"quantity": str(val)}} 
                                                     for i, val in enumerate(all_monthly_values)]
                                        }]
                                    }]
                                }
                            }]
                        }
                        combined_ts = TimeSeries(fake_response)
                        self._year_data = YearData(combined_ts)
                        # Cache the year data
                        _YEAR_DATA_CACHE[cache_key] = (self._year_data, datetime.now())
                        _LOGGER.debug("Year data updated and cached")
                else:
                    _LOGGER.warning("No year data parsed from response. Data may not be available yet.")
            else:
                _LOGGER.warning("Failed to get year data from Eloverblik. Data may not be available yet.")
                # Use cached data if available
                if cache_key in _YEAR_DATA_CACHE:
                    cached_data, _ = _YEAR_DATA_CACHE[cache_key]
                    self._year_data = cached_data
                    _LOGGER.debug("Using cached year data due to API failure")
                
        except EloverblikAuthError as e:
            _LOGGER.warning(f"Authentication error while fetching energy data: {e}")
        except EloverblikAPIError as e:
            _LOGGER.warning(f"API error while fetching energy data: {e}")
        except Exception as e:
            _LOGGER.warning(f"Unexpected exception while fetching energy data: {e}", exc_info=True)

        _LOGGER.debug("Done fetching energy data from Eloverblik")

    def _parse_time_series_response(self, response: Dict) -> Optional[Dict[datetime, TimeSeries]]:
        """Parse time series response into TimeSeries objects.
        
        Args:
            response: Raw API response dictionary
            
        Returns:
            Dictionary mapping datetime to TimeSeries objects, or None if parsing fails
        """
        result_dict: Dict[datetime, TimeSeries] = {}
        
        try:
            if "result" in response:
                for response_item in response["result"]:
                    # Wrap single response item in full response structure for TimeSeries parser
                    wrapped_response = {"result": [response_item]}
                    time_series = TimeSeries(wrapped_response)
                    if time_series.data_date and time_series._metering_data:
                        result_dict[time_series.data_date] = time_series
        except Exception as e:
            _LOGGER.warning(f"Error parsing time series response: {e}", exc_info=True)
            
        return result_dict if result_dict else None

    @Throttle(MIN_TIME_BETWEEN_TARIFF_UPDATES)
    def update_tariffs(self):
        """Update tariff data from Eloverblik API.
        
        Uses caching to avoid unnecessary API calls since tariffs rarely change.
        """
        _LOGGER.debug("Fetching tariff data from Eloverblik")

        try:
            # Check cache first
            cache_key = self._metering_point
            if cache_key in _TARIFF_CACHE:
                cached_data, cache_time = _TARIFF_CACHE[cache_key]
                # Use cached data if less than 24 hours old
                if datetime.now() - cache_time < timedelta(hours=24):
                    _LOGGER.debug("Using cached tariff data")
                    self._tariff_data = cached_data
                    return
            
            # Check if service is alive first
            if not self._api.check_isalive():
                _LOGGER.warning("Eloverblik service is not available, skipping tariff update")
                # Use cached data if available
                if cache_key in _TARIFF_CACHE:
                    cached_data, _ = _TARIFF_CACHE[cache_key]
                    self._tariff_data = cached_data
                    _LOGGER.debug("Using cached tariff data due to service unavailability")
                return
                
            charges_response = self._api.get_charges(self._metering_point)
            
            if charges_response:
                new_tariff_data = ChargesData(charges_response)
                # Check if data actually changed
                if self._tariff_data is None or new_tariff_data.charges != self._tariff_data.charges:
                    self._tariff_data = new_tariff_data
                    # Update cache
                    _TARIFF_CACHE[cache_key] = (new_tariff_data, datetime.now())
                    _LOGGER.debug("Tariff data updated and cached")
                else:
                    _LOGGER.debug("Tariff data unchanged, using existing data")
                    # Update cache timestamp
                    _TARIFF_CACHE[cache_key] = (self._tariff_data, datetime.now())
            else:
                _LOGGER.warning("Failed to get tariff data from Eloverblik")
                # Use cached data if available
                if cache_key in _TARIFF_CACHE:
                    cached_data, _ = _TARIFF_CACHE[cache_key]
                    self._tariff_data = cached_data
                    _LOGGER.debug("Using cached tariff data due to API failure")
                
        except EloverblikAuthError as e:
            _LOGGER.warning(f"Authentication error while fetching tariff data: {e}")
            # Use cached data if available
            if cache_key in _TARIFF_CACHE:
                cached_data, _ = _TARIFF_CACHE[cache_key]
                self._tariff_data = cached_data
        except EloverblikAPIError as e:
            _LOGGER.warning(f"API error while fetching tariff data: {e}")
            # Use cached data if available
            if cache_key in _TARIFF_CACHE:
                cached_data, _ = _TARIFF_CACHE[cache_key]
                self._tariff_data = cached_data
        except Exception as e:
            _LOGGER.warning(f"Unexpected exception while fetching tariff data: {e}", exc_info=True)

        _LOGGER.debug("Done fetching tariff data from Eloverblik")
