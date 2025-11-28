"""Data models for Eloverblik API responses."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

_LOGGER = logging.getLogger(__name__)


class TimeSeries:
    """Represents a time series of metering data."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize TimeSeries from API response data.
        
        Args:
            data: Parsed JSON data from API response
        """
        self._metering_data: Optional[List[float]] = None
        self.data_date: Optional[datetime] = None
        self._parse_data(data)

    def _parse_data(self, data: Dict[str, Any]):
        """Parse time series data from API response.
        
        API response structure:
        {
          "result": [
            {
              "success": true,
              "MyEnergyData_MarketDocument": {
                "TimeSeries": [
                  {
                    "Period": [
                      {
                        "timeInterval": {"start": "...", "end": "..."},
                        "Point": [{"position": "1", "out_Quantity": {"quantity": "..."}}]
                      }
                    ]
                  }
                ]
              }
            }
          ]
        }
        """
        try:
            # Navigate through the API response structure
            if "result" in data and len(data["result"]) > 0:
                response_item = data["result"][0]
                
                # Check if request was successful
                if not response_item.get("success", True):
                    error_code = response_item.get("errorCode")
                    error_text = response_item.get("errorText", "Unknown error")
                    _LOGGER.warning(f"API returned error: {error_code} - {error_text}")
                    return
                
                # Try different possible keys for the market document
                market_doc = response_item.get("MyEnergyData_MarketDocument") or response_item.get("MyEnergyDataMarketDocument", {})
                
                time_series_list = market_doc.get("TimeSeries", []) if isinstance(market_doc, dict) else []
                
                if time_series_list:
                    # Combine all periods into one time series
                    all_points = []
                    latest_end = None
                    
                    for time_series in time_series_list:
                        periods = time_series.get("Period", [])
                        
                        for period in periods:
                            points = period.get("Point", [])
                            
                            # Extract time interval
                            time_interval = period.get("timeInterval", {})
                            if time_interval:
                                end_str = time_interval.get("end")
                                if end_str:
                                    try:
                                        # Parse ISO 8601 datetime (handle both Z and +00:00)
                                        end_date = end_str.replace("Z", "+00:00")
                                        parsed_date = datetime.fromisoformat(end_date)
                                        if latest_end is None or parsed_date > latest_end:
                                            latest_end = parsed_date
                                    except (ValueError, AttributeError) as e:
                                        _LOGGER.debug(f"Could not parse date: {end_str} - {e}")
                            
                            # Extract metering data from points
                            for point in points:
                                position = point.get("position")
                                quantity_obj = point.get("out_Quantity", {})
                                quantity = quantity_obj.get("quantity") if isinstance(quantity_obj, dict) else None
                                
                                if quantity is not None:
                                    try:
                                        all_points.append((int(position), float(quantity)))
                                    except (ValueError, TypeError):
                                        pass
                    
                    # Sort by position and extract values
                    if all_points:
                        all_points.sort(key=lambda x: x[0])
                        self._metering_data = [qty for _, qty in all_points]
                        self.data_date = latest_end
                    
        except (KeyError, IndexError, TypeError, AttributeError) as e:
            _LOGGER.warning(f"Error parsing time series data: {e}", exc_info=True)

    def get_metering_data(self, hour: int) -> float:
        """Get metering data for a specific hour (1-indexed).
        
        Args:
            hour: Hour number (1-24 for daily, 1-96 for quarter-hourly, etc.)
            
        Returns:
            Energy consumption in kWh
            
        Raises:
            IndexError: If hour is out of range
        """
        if self._metering_data is None:
            raise IndexError("No metering data available")
        if hour < 1 or hour > len(self._metering_data):
            raise IndexError(f"Hour {hour} out of range (1-{len(self._metering_data)})")
        return self._metering_data[hour - 1]

    def get_total_metering_data(self) -> float:
        """Get total metering data for the time series.
        
        Returns:
            Total energy consumption in kWh
        """
        if self._metering_data is None:
            return 0.0
        return sum(self._metering_data)


class ChargesData:
    """Represents charges (tariffs, subscriptions, fees) for a metering point."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize ChargesData from API response.
        
        Args:
            data: Parsed JSON data from API response
        """
        self.charges: Dict[str, Any] = {}
        self._parse_data(data)

    def _parse_data(self, data: Dict[str, Any]):
        """Parse charges data from API response."""
        try:
            # Response structure: result[0].result.tariffs[], subscriptions[], fees[]
            if "result" in data and len(data["result"]) > 0:
                result = data["result"][0].get("result", {})
                
                # Parse tariffs
                tariffs = result.get("tariffs", [])
                for tariff in tariffs:
                    name = tariff.get("name", "unknown")
                    prices = tariff.get("prices", [])
                    
                    if prices:
                        # Create hourly price array
                        hourly_prices = [0.0] * 24
                        for price_entry in prices:
                            position = price_entry.get("position")
                            price = price_entry.get("price", 0.0)
                            if position:
                                try:
                                    hour = int(position) - 1
                                    if 0 <= hour < 24:
                                        hourly_prices[hour] = float(price)
                                except (ValueError, TypeError):
                                    pass
                        self.charges[name] = hourly_prices
                    else:
                        # Fixed price tariff
                        self.charges[name] = 0.0
                
                # Parse subscriptions and fees (fixed prices)
                for charge_type in ["subscriptions", "fees"]:
                    items = result.get(charge_type, [])
                    for item in items:
                        name = item.get("name", "unknown")
                        price = item.get("price", 0.0)
                        self.charges[name] = float(price)
                        
        except (KeyError, TypeError, ValueError) as e:
            _LOGGER.warning(f"Error parsing charges data: {e}")


class DayData:
    """Represents daily energy consumption data."""

    def __init__(self, time_series: TimeSeries):
        """Initialize DayData from TimeSeries.
        
        Args:
            time_series: TimeSeries object with hourly data
        """
        self._time_series = time_series

    @property
    def data_date(self) -> Optional[datetime]:
        """Get the date of the data."""
        return self._time_series.data_date

    def get_metering_data(self, hour: int) -> float:
        """Get metering data for a specific hour (1-24).
        
        Args:
            hour: Hour number (1-24)
            
        Returns:
            Energy consumption in kWh for that hour
        """
        return self._time_series.get_metering_data(hour)

    def get_total_metering_data(self) -> float:
        """Get total daily energy consumption.
        
        Returns:
            Total daily energy consumption in kWh
        """
        return self._time_series.get_total_metering_data()


class YearData:
    """Represents yearly energy consumption data (monthly aggregation)."""

    def __init__(self, time_series: TimeSeries):
        """Initialize YearData from TimeSeries.
        
        Args:
            time_series: TimeSeries object with monthly data
        """
        self._time_series = time_series

    def get_total_metering_data(self) -> float:
        """Get total yearly energy consumption.
        
        Returns:
            Total yearly energy consumption in kWh
        """
        return self._time_series.get_total_metering_data()

