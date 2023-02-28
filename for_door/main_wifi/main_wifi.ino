#include <ESP8266WiFi.h>  // Библиотека для создания Wi-Fi подключения (клиент или точка доступа)
#include <ESP8266HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>


#define SS_PIN D10
#define RST_PIN D9
#define DOOR_SENSOR D2


MFRC522 rfid(SS_PIN, RST_PIN);  // Instance of the class
MFRC522::MIFARE_Key key;


String ssid = "";
String password = "";
String host = "";
unsigned long rfidRebootTimer = millis();
String new_uid = "";
String last_uid = "";
int int_response = 0;
unsigned long blue_led_start_time = 0;
unsigned long fire_alarm_checker_start_time = 0;
bool is_fire_alarm = false;
bool blue_led_state = false;
uint8_t control = 0x00;

String scan_ssid;
int32_t rssi;
uint8_t encryptionType;
uint8_t* bssid;
int32_t channel;
bool hidden;
int scanResult;


const String alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789= ";
const int blue_led_coldown = 250;
const int fire_alarm_checker_cooldown = 5000;
const int open_door_delay = 3000;

const int connection_attempts = 5;
const String wifiNetworks[][3] = {
  { "Keenetic_1330", "xE53nD7m", "10.10.10.58:5002" },
  { "HUAWEI-B535-6D9A", "x19KNa5C", "192.168.8.100:5002" },
  { "Galaxy_A51", "tixe5757", "192.168.149.182:5002" }
};

const char* protocol = "http://";
const char* main_domain = "robotics-acs-project.tk:5002";
const bool use_main_domain = true;


void send_data(int number) {
  Serial.println("Sending " + String(number) + "...");
  if (number == 8) {
    if ((not is_door_closed()) and (not blue_led_state)) {
      send_data(12);
      blue_led_state = true;
    }
    while (not is_door_closed()) {
      Serial.println("Door isn't closed!");
      delay(100);
    }
    if (blue_led_state) {
      send_data(13);
      blue_led_state = false;
      delay(500);
    }
  }
  Wire.beginTransmission(0x0B);
  Wire.write(number);
  Wire.endTransmission();
  Wire.beginTransmission(0x0B);
  Wire.write(number);
  Wire.endTransmission();
  Serial.println("Send " + String(number));
}


String get_card_uid_from_uno() {
  String card_uid = "";
  Wire.requestFrom(0x0B, 30);
  delay(20);
  while (Wire.available()) {
    char c = Wire.read();
    card_uid += c;
  }
  String new_uid_f = "";
  for (int i = 0; i < card_uid.length(); i++) {
    for (int j = 0; j < alphabet.length(); j++) {
      if (String(card_uid[i]).indexOf(alphabet[j]) != -1) {
        new_uid_f += card_uid[i];
        break;
      }
    }
  }
  new_uid_f = new_uid_f.substring(4);
  return new_uid_f;
}


bool check_card_uid() {
  new_uid = get_card_uid_from_uno();
  return new_uid != "";
}


bool isnt_card_present() {
  control = 0;
  for (int i = 0; i < 3; i++) {
    if (!rfid.PICC_IsNewCardPresent()) {
      if (rfid.PICC_ReadCardSerial()) {
        //Serial.print('a');
        control |= 0x16;
      }
      if (rfid.PICC_ReadCardSerial()) {
        //Serial.print('b');
        control |= 0x16;
      }
      //Serial.print('c');
      control += 0x1;
    }
    //Serial.print('d');
    control += 0x4;
  }

  //Serial.println(control);
  if (not(control == 13 || control == 14)) {
    return true;
  }
  return false;
}


bool blink_red_led_twice_uno(bool use_condition, bool condition) {
  if ((not use_condition) or condition) {
    for (int i = 0; i < 2; i++) {
      send_data(5);
      if (not check_card_uid()) {
        return true;
      }
      delay(100);
      send_data(6);
      if (not check_card_uid()) {
        return true;
      }
      delay(400);
    }
  }
  if (not check_card_uid()) {
    return true;
  }
  delay(250);
  return false;
}


bool blink_red_led_twice_wifi(bool use_condition, bool condition) {
  if ((not use_condition) or condition) {
    for (int i = 0; i < 2; i++) {
      send_data(5);
      if (isnt_card_present()) {
        return true;
      }
      delay(100);
      send_data(6);
      if (isnt_card_present()) {
        return true;
      }
      delay(400);
    }
  }
  if (isnt_card_present()) {
    return true;
  }
  delay(250);
  return false;
}


