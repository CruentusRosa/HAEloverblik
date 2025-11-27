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


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eloverblik."""

    VERSION = 3
    
    async def async_step_reauth(self, user_input=None):
        """Handle reauth flow."""
        return await self.async_step_user(user_input)
    
    async def async_step_import(self, user_input=None):
        """Handle import from configuration.yaml (legacy)."""
        # This handles old config entries that might have metering_point in first step
        if user_input and "metering_point" in user_input:
            # Old format - migrate to new format
            refresh_token = user_input.get("refresh_token")
            metering_point = user_input.get("metering_point")
            
            if refresh_token and metering_point:
                # Create entry with single metering point (legacy support)
                await self.async_set_unique_id(refresh_token)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=f"Eloverblik {metering_point}",
                    data={
                        "refresh_token": refresh_token,
                        "metering_points": [metering_point]
                    }
                )
        
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            refresh_token = user_input.get("refresh_token")
            
            if not refresh_token:
                errors["base"] = "invalid_auth"
            else:
                try:
                    # Validate token format first
                    if not validate_refresh_token(refresh_token):
                        errors["base"] = "invalid_auth"
                    else:
                        api = EloverblikAPI(refresh_token)
                        # Get all metering points
                        metering_points = await self.hass.async_add_executor_job(
                            api.get_metering_points, False
                        )
                        
                        if metering_points is None:
                            errors["base"] = "cannot_connect"
                        elif not metering_points:
                            errors["base"] = "no_metering_points"
                        else:
                            # Extract metering point IDs
                            mp_ids = [mp.get("meteringPointId") for mp in metering_points if mp.get("meteringPointId")]
                            
                            if not mp_ids:
                                errors["base"] = "no_metering_points"
                            else:
                                # Create entry with all metering points
                                await self.async_set_unique_id(refresh_token)
                                self._abort_if_unique_id_configured()
                                
                                return self.async_create_entry(
                                    title=f"Eloverblik ({len(mp_ids)} målepunkt{'er' if len(mp_ids) > 1 else ''})",
                                    data={
                                        "refresh_token": refresh_token,
                                        "metering_points": mp_ids
                                    }
                                )
                            
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


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class NoMeteringPoints(exceptions.HomeAssistantError):
    """Error to indicate no metering points found."""


class InvalidMeteringPoint(exceptions.HomeAssistantError):
    """Error to indicate invalid metering point."""
