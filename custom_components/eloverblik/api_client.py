"""Native Eloverblik API client."""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import requests
from requests.exceptions import HTTPError, RequestException

_LOGGER = logging.getLogger(__name__)

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
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response
        except HTTPError as e:
            if e.response.status_code == 401:
                # Token might be expired, try refreshing once
                self._access_token = None
                access_token = self._get_access_token()
                headers["Authorization"] = f"Bearer {access_token}"
                try:
                    response = requests.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=data,
                        params=params,
                        timeout=30
                    )
                    response.raise_for_status()
                    return response
                except HTTPError:
                    raise EloverblikAuthError("Authentication failed") from e
            raise EloverblikAPIError(f"API request failed: {e}") from e
        except RequestException as e:
            raise EloverblikAPIError(f"Request error: {e}") from e

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
        date_from_str = date_from.strftime("%Y-%m-%d")
        date_to_str = date_to.strftime("%Y-%m-%d")
        
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
            _LOGGER.warning(f"Failed to get time series: {e}")
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
            _LOGGER.warning(f"Failed to get charges: {e}")
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
            _LOGGER.warning(f"Failed to get metering points: {e}")
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
            _LOGGER.warning(f"Failed to get metering point details: {e}")
            return None

