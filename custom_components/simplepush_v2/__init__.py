"""The Simplepush V2 integration."""

import asyncio
from datetime import datetime, timezone
import json
import logging
import mimetypes
from urllib.parse import quote
import uuid
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import aiohttp_client
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    API_NOTIFICATIONS_ENDPOINT,
    API_TASKS_ENDPOINT,
    API_USER_ENDPOINT,
    API_WS_URL,
    ATTR_ACTIONS,
    ATTR_CHOICES,
    ATTR_CRITICAL,
    ATTR_IMAGE,
    ATTR_LINK,
    ATTR_MARKDOWN,
    ATTR_MESSAGE,
    ATTR_SHARED,
    ATTR_TAG,
    ATTR_TASK,
    ATTR_TITLE,
    ATTR_TOPIC,
    ATTR_URL,
    CONF_API_TOKEN,
    CONF_DEFAULT_TOPIC,
    DOMAIN,
    EVENT_SIMPLEPUSH_ACTION,
    SERVICE_SEND_NOTIFICATION,
    SERVICE_SEND_TASK,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NOTIFY]

IMAGE_EXT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

SERVICE_NOTIFICATION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MESSAGE): cv.string,
        vol.Optional(ATTR_TITLE): cv.string,
        vol.Optional(ATTR_TOPIC): cv.string,
        vol.Optional(ATTR_IMAGE): cv.string,
        vol.Optional(ATTR_LINK): cv.string,
        vol.Optional(ATTR_URL): cv.string,
        vol.Optional(ATTR_CRITICAL, default=False): cv.boolean,
        vol.Optional(ATTR_TAG): cv.string,
        vol.Optional(ATTR_ACTIONS): vol.Any(cv.ensure_list, cv.string),
        vol.Optional(ATTR_CHOICES): vol.Any(cv.ensure_list, cv.string),
        vol.Optional(ATTR_SHARED, default=False): cv.boolean,
        vol.Optional(ATTR_TASK, default=False): cv.boolean,
        vol.Optional(ATTR_MARKDOWN, default=False): cv.boolean,
    }
)

SERVICE_TASK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MESSAGE): cv.string,
        vol.Optional(ATTR_TITLE): cv.string,
        vol.Optional(ATTR_TOPIC): cv.string,
        vol.Optional(ATTR_LINK): cv.string,
        vol.Optional(ATTR_URL): cv.string,
        vol.Optional(ATTR_MARKDOWN, default=False): cv.boolean,
        vol.Optional(ATTR_CRITICAL, default=False): cv.boolean,
        vol.Optional(ATTR_TAG): cv.string,
        vol.Optional(ATTR_ACTIONS): vol.Any(cv.ensure_list, cv.string),
        vol.Optional(ATTR_CHOICES): vol.Any(cv.ensure_list, cv.string),
        vol.Optional(ATTR_SHARED, default=False): cv.boolean,
    }
)



def _parse_action(action_item: Any) -> dict[str, str]:
    """Parse a single action item into Simplepush action wire format."""
    if isinstance(action_item, dict):
        key = str(
            action_item.get("key")
            or action_item.get("action")
            or action_item.get("id")
            or action_item.get("title", "")
        )
        label = str(
            action_item.get("label")
            or action_item.get("title")
            or action_item.get("key")
            or key
        )
        style = action_item.get("style", "default")
        if style not in ("default", "primary", "destructive"):
            style = "default"
        return {"key": key, "label": label, "style": style}

    if isinstance(action_item, str):
        # Format can be:
        # 1. "key=label:style"
        # 2. "key=label"
        # 3. "key:label:style"
        # 4. "key:label"
        # 5. "label"
        val = action_item.strip()
        style = "default"
        if "=" in val:
            key, rest = val.split("=", 1)
            if ":" in rest:
                label, style_val = rest.split(":", 1)
                if style_val in ("default", "primary", "destructive"):
                    style = style_val
            else:
                label = rest
            return {"key": key.strip(), "label": label.strip(), "style": style}

        parts = val.split(":")
        if len(parts) == 3:
            key, label, style_val = parts
            if style_val in ("default", "primary", "destructive"):
                style = style_val
            return {"key": key.strip(), "label": label.strip(), "style": style}
        if len(parts) == 2:
            key, label = parts
            return {"key": key.strip(), "label": label.strip(), "style": style}

        return {"key": val, "label": val, "style": style}

    return {"key": str(action_item), "label": str(action_item), "style": "default"}