bool blink_red_led_twice(String board_type, bool use_condition, bool condition) {
  bool ret = false;
  if (board_type == "wifi") {
    ret = blink_red_led_twice_wifi(use_condition, condition);
  } else if (board_type == "uno") {
    ret = blink_red_led_twice_uno(use_condition, condition);
  }
  if ((not use_condition) or condition) {
    send_data(6);
  }
  return ret;
}


bool is_door_closed() {
  int value = (digitalRead(DOOR_SENSOR) == LOW);
  return value;
}


void blue_led_coolldown_function() {
  if (blue_led_start_time + blue_led_coldown < millis()) {
    if (is_door_closed()) {
      if (blue_led_state) {
        send_data(13);
        blue_led_state = false;
      }
    } else {
      if (not blue_led_state) {
        send_data(12);
        blue_led_state = true;
      }
    }
    blue_led_start_time = millis();
  }
}


void fire_alarm_checker_cooldown_function() {
  if (fire_alarm_checker_start_time + fire_alarm_checker_cooldown < millis()) {
    if (WiFi.status() == WL_CONNECTED) {
      int_response = send_request("/api/get_fire_alarm_state/");
      if (int_response == 1) {
        is_fire_alarm = true;
        send_data(7);
      } else if (int_response == 0) {
        is_fire_alarm = false;
        send_data(8);
      }
      fire_alarm_checker_start_time = millis();
    }
  }
}


void setup() {
  Serial.begin(115200);
  Serial.println();

  Wire.begin();

  pinMode(DOOR_SENSOR, INPUT);
  pinMode(D8, OUTPUT);
  digitalWrite(D8, HIGH);

  Serial.println("Waiting 2 seconds...");

  delay(2000);

  send_data(1);
  send_data(3);
  send_data(5);

  Serial.println("Scaning wifi networks...");

  scanResult = WiFi.scanNetworks(/*async=*/false, /*hidden=*/false);
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

    delay(2000);

    unsigned long start_time = millis();
    while (WiFi.waitForConnectResult() != WL_CONNECTED && millis() - start_time < 10000) {}

    if (WiFi.waitForConnectResult() == WL_CONNECTED) {
      Serial.println("Connected!");
      Serial.println("Network ssid: " + ssid);
      Serial.print("IP address: ");
      Serial.println(WiFi.localIP());
      Serial.print("MAC address: ");
      Serial.println(WiFi.macAddress());
    } else {
      Serial.println("No connection to wifi network!");
      send_data(2);
      send_data(4);
      delay(2000);
    }
  } else if (scanResult == 0) {
    send_data(2);
    send_data(4);
    Serial.println("No wifi networks!");
    delay(2000);
  } else {
    Serial.printf(PSTR("WiFi scan error %d"), scanResult);
  }

  SPI.begin();      // инициализация SPI
  rfid.PCD_Init();  // инициализация rfid
  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF;
  }

  send_data(2);
  send_data(4);
  send_data(6);

  Serial.println(F("Waiting for card..."));
}


void rebootRFID() {
  if (millis() - rfidRebootTimer > 3000) {
    rfidRebootTimer = millis();
    digitalWrite(RST_PIN, HIGH);
    delay(1);
    digitalWrite(RST_PIN, LOW);
    rfid.PCD_Init();
    Serial.println(F("Rebooted!"));
  }
}


