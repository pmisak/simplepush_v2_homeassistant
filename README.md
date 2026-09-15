# Simplepush V2 – Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)

Integrace služby **[Simplepush](https://simplepu.sh)** pro Home Assistant kompatibilní s novou verzí API (v2 / simplepu.sh).

> **Proč tato integrace?**  
> Původní vestavěná integrace v Home Assistantu i starší komunitní doplňky přestaly fungovat po vydání zcela nové verze Simplepush. Nový Simplepush přešel na moderní architekturu s **API Tokenem** a novými bezpečnými REST endpointy (`https://api.simplepu.sh/v1/notifications/json`).  
> Tato integrace používá unikátní doménu **`simplepush_v2`**, takže nekoliduje s žádnou původní integrací.

---

## 🌟 Hlavní funkce

- 🔑 **Jednoduché nastavení přes UI (Config Flow):** Stačí zadat API Token přímo v rozhraní Home Assistantu (*Nastavení -> Zařízení a služby*).
- 📲 **Osobní notifikace i Topics:** Odesílání na vlastní zařízení bez nutnosti zadávat topic, nebo cílení na konkrétní odběrová témata (Topics).
- 📌 **Podpora úkolů / karet (Tasks):** Zpráva zůstane v mobilní aplikaci Simplepush uložená jako interaktivní karta, dokud ji neodškrtnete nebo nesplníte (na rozdíl od běžných push notifikací, které po přečtení zmizí).
- 📝 **Markdown formátování:** U úkolů lze zapnout Markdown pro přehledné odrážky, tučný text nebo odkazy.
- 🔔 **Moderní `NotifyEntity`:** Vytváří standardní entitu `notify.simplepush_v2` kompatibilní s akcí `notify.send_message`.
- ⚡ **Dedikované služby:** `simplepush_v2.send_notification` a `simplepush_v2.send_task` s plnou podporou vizuálního editoru automatizací.
- 🖼️ **Obrázky (`image`):** Připojení URL obrázku k notifikaci (např. snímek z kamery).
- 🔗 **Odkazy (`link` / `url`):** Webové adresy i aplikační deep linky (např. otevření kamery).
- 🚨 **Kritické notifikace (`critical`):** Možnost obejít tichý režim a režim Nerušit na zařízeních iOS.
- 🔘 **Interaktivní tlačítka (`actions`, `choices`):** Tlačítka pro rychlé volby přímo z notifikace i úkolové karty.
- ⚡ **Rychlé a asynchronní:** Běží čistě na vestavěném `aiohttp` Home Assistantu bez nutnosti instalovat externí Python balíčky.

---

## 🚀 Kde získat API Token?

1. Stáhněte si aplikaci **Simplepush** z App Store nebo Google Play.
2. Otevřete aplikaci a přejděte do **Settings (Nastavení)**.
3. Klikněte na položku **API Token** a zkopírujte svůj osobní token.

---

## 📦 Instalace

### Možnost 1: Manuální instalace (nejjednodušší)

1. Stáhněte nebo zkopírujte složku `custom_components/simplepush_v2` z tohoto repozitáře.
2. Vložte ji do své složky `config/custom_components/` v Home Assistantu:
   ```
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
           └── translations/
   ```
3. **Restartujte Home Assistant.**

### Možnost 2: Přes HACS (Home Assistant Community Store)

1. V Home Assistantu otevřete **HACS** -> **Integrace**.
2. V pravém horním rohu klikněte na tři tečky a zvolte **Vlastní repozitáře (Custom repositories)**.
3. Vložte URL vašeho repozitáře a vyberte kategorii **Integrace (Integration)**.
4. Klikněte na **Přidat (Add)**, vyhledejte *Simplepush V2* a stáhněte jej.
5. **Restartujte Home Assistant.**

---

## ⚙️ Konfigurace

1. V Home Assistantu přejděte do **Nastavení** -> **Zařízení a služby**.
2. Klikněte na tlačítko **+ Přidat integraci**.
3. Vyhledejte **Simplepush V2**.
4. Zadejte svůj **API Token** (a volitelně výchozí Topic).
5. Klikněte na **Odeslat**.

Nastavení (např. výchozí téma nebo změnu tokenu) můžete kdykoliv upravit kliknutím na tlačítko **Konfigurovat** u přidané integrace.

---

## 📖 Příklady použití v automatizacích

### 1. Základní notifikace (přes `notify.send_message`)

```yaml
action: notify.send_message
target:
  entity_id: notify.simplepush_v2
data:
  title: "Domácnost"
  message: "Pračka právě doprala."
```

### 2. Notifikace s obrázkem a odkazem (přes `simplepush_v2.send_notification`)

```yaml
action: simplepush_v2.send_notification
data:
  title: "Pohyb u vchodu"
  message: "Byl zaznamenán pohyb před domem."
  image: "https://moje-domena.cz/local/kamera_vchod.jpg"
  link: "https://homeassistant.local:8123/lovelace/kamery"
```

### 3. Kritická notifikace (pro iOS – obejde tichý režim)

```yaml
action: simplepush_v2.send_notification
data:
  title: "POŽÁRNÍ POPLACH"
  message: "Detekován kouř v kuchyni!"
  critical: true
```

### 4. Cílení na konkrétní Topic

Pokud jste si v aplikaci Simplepush vytvořili např. topic `kamery` nebo `zabezpeceni`:

```yaml
action: simplepush_v2.send_notification
data:
  topic: "kamery"
  title: "Garáž"
  message: "Garážová vrata jsou otevřena déle než 15 minut."
```

### 5. Notifikace s akčními tlačítky (Action buttons)

Simplepush podporuje akční tlačítka přímo na push notifikaci:

```yaml
action: simplepush_v2.send_notification
data:
  title: "Odchod z domu"
  message: "Nezapomněli jste zhasnout v obýváku?"
  actions:
    - key: "turn_off"
      label: "Zhasnout"
      style: "primary"
    - key: "ignore"
      label: "Ponechat"
      style: "default"
```

Lze zadat také jednoduše textem:
```yaml
action: simplepush_v2.send_notification
data:
  title: "Vrata"
  message: "Zavřít vrata?"
  actions: "ano=Ano:primary,ne=Ne:destructive"
```

### 6. Odeslání úkolu / karty do aplikace (`simplepush_v2.send_task`)

Pokud chcete, aby zpráva **nezmizela po odkliknutí notifikace**, ale zůstala v aplikaci Simplepush na telefonu jako aktivní karta/úkol:

```yaml
action: simplepush_v2.send_task
data:
  title: "Nákupní seznam"
  message: |
    - Mléko
    - Chleba
    - Máslo
  markdown: true
```

### 7. Úkol s akčními tlačítky (potvrzení z karty)

```yaml
action: simplepush_v2.send_task
data:
  title: "Závlaha zahrady"
  message: "Půda je suchá. Spustit noční závlahu?"
  actions: "spustit=Spustit:primary,odlozit=Odložit:default"
```

### 8. Úkol přes standardní `notify.send_message`

Úkol lze poslat i přes entitu `notify.simplepush_v2` předáním `task: true`:

```yaml
action: notify.send_message
target:
  entity_id: notify.simplepush_v2
data:
  title: "Úkol pro dnešek"
  message: "Zkontrolovat stav baterií v čidlech"
  data:
    task: true
    markdown: true
```

---

## 🛠️ Dostupné služby

### Služba `simplepush_v2.send_notification`
Běžná push notifikace (po odkliknutí zmizí z notifikační lišty).

| Parametr | Typ | Povinný | Popis |
|---|---|---|---|
| `message` | Text | **Ano** | Text zprávy notifikace. |
| `title` | Text | Ne | Titulek notifikace. |
| `topic` | Text | Ne | Cílový topic. Pokud není zadán, odešle se na všechna vaše zařízení. |
| `image` | Text (URL) | Ne | Veřejně dostupná URL adresa obrázku. |
| `link` / `url` | Text (URL) | Ne | Webový odkaz nebo deep link (např. `unifi-protect://...`). |
| `critical` | Boolean | Ne | Pro iOS – obejde tichý režim a Nerušit (`true`/`false`). |
| `tag` | Text | Ne | Značka pro seskupování nebo nahrazení předchozí notifikace. |
| `actions` | Seznam / Text | Ne | Seznam akčních tlačítek (např. `ano=Ano:primary,ne=Ne`). |
| `choices` | Seznam / Text | Ne | Výběr z možností (options). |
| `shared` | Boolean | Ne | Sdílený režim (první odpověď uzavře notifikaci pro všechny). |
| `task` | Boolean | Ne | Pokud je zapnuto, odešle zprávu jako trvalý úkol do aplikace. |
| `markdown` | Boolean | Ne | Formátování textu pomocí Markdown. |

### Služba `simplepush_v2.send_task`
Úkolová karta v aplikaci Simplepush (zůstane v aplikaci uložená).

| Parametr | Typ | Povinný | Popis |
|---|---|---|---|
| `message` | Text | **Ano** | Text obsahu úkolové karty (podporuje více řádků i Markdown). |
| `title` | Text | Ne | Titulek úkolu. |
| `topic` | Text | Ne | Cílový topic. Odesílá na vlastní zařízení při vynechání. |
| `markdown` | Boolean | Ne | Povolit formátování obsahu pomocí Markdown (`true`/`false`). |
| `link` / `url` | Text (URL) | Ne | Připojený odkaz nebo deep link k úkolu. |
| `critical` | Boolean | Ne | Pro iOS – obejde tichý režim a Nerušit (`true`/`false`). |
| `tag` | Text | Ne | Značka pro seskupování nebo nahrazení úkolu. |
| `actions` | Seznam / Text | Ne | Akční tlačítka pro splnění/výběr. |
| `choices` | Seznam / Text | Ne | Výběr z možností. |
| `shared` | Boolean | Ne | Sdílený úkol (první kdo odpoví, splní ho pro všechny). |

---

## 📄 Licence
Tento projekt je licencován pod licencí MIT - viz soubor [LICENSE](LICENSE).