def build_notification_payload(
    message: str,
    title: str | None = None,
    topic: str | None = None,
    image: str | None = None,
    link: str | None = None,
    critical: bool = False,
    tag: str | None = None,
    actions: list[Any] | str | None = None,
    choices: list[Any] | str | None = None,
    shared: bool = False,
) -> dict[str, Any]:
    """Build the JSON payload for Simplepush notification endpoint."""
    payload: dict[str, Any] = {
        "content": message,
        "idempotencyKey": str(uuid.uuid4()),
    }

    if title:
        payload["title"] = title

    if topic:
        clean_topic = str(topic).strip().replace(" ", "_")
        if clean_topic:
            payload["topic"] = clean_topic

    if critical:
        payload["critical"] = True

    if tag:
        payload["tag"] = tag

    if shared:
        payload["shared"] = True

    # Parse actions or choices
    has_input = False
    if actions:
        has_input = True
        action_list = actions if isinstance(actions, list) else [a.strip() for a in actions.split(",")]
        parsed_actions = [_parse_action(a) for a in action_list if a]
        if parsed_actions:
            payload["actionInput"] = {"actions": parsed_actions}
    elif choices:
        has_input = True
        choice_list = choices if isinstance(choices, list) else [c.strip() for c in choices.split(",")]
        cleaned_choices = [str(c) for c in choice_list if c]
        if cleaned_choices:
            payload["choiceInput"] = {"options": cleaned_choices}

    # Handle media (image)
    if image:
        ext = ""
        url_part = image.split("?", 1)[0]
        if "." in url_part:
            ext = f".{url_part.rsplit('.', 1)[1].lower()}"
        content_type = IMAGE_EXT_TYPES.get(ext) or mimetypes.guess_type(image)[0] or "image/jpeg"
        payload["media"] = {
            "type": "link",
            "url": image,
            "contentType": content_type,
        }

    # Link: Simplepush rules state that link and input are mutually exclusive
    if link and not has_input:
        payload["link"] = link
    elif link and has_input:
        _LOGGER.warning(
            "Simplepush notification: 'link' ignored because action/choice buttons were also specified"
        )

    return payload


