#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <Servo.h>


#define SS_PIN 10
#define RST_PIN 9

#define YELLOW_LED 2
#define GREEN_LED 3
#define RED_LED 4
#define BLUE_LEN 5
#define BUZZER_PIN 6
#define SERVO_PIN 7

#define SERVO_CLOSE_DEG 130
#define SERVO_OPEN_DEG 15


MFRC522 rfid(SS_PIN, RST_PIN);  // Instance of the class
MFRC522::MIFARE_Key key;

Servo servo;


unsigned long rfidRebootTimer = 0;
static String now_uid = "";
uint8_t control = 0x00;
int tone_index;


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


void setup() {
  Serial.begin(115200);
  Wire.begin(0x0B);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);

  SPI.begin();      // Init SPI bus
  rfid.PCD_Init();  // Init MFRC522

  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF;
  }

  pinMode(YELLOW_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  servo.attach(SERVO_PIN);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);

  servo.write(SERVO_CLOSE_DEG);
  noTone(BUZZER_PIN);

  Serial.println("Started!");
}


void requestEvent() {
  Wire.write(now_uid.c_str());
  // if (now_uid != "") {
  //   Serial.println("Uid geted! " + now_uid);
  // }
}


void receiveEvent(int response_number) {
  response_number = Wire.read();
  Serial.println("Get " + String(response_number));

  switch (response_number) {
    case 1:
      digitalWrite(YELLOW_LED, 1);
      break;
    case 2:
      digitalWrite(YELLOW_LED, 0);
      break;
    case 3:
      digitalWrite(GREEN_LED, 1);
      break;
    case 4:
      digitalWrite(GREEN_LED, 0);
      break;
    case 5:
      digitalWrite(RED_LED, 1);
      break;
    case 6:
      digitalWrite(RED_LED, 0);
      break;
    case 12:
      digitalWrite(BLUE_LEN, 1);
      break;
    case 13:
      digitalWrite(BLUE_LEN, 0);
      break;
    case 7:
      servo.write(SERVO_OPEN_DEG);
      break;
    case 8:
      servo.write(SERVO_CLOSE_DEG);
      break;
      case 9:
        tone_index = 9;
        break;
      case 10:
        tone_index = 10;
        break;
      case 11:
        tone_index = 11;
        break;
  }
}


void check_tone() {
  switch (tone_index) {
    case 9:
      tone(BUZZER_PIN, 890, 330);
      break;
    case 10:
      tone(BUZZER_PIN, 100, 300);
      break;
    case 11:
      tone(BUZZER_PIN, 890, 180);
      break;
  }
  tone_index = 0;
}


void _delay(int del) {
  unsigned long start_time = millis();
  while (millis() - start_time <= del) {
    check_tone();
  }
}


void loop() {
  if (millis() - rfidRebootTimer > 3000) {
    rfidRebootTimer = millis();
    digitalWrite(RST_PIN, HIGH);
    _delay(1);
    digitalWrite(RST_PIN, LOW);
    rfid.PCD_Init();
    Serial.println(F("Rebooted!"));
  }

  check_tone();

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
    tone(BUZZER_PIN, 890, 180);
    digitalWrite(RED_LED, HIGH);
    _delay(300);
    tone(BUZZER_PIN, 890, 180);
    _delay(500);
    digitalWrite(RED_LED, LOW);
    return;
  }

  String card_uid = get_uid();
  Serial.println("Card UID=" + card_uid);

  now_uid = "UID=" + card_uid;

  digitalWrite(13, HIGH);
  digitalWrite(YELLOW_LED, HIGH);
  while (true) {
    _delay(400);
    // Serial.println(F("Is card attach=1"));
    if (isnt_card_present()) {
      break;
    }
  }
  // Serial.println("Is card attach=0");
  digitalWrite(13, LOW);

  now_uid = "";
  analogWrite(YELLOW_LED, LOW);

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
