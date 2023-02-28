#include <ESP8266WiFi.h>                                      // Библиотека для создания Wi-Fi подключения (клиент или точка доступа)
#include <ESP8266HTTPClient.h>


#define BTN_PIN    A0
#define YELLOW_LED D8
#define GREEN_LED  D3
#define RED_LED    D2


String ssid = "";
String password = "";
String host = "";
bool last_btn_state = false;
bool fire_alarm_state = false;
unsigned long ping_start_time = 0;

String scan_ssid;
int32_t rssi;
uint8_t encryptionType;
uint8_t* bssid;
int32_t channel;
bool hidden;
int scanResult;


const bool use_ping = true;
const int ping_cooldown = 1500;

const int connection_attempts = 30;
const String wifiNetworks[][3] = {
  {"Keenetic_1330", "xE53nD7m", "10.10.10.58:5002"},
  {"HUAWEI-B535-6D9A", "x19KNa5C", "192.168.8.100:5002"},
  {"Galaxy_A51", "tixe5757", "192.168.149.182:5002"}
};

const char* protocol = "http://";
const char* main_domain = "robotics-acs-project.tk:5002";
const bool use_main_domain = true;


int send_request(String route, bool is_ping = false) {
  WiFiClient client;
  HTTPClient http;

  if (not is_ping) {
    digitalWrite(YELLOW_LED, HIGH);
  }

  if (WiFi.status() != WL_CONNECTED and (not is_ping)) {
    Serial.println("Connecting to wifi network...");
    //    WiFi.disconnect();
    WiFi.reconnect();
    WiFi.waitForConnectResult();
  }

  if (not use_main_domain) {
    http.begin(client, String(protocol) + String(host) + String(route));
  } else {
    http.begin(client, String(protocol) + String(main_domain) + String(route));
  }

  http.addHeader("Content-Type", "text/plain");

  int status_code = http.POST("Message from ESP8266");
  String payload = http.getString();

  Serial.println("Status code: " + String(status_code));
  Serial.println("Response: " + payload);

  http.end();

  digitalWrite(YELLOW_LED, LOW);

  if (status_code == 200) {
    return 1;
  }
  return 0;
}


int send_fire_alarm_request(bool state) {
  return send_request("/api/set_fire_alarm_state/" + String(int(state)) + "/");
}


unsigned long ping_server() {
  unsigned long start_time = millis();
  int int_response = send_request("/api/ping/", true);
  if (int_response == 1) {
    return millis() - start_time;
  }
  return -1;
}


void ping_server_cooldown() {
  if (use_ping && ping_start_time + ping_cooldown < millis()) {
    int ret = ping_server();
    Serial.println("Ping: " + String(ret));
    ping_start_time = millis();
  }
}


void setup() {
  Serial.begin(115200);

  pinMode(BTN_PIN, INPUT_PULLUP);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);

  digitalWrite(YELLOW_LED, HIGH);
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, HIGH);

  Serial.println("Scaning wifi networks...");

  scanResult = WiFi.scanNetworks(/*async=*/false, /*hidden=*/true);
  if (scanResult > 0) {
    for (int j = 0; j < (sizeof(wifiNetworks) / sizeof(String) / 3); j++) {
      for (int8_t i = 0; i < scanResult; i++) {
        WiFi.getNetworkInfo(i, scan_ssid, encryptionType, rssi, bssid, channel, hidden);
        if (wifiNetworks[j][0] == scan_ssid.c_str()) {
          ssid = wifiNetworks[j][0];
          password = wifiNetworks[j][1];
          host = wifiNetworks[j][2];
          break;
        }
      }
    }

    Serial.println("Connecting to wifi network...");
    WiFi.begin(ssid, password);

    if (WiFi.waitForConnectResult() != WL_CONNECTED) {
      digitalWrite(YELLOW_LED, LOW);
      digitalWrite(GREEN_LED, LOW);
      delay(2000);
      digitalWrite(RED_LED, LOW);
    } else {
      digitalWrite(YELLOW_LED, LOW);
      digitalWrite(GREEN_LED, LOW);
      digitalWrite(RED_LED, LOW);
    }
    Serial.println();

    Serial.println("Connected!");
    Serial.println("Network ssid: " + ssid);
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("MAC address: ");
    Serial.println(WiFi.macAddress());

    send_fire_alarm_request(false);
  } else {
    if (scanResult == 0) {
      Serial.println("No wifi networks!");
    } else {
      Serial.printf(PSTR("WiFi scan error %d"), scanResult);
    }
    digitalWrite(YELLOW_LED, HIGH);
    digitalWrite(RED_LED, HIGH);
    delay(2000);
  }
}


void loop() {
  ping_server_cooldown();

  int btn_val = analogRead(BTN_PIN);

  if (btn_val == 1024 and (not last_btn_state)) {
    Serial.println("Pressed!");
    last_btn_state = true;

    int int_response = send_fire_alarm_request(not fire_alarm_state);
    if (int_response == 1) {
      fire_alarm_state = not fire_alarm_state;
      digitalWrite(GREEN_LED, HIGH);
      delay(1000);
    } else {
      digitalWrite(RED_LED, HIGH);
      delay(1000);
    }
  }
  if ((btn_val == 0 or btn_val == 1 or btn_val == 2 or btn_val == 3) and last_btn_state) {
    last_btn_state = false;
    digitalWrite(RED_LED, LOW);
    digitalWrite(GREEN_LED, LOW);
  }
}
