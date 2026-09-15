# Simplepush V2 – Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)

[🇬🇧 English](README.md) | [🇨🇿 Česky](README_CZ.md)

Custom integration for the **[Simplepush](https://simplepu.sh)** service in Home Assistant, fully compatible with the new API version (v2 / simplepu.sh).

> **Why this integration?**  
> The original built-in integration in Home Assistant and older community plugins stopped working after Simplepush launched its completely redesigned platform. The new Simplepush transitioned to a modern architecture with **API Tokens** and secure REST endpoints (`https://api.simplepu.sh/v1/notifications/json`).  
> This custom integration uses the dedicated domain **`simplepush_v2`**, avoiding any conflict with legacy integrations.  
>  
> 🤖 *This integration was completely vibe-coded.*

---

## 🌟 Key Features

- 🔑 **Simple UI Configuration (Config Flow):** Set up your API Token directly in the Home Assistant interface (*Settings -> Devices & Services*).
- 📲 **Personal Devices & Topics:** Send notifications to all your personal devices without specifying a topic, or target specific subscription Topics.
- 📌 **Tasks / Persistent Cards Support:** Messages stay saved in the Simplepush mobile app as interactive cards until completed or dismissed (unlike transient push notifications that vanish when swiped away).
- 📝 **Markdown Formatting:** Enable rich text formatting with Markdown for tasks (headings, bold text, bullet lists, inline code, links).
- ⚡ **Bi-directional Real-Time WebSocket:** Instant feedback when buttons are tapped or choices selected on your phone via the `simplepush_v2_action` event.
- 🔔 **Modern `NotifyEntity`:** Provides standard `notify.simplepush_v2` entity compatible with the `notify.send_message` action.
- ⚡ **Dedicated Actions / Services:** `simplepush_v2.send_notification` and `simplepush_v2.send_task` with full Visual Automation Editor form support.
- 🖼️ **Image Attachments (`image`):** Attach public image URLs to push notifications (e.g. camera snapshots).
- 🔗 **Web Links & Deep Links (`link` / `url`):** Open web URLs or launch native mobile apps (e.g. `unifi-protect://`).
- 🚨 **Critical Alerts (`critical`):** Bypass mute switch and Do Not Disturb on iOS devices.
- 🔘 **Interactive Buttons (`actions`, `choices`):** Action buttons and selection menus directly on push notifications and task cards.
- ⚡ **Fast and Asynchronous:** Built purely on Home Assistant's native `aiohttp` client with zero external Python dependencies.

---

## 🚀 Getting Your API Token

1. Download the **Simplepush** app from the App Store or Google Play.
2. Open the app and navigate to **Settings**.
3. Tap on **API Token** and copy your personal token.

---

## 📦 Installation

### Option 1: Manual Installation (Recommended)

1. Download or copy the `custom_components/simplepush_v2` directory from this repository.
2. Place it into your Home Assistant's `config/custom_components/` folder:
   ```text
   config/
   └── custom_components/
       └── simplepush_v2/
           ├── __init__.py
           ├── manifest.json
           ├── const.py
           ├── config_flow.py
           ├── notify.py
           ├── services.yaml
           ├── strings.json
           ├── icons.json
           ├── brand/
           └── translations/
   ```
3. **Restart Home Assistant.**

### Option 2: Via HACS (Home Assistant Community Store)

1. Open **HACS** -> **Integrations** in Home Assistant.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Enter the repository URL: `https://github.com/pmisak/simplepush_v2_homeassistant` and choose the category **Integration**.
4. Click **Add**, search for *Simplepush V2*, and download it.
5. **Restart Home Assistant.**

---

## ⚙️ Configuration

1. In Home Assistant, go to **Settings** -> **Devices & Services**.
2. Click **+ Add Integration**.
3. Search for **Simplepush V2**.
4. Enter your **API Token** (and optionally a default Topic).
5. Click **Submit**.

You can adjust these settings (e.g. default topic or token) at any time by clicking **Configure** on the integration card.

---

## 📖 Automation Examples
 
### 1. Easy Migration from Legacy Simplepush (`notify.simplepush_v2`)

If you are migrating existing scripts and automations from the legacy Simplepush integration, simply change `notify.simplepush` to `notify.simplepush_v2`.
This action delivers messages directly as **Tasks** so they remain saved in your Simplepush mobile app. Legacy `target` and `data` parameters are safely ignored.

```yaml
action: notify.simplepush_v2
data:
  title: "Front door"
  message: "The front door is open."
```

### 2. Basic Notification (via `notify.send_message`)

```yaml
action: notify.send_message
target:
  entity_id: notify.simplepush_v2
data:
  title: "Household"
  message: "Washing machine cycle finished."
```

### 3. Notification with Image and Link (via `simplepush_v2.send_notification`)

```yaml
action: simplepush_v2.send_notification
data:
  title: "Front Door Motion"
  message: "Movement detected in front of the house."
  image: "https://my-domain.com/local/front_camera.jpg"
  link: "https://homeassistant.local:8123/lovelace/cameras"
```

### 4. Critical Alert (for iOS – bypasses silent mode)

```yaml
action: simplepush_v2.send_notification
data:
  title: "FIRE ALARM"
  message: "Smoke detected in the kitchen!"
  critical: true
```

### 5. Targeting a Specific Topic

If you created topics like `cameras` or `security` in the Simplepush app:

```yaml
action: simplepush_v2.send_notification
data:
  topic: "cameras"
  title: "Garage"
  message: "Garage door has been left open for more than 15 minutes."
```

### 6. Action Buttons on Notifications

```yaml
action: simplepush_v2.send_notification
data:
  title: "Leaving Home"
  message: "Did you forget to turn off the living room lights?"
  actions:
    - key: "turn_off"
      label: "Turn Off"
      style: "primary"
    - key: "ignore"
      label: "Leave On"
      style: "default"
```

Can also be specified as simple shorthand text:
```yaml
action: simplepush_v2.send_notification
data:
  title: "Gate"
  message: "Close the gate?"
  actions: "close=Close:primary,leave=Leave open:destructive"
```

### 7. Persistent Task Card in Mobile App (`simplepush_v2.send_task`)

When you want the message to **remain saved in the Simplepush mobile app** until you complete or dismiss it:

```yaml
action: simplepush_v2.send_task
data:
  title: "Grocery List"
  message: |
    - Milk
    - Bread
    - Butter
  markdown: true
```

### 8. Task with Action Buttons (in-app confirmation)

```yaml
action: simplepush_v2.send_task
data:
  title: "Garden Irrigation"
  message: "Soil moisture is low. Run evening watering schedule?"
  actions: "start=Start:primary,delay=Delay:default"
```

### 9. Task via Standard `notify.send_message`

Send tasks using the standard notify entity by passing `task: true`:

```yaml
action: notify.send_message
target:
  entity_id: notify.simplepush_v2
data:
  title: "Today's Task"
  message: "Check sensor battery levels"
  data:
    task: true
    markdown: true
```

---

## ⚡ Handling Button Clicks (Real-time WebSocket)

The integration maintains an **automatic bi-directional WebSocket listener** connected to Simplepush in the background. When an action button is tapped or a choice is selected on your mobile device, Home Assistant immediately fires the **`simplepush_v2_action`** event.

### Example 1: Waiting for Response in a Script (`wait_for_trigger`)

An interactive script that sends a prompt and waits for your response:

```yaml
sequence:
  # Step 1: Send notification with action buttons
  - action: simplepush_v2.send_notification
    data:
      title: "Garage Door"
      message: "Garage door is still open. Close it now?"
      actions: "close=Close:primary,leave=Leave open:default"

  # Step 2: Wait for user to tap "Close" (up to 10 minutes)
  - wait_for_trigger:
      - trigger: event
        event_type: simplepush_v2_action
        event_data:
          action: "close"
    timeout: "00:10:00"
    continue_on_timeout: false

  # Step 3: Executes only if "Close" was clicked
  - action: cover.close_cover
    target:
      entity_id: cover.garage_door
```

### Example 2: Automation Triggered by Button Tap

```yaml
trigger:
  - trigger: event
    event_type: simplepush_v2_action
    event_data:
      action: "start_irrigation"
action:
  - action: switch.turn_on
    target:
      entity_id: switch.garden_valve
```

### Available Event Data (`trigger.event.data`):

| Key | Description | Example |
|---|---|---|
| `action` | Identifier of the selected button or choice value | `"close"` |
| `value` | Response value | `"close"` or `"Approve"` |
| `type` | Type of response | `"action"`, `"choice"`, `"text"` |
| `device_name` | Name of the responding device | `"iPhone 15"` |
| `user_name` | User name | `"Petr"` |
| `task_id` / `notification_id` | Original message ID | `"tsk_..."` |

---

## 🛠️ Available Services

### Service `simplepush_v2.send_notification`
Standard push notification (cleared once dismissed from notification shade).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `message` | String | **Yes** | Message body content. |
| `title` | String | No | Notification title. |
| `topic` | String | No | Target topic. Omit to send to all personal devices. |
| `image` | String (URL) | No | Publicly accessible image URL. |
| `link` / `url` | String (URL) | No | Web URL or app deep link (e.g. `unifi-protect://...`). |
| `critical` | Boolean | No | For iOS – bypasses silent switch and Do Not Disturb (`true`/`false`). |
| `tag` | String | No | Tag for grouping or replacing pending notifications. |
| `actions` | List / String | No | List of action buttons (e.g. `yes=Yes:primary,no=No:destructive`). |
| `choices` | List / String | No | Selection options. |
| `shared` | Boolean | No | Shared mode (first response answers for everyone). |
| `task` | Boolean | No | Deliver as persistent task card instead of transient push. |
| `markdown` | Boolean | No | Render content using Markdown formatting (automatically routes as task). |

### Service `simplepush_v2.send_task`
Persistent task card in the Simplepush app (stays saved until completed or dismissed).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `message` | String | **Yes** | Task card body content (supports multi-line & Markdown). |
| `title` | String | No | Task title. |
| `topic` | String | No | Target topic. Omit to send to personal devices. |
| `markdown` | Boolean | No | Render content as rich Markdown (`true`/`false`). |
| `link` / `url` | String (URL) | No | Attached web URL or app deep link. |
| `critical` | Boolean | No | For iOS – bypasses silent switch (`true`/`false`). |
| `tag` | String | No | Tag for grouping or replacing pending tasks. |
| `actions` | List / String | No | Action buttons for completion/selection. |
| `choices` | List / String | No | Selection options. |
| `shared` | Boolean | No | Shared task (first answer completes for everyone). |

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
