import cv2
import numpy as np
import serial
import time

# --- Inițializări cameră ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Camera NU a fost detectată.")
    exit()

# --- Inițializări seriale Arduino ---
ser = serial.Serial('COM4', 9600, timeout=1)
time.sleep(2)

# --- Variabile globale pentru control ---
pan_us = 1500         # poziție inițială servo pan (stânga-dreapta)
tilt_us = 1500        # poziție inițială servo tilt (sus-jos)
step_us = 1           # pas de ajustare servo
send_delay = 0.001    # delay minim între comenzi seriale
last_sent = time.time()
fired = False         # flag dacă s-a tras deja
last_print_time = 0   # pentru afișare „Target Hit!”

# --- Trimite o comandă serială dacă a trecut destul timp ---
def send(cmd):
    global last_sent
    if time.time() - last_sent > send_delay:
        ser.write((cmd + '\n').encode())
        last_sent = time.time()
        print(f"[SERIAL] Trimis: {cmd}")

# --- Funcție pentru detecția celui mai mare cerc ---
def find_biggest_circle(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT,
                               dp=1.2, minDist=100,
                               param1=50, param2=38,
                               minRadius=35, maxRadius=60)
    if circles is not None:
        c = max(np.uint16(np.around(circles[0])), key=lambda x: x[2])
        return int(c[0]), int(c[1]), int(c[2])  # x, y, r
    return None

# --- Resetare buffer și trimitere mod inițial ---
time.sleep(1)
ser.reset_input_buffer()
time.sleep(1)
send("MODE=FREE")

# --- Parametri pentru explorare ---
exploration_angles = [1500, 1700, 1500, 1300, 1500]  # unghiuri presetate pentru scanare
required_confirmations = 3  # câte cadre consecutive trebuie să confirme o țintă

# --- Stări globale ---
exploration_active = False
found_target = False
exploration_count = 0
last_circle = None

# --- Pentru urmărirea unei ținte detectate ---
current_target = None
confidence = 0
lost_counter = 0

# --- Detectează o țintă circulară ---
def detect_target(frame):
    global current_target, confidence, lost_counter, fired
    if fired:
        return None
    result = find_biggest_circle(frame)
    if result:
        x, y, r = result
        if current_target:
            d = np.hypot(x - current_target[0], y - current_target[1])
            confidence = min(confidence + 1, 10) if d < 20 else 1
        else:
            confidence = 1
        lost_counter = 0
        if confidence >= 1:
            current_target = (x, y, r)
    else:
        confidence = max(confidence - 1, 0)
        lost_counter += 1
        if lost_counter >= 5:
            current_target = None
    return current_target

# --- Detectează punctul laser (roșu intens) ---
def detect_laser(frame):
    global fired
    if fired:
        return None
    red = frame[:, :, 2]
    _, thresh = cv2.threshold(red, 252, 255, cv2.THRESH_BINARY)
    cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cnts:
        c = max(cnts, key=cv2.contourArea)
        if cv2.contourArea(c) > 5:
            M = cv2.moments(c)
            if M["m00"]:
                return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
    return None

# --- Activează modul de scanare exploratorie ---
def run_exploration_mode():
    global exploration_active, found_target, exploration_count, last_circle, pan_us
    print("🟢 Modul SCANARE activat.")
    send("MODE=SCAN")
    
	# 🔁 Resetăm poziția de pornire
    pan_us = 1500
    send(f"PANU={pan_us}")
    time.sleep(0.01)

    exploration_active = True
    found_target = False
    exploration_count = 0
    last_circle = None

    for target_us in exploration_angles:
        while pan_us != target_us:
            # Verificare mesaje de la Arduino
            if ser.in_waiting:
                msg = ser.readline().decode().strip()
                if msg == "Q":
                    send("MODE=OFF")
                    print("🛑 Scanare întreruptă prin Q.")
                    exploration_active = False
                    return
                elif msg == "F":
                    send("MODE=FREE")
                    print("↩️ Scanare întreruptă prin F.")
                    exploration_active = False
                    return

            # Verificare tastatură pentru oprire
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                send("MODE=OFF")
                print("🛑 Scanare întreruptă din tastatură (q).")
                exploration_active = False
                return
            if key == ord('f'):
                send("MODE=FREE")
                print("↩️ Scanare întreruptă din tastatură (f).")
                exploration_active = False
                return

            # Mișcă servo spre target_us
            step = np.sign(target_us - pan_us)
            pan_us += step
            pan_us = np.clip(pan_us, 500, 2500)
            send(f"PANU={pan_us}")
            time.sleep(0.002)

            ret2, f2 = cap.read()
            if not ret2:
                continue

            result = find_biggest_circle(f2)
            if result:
                x, y, r = result
                if r >= 38:
                    if last_circle:
                        d = np.hypot(x - last_circle[0], y - last_circle[1])
                        exploration_count = exploration_count + 1 if d < 10 else 1
                    else:
                        exploration_count = 1
                    last_circle = (x, y, r)
                    if exploration_count >= required_confirmations:
                        print(f"🎯 Țintă confirmată în scanare (r={r})")
                        found_target = True
                        break
                else:
                    exploration_count = 0
                    last_circle = None
                cv2.circle(f2, (x, y), r, (0, 255, 0), 2)
                cv2.circle(f2, (x, y), 2, (0, 0, 255), 3)

            cv2.imshow("Auto-Turret", f2)

        if found_target:
            break

    # Final scanare
    if found_target:
        send("MODE=LOCK")
        print("🔒 Modul LOCK: țintă găsită.")
    else:
        send("MODE=FREE")
        print("❌ Nicio țintă detectată. Revenire la FREE.")
    exploration_active = False
    print("💡 Apasă 's' pentru o nouă scanare sau 'q' pentru a ieși.")

