"""Support for Yasno Outages Calendar."""
from datetime import datetime, timedelta
import logging
import aiohttp
from zoneinfo import ZoneInfo

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import STATE_ON, STATE_OFF

from . import DOMAIN, CONF_CITY, CONF_GROUP, CONF_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)
YASNO_URL = 'https://api.yasno.com.ua/api/v1/pages/home/schedule-turn-off-electricity'

# Custom states for clarity in attributes
STATE_NO_SCHEDULE = "no_schedule"
STATE_GRID_ON = "grid_on"
STATE_OUTAGE = "outage"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Yasno Calendar platform."""
    coordinator = YasnoDataUpdateCoordinator(
        hass,
        entry.data[CONF_CITY],
        entry.data[CONF_GROUP],
        entry.data.get(CONF_SCAN_INTERVAL, 5)
    )
    
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([YasnoOutagesCalendar(coordinator)], True)

[... YasnoDataUpdateCoordinator class remains the same ...]

class YasnoOutagesCalendar(CoordinatorEntity, CalendarEntity):
    """Yasno Outages Calendar."""

    def __init__(self, coordinator):
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_name = f"Yasno Outages {coordinator.city.title()} Group {coordinator.group}"
        self._attr_unique_id = f"yasno_outages_{coordinator.city}_{coordinator.group}"
        self._internal_state = STATE_NO_SCHEDULE
        self._attr_extra_state_attributes = {}

    @property
    def state(self):
        """Return the state of the calendar."""
        now = datetime.now(ZoneInfo("Europe/Kiev"))
        events = self.coordinator.data["events"]
        
        if not events:
            self._internal_state = STATE_NO_SCHEDULE
            return STATE_OFF
            
        # Check for current outage
        current_outage = next(
            (event for event in events 
             if event.start <= now <= event.end),
            None
        )
        
        if current_outage:
            self._internal_state = STATE_OUTAGE
            return STATE_OFF
        else:
            self._internal_state = STATE_GRID_ON
            return STATE_ON

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        now = datetime.now(ZoneInfo("Europe/Kiev"))
        events = self.coordinator.data["events"]
        attributes = {}
        
        # Add internal state for more detailed status
        attributes["detailed_state"] = self._internal_state
        
        # Add schedule status
        attributes["has_schedule"] = bool(events)
        
        if events:
            # Find current and next events
            current_event = next(
                (event for event in events 
                 if event.start <= now <= event.end),
                None
            )
            
            future_events = [
                event for event in events
                if event.start > now
            ]
            
            next_event = min(future_events, key=lambda x: x.start) if future_events else None
            
            # Add current outage info if exists
            if current_event:
                attributes["current_outage_start"] = current_event.start.isoformat()
                attributes["current_outage_end"] = current_event.end.isoformat()
                attributes["minutes_until_power"] = int(
                    (current_event.end - now).total_seconds() / 60
                )
            
            # Add next outage info if exists
            if next_event:
                attributes["next_outage_start"] = next_event.start.isoformat()
                attributes["next_outage_end"] = next_event.end.isoformat()
                attributes["minutes_until_outage"] = int(
                    (next_event.start - now).total_seconds() / 60
                )
            
            # Add total outages count
            attributes["total_outages_scheduled"] = len(events)

        return attributes

    @property
    def event(self):
        """Return the next upcoming event."""
        now = datetime.now(ZoneInfo("Europe/Kiev"))
        
        # First check for current event
        current_event = next(
            (event for event in self.coordinator.data["events"] 
             if event.start <= now <= event.end),
            None
        )
        
        if current_event:
            return current_event
            
        # Then check for next event
        future_events = [
            event for event in self.coordinator.data["events"]
            if event.start > now
        ]
        return min(future_events, key=lambda x: x.start) if future_events else None

    async def async_get_events(self, hass: HomeAssistant, start_datetime, end_datetime):
        """Get events in a specific time frame."""
        return [
            event for event in self.coordinator.data["events"]
            if (start_datetime <= event.start <= end_datetime or
                start_datetime <= event.end <= end_datetime or
                (event.start <= start_datetime and event.end >= end_datetime))
        ]
