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
▶️ [Demo pe YouTube](hhttps://youtu.be/r3NM0cNHf28)

## 📂 Structura fișierelor
```
📁 Auto-Turret-System/
├── Arduino/src/                 # cod firmware pentru Arduino UNO
│   └── main.cpp
├── pc_control/              # script OpenCV + control UART
│   └── turret.py
├── README.md
└── Schema+Demo/                  # imagini + scheme electrice
    └── autoturret-schema.png
```

## ⚙️ Instrucțiuni de rulare

### 1. Upload cod pe Arduino
- Deschide folderul `arduino/` cu PlatformIO sau Arduino IDE.
- Conectează placa Arduino UNO și flash-uiește sketch-ul.

### 2. Rulează codul PC
```bash
cd pc_control/
pip install -r requirements.txt
python turret.py
```

> Asigură-te că portul `COM` din codul Python corespunde plăcii tale.

### 3. Taste utile în timpul rulării:
- `s` → începe modul scanare (automat)
- `f` → revine în mod liber (FREE)
- `q` → oprește complet

## 🤣 Notă amuzantă
> Jumătate din problemele întâmpinate în proiect au fost rezolvate cu **bandă adezivă**.

## 📜 Licență
Open-source, cu scop educațional.
