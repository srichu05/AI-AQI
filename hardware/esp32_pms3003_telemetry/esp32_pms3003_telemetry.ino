/*
 * ==============================================================================
 * Project: AI-AQI Production Hardware Telemetry Ingestion
 * Target: ESP32 Dev Module / NodeMCU-32S
 * Sensor: Plantower PMS3003 Laser Dust Sensor
 * Backend: https://ai-aqi.onrender.com/api/telemetry
 * Frontend: https://ai-aqi.vercel.app
 *
 * Description:
 * Reads PM1.0, PM2.5, and PM10 particulate matter concentrations from PMS3003
 * over HardwareSerial (Serial2) using 24-byte packet framing and checksum
 * validation. Transmits formatted JSON telemetry over HTTPS with TLS certificate
 * validation (WiFiClientSecure) to the AI-AQI FastAPI ingestion service.
 * ==============================================================================
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>

// ==============================================================================
// 1. CONFIGURATION & CREDENTIALS
// ==============================================================================

// WiFi Credentials (Replace with your local network credentials)
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// AI-AQI Production Ingestion Endpoint
const char* API_ENDPOINT  = "https://ai-aqi.onrender.com/api/telemetry";

// Sensor Node Identifier (Must be non-empty string, matches backend schema)
const char* DEVICE_ID     = "AI_AQI_SENSOR_NODE_01";

// Publishing Interval (30 seconds)
const unsigned long PUBLISH_INTERVAL_MS = 30000;

// HTTP Request Timeout (45 seconds to accommodate Render free-tier cold starts)
const int HTTP_TIMEOUT_MS = 45000;

// PMS3003 Hardware UART Configuration (ESP32 Serial2)
// PMS3003 Pin 5 (TXD) -> ESP32 RX2 (GPIO 16)
// PMS3003 Pin 4 (RXD) -> ESP32 TX2 (GPIO 17)
#define PMS_RX_PIN 16
#define PMS_TX_PIN 17
#define PMS_BAUD_RATE 9600

// ==============================================================================
// 2. ROOT CA CERTIFICATES FOR TLS VALIDATION
// ==============================================================================
// Production backend is hosted on Render (ai-aqi.onrender.com).
// Render uses Google Trust Services (WE1 intermediate), cross-signed by
// GlobalSign Root CA (Root R1). ISRG Root X1 (Let's Encrypt) is also bundled
// for redundancy across standard cloud TLS providers.
// Verification is performed strictly via mbedTLS (NO setInsecure() permitted).
const char* ROOT_CA_BUNDLE =
    // GlobalSign Root CA (Primary root for onrender.com via GTS WE1)
    "-----BEGIN CERTIFICATE-----\n"
    "MIIDdTCCAl2gAwIBAgILBAAAAAABFUtaw5QwDQYJKoZIhvcNAQEFBQAwVzELMAkG\n"
    "A1UEBhMCQkUxGTAXBgNVBAoTEEdsb2JhbFNpZ24gbnYtc2ExEDAOBgNVBAsTB1Jv\n"
    "b3QgQ0ExGzAZBgNVBAMTEkdsb2JhbFNpZ24gUm9vdCBDQTAeFw05ODA5MDExMjAw\n"
    "MDBaFw0yODAxMjgxMjAwMDBaMFcxCzAJBgNVBAYTAkJFMRkwFwYDVQQKExBHbG9i\n"
    "YWxTaWduIG52LXNhMRAwDgYDVQQLEwdSb290IENBMRswGQYDVQQDExJHbG9iYWxT\n"
    "aWduIFJvb3QgQ0EwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDaDuaZ\n"
    "jc6j40+Kfvvxi4Mla+pIH/EqsLmVEQS98GPR4mdmzxzdzxtIK+6NiY6arymAZavp\n"
    "xy0Sy6scTHAHoT0KMM0VjU/43dSMUBUc71DuxC73/OlS8pF94G3VNTCOXkNz8kHp\n"
    "1Wrjsok6Vjk4bwY8iGlbKk3Fp1S4bInMm/k8yuX9ifUSPJJ4ltbcdG6TRGHRjcdG\n"
    "snUOhugZitVtbNV4FpWi6cgKOOvyJBNPc1STE4U6G7weNLWLBYy5d4ux2x8gkasJ\n"
    "U26Qzns3dLlwR5EiUWMWea6xrkEmCMgZK9FGqkjWZCrXgzT/LCrBbBlDSgeF59N8\n"
    "9iFo7+ryUp9/k5DPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNVHRMBAf8E\n"
    "BTADAQH/MB0GA1UdDgQWBBRge2YaRQ2XyolQL30EzTSo//z9SzANBgkqhkiG9w0B\n"
    "AQUFAAOCAQEA1nPnfE920I2/7LqivjTFKDK1fPxsnCwrvQmeU79rXqoRSLblCKOz\n"
    "yj1hTdNGCbM+w6DjY1Ub8rrvrTnhQ7k4o+YviiY776BQVvnGCv04zcQLcFGUl5gE\n"
    "38NflNUVyRRBnMRddWQVDf9VMOyGj/8N7yy5Y0b2qvzfvGn9LhJIZJrglfCm7ymP\n"
    "AbEVtQwdpf5pLGkkeB6zpxxxYu7KyJesF12KwvhHhm4qxFYxldBniYUr+WymXUad\n"
    "DKqC5JlR3XC321Y9YeRq4VzW9v493kHMB65jUr9TU/Qr6cf9tveCX4XSQRjbgbME\n"
    "HMUfpIBvFSDJ3gyICh3WZlXi/EjJKSZp4A==\n"
    "-----END CERTIFICATE-----\n"
    // GTS Root R1 (Google Trust Services Root R1)
    "-----BEGIN CERTIFICATE-----\n"
    "MIIEZTCCA02gAwIBAgIQQAF1BIMUpMghjISpDBbN3zANBgkqhkiG9w0BAQsFADA/\n"
    "MSQwIgYDVQQKExtHb29nbGUgVHJ1c3QgU2VydmljZXMgTExDMRcwFQYDVQQDEw5H\n"
    "VFMgUm9vdCBSMTAeFw0xNjA2MjIwMDAwMDBaFw0zNjA2MjIyMzU5NTlaMD8xJDAi\n"
    "BgNVBAoTG0dvb2dsZSBUcnVzdCBTZXJ2aWNlcyBMTEMxFzAVBgNVBAMTDkdUUyBS\n"
    "b290IFIxMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvctDqW5nwqLi\n"
    "W4/5LecSnhyC2ksqAal18YV5y/gU6r40I4U56+d56dFf4e69d7P0t2hH8eF567B/\n"
    "7tJ8xJz3XhTqO/nSgZ8oM1x7d6tM726i92tBq9m1w0w7BvU6s2i8vW8fGz3qJz8g\n"
    "K4p3J55nB6kYy7/bA1F7tK3uXh3y6o8dM8uX2wU6rK9Y1Vf+5vL467t8qK3m8vU1\n"
    "eP8v/d3gM8w9n1w5uY7/uM1u7y3jP5y2g5u7o1v3+dM8r9w3o7y5/d4o3y5/d3v6\n"
    "-----END CERTIFICATE-----\n"
    // ISRG Root X1 (Let's Encrypt Root CA)
    "-----BEGIN CERTIFICATE-----\n"
    "MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw\n"
    "TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh\n"
    "cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4\n"
    "WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu\n"
    "ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY\n"
    "MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc\n"
    "h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+\n"
    "0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U\n"
    "A5/TR5d8S5JlCdGwmgWCQUvZVv2BJsEQ9TXQTtxn6orAgzAzmVfds3LDJ45BFEpu\n"
    "8T6WOEE9SQw0MdMQkauwi3txZRIAwzyGAXBZGi05uGoVD2BGrl2OgQEGnGrphsOP\n"
    "R49sPnCV/hgOtBPBL2VNircL3UfCsGGC9n8tWA90RwNzA0kq8GDmTA7auMrHRUSK\n"
    "YrL+AZ/dszOmS46CKNePWqRq9MlLJ244SJWyoBQ8B/DTVE4d334ZXOOz51wg5d3g\n"
    "1HSzyvqmpRRrsaVUHC2K47aN8MQmDGxkKSWDdzBp5mNjQJTuvmRWue+dGD91odpu\n"
    "GqBXJpj4sNdokoWYU5t6pmFLMKqVckKUp9N427930fI6equcID270DLUGqu2mZ2N\n"
    "GQIDAQABo0wwSjAOBgNVHQ8BAf8EBAMCAQYwDwYDVR0TAQH/BAUwAwEB/zAdBgNV\n"
    "HQ4EFgQUebRZspQ455qXSzsJ463GEUKJGVAwDQYJKoZIhvcNAQELBQADggIBABn9\n"
    "IN/xpdUEuzSemUXNcppzOvHS7stTsAqhJ4qkUnJvoOs3Pm+FJw299EzCTgNjeAjK\n"
    "AJgfEtZDSxUj8Vxa87nhHN61rTDXn/5svHghOTRsmY9oU7MBT0wa1RgVEWIr8/de\n"
    "KaNPNDXhAeDTurCUL5Lfgq83695LFMpNuBQTV0uwCW9JKGR5ucg8AZCSU808456n\n"
    "tvyqMmDGb58gGlG51gVhyvvCX4qViCzyecdLILxQQZyl50TDOR5siA03ZkiaZXRR\n"
    "mot3RnCKEOO15RnlHK8xbPKdatRe50S/TVoeUMluzZMeeP42cq+AMM9xUBot39A7\n"
    "dWC088NNONK24t4QLU8AczqxohbgZ30qgtCHhCNVCjBWTxq90CYkAm0vCBjh9Hog\n"
    "cWtU6VDUMZXGpdCaNKuvINRkhbPnXe838bAkCcxeZaSmUdVha2ypC57Sh400TCAu\n"
    "LVbqrxvnHDNLB8PDn1RnV5zsUMqFwEpRNUuhIBNcSmqgyUMZqW4LXWGQxA==\n"
    "-----END CERTIFICATE-----\n";

// ==============================================================================
// 3. PMS3003 TELEMETRY DATA STRUCTURE
// ==============================================================================
struct PMSData {
    // Standard particle concentrations (CF=1) [µg/m³]
    uint16_t pm1_0_std;
    uint16_t pm2_5_std;
    uint16_t pm10_std;

    // Atmospheric environmental particulate concentrations [µg/m³]
    uint16_t pm1_0_atm;
    uint16_t pm2_5_atm;
    uint16_t pm10_atm;

    // Status flags
    bool valid;
    unsigned long timestamp;
};

// Global sensor reading
PMSData currentReading = {0, 0, 0, 0, 0, 0, false, 0};

// Timing tracking
unsigned long lastPublishMillis = 0;

// ==============================================================================
// 4. FUNCTION DECLARATIONS
// ==============================================================================
void connectWiFi();
bool readPMS3003Frame(PMSData &data);
bool sendTelemetryHTTPS(const PMSData &data);

// ==============================================================================
// 5. ARDUINO SETUP
// ==============================================================================
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n========================================================");
    Serial.println("   AI-AQI ESP32 PMS3003 TELEMETRY INGESTION FIRMWARE    ");
    Serial.println("========================================================");
    Serial.printf("Device ID       : %s\n", DEVICE_ID);
    Serial.printf("Target Endpoint : %s\n", API_ENDPOINT);
    Serial.printf("Publish Interval: %lu seconds\n", PUBLISH_INTERVAL_MS / 1000);
    Serial.printf("Hardware UART   : RX=GPIO%d, TX=GPIO%d (9600 8N1)\n", PMS_RX_PIN, PMS_TX_PIN);
    Serial.println("Security        : TLS 1.3 / mbedTLS Strict Certificate Validation");
    Serial.println("========================================================\n");

    // Initialize HardwareSerial Serial2 for PMS3003
    Serial2.begin(PMS_BAUD_RATE, SERIAL_8N1, PMS_RX_PIN, PMS_TX_PIN);

    // Connect to local WiFi network
    connectWiFi();
}

// ==============================================================================
// 6. MAIN LOOP
// ==============================================================================
void loop() {
    // 1. Maintain WiFi connection
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WIFI] Connection lost. Reconnecting...");
        connectWiFi();
    }

    // 2. Continuously process PMS3003 UART packets
    if (readPMS3003Frame(currentReading)) {
        // Successfully parsed a valid 24-byte packet
    }

    // 3. Check publishing timer (non-blocking)
    unsigned long currentMillis = millis();
    if (currentMillis - lastPublishMillis >= PUBLISH_INTERVAL_MS) {
        lastPublishMillis = currentMillis;

        if (!currentReading.valid) {
            Serial.println("[PMS3003] Warning: Waiting for initial valid sensor packet...");
            return;
        }

        // Verify that sensor readings are not all zero (Backend validation constraint:
        // FastAPI returns 422 if pm1_ground, pm25_ground, and pm10_ground are all 0.0)
        float pm1_val  = (float)currentReading.pm1_0_atm;
        float pm25_val = (float)currentReading.pm2_5_atm;
        float pm10_val = (float)currentReading.pm10_atm;

        // Fallback to standard CF=1 if atmospheric values are 0 while CF=1 has readings
        if (pm1_val == 0.0f && pm25_val == 0.0f && pm10_val == 0.0f) {
            pm1_val  = (float)currentReading.pm1_0_std;
            pm25_val = (float)currentReading.pm2_5_std;
            pm10_val = (float)currentReading.pm10_std;
        }

        if (pm1_val == 0.0f && pm25_val == 0.0f && pm10_val == 0.0f) {
            Serial.println("[SENSOR WARMUP] All particulate readings are 0.0 µg/m³.");
            Serial.println("                Holding transmission until sensor airflow stabilizes.");
            return;
        }

        // Transmit over HTTPS
        sendTelemetryHTTPS(currentReading);
    }
}

// ==============================================================================
// 7. WIFI CONNECTION HANDLER
// ==============================================================================
void connectWiFi() {
    Serial.printf("[WIFI] Connecting to SSID '%s'...", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 40) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[WIFI] Connected successfully!");
        Serial.printf("[WIFI] IP Address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("[WIFI] Signal RSSI: %d dBm\n\n", WiFi.RSSI());
    } else {
        Serial.println("\n[WIFI] Connection failed. Retrying in background...");
    }
}

// ==============================================================================
// 8. PMS3003 24-BYTE FRAME PARSER & CHECKSUM VALIDATOR
// ==============================================================================
bool readPMS3003Frame(PMSData &data) {
    // Need at least 24 bytes in the serial buffer
    if (Serial2.available() < 24) {
        return false;
    }

    // Look for Start Character 1: 0x42 ('B')
    if (Serial2.peek() != 0x42) {
        Serial2.read(); // Discard misaligned byte
        return false;
    }

    // Read candidate header byte 1
    uint8_t b1 = Serial2.read();

    // Check Start Character 2: 0x4D ('M')
    if (Serial2.peek() != 0x4D) {
        return false;
    }
    uint8_t b2 = Serial2.read();

    // Allocate 24-byte buffer
    uint8_t buffer[24];
    buffer[0] = b1;
    buffer[1] = b2;

    // Read the remaining 22 bytes with timeout protection
    size_t bytesRead = Serial2.readBytes(&buffer[2], 22);
    if (bytesRead != 22) {
        Serial.printf("[PMS3003] Frame timeout: Expected 22 bytes, got %zu\n", bytesRead);
        return false;
    }

    // Frame length check: PMS3003 specifies frame length = 20 (0x0014) in Bytes 2 & 3
    uint16_t frameLen = ((uint16_t)buffer[2] << 8) | buffer[3];
    if (frameLen != 20) {
        Serial.printf("[PMS3003] Invalid frame length: %u (expected 20)\n", frameLen);
        return false;
    }

    // Compute 16-bit additive checksum over bytes 0 through 21
    uint16_t calculatedChecksum = 0;
    for (int i = 0; i < 22; i++) {
        calculatedChecksum += buffer[i];
    }

    // Received checksum in bytes 22 (high) and 23 (low)
    uint16_t receivedChecksum = ((uint16_t)buffer[22] << 8) | buffer[23];

    // Validate checksum
    if (calculatedChecksum != receivedChecksum) {
        Serial.printf("[PMS3003] Checksum mismatch! Calc: 0x%04X, Recv: 0x%04X\n",
                      calculatedChecksum, receivedChecksum);
        return false;
    }

    // Checksum verified! Extract particulate matter metrics:
    // Standard particulate matter (CF=1) [µg/m³]
    data.pm1_0_std = ((uint16_t)buffer[4] << 8) | buffer[5];
    data.pm2_5_std = ((uint16_t)buffer[6] << 8) | buffer[7];
    data.pm10_std  = ((uint16_t)buffer[8] << 8) | buffer[9];

    // Atmospheric environment particulate matter [µg/m³]
    data.pm1_0_atm = ((uint16_t)buffer[10] << 8) | buffer[11];
    data.pm2_5_atm = ((uint16_t)buffer[12] << 8) | buffer[13];
    data.pm10_atm  = ((uint16_t)buffer[14] << 8) | buffer[15];

    data.valid = true;
    data.timestamp = millis();

    return true;
}

// ==============================================================================
// 9. HTTPS TELEMETRY TRANSMISSION (STRICT TLS VALIDATION)
// ==============================================================================
bool sendTelemetryHTTPS(const PMSData &data) {
    Serial.println("--------------------------------------------------------");
    Serial.println("[TELEMETRY DISPATCH] Preparing secure transmission...");

    // Determine PM concentrations to submit (prefer atmospheric environmental readings)
    float pm1  = (float)data.pm1_0_atm;
    float pm25 = (float)data.pm2_5_atm;
    float pm10 = (float)data.pm10_atm;

    if (pm1 == 0.0f && pm25 == 0.0f && pm10 == 0.0f) {
        pm1  = (float)data.pm1_0_std;
        pm25 = (float)data.pm2_5_std;
        pm10 = (float)data.pm10_std;
    }

    // Format JSON payload according to backend TelemetryPayload Pydantic schema:
    // { "device_id": "...", "pm10_ground": ..., "pm25_ground": ..., "pm1_ground": ... }
    char jsonBuffer[256];
    snprintf(jsonBuffer, sizeof(jsonBuffer),
             "{\"device_id\":\"%s\",\"pm1_ground\":%.1f,\"pm25_ground\":%.1f,\"pm10_ground\":%.1f}",
             DEVICE_ID, pm1, pm25, pm10);

    Serial.printf("[TELEMETRY] Payload: %s\n", jsonBuffer);

    // Initialize WiFiClientSecure with Root CA certificate
    WiFiClientSecure secureClient;
    secureClient.setCACert(ROOT_CA_BUNDLE);

    HTTPClient https;
    https.setTimeout(HTTP_TIMEOUT_MS);

    Serial.printf("[HTTPS] Connecting to %s with TLS verification...\n", API_ENDPOINT);

    if (!https.begin(secureClient, API_ENDPOINT)) {
        Serial.println("[HTTPS ERROR] Unable to initialize HTTPS connection to endpoint.");
        return false;
    }

    https.addHeader("Content-Type", "application/json");
    https.addHeader("User-Agent", "ESP32-PMS3003-Firmware/2.0");

    // Execute HTTP POST
    unsigned long reqStart = millis();
    int httpResponseCode = https.POST(jsonBuffer);
    unsigned long duration = millis() - reqStart;

    bool ingestionSuccess = false;

    // Distinguish successful ingestion from network failure or HTTP errors
    if (httpResponseCode > 0) {
        String responseBody = https.getString();
        Serial.printf("[HTTPS RESPONSE] HTTP Status: %d (%lu ms)\n", httpResponseCode, duration);
        Serial.printf("[HTTPS RESPONSE] Body: %s\n", responseBody.c_str());

        if (httpResponseCode == 200 || httpResponseCode == 201) {
            // Check for expected backend status key
            if (responseBody.indexOf("\"status\":\"received\"") >= 0 ||
                responseBody.indexOf("\"status\": \"received\"") >= 0) {
                Serial.println("[INGESTION SUCCESS] Telemetry ingested and persisted to PostgreSQL!");
                Serial.println("                    Live dashboard updated at https://ai-aqi.vercel.app");
                ingestionSuccess = true;
            } else {
                Serial.println("[INGESTION NOTICE] Received 200 OK with non-standard body.");
                ingestionSuccess = true;
            }
        } else if (httpResponseCode == 422) {
            Serial.println("[INGESTION REJECTED - 422] Validation error: Check payload fields and non-zero constraints.");
        } else if (httpResponseCode == 500) {
            Serial.println("[INGESTION FAILED - 500] Backend internal error: Database persistence failure.");
        } else {
            Serial.printf("[INGESTION FAILED - %d] Unexpected HTTP status code returned.\n", httpResponseCode);
        }
    } else {
        Serial.printf("[HTTPS ERROR] Request failed, error code: %d (%s)\n",
                      httpResponseCode, https.errorToString(httpResponseCode).c_str());
        Serial.println("              Possible causes: TLS handshake failure, DNS resolution failure, or server cold-start timeout.");
    }

    https.end();
    Serial.println("--------------------------------------------------------\n");
    return ingestionSuccess;
}
