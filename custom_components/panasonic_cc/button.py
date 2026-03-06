import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN, DATA_COORDINATORS, ENERGY_COORDINATORS
from .coordinator import PanasonicDeviceCoordinator, PanasonicDeviceEnergyCoordinator
from .base import PanasonicDataEntity

_LOGGER = logging.getLogger(__name__)

UPDATE_DATA_DESCRIPTION = ButtonEntityDescription(
    key="update_data",
    name="Fetch latest data",
    icon="mdi:update",
    entity_category=EntityCategory.DIAGNOSTIC
)
UPDATE_ENERGY_DESCRIPTION = ButtonEntityDescription(
    key="update_energy",
    name="Fetch latest energy data",
    icon="mdi:update",
    entity_category=EntityCategory.DIAGNOSTIC
)

async def async_setup_entry(hass: HomeAssistant, config, async_add_entities):
    entities = []
    data_coordinators: list[PanasonicDeviceCoordinator] = hass.data[DOMAIN][DATA_COORDINATORS]
    energy_coordinators: list[PanasonicDeviceEnergyCoordinator] = hass.data[DOMAIN][ENERGY_COORDINATORS]

    for coordinator in data_coordinators:
        entities.append(CoordinatorUpdateButtonEntity(coordinator, UPDATE_DATA_DESCRIPTION))
    for coordinator in energy_coordinators:
        entities.append(CoordinatorUpdateButtonEntity(coordinator, UPDATE_ENERGY_DESCRIPTION))
        
    async_add_entities(entities)

class CoordinatorUpdateButtonEntity(PanasonicDataEntity, ButtonEntity):
    """Representation of a Coordinator Update Button."""
    
    def __init__(self, coordinator: DataUpdateCoordinator, description: ButtonEntityDescription) -> None:
        self.entity_description = description
        super().__init__(coordinator, description.key)
    

    def _async_update_attrs(self) -> None:
        """Update the attributes of the entity."""

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_request_refresh()
