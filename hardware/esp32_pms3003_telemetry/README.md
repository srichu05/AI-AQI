# AI-AQI ESP32 PMS3003 Production Firmware

Production-grade firmware for the **Plantower PMS3003** laser particulate matter sensor connected to an **ESP32 Dev Module**, streaming real-time $PM_{1.0}$, $PM_{2.5}$, and $PM_{10}$ telemetry to the AI-AQI production ingestion backend.

- **Production Backend Endpoint**: `https://ai-aqi.onrender.com/api/telemetry`
- **Production Dashboard**: `https://ai-aqi.vercel.app`
- **Transport Security**: Native HTTPS via `WiFiClientSecure` with strict X.509 Root CA certificate validation (no insecure TLS bypass).
- **Communication Protocol**: HardwareSerial UART (`Serial2` on GPIO16/17, 9600 baud 8N1).
- **Packet Format**: 24-byte Plantower binary frames with start bytes `0x42 0x4D` and 16-bit additive checksum verification.
- **Publishing Cadence**: Non-blocking 30-second interval via `millis()`.

---

## 1. Hardware Pinout & Wiring

| PMS3003 Pin | Signal Name | ESP32 Pin | Function / Notes |
|:---:|:---:|:---:|:---|
| **Pin 1** | **VCC** | **VIN / 5V** | Sensor laser and fan require 5.0V regulated power (do **not** connect to 3.3V). |
| **Pin 2** | **GND** | **GND** | Common ground with ESP32. |
| **Pin 3** | **SET** | *NC / 3.3V* | Working mode selection. High or floating = normal continuous operation. |
| **Pin 4** | **RXD** | **GPIO 17 (TX2)** | Sensor serial input (3.3V logic level). Connected to ESP32 HardwareSerial2 TX. |
| **Pin 5** | **TXD** | **GPIO 16 (RX2)** | Sensor serial output (3.3V logic level). Connected to ESP32 HardwareSerial2 RX. |
| **Pin 6** | **RESET** | *NC / 3.3V* | Hardware reset. High or floating = normal operation. |
| **Pin 7 / 8** | **NC** | *NC* | Not connected / Factory test pins. |

> [!NOTE]
> The PMS3003 sensor operates internally at 3.3V logic level on TXD and RXD pins. It can be wired directly to ESP32 GPIO16 and GPIO17 without logic-level shifters. Ensure the VCC pin is supplied with **5V** to drive the internal laser diode and airflow fan.

---

## 2. Arduino IDE Setup Instructions

### Step 1: Install ESP32 Board Support
1. Open **Arduino IDE** (v2.x or v1.8.x).
2. Go to **File -> Preferences**.
3. In **Additional Board Manager URLs**, add:
   ```text
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Open **Tools -> Board -> Boards Manager...**, search for `esp32` by **Espressif Systems**, and click **Install** (version 2.0.14 or later).

### Step 2: Configure Board Settings
Select your board under the **Tools** menu:
- **Board**: `ESP32 Dev Module` (or `NodeMCU-32S`)
- **Upload Speed**: `921600` (or `115200` if upload fails)
- **CPU Frequency**: `240MHz (WiFi/BT)`
- **Flash Frequency**: `80MHz`
- **Flash Mode**: `QIO`
- **Flash Size**: `4MB (32Mb)`
- **Partition Scheme**: `Default 4MB with spiffs (1.2MB APP/1.5MB SPIFFS)`
- **Port**: Select the COM port corresponding to your plugged-in ESP32 (e.g., `COM3`, `COM5`).

---

## 3. Firmware Configuration

Open [`esp32_pms3003_telemetry.ino`](./esp32_pms3003_telemetry.ino) and update your local WiFi network credentials:

```cpp
// WiFi Credentials
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Node Identifier
const char* DEVICE_ID     = "AI_AQI_SENSOR_NODE_01";
```

### Backend Request Contract (Pydantic Schema)
The firmware publishes JSON matching the backend's `TelemetryPayload` model:
```json
{
  "device_id": "AI_AQI_SENSOR_NODE_01",
  "pm1_ground": 8.0,
  "pm25_ground": 18.0,
  "pm10_ground": 35.0
}
```
- **Zero-Reading Guard**: The backend rejects payloads where all PM values are `0.0` with HTTP `422 Unprocessable Entity`. The firmware includes an airflow stabilization guard that pauses transmission if all values are zero until valid laser readings are obtained.
- **Authentication**: The public ingestion route `/api/telemetry` requires no API key or Bearer token.
- **Cold-Start Handling**: Render free instances spin down after inactivity. The firmware configures a 45-second HTTP timeout (`http.setTimeout(45000)`) to ensure the request completes gracefully while the backend wakes up.

---

## 4. Compilation & Flashing

1. Connect the ESP32 to your computer via USB.
2. In Arduino IDE, click the **Verify** button (check mark) to compile the sketch.
3. Click the **Upload** button (right arrow). If your ESP32 does not automatically enter flash mode, press and hold the **BOOT** button on the board until uploading begins (`Writing at 0x00010000... (100 %)`).
4. Open the **Serial Monitor** at **115200 baud**.

---

## 5. Serial Monitor Output & Ingestion Verification

When the firmware boots, the Serial Monitor displays:

```text
========================================================
   AI-AQI ESP32 PMS3003 TELEMETRY INGESTION FIRMWARE    