# --- Afișare mesaj inițial ---
print("💡 Sistem inițializat în modul FREE. Apasă 's' pentru scanare, 'q' pentru ieșire.")

# --- Buclă principală ---
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # 🔁 Mesaje seriale de la Arduino
    if ser.in_waiting:
        msg = ser.readline().decode().strip()
        if msg:
            print(f"[ARDUINO] Trimite: {msg}")
            if msg == "S" and not exploration_active and not fired:
                run_exploration_mode()
            elif msg == "Q":
                send("MODE=OFF")
                break
            elif msg == "F":
                send("MODE=FREE")
                found_target = False
                fired = False
                exploration_active = False
                print("↩️ Forțat în modul FREE din buton.")
            elif msg == "M":
                send("MODE=MANUAL")
                print("🎮 Modul MANUAL activat.")

    # 🔁 Comenzi tastatură
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s') and not exploration_active and not fired:
        run_exploration_mode()
    if key == ord('q'):
        send("MODE=OFF")
        break
    if exploration_active:
        continue

    # 🔍 Țintire și tragere
    if found_target and not fired:
        tgt = detect_target(frame)
        lsr = detect_laser(frame)
        if tgt:
            x, y, r = tgt
            cv2.circle(frame, (x, y), r, (0, 255, 0), 3)
            cv2.circle(frame, (x, y), 2, (0, 0, 255), 4)
        if lsr:
            lx, ly = lsr
            cv2.circle(frame, (lx, ly), 8, (0, 255, 255), -1)
        if tgt and lsr:
            dx, dy = x - lx, y - ly
            cv2.line(frame, (lx, ly), (x, y), (255, 255, 0), 2)
            if abs(dx) > 8:
                pan_us -= int(np.sign(dx)) * step_us
                pan_us = np.clip(pan_us, 500, 2500)
                send(f"PANU={pan_us}")
            if abs(dy) > 8:
                tilt_us -= int(np.sign(dy)) * step_us
                tilt_us = np.clip(tilt_us, 500, 2500)
                send(f"TILTU={tilt_us}")
            if abs(dx) < 8 and abs(dy) < 8:
                send("MODE=FIRE_WARN")
                time.sleep(1)
                send("FIRE=1")
                fired = True
                print("💥 TRAGERE executată.")
                time.sleep(1)
                send("MODE=FREE")
                print("↩️ Revenire completă la centru.")
                print("💡 Sistem revenit în modul FREE. Apasă 's' pentru o nouă scanare sau 'q' pentru a ieși.")
                found_target = False
                fired = False
                current_target = None
                confidence = 0
                lost_counter = 0

    # 🎯 Overlay „Target Hit!” după tragere
    if fired:
        if time.time() - last_print_time > 1:
            print("✅ Țintă lovită!")
            last_print_time = time.time()
        txt, font = "Target Hit!", cv2.FONT_HERSHEY_DUPLEX
        s, th = 2, 3
        tw, tht = cv2.getTextSize(txt, font, s, th)[0]
        x = (frame.shape[1] - tw) // 2
        y = (frame.shape[0] + tht) // 2
        cv2.putText(frame, txt, (x, y), font, s, (0, 0, 0), th + 2)
        cv2.putText(frame, txt, (x, y), font, s, (0, 0, 255), th)

    cv2.imshow("Auto-Turret", frame)

# --- Cleanup final ---
cap.release()
ser.close()
cv2.destroyAllWindows()
