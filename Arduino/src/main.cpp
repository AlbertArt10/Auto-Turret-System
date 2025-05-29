#include <Arduino.h>
#include <Servo.h>

// 🧱 Funcții bare-metal pentru I/O direct pe registre

// Configurează sensul pinului și pull-up fără API Arduino
void pinModeBare(uint8_t pin, uint8_t mode) {
    if (pin <= 7) { // Pinii D0–D7 → PORTD
        if (mode == OUTPUT)        DDRD |=  (1 << pin);   // setare ca OUTPUT
        else {
            DDRD &= ~(1 << pin);                        // setare ca INPUT
            if (mode == INPUT_PULLUP) PORTD |=  (1 << pin); // activează pull-up
            else                      PORTD &= ~(1 << pin); // dezactivează pull-up
        }
    }
    else if (pin <= 13) { // Pinii D8–D13 → PORTB
        uint8_t p = pin - 8;
        if (mode == OUTPUT)        DDRB |=  (1 << p);
        else {
            DDRB &= ~(1 << p);
            if (mode == INPUT_PULLUP) PORTB |=  (1 << p);
            else                      PORTB &= ~(1 << p);
        }
    }
}

// Scrie HIGH/LOW direct în registrul PORT
void digitalWriteBare(uint8_t pin, bool value) {
    if (pin <= 7) {
        if (value) PORTD |=  (1 << pin);
        else       PORTD &= ~(1 << pin);
    }
    else if (pin <= 13) {
        uint8_t p = pin - 8;
        if (value) PORTB |=  (1 << p);
        else       PORTB &= ~(1 << p);
    }
}

// Citește starea unui pin digital din registrul PIN
bool digitalReadBare(uint8_t pin) {
    if (pin <= 7)       return (PIND &  (1 << pin)) != 0;
    else if (pin <= 13) return (PINB &  (1 << (pin - 8))) != 0;
    return false;
}

// Efectuează o conversie ADC pe canalul 0–7 (A0–A7)
int analogReadBare(uint8_t channel) {
    ADMUX  = (1 << REFS0) | (channel & 0x07);                 // AVcc ca referință, selectează canal
    ADCSRA = (1 << ADEN) | (1 << ADSC)                        // activează ADC și pornește conversia
           | (1 << ADPS2) | (1 << ADPS1);                     // prescaler 64
    while (ADCSRA & (1 << ADSC));                             // așteaptă final conversie
    return ADC;                                               // returnează valoarea
}

// 🔧 Obiecte Servo pentru controlul servomotoarelor
Servo servoPan;   // Servomotor pentru pan (D9)
Servo servoTilt;  // Servomotor pentru tilt (D10)
Servo servoFire;  // Servomotor pentru trăgaci (D11)

// Definire pini
const int laserPin  = 8;    // D8 – laser ON/OFF
const int ledR      = 2;    // D2 – LED roșu
const int ledG      = 3;    // D3 – LED verde
const int ledB      = 4;    // D4 – LED albastru
const int joyY      = A5;   // A5 – axa Y joystick
const int joyX      = A4;   // A4 – axa X joystick
const int joySW     = 13;   // D13 – buton joystick
const int buzzerPin = 12;   // D12 – buzzer

// Butoane moduri (cu pull-up intern)
const int BTN_FREE = 5;  // D5 – mod FREE
const int BTN_SCAN = 6;  // D6 – mod SCAN
const int BTN_MAN  = 7;  // D7 – mod MANUAL

// Variabile de stare
int panAngle      = 90;       // Unghi inițial pan
int tiltAngle     = 90;       // Unghi inițial tilt
String currentMode = "OFF";   // Mod curent
unsigned long lastBeep = 0;   // Timpul ultimei bipări
int pan_us        = 1500;     // Puls servo pan
int tilt_us       = 1500;     // Puls servo tilt

// Setează culoarea RGB cu scriere bare-metal
void setRGB(bool r, bool g, bool b) {
    digitalWriteBare(ledR, r);
    digitalWriteBare(ledG, g);
    digitalWriteBare(ledB, b);
}

// Generează un beep folosind tone() (poate fi înlocuit cu PWM bare-metal)
void beep(int freq, int duration) {
    tone(buzzerPin, freq);
    delay(duration);
    noTone(buzzerPin);
}