========================================================
Device ID       : AI_AQI_SENSOR_NODE_01
Target Endpoint : https://ai-aqi.onrender.com/api/telemetry
Publish Interval: 30 seconds
Hardware UART   : RX=GPIO16, TX=GPIO17 (9600 8N1)
Security        : TLS 1.3 / mbedTLS Strict Certificate Validation
========================================================

[WIFI] Connecting to SSID 'MyHomeWiFi'......
[WIFI] Connected successfully!
[WIFI] IP Address: 192.168.1.145
[WIFI] Signal RSSI: -54 dBm

--------------------------------------------------------
[TELEMETRY DISPATCH] Preparing secure transmission...
[TELEMETRY] Payload: {"device_id":"AI_AQI_SENSOR_NODE_01","pm1_ground":8.0,"pm25_ground":18.0,"pm10_ground":35.0}
[HTTPS] Connecting to https://ai-aqi.onrender.com/api/telemetry with TLS verification...
[HTTPS RESPONSE] HTTP Status: 200 (1240 ms)
[HTTPS RESPONSE] Body: {"status":"received","device_id":"AI_AQI_SENSOR_NODE_01","timestamp":"2026-10-14T15:46:35.895769+00:00","telemetry":{"id":516,"device_id":"AI_AQI_SENSOR_NODE_01","pm1_ground":8.0,"pm25_ground":18.0,"pm10_ground":35.0,"timestamp_utc":"2026-10-14T15:46:35.895769+00:00","source":"ESP32_PMS3003","created_at":"2026-10-14T15:46:35.994237+00:00"},"fused_features":{"feature_vector_id":182,"temperature_c":26.5,"relative_humidity":58.0,"provenance":"ESP32_PMS3003+OpenMeteo_Fusion"}}
[INGESTION SUCCESS] Telemetry ingested and persisted to PostgreSQL!
                    Live dashboard updated at https://ai-aqi.vercel.app
--------------------------------------------------------
```

---

## 6. End-to-End Verification Checkpoints

1. **Verify Backend Persistence**:
   Query the live REST endpoint from any browser or terminal:
   ```bash
   curl -s https://ai-aqi.onrender.com/api/telemetry/latest
   ```
   Expected response:
   ```json
   {
     "status": "success",
     "data": {
       "device_id": "AI_AQI_SENSOR_NODE_01",
       "pm1_ground": 8.0,
       "pm25_ground": 18.0,
       "pm10_ground": 35.0,
       "source": "ESP32_PMS3003"
     }
   }
   ```

2. **Verify Frontend Live Dashboard**:
   Open [`https://ai-aqi.vercel.app`](https://ai-aqi.vercel.app). Under the **Live Telemetry & Field Sensors** card, your device reading will show real-time $PM_{1.0}$, $PM_{2.5}$, and $PM_{10}$ metrics updated automatically.
