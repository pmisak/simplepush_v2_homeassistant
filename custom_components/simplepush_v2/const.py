"""Constants for the Simplepush V2 integration."""

from typing import Final

DOMAIN: Final = "simplepush_v2"

# Configuration keys
CONF_API_TOKEN: Final = "api_token"
CONF_DEFAULT_TOPIC: Final = "default_topic"
CONF_NAME: Final = "name"

# Defaults
DEFAULT_NAME: Final = "Simplepush V2"

# API Endpoints
API_BASE_URL: Final = "https://api.simplepu.sh/v1"
API_USER_ENDPOINT: Final = f"{API_BASE_URL}/user"
API_NOTIFICATIONS_ENDPOINT: Final = f"{API_BASE_URL}/notifications/json"
API_TASKS_ENDPOINT: Final = f"{API_BASE_URL}/tasks/json"
API_WS_URL: Final = "wss://api.simplepu.sh/ws/v1/events"

# Events
EVENT_SIMPLEPUSH_ACTION: Final = "simplepush_v2_action"

# Service names and attributes
SERVICE_SEND_NOTIFICATION: Final = "send_notification"
SERVICE_SEND_TASK: Final = "send_task"

ATTR_MESSAGE: Final = "message"
ATTR_TITLE: Final = "title"
ATTR_TOPIC: Final = "topic"
ATTR_IMAGE: Final = "image"
ATTR_LINK: Final = "link"
ATTR_URL: Final = "url"
ATTR_CRITICAL: Final = "critical"
ATTR_TAG: Final = "tag"
ATTR_ACTIONS: Final = "actions"
ATTR_CHOICES: Final = "choices"
ATTR_SHARED: Final = "shared"
ATTR_TASK: Final = "task"
ATTR_MARKDOWN: Final = "markdown"