void loop() {
  rebootRFID();

  blue_led_coolldown_function();
  if (new_uid == "") {
    fire_alarm_checker_cooldown_function();
  }

  if (is_fire_alarm) {
    send_data(5);
    send_data(11);
    delay(300);
    send_data(6);
    delay(300);

    return;
  }

  new_uid = get_card_uid_from_uno();

  if (last_uid != new_uid and new_uid != "") {
    if (WiFi.status() == WL_CONNECTED) {
      send_data(1);
      int_response = send_request("/api/exit_uid/" + new_uid + "/");
      if (int_response == 1) {
        send_data(3);
        send_data(9);
        send_data(7);
      } else if (int_response == 0) {
        send_data(5);
        send_data(10);
      } else {
        send_data(10);
        blink_red_led_twice("uno", false, false);
      }
    } else {
      send_data(10);
      while (true) {
        if (blink_red_led_twice("uno", false, false)) {
          break;
        }
      }
      send_data(7);
      unsigned long start_time = millis();
      while (start_time + open_door_delay > millis()) {
        blue_led_coolldown_function();
        rebootRFID();
        delay(100);
      }
      send_data(8);
    }
    last_uid = new_uid;
  }
  if (new_uid != "") {
    last_uid = new_uid;
    Serial.println("UID=" + new_uid);
    if (int_response < 0 or WiFi.status() != WL_CONNECTED) {
      blink_red_led_twice("uno", false, false);
    }
    return;
  } else if (last_uid != new_uid) {
    Serial.println("Card attached!");
    send_data(4);
    send_data(6);
    if (int_response == 1) send_data(7);

    unsigned long start_time = millis();
    while (start_time + open_door_delay > millis()) {
      blue_led_coolldown_function();
      rebootRFID();
      delay(100);
    }
    send_data(8);
    last_uid = new_uid;
    new_uid = "";
  }

  // Reset the loop if no new card present on the sensor/reader. This saves the entire process when idle.
  if (!rfid.PICC_IsNewCardPresent()) {
    return;
  }

  // Verify if the NUID has been readed
  if (!rfid.PICC_ReadCardSerial()) {
    return;
  }

  MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);

  if (piccType != MFRC522::PICC_TYPE_MIFARE_MINI && piccType != MFRC522::PICC_TYPE_MIFARE_1K && piccType != MFRC522::PICC_TYPE_MIFARE_4K) {
    Serial.println(F("Your tag is not of type MIFARE Classic."));
    send_data(11);
    send_data(5);
    delay(300);
    send_data(11);
    delay(500);
    send_data(6);
    return;
  }

  if (WiFi.status() == WL_CONNECTED) {
    send_data(1);

    String card_uid = get_uid();
    Serial.println("Card UID=" + card_uid);

    int int_response = send_request("/api/entry_uid/" + card_uid + "/");
    if (int_response == 1) {
      send_data(3);
      send_data(7);
      send_data(9);
    } else if (int_response == 0) {
      send_data(5);
      send_data(10);
    }

    delay(250);
    if (int_response < 0) {
      send_data(10);
    }
    while (true) {
      blue_led_coolldown_function();
      if (blink_red_led_twice("wifi", true, (int_response < 0))) {
        break;
      }
    }

    Serial.println("Is card attach=0");
    for (int i = 0; i < 2; i++) {
      send_data(2);
      send_data(4);
      send_data(6);
    }

    if (int_response == 1 || int_response < 0) {
      send_data(7);
      Serial.println("Waiting 4 seconds...");
      unsigned long start_time = millis();
      while (start_time + open_door_delay > millis()) {
        blue_led_coolldown_function();
        rebootRFID();
        delay(100);
      }
      send_data(8);
    }
  } else {
    send_data(10);

    delay(250);
    while (true) {
      blue_led_coolldown_function();
      rebootRFID();
      if (blink_red_led_twice("wifi", false, false)) {
        break;
      }
    }
    send_data(6);
    send_data(7);
    unsigned int start_time = millis();
    while (start_time + open_door_delay > millis()) {
      blue_led_coolldown_function();
      rebootRFID();
      delay(100);
    }
    send_data(8);
  }

  // Halt PICC
  rfid.PICC_HaltA();
  // Stop encryption on PCD
  rfid.PCD_StopCrypto1();
}


String get_uid() {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    uid.concat(String(rfid.uid.uidByte[i] < 0x10 ? " 0" : " "));
    uid.concat(String(rfid.uid.uidByte[i], HEX));
  }
  uid.toUpperCase();
  uid = uid.substring(1);
  return uid;
}


int send_request(String route) {
  WiFiClient client;
  HTTPClient http;

  route.replace(" ", "%20");

  if (not use_main_domain) {
    http.begin(client, String(protocol) + String(host) + String(route));
  } else {
    http.begin(client, String(protocol) + String(main_domain) + String(route));
  }

  http.addHeader("Content-Type", "text/plain");

  int status_code = http.POST("");
  String payload = http.getString();

  Serial.println("Status code: " + String(status_code));
  Serial.println("Response: " + payload);

  http.end();

  if (status_code == 200) {
    return payload == "1";
  } else if (status_code < 0) {
    return status_code;
  }
  return 0;
}
