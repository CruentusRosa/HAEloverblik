"""Config flow for Eloverblik integration."""
import logging
from typing import Dict, Any, Optional

import voluptuous as vol

from homeassistant import config_entries, core, exceptions

from .const import DOMAIN  # pylint:disable=unused-import
from .api_client import EloverblikAPI, EloverblikAuthError, EloverblikAPIError

_LOGGER = logging.getLogger(__name__)

INITIAL_SCHEMA = vol.Schema(
    {
        vol.Required("refresh_token"): str,
    })

def validate_refresh_token(token: str) -> bool:
    """Validate refresh token format.
    
    Refresh tokens are JWT tokens, so they should:
    - Start with 'eyJ' (base64 encoded JWT header)
    - Contain at least two dots (header.payload.signature)
    - Be reasonably long (JWT tokens are typically 100+ characters)
    """
    if not token or not isinstance(token, str):
        return False
    
    # Basic JWT format check (header.payload.signature)
    parts = token.split('.')
    if len(parts) != 3:
        return False
    
    # Check if it starts with typical JWT header
    if not token.startswith('eyJ'):
        return False
    
    # Check minimum length (JWT tokens are typically 100+ characters)
    if len(token) < 50:
        return False
    
    return True

def validate_metering_point_id(mp_id: str) -> bool:
    """Validate metering point ID format.
    
    Metering point IDs should be 18 characters (alphanumeric).
    """
    if not mp_id or not isinstance(mp_id, str):
        return False
    
    # Should be 18 characters
    if len(mp_id) != 18:
        return False
    
    # Should be alphanumeric
    if not mp_id.isalnum():
        return False
    
    return True

async def validate_input(hass: core.HomeAssistant, data: Dict[str, Any]):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    token = data["refresh_token"]
    metering_point = data.get("metering_point")

    # Validate refresh token format
    if not validate_refresh_token(token):
        raise InvalidAuth("Invalid refresh token format. Please check your token from eloverblik.dk")

    # Validate metering point format if provided
    if metering_point and not validate_metering_point_id(metering_point):
        raise InvalidMeteringPoint("Invalid metering point ID format. Must be 18 alphanumeric characters.")

    api = EloverblikAPI(token)

    try:
        # Validate token by getting metering points
        metering_points = await hass.async_add_executor_job(api.get_metering_points, False)
        if metering_points is None:
            raise CannotConnect("Failed to retrieve metering points. Please check your internet connection and try again.")
        
        if not metering_points:
            raise NoMeteringPoints("No metering points found. Please ensure you have linked metering points in the Eloverblik portal.")
        
        # If metering point is specified, validate it exists
        if metering_point:
            valid_ids = [mp.get("meteringPointId") for mp in metering_points if mp.get("meteringPointId")]
            if metering_point not in valid_ids:
                raise InvalidMeteringPoint(f"Metering point {metering_point} not found in your account. Please select from the list.")
        
        return {"title": f"Eloverblik {metering_point}" if metering_point else "Eloverblik"}
    except EloverblikAuthError as error:
        raise InvalidAuth("Invalid or expired refresh token. Please generate a new token from eloverblik.dk") from error
    except EloverblikAPIError as error:
        raise CannotConnect(f"Unable to connect to Eloverblik API: {error}") from error


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eloverblik."""

    VERSION = 1

    def __init__(self):
        """Initialize config flow."""
        self._metering_points: Optional[list] = None
        self._refresh_token: Optional[str] = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            self._refresh_token = user_input["refresh_token"]
            
            try:
                api = EloverblikAPI(self._refresh_token)
                # Get metering points
                self._metering_points = await self.hass.async_add_executor_job(
                    api.get_metering_points, False
                )
                
                if self._metering_points is None:
                    errors["base"] = "cannot_connect"
                elif not self._metering_points:
                    errors["base"] = "no_metering_points"
                else:
                    # Move to metering point selection step
                    return await self.async_step_metering_point()
                    
            except EloverblikAuthError:
                errors["base"] = "invalid_auth"
            except EloverblikAPIError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=INITIAL_SCHEMA, errors=errors
        )

    async def async_step_metering_point(self, user_input=None):
        """Handle metering point selection step."""
        errors = {}
        
        if user_input is not None:
            metering_point = user_input["metering_point"]
            
            try:
                info = await validate_input(self.hass, {
                    "refresh_token": self._refresh_token,
                    "metering_point": metering_point
                })
                
                await self.async_set_unique_id(metering_point)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        "refresh_token": self._refresh_token,
                        "metering_point": metering_point
                    }
                )
            except InvalidMeteringPoint:
                errors["base"] = "invalid_metering_point"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Build selection schema with metering points
        metering_point_options = {}
        for mp in self._metering_points or []:
            mp_id = mp.get("meteringPointId")
            if not mp_id:
                continue
                
            mp_type = mp.get("typeOfMP", "")
            city = mp.get("cityName", "")
            postcode = mp.get("postcode", "")
            
            # Create a readable label
            label_parts = [mp_id]
            if mp_type:
                label_parts.append(f"({mp_type})")
            if city:
                label_parts.append(f"- {city}")
            if postcode:
                label_parts.append(postcode)
            
            metering_point_options[mp_id] = " ".join(label_parts)

        schema = vol.Schema({
            vol.Required("metering_point"): vol.In(metering_point_options)
        })

        return self.async_show_form(
            step_id="metering_point",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "count": str(len(metering_point_options))
            }
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class NoMeteringPoints(exceptions.HomeAssistantError):
    """Error to indicate no metering points found."""


class InvalidMeteringPoint(exceptions.HomeAssistantError):
    """Error to indicate invalid metering point."""

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
