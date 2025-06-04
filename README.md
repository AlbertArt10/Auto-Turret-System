# Sistem Automat de Țintire – Auto-Turret

Acest proiect reprezintă un **Auto-Turret** controlat cu Arduino UNO și o aplicație Python + OpenCV. Sistemul identifică o țintă vizuală (cerc roșu) cu o cameră web, aliniază poziția folosind servomotoare și acționează trăgaciul când ținta este centrată.

## 🎯 Funcționalități
- Detecție țintă (cerc) și laser cu OpenCV
- Control servo: **Pan**, **Tilt**, **Fire**
- Feedback vizual (LED RGB) și sonor (buzzer)
- 3 moduri de funcționare: `FREE`, `SCAN`, `MANUAL`
- Control UART între PC și Arduino
- Interfață fizică: joystick și butoane dedicate modurilor

## 🔧 Componente hardware
- Arduino UNO
- 3× Servomotoare (SG90 + MG996R)
- Joystick PS2 (X, Y, buton)
- LED RGB (3 pini)
- Buzzer pasiv
- Cameră Web USB (pentru OpenCV)
- Fire, breadboard, sursă 5V/2A etc.

## 🧠 Tehnologii utilizate
- Python 3.10, OpenCV
- PlatformIO + Arduino (C++)
- Bare-metal: `digitalWriteBare`, `analogReadBare` etc.

## 🔗 Link video demo
▶️ [Demo pe YouTube](https://youtu.be/r3NM0cNHf28)

## 📂 Structura fișierelor
```
📁 Auto-Turret-System/
├── Arduino/src/                 # cod firmware pentru Arduino UNO
│   └── main.cpp
├── ScriptPM/              # script OpenCV + control UART
│   └── main.py
├── README.md
└── Schema+Demo/                  # imagini + scheme electrice
```

## 🤣 Notă amuzantă
> Jumătate din problemele întâmpinate în proiect au fost rezolvate cu **bandă adezivă**.

## 📜 Licență
Open-source, cu scop educațional.
