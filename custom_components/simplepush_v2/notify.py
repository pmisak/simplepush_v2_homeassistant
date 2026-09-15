"""Notify platform for Simplepush V2."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import async_send_simplepush_notification, async_send_simplepush_task
from .const import (
    ATTR_ACTIONS,
    ATTR_CHOICES,
    ATTR_CRITICAL,
    ATTR_IMAGE,
    ATTR_LINK,
    ATTR_MARKDOWN,
    ATTR_SHARED,
    ATTR_TAG,
    ATTR_TASK,
    ATTR_TOPIC,
    ATTR_URL,
    CONF_API_TOKEN,
    CONF_DEFAULT_TOPIC,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Simplepush V2 notify entity."""
    async_add_entities([SimplepushNotifyEntity(hass, entry)])


class SimplepushNotifyEntity(NotifyEntity):
    """Implementation of a Simplepush V2 notify entity."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:bell-ring-outline"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        self.hass = hass
        self._entry = entry
        self._attr_name = None  # Uses device name
        self._attr_unique_id = f"{entry.entry_id}_notify"
        self._attr_icon = "mdi:bell-ring-outline"
        self._attr_state = "ready"

    @property
    def _entry_data(self) -> dict[str, Any]:
        """Get the latest entry data from hass."""
        return self.hass.data[DOMAIN][self._entry.entry_id]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        topic = self._entry_data.get(CONF_DEFAULT_TOPIC)
        return {
            "default_topic": topic if topic else "all_devices",
            "service": "Simplepush V2",
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title or DEFAULT_NAME,
            manufacturer="Simplepush",
            model="Notification Service (API v2)",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_send_message(
        self, message: str, title: str | None = None, **kwargs: Any
    ) -> None:
        """Send a notification message or task."""
        data = kwargs.get("data") or {}

        topic = data.get(ATTR_TOPIC) or self._entry_data.get(CONF_DEFAULT_TOPIC)
        link = data.get(ATTR_LINK) or data.get(ATTR_URL)
        image = data.get(ATTR_IMAGE)
        critical = data.get(ATTR_CRITICAL, False)
        tag = data.get(ATTR_TAG)
        actions = data.get(ATTR_ACTIONS)
        choices = data.get(ATTR_CHOICES)
        shared = data.get(ATTR_SHARED, False)
        markdown = data.get(ATTR_MARKDOWN, False)
        is_task = data.get(ATTR_TASK, False) or markdown

        session = self._entry_data["session"]
        api_token = self._entry_data[CONF_API_TOKEN]

        if is_task:
            await async_send_simplepush_task(
                session=session,
                api_token=api_token,
                message=message,
                title=title,
                topic=topic,
                link=link,
                markdown=markdown,
                critical=critical,
                tag=tag,
                actions=actions,
                choices=choices,
                shared=shared,
            )
        else:
            await async_send_simplepush_notification(
                session=session,
                api_token=api_token,
                message=message,
                title=title,
                topic=topic,
                image=image,
                link=link,
                critical=critical,
                tag=tag,
                actions=actions,
                choices=choices,
                shared=shared,
            )