async def async_validate_token(session: aiohttp.ClientSession, api_token: str) -> bool:
    """Validate API token by querying the user endpoint."""
    headers = {
        "API-Token": api_token,
        "Accept": "application/json",
    }
    try:
        async with session.get(
            API_USER_ENDPOINT,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            return response.status == 200
    except (aiohttp.ClientError, TimeoutError) as err:
        _LOGGER.debug("Error while validating Simplepush token: %s", err)
        raise


async def async_send_simplepush_notification(
    session: aiohttp.ClientSession,
    api_token: str,
    message: str,
    title: str | None = None,
    topic: str | None = None,
    image: str | None = None,
    link: str | None = None,
    critical: bool = False,
    tag: str | None = None,
    actions: list[Any] | str | None = None,
    choices: list[Any] | str | None = None,
    shared: bool = False,
) -> dict[str, Any]:
    """Send notification to Simplepush."""
    payload = build_notification_payload(
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

    headers = {
        "API-Token": api_token,
        "Content-Type": "application/json",
    }

    try:
        async with session.post(
            API_NOTIFICATIONS_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            if response.status not in (200, 201):
                err_text = await response.text()
                _LOGGER.error(
                    "Simplepush API returned error %s: %s", response.status, err_text
                )
                raise HomeAssistantError(
                    f"Simplepush API error ({response.status}): {err_text}"
                )

            if response.content_type == "application/json":
                return await response.json()
            return {}
    except (aiohttp.ClientError, TimeoutError) as err:
        _LOGGER.error("Failed to communicate with Simplepush API: %s", err)
        raise HomeAssistantError(f"Simplepush connection error: {err}") from err


def build_task_payload(
    message: str,
    title: str | None = None,
    topic: str | None = None,
    link: str | None = None,
    markdown: bool = False,
    critical: bool = False,
    tag: str | None = None,
    actions: list[Any] | str | None = None,
    choices: list[Any] | str | None = None,
    shared: bool = False,
) -> dict[str, Any]:
    """Build the JSON payload for Simplepush task endpoint."""
    payload: dict[str, Any] = {
        "content": message,
        "idempotencyKey": str(uuid.uuid4()),
    }

    if title:
        payload["title"] = title

    if topic:
        clean_topic = str(topic).strip().replace(" ", "_")
        if clean_topic:
            payload["topic"] = clean_topic

    if markdown:
        payload["contentFormat"] = "markdown"

    if critical:
        payload["critical"] = True

    if tag:
        payload["tag"] = tag

    if shared:
        payload["shared"] = True

    if link:
        payload["links"] = [link]

    # Build inputs for actions or choices if provided
    inputs: list[dict[str, Any]] = []
    if actions:
        action_list = (
            actions if isinstance(actions, list) else [a.strip() for a in actions.split(",")]
        )
        parsed_actions = [_parse_action(a) for a in action_list if a]
        if parsed_actions:
            inputs.append({
                "type": "actions",
                "required": True,
                "actions": parsed_actions,
            })
    elif choices:
        choice_list = (
            choices if isinstance(choices, list) else [c.strip() for c in choices.split(",")]
        )
        cleaned_choices = [str(c) for c in choice_list if c]
        if cleaned_choices:
            inputs.append({
                "type": "choice",
                "required": True,
                "options": cleaned_choices,
            })

    if inputs:
        payload["inputs"] = inputs

    return payload


async def async_send_simplepush_task(
    session: aiohttp.ClientSession,
    api_token: str,
    message: str,
    title: str | None = None,
    topic: str | None = None,
    link: str | None = None,
    markdown: bool = False,
    critical: bool = False,
    tag: str | None = None,
    actions: list[Any] | str | None = None,
    choices: list[Any] | str | None = None,
    shared: bool = False,
) -> dict[str, Any]:
    """Send a persistent task to Simplepush."""
    payload = build_task_payload(
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

    headers = {
        "API-Token": api_token,
        "Content-Type": "application/json",
    }

    try:
        async with session.post(
            API_TASKS_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            if response.status not in (200, 201):
                err_text = await response.text()
                _LOGGER.error(
                    "Simplepush Task API returned error %s: %s", response.status, err_text
                )
                raise HomeAssistantError(
                    f"Simplepush Task API error ({response.status}): {err_text}"
                )

            if response.content_type == "application/json":
                return await response.json()
            return {}
    except (aiohttp.ClientError, TimeoutError) as err:
        _LOGGER.error("Failed to communicate with Simplepush Task API: %s", err)
        raise HomeAssistantError(f"Simplepush connection error: {err}") from err


def extract_event_actions(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract action/choice/text responses from a Simplepush event."""
    results: list[dict[str, Any]] = []
    if not isinstance(raw, dict):
        return results

    data = raw.get("data")
    if not isinstance(data, dict):
        return results

    actor = raw.get("actor") or {}
    task_id = data.get("taskId") or data.get("parentTaskId")
    notification_id = data.get("notificationId")
    device_name = actor.get("deviceName")
    device_id = actor.get("devicePublicId")
    user_name = actor.get("name")

    # 1. Notification reply
    reply = data.get("reply")
    if isinstance(reply, dict):
        rep_type = reply.get("type")
        if rep_type in ("actions", "actionSelected") or "selectedKey" in reply:
            key = reply.get("selectedKey")
            results.append({
                "action": key,
                "value": key,
                "type": "action",
                "task_id": task_id,
                "notification_id": notification_id,
                "device_name": device_name,
                "device_id": device_id,
                "user_name": user_name,
            })
        elif rep_type in ("choice", "choiceSelected") or "selectedValue" in reply:
            val = reply.get("selectedValue")
            results.append({
                "action": val,
                "value": val,
                "choice_index": reply.get("selectedIndex"),
                "type": "choice",
                "task_id": task_id,
                "notification_id": notification_id,
                "device_name": device_name,
                "device_id": device_id,
                "user_name": user_name,
            })
        elif rep_type in ("text", "textUploaded") or "value" in reply:
            val = reply.get("value")
            results.append({
                "action": val,
                "value": val,
                "type": "text",
                "task_id": task_id,
                "notification_id": notification_id,
                "device_name": device_name,
                "device_id": device_id,
                "user_name": user_name,
            })

    # 2. Task single upload or completed list of uploads
    uploads = []
    if isinstance(data.get("inputUploaded"), dict):
        uploads.append(data["inputUploaded"])
    if isinstance(data.get("inputsUploaded"), list):
        uploads.extend([u for u in data["inputsUploaded"] if isinstance(u, dict)])

    for u in uploads:
        u_type = u.get("type")
        if u_type == "actionSelected" or "selectedKey" in u:
            key = u.get("selectedKey")
            results.append({
                "action": key,
                "value": key,
                "type": "action",
                "task_id": task_id,
                "notification_id": notification_id,
                "device_name": device_name,
                "device_id": device_id,
                "user_name": user_name,
            })
        elif u_type == "choiceSelected" or "selectedValue" in u:
            val = u.get("selectedValue")
            results.append({
                "action": val,
                "value": val,
                "choice_index": u.get("selectedIndex"),
                "type": "choice",
                "task_id": task_id,
                "notification_id": notification_id,
                "device_name": device_name,
                "device_id": device_id,
                "user_name": user_name,
            })
        elif u_type == "multiChoiceSelected" or "selectedValues" in u:
            vals = u.get("selectedValues")
            results.append({
                "action": vals,
                "value": vals,
                "choice_indices": u.get("selectedIndices"),
                "type": "multi_choice",
                "task_id": task_id,
                "notification_id": notification_id,
                "device_name": device_name,
                "device_id": device_id,
                "user_name": user_name,
            })
        elif u_type == "textUploaded" or "value" in u:
            val = u.get("value")
            results.append({
                "action": val,
                "value": val,
                "type": "text",
                "task_id": task_id,
                "notification_id": notification_id,
                "device_name": device_name,
                "device_id": device_id,
                "user_name": user_name,
            })

    return results


async def async_listen_simplepush_events(
    hass: HomeAssistant, entry_id: str, api_token: str
) -> None:
    """Listen for Simplepush events via WebSocket and fire events on the HA bus."""
    session = aiohttp_client.async_get_clientsession(hass)
    headers = {"API-Token": api_token}
    since = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    backoff = 2.0

    while True:
        try:
            url = f"{API_WS_URL}?since={quote(since, safe='')}"
            _LOGGER.debug("Connecting to Simplepush WebSocket: %s", url)
            async with session.ws_connect(
                url,
                headers=headers,
                heartbeat=30.0,
            ) as ws:
                _LOGGER.info("Connected to Simplepush WebSocket event stream")
                backoff = 2.0
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            raw = json.loads(msg.data)
                            if raw.get("createdAt"):
                                since = raw["createdAt"]
                            actions = extract_event_actions(raw)
                            for action_data in actions:
                                _LOGGER.info(
                                    "Simplepush action received: %s (action=%s)",
                                    action_data.get("action"),
                                    action_data,
                                )
                                hass.bus.async_fire(EVENT_SIMPLEPUSH_ACTION, action_data)
                        except Exception as err:
                            _LOGGER.warning("Error processing Simplepush event: %s", err)
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.ERROR):
                        _LOGGER.debug("Simplepush WebSocket closed")
                        break
        except asyncio.CancelledError:
            _LOGGER.debug("Simplepush WebSocket listener canceled for entry %s", entry_id)
            raise
        except Exception as exc:
            _LOGGER.debug(
                "Simplepush WebSocket error: %s (reconnecting in %ss)", exc, backoff
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60.0)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Simplepush V2 component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Simplepush V2 from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    session = aiohttp_client.async_get_clientsession(hass)
    api_token = entry.data[CONF_API_TOKEN]

    # Start background WebSocket event listener
    ws_task = hass.async_create_background_task(
        async_listen_simplepush_events(hass, entry.entry_id, api_token),
        name=f"simplepush_v2_ws_{entry.entry_id}",
    )

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_API_TOKEN: api_token,
        CONF_DEFAULT_TOPIC: entry.options.get(
            CONF_DEFAULT_TOPIC, entry.data.get(CONF_DEFAULT_TOPIC)
        ),
        "session": session,
        "ws_task": ws_task,
    }

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))


    # Register send_notification service if not already registered
    if not hass.services.has_service(DOMAIN, SERVICE_SEND_NOTIFICATION):
        async def handle_send_notification(call: ServiceCall) -> None:
            """Handle the send_notification service call."""
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                raise HomeAssistantError("Simplepush V2 integration is not configured")

            selected_entry = entries[0]
            entry_data = hass.data[DOMAIN][selected_entry.entry_id]
            api_token = entry_data[CONF_API_TOKEN]
            default_topic = entry_data.get(CONF_DEFAULT_TOPIC)

            topic = call.data.get(ATTR_TOPIC) or default_topic
            link = call.data.get(ATTR_LINK) or call.data.get(ATTR_URL)
            markdown = call.data.get(ATTR_MARKDOWN, False)
            is_task = call.data.get(ATTR_TASK, False) or markdown

            if is_task:
                await async_send_simplepush_task(
                    session=entry_data["session"],
                    api_token=api_token,
                    message=call.data[ATTR_MESSAGE],
                    title=call.data.get(ATTR_TITLE),
                    topic=topic,
                    link=link,
                    markdown=call.data.get(ATTR_MARKDOWN, False),
                    critical=call.data.get(ATTR_CRITICAL, False),
                    tag=call.data.get(ATTR_TAG),
                    actions=call.data.get(ATTR_ACTIONS),
                    choices=call.data.get(ATTR_CHOICES),
                    shared=call.data.get(ATTR_SHARED, False),
                )
            else:
                await async_send_simplepush_notification(
                    session=entry_data["session"],
                    api_token=api_token,
                    message=call.data[ATTR_MESSAGE],
                    title=call.data.get(ATTR_TITLE),
                    topic=topic,
                    image=call.data.get(ATTR_IMAGE),
                    link=link,
                    critical=call.data.get(ATTR_CRITICAL, False),
                    tag=call.data.get(ATTR_TAG),
                    actions=call.data.get(ATTR_ACTIONS),
                    choices=call.data.get(ATTR_CHOICES),
                    shared=call.data.get(ATTR_SHARED, False),
                )

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_NOTIFICATION,
            handle_send_notification,
            schema=SERVICE_NOTIFICATION_SCHEMA,
        )

    # Register send_task service if not already registered
    if not hass.services.has_service(DOMAIN, SERVICE_SEND_TASK):
        async def handle_send_task(call: ServiceCall) -> None:
            """Handle the send_task service call."""
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                raise HomeAssistantError("Simplepush V2 integration is not configured")

            selected_entry = entries[0]
            entry_data = hass.data[DOMAIN][selected_entry.entry_id]
            api_token = entry_data[CONF_API_TOKEN]
            default_topic = entry_data.get(CONF_DEFAULT_TOPIC)

            topic = call.data.get(ATTR_TOPIC) or default_topic
            link = call.data.get(ATTR_LINK) or call.data.get(ATTR_URL)

            await async_send_simplepush_task(
                session=entry_data["session"],
                api_token=api_token,
                message=call.data[ATTR_MESSAGE],
                title=call.data.get(ATTR_TITLE),
                topic=topic,
                link=link,
                markdown=call.data.get(ATTR_MARKDOWN, False),
                critical=call.data.get(ATTR_CRITICAL, False),
                tag=call.data.get(ATTR_TAG),
                actions=call.data.get(ATTR_ACTIONS),
                choices=call.data.get(ATTR_CHOICES),
                shared=call.data.get(ATTR_SHARED, False),
            )

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_TASK,
            handle_send_task,
            schema=SERVICE_TASK_SCHEMA,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
    ws_task = entry_data.get("ws_task")
    if ws_task and not ws_task.done():
        ws_task.cancel()
        try:
            await ws_task
        except asyncio.CancelledError:
            pass

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        # If no more entries exist, unregister services
        if not hass.data[DOMAIN]:
            if hass.services.has_service(DOMAIN, SERVICE_SEND_NOTIFICATION):
                hass.services.async_remove(DOMAIN, SERVICE_SEND_NOTIFICATION)
            if hass.services.has_service(DOMAIN, SERVICE_SEND_TASK):
                hass.services.async_remove(DOMAIN, SERVICE_SEND_TASK)
    return unload_ok



async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
