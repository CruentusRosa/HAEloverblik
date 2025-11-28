"""Native Eloverblik API client."""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import requests
from requests.exceptions import HTTPError, RequestException

_LOGGER = logging.getLogger(__name__)

# Version for logging
try:
    from .manifest import VERSION
except ImportError:
    try:
        import json
        import os
        manifest_path = os.path.join(os.path.dirname(__file__), 'manifest.json')
        with open(manifest_path) as f:
            VERSION = json.load(f).get('version', 'unknown')
    except Exception:
        VERSION = 'unknown'

# Eloverblik API base URL
API_BASE_URL = "https://api.eloverblik.dk/customerapi/api"

# API version header
API_VERSION_HEADER = "1.0"


class EloverblikAPIError(Exception):
    """Base exception for Eloverblik API errors."""
    pass


class EloverblikAuthError(EloverblikAPIError):
    """Exception for authentication errors."""
    pass


class EloverblikAPI:
    """Native Eloverblik API client."""

    def __init__(self, refresh_token: str):
        """Initialize the Eloverblik API client.
        
        Args:
            refresh_token: Refresh token from eloverblik.dk portal
        """
        self._refresh_token = refresh_token
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    def _get_access_token(self) -> str:
        """Get access token, refreshing if necessary.
        
        Returns:
            Access token string
            
        Raises:
            EloverblikAuthError: If token cannot be obtained
        """
        # Check if we have a valid token
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token

        # Get new token
        try:
            response = requests.get(
                f"{API_BASE_URL}/token",
                headers={
                    "Authorization": f"Bearer {self._refresh_token}",
                    "api-version": API_VERSION_HEADER
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if "result" in result:
                self._access_token = result["result"]
                # Token is valid for 24 hours, set expiry to 23 hours to be safe
                self._token_expires_at = datetime.now() + timedelta(hours=23)
                return self._access_token
            else:
                raise EloverblikAuthError("Invalid token response format")
                
        except HTTPError as e:
            if e.response.status_code in (401, 403):
                raise EloverblikAuthError("Invalid or expired refresh token") from e
            raise EloverblikAPIError(f"Failed to get access token: {e}") from e
        except RequestException as e:
            raise EloverblikAPIError(f"Request error getting token: {e}") from e

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Make an authenticated API request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: URL parameters
            
        Returns:
            Response object
            
        Raises:
            EloverblikAPIError: If request fails
        """
        access_token = self._get_access_token()
        url = f"{API_BASE_URL}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "api-version": API_VERSION_HEADER,
            "Content-Type": "application/json"
        }
        
        max_retries = 3
        retry_delay = 1  # Start with 1 second
        
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=30  # 30 second timeout for API calls
                )
                response.raise_for_status()
                return response
            except HTTPError as e:
                status_code = e.response.status_code
                
                # Handle 401 - token might be expired, try refreshing once
                if status_code == 401:
                    if attempt == 0:  # Only retry once for 401
                        self._access_token = None
                        access_token = self._get_access_token()
                        headers["Authorization"] = f"Bearer {access_token}"
                        continue
                    raise EloverblikAuthError("Authentication failed") from e
                
                # Handle 429 - Too Many Requests
                elif status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        _LOGGER.warning(f"[v{VERSION}] Rate limited (429). Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    raise EloverblikAPIError("Rate limit exceeded. Please try again later.") from e
                
                # Handle 503 - Service Unavailable
                elif status_code == 503:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        _LOGGER.warning(f"[v{VERSION}] Service unavailable (503). Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    raise EloverblikAPIError("Service is temporarily unavailable. Please try again later.") from e
                
                # Other HTTP errors
                raise EloverblikAPIError(f"API request failed with status {status_code}: {e}") from e
                
            except RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    _LOGGER.warning(f"[v{VERSION}] Request error: {e}. Retrying in {wait_time} seconds ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                raise EloverblikAPIError(f"Request error after {max_retries} attempts: {e}") from e
        
        # Should never reach here, but just in case
        raise EloverblikAPIError(f"Request failed after {max_retries} attempts")

    def check_isalive(self) -> bool:
        """Check if Eloverblik API service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            response = requests.get(
                f"{API_BASE_URL}/isalive",
                headers={"api-version": API_VERSION_HEADER},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                return result if isinstance(result, bool) else True
            elif response.status_code == 503:
                # Service is overloaded or down
                _LOGGER.warning(f"[v{VERSION}] Eloverblik service is unavailable (503). Service may be overloaded or down.")
                return False
            return False
        except requests.exceptions.RequestException as e:
            _LOGGER.debug(f"IsAlive check failed: {e}")
            return False
        except Exception as e:
            _LOGGER.debug(f"IsAlive check failed: {e}")
            return False

    def get_time_series(
        self,
        metering_point: str,
        date_from: datetime,
        date_to: datetime,
        aggregation: str = "Hour"
    ) -> Optional[Dict[str, Any]]:
        """Get time series data for a metering point.
        
        Args:
            metering_point: Metering point ID
            date_from: Start date
            date_to: End date
            aggregation: Aggregation level (Actual, Quarter, Hour, Day, Month, Year)
            
        Returns:
            Parsed time series data or None if error
        """
        # Convert to naive datetime if timezone-aware (API expects dates without timezone)
        if date_from.tzinfo is not None:
            date_from = date_from.replace(tzinfo=None)
        if date_to.tzinfo is not None:
            date_to = date_to.replace(tzinfo=None)
        
        # Ensure we're using date only (no time component)
        date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Validate dates - API doesn't accept future dates
        today_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if date_from > today_utc:
            _LOGGER.warning(f"[v{VERSION}] Date from ({date_from.date()}) is in the future. Using today ({today_utc.date()}) instead.")
            date_from = today_utc
        if date_to > today_utc:
            _LOGGER.warning(f"[v{VERSION}] Date to ({date_to.date()}) is in the future. Using today ({today_utc.date()}) instead.")
            date_to = today_utc
        
        # Ensure date_to is not before date_from
        if date_to < date_from:
            _LOGGER.warning(f"[v{VERSION}] Date to ({date_to.date()}) is before date from ({date_from.date()}). Swapping dates.")
            date_from, date_to = date_to, date_from
        
        date_from_str = date_from.strftime("%Y-%m-%d")
        date_to_str = date_to.strftime("%Y-%m-%d")
        
        _LOGGER.debug(f"[v{VERSION}] Requesting time series: {date_from_str} to {date_to_str} ({aggregation})")
        
        endpoint = f"/meterdata/gettimeseries/{date_from_str}/{date_to_str}/{aggregation}"
        data = {
            "meteringPoints": {
                "meteringPoint": [metering_point]
            }
        }
        
        try:
            response = self._make_request("POST", endpoint, data=data)
            return response.json()
        except EloverblikAPIError as e:
            _LOGGER.warning(f"[v{VERSION}] Failed to get time series: {e}")
            return None

    def get_charges(self, metering_point: str) -> Optional[Dict[str, Any]]:
        """Get charges (tariffs, subscriptions, fees) for a metering point.
        
        Args:
            metering_point: Metering point ID
            
        Returns:
            Charges data or None if error
        """
        endpoint = "/meteringpoints/meteringpoint/getcharges"
        data = {
            "meteringPoints": {
                "meteringPoint": [metering_point]
            }
        }
        
        try:
            response = self._make_request("POST", endpoint, data=data)
            return response.json()
        except EloverblikAPIError as e:
            _LOGGER.warning(f"[v{VERSION}] Failed to get charges: {e}")
            return None

    def get_metering_points(self, include_all: bool = False) -> Optional[List[Dict[str, Any]]]:
        """Get list of metering points for the authenticated user.
        
        Args:
            include_all: If True, includes non-linked metering points registered to CPR/CVR
            
        Returns:
            List of metering point dictionaries with meteringPointId, hasRelation, typeOfMP, etc.
            or None if error
        """
        endpoint = "/meteringpoints/meteringpoints"
        params = {"includeAll": str(include_all).lower()}
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            result = response.json()
            
            # Parse response structure: {"result": [{"meteringPointId": "...", ...}, ...]}
            if "result" in result and isinstance(result["result"], list):
                return result["result"]
            return []
        except EloverblikAPIError as e:
            _LOGGER.warning(f"[v{VERSION}] Failed to get metering points: {e}")
            return None

    def get_metering_point_details(self, metering_point: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a metering point.
        
        Args:
            metering_point: Metering point ID
            
        Returns:
            Metering point details or None if error
        """
        endpoint = "/meteringpoints/meteringpoint/getdetails"
        data = {
            "meteringPoints": {
                "meteringPoint": [metering_point]
            }
        }
        
        try:
            response = self._make_request("POST", endpoint, data=data)
            return response.json()
        except EloverblikAPIError as e:
            _LOGGER.warning(f"[v{VERSION}] Failed to get metering point details: {e}")
            return None