void setup() {
    Serial.begin(9600); // Pornire comunicație serială

    // Atașare servomotoare (folosește PWM Arduino)
    servoPan.attach(9);
    servoTilt.attach(10);
    servoFire.attach(11);

    // Configurare I/O bare-metal
    pinModeBare(buzzerPin, OUTPUT);
    pinModeBare(laserPin, OUTPUT);
    digitalWriteBare(laserPin, HIGH); // Laser pornit

    pinModeBare(ledR, OUTPUT);
    pinModeBare(ledG, OUTPUT);
    pinModeBare(ledB, OUTPUT);

    pinModeBare(BTN_FREE, INPUT_PULLUP);
    pinModeBare(BTN_SCAN, INPUT_PULLUP);
    pinModeBare(BTN_MAN,  INPUT_PULLUP);
    pinModeBare(joySW,    INPUT_PULLUP);

    // Inițializare servomotoare centru
    servoPan.write(panAngle);
    servoTilt.write(tiltAngle);
    servoFire.write(90);

    setRGB(false, false, false); // LED-uri stinse
}

void loop() {
    // Citește butoane mod cu bare-metal digitalRead
    if (!digitalReadBare(BTN_FREE)) { Serial.println("F"); delay(300); }
    if (!digitalReadBare(BTN_SCAN)) { Serial.println("S"); delay(300); }
    if (!digitalReadBare(BTN_MAN))  { Serial.println("M"); delay(300); }

    // Procesează comenzi seriale
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        if (cmd.startsWith("PANU=")) {
            int pulse = constrain(cmd.substring(5).toInt(), 500, 2500);
            servoPan.writeMicroseconds(pulse);
        }
        else if (cmd.startsWith("TILTU=")) {
            int pulse = constrain(cmd.substring(6).toInt(), 500, 2500);
            servoTilt.writeMicroseconds(pulse);
        }
        else if (cmd.startsWith("PAN=")) {
            panAngle = constrain(cmd.substring(4).toInt(), 0, 180);
            servoPan.write(panAngle);
        }
        else if (cmd.startsWith("TILT=")) {
            tiltAngle = constrain(cmd.substring(5).toInt(), 0, 180);
            servoTilt.write(tiltAngle);
        }
        else if (cmd == "FIRE=1") {
            servoFire.write(180); delay(500);
            servoFire.write(0);   delay(500);
            servoFire.write(90);
        }
        else if (cmd.startsWith("MODE=")) {
            currentMode = cmd.substring(5);
            if (currentMode == "SCAN")       setRGB(false, true, false);
            else if (currentMode == "LOCK")  setRGB(true, true, false);
            else if (currentMode == "MANUAL") setRGB(false, false, true);
            else if (currentMode == "FIRE_WARN") {
                setRGB(true, false, false);
                tone(buzzerPin, 3500); delay(1500); noTone(buzzerPin);
            }
            else if (currentMode == "OFF")   setRGB(false, false, false);
        }
    }

    // Mod FREE: centrează servomotoarele
    if (currentMode == "FREE") {
        setRGB(true, true, true);  // alb
        pan_us  = servoPan.readMicroseconds();
        tilt_us = servoTilt.readMicroseconds();
        while (pan_us != 1500 || tilt_us != 1500) {
            if (pan_us  < 1500) pan_us++;
            else if (pan_us  > 1500) pan_us--;
            if (tilt_us < 1500) tilt_us++;
            else if (tilt_us > 1500) tilt_us--;
            servoPan.writeMicroseconds(pan_us);
            servoTilt.writeMicroseconds(tilt_us);
            delay(2);
        }
    }

    // Mod SCAN: bip periodic
    if (currentMode == "SCAN" && millis() - lastBeep > 750) {
        beep(1000, 100);
        delay(100);
        lastBeep = millis();
    }

    // Mod LOCK: bip mai rapid
    if (currentMode == "LOCK" && millis() - lastBeep > 250) {
        beep(1500, 100);
        lastBeep = millis();
    }

    // Mod MANUAL: citire joystick cu ADC bare-metal
    if (currentMode == "MANUAL") {
        int xVal = analogReadBare(4); // A4
        int yVal = analogReadBare(5); // A5

        if (xVal < 256) {
            pan_us = constrain(pan_us - 1, 500, 2500);
            servoPan.writeMicroseconds(pan_us);
            delay(5);
        } else if (xVal > 768) {
            pan_us = constrain(pan_us + 1, 500, 2500);
            servoPan.writeMicroseconds(pan_us);
            delay(5);
        }
        if (yVal < 256) {
            tilt_us = constrain(tilt_us - 1, 500, 2500);
            servoTilt.writeMicroseconds(tilt_us);
            delay(5);
        } else if (yVal > 768) {
            tilt_us = constrain(tilt_us + 1, 500, 2500);
            servoTilt.writeMicroseconds(tilt_us);
            delay(5);
        }

        // Buton joystick cu bare-metal digitalRead
        if (!digitalReadBare(joySW)) {
            servoFire.write(180); delay(500);
            servoFire.write(0);   delay(500);
            servoFire.write(90);  delay(500);
        }
    }
}
