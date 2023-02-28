#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN      10
#define RST_PIN     9
#define YELLOW_LED  3
#define RED_LED     4
#define BUZZER_PIN  5


MFRC522 rfid(SS_PIN, RST_PIN); // Instance of the class
MFRC522::MIFARE_Key key;

static uint32_t rfidRebootTimer = 0;
uint8_t control = 0x00;


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
  if (not (control == 13 || control == 14)) {
    return true;
  }
  return false;
}


void setup() {
  Serial.begin(9600);
  SPI.begin(); // Init SPI bus
  rfid.PCD_Init(); // Init MFRC522

  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF;
  }

  pinMode(RED_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  noTone(BUZZER_PIN);

  analogWrite(RED_LED, 255);
  analogWrite(YELLOW_LED, 255);
  delay(1000);
  analogWrite(YELLOW_LED, LOW);
  Serial.println(F("Waiting for card..."));
}


void loop() {
  if (millis() - rfidRebootTimer > 3000) {
    rfidRebootTimer = millis();
    digitalWrite(RST_PIN, HIGH);
    delay(1);
    digitalWrite(RST_PIN, LOW);
    rfid.PCD_Init();
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

  digitalWrite(YELLOW_LED, HIGH);

  tone(BUZZER_PIN, 890, 180);
//  delay(430);
//  tone(BUZZER_PIN, 890, 330);

  String card_uid = get_uid();
  Serial.println("Card UID=" + card_uid);

  while (true) {
    delay(50);
    Serial.println("Is card attach=1");
    if (isnt_card_present()) {
      break;
    }
  }
  Serial.println("Is card attach=0");

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
