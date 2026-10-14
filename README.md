# SafeGuard GPS Pendant — Complete Guide
## Breadboard Wiring + Wokwi Simulation + Code Walkthrough

> **Can you simulate RIGHT NOW?** ✅ Yes — open VS Code, install the Wokwi extension, and follow Part 2. No physical hardware needed.

---

## PART 1 — BREADBOARD WIRING
### Step-by-step physical connections

---

### Before you start — orient your breadboard

```
Breadboard long rails (top and bottom strips):
  + rail (red)  ← connect to ESP32-C3  3V3 pin
  − rail (black) ← connect to ESP32-C3  GND pin

Do this FIRST before placing any component.
```

Your breadboard has two halves (left/right gap in the middle).
Place the **ESP32-C3 Super Mini straddling the centre gap** so both sides of pins are accessible.

---

### STEP 1 — Place the ESP32-C3 Super Mini

Straddle the ESP32-C3 across the **centre gap** of the breadboard, rows 1–10 (approximately).

```
Left side pins:                Right side pins:
  Row 1 — GND                   Row 1 — 3V3
  Row 2 — GPIO1 (ADC/mic)       Row 2 — GPIO2 (touch)
  Row 3 — GPIO3                  Row 3 — GPIO3
  Row 4 — GPIO4 (GSM RX in)     Row 4 — GPIO5 (GSM TX out)
  Row 5 — GPIO6 (GPS RX in)     Row 5 — GPIO7 (GPS TX out)
  Row 6 — GPIO8 (speaker)       Row 6 — GPIO9
  Row 7 — GPIO10                Row 7 — GPIO10
  Row 8 — GND                   Row 8 — VUSB (5V from USB)
```

> The exact row numbers don't matter — just note which GPIO is in which row.
> Use a phone photo or label stickers to track it.

---

### STEP 2 — Power the rails

```
ESP32-C3  3V3  ──── breadboard + rail (red stripe)
ESP32-C3  GND  ──── breadboard − rail (black stripe)
```

Now every component can just grab power from the rail instead of crowding the ESP32-C3 pins.

---

### STEP 3 — SIM800L GSM Module (MOST IMPORTANT — read carefully)

#### 3a. Power + Decoupling Capacitors

The SIM800L **draws up to 2 Amperes** in short bursts when it sends an SMS or connects to GPRS. Without capacitors, this current spike makes the ESP32-C3 reboot.

**Place 2 × 470µF capacitors in parallel directly at the SIM800L VCC and GND pins:**

```
  SIM800L VCC row ──── cap1 (+) long leg ──── cap1 (−) short leg/stripe ──── SIM800L GND row
  SIM800L VCC row ──── cap2 (+) long leg ──── cap2 (−) short leg/stripe ──── SIM800L GND row
```

Then connect power:
```
  breadboard + rail ──── SIM800L VCC row
  breadboard − rail ──── SIM800L GND row
```

> ⚠️ POLARITY: The stripe on the capacitor side = NEGATIVE.
> The longer leg = POSITIVE.
> Getting this backwards will destroy the capacitor (possibly explosively).

#### 3b. UART — SIM800L TX → ESP32-C3 (direct, no resistor)

SIM800L outputs 2.8V logic → ESP32-C3's 3.3V input can read it fine.

```
SIM800L TX ──── ESP32-C3 GPIO4
```

#### 3c. UART — ESP32-C3 TX → SIM800L RX (NEEDS VOLTAGE DIVIDER)

The ESP32-C3 outputs 3.3V on TX. The SIM800L RX pin maximum is 2.8V.
Use your **1kΩ and 330Ω resistors** to make a voltage divider:

```
ESP32-C3 GPIO5 ──[1kΩ]──┬──[330Ω]──── breadboard − rail (GND)
                          │
                     SIM800L RX
```

This reduces 3.3V to about 0.82V — safely within SIM800L's spec.

Place on breadboard:
1. Put 1kΩ resistor: one leg in the GPIO5 row, other leg in a free row (call it "mid-node")
2. Put 330Ω resistor: one leg in "mid-node", other leg in GND rail
3. Wire SIM800L RX to "mid-node"

---

### STEP 4 — GY-NEO6MV2 GPS Module

GPS is 3.3V logic — straightforward, no resistors needed:

```
GPS VCC  ──── breadboard + rail (3V3)
GPS GND  ──── breadboard − rail (GND)
GPS TX   ──── ESP32-C3 GPIO6
GPS RX   ──── ESP32-C3 GPIO7
```

> The GPS module needs **clear sky** to get a fix. For simulation this is mocked. Indoors, it will time out after 30s and fall back to a Nairobi default coordinate.

---

### STEP 5 — TTP223B Capacitive Touch Sensor

This is the simplest component — just 3 wires:

```
TTP223B VCC ──── breadboard + rail (3V3)
TTP223B GND ──── breadboard − rail (GND)
TTP223B SIG ──── ESP32-C3 GPIO2
```

**No resistors needed.** No I2C. No library. The sensor outputs:
- `HIGH` (3.3V) when a finger is on the pad
- `LOW` (0V) when not touched

The gold circular pad on the module is the touch area. You can wrap wire around it or just touch it with your finger.

---

### STEP 6 — Electret Condenser Microphone (6mm capsule)

The capsule needs a **DC bias resistor** — without it, the mic produces no signal.

```
breadboard + rail (3V3) ──[10kΩ]──┬──── Mic + (longer / marked lead)
                                   │
                              ESP32-C3 GPIO1
                                   │
                          Mic − (shorter lead) ──── breadboard − rail (GND)
```

Breadboard steps:
1. Put 10kΩ resistor: one leg in + rail, other leg in a free row (call it "mic-bias-node")
2. Put mic +lead in "mic-bias-node"
3. Put a jumper from "mic-bias-node" to GPIO1 row
4. Put mic −lead in GND rail

> The capsule is very small (6mm). Use thin solid-core wire or a small PCB socket.
> You can hold the legs with tape on the breadboard if they don't grip.
> Idle ADC reading ≈ 1500–2500 (varies). Shout into the mic = reading jumps.

---

### STEP 7 — Mini Speaker 8Ω 1W

Use a **22Ω series resistor** to protect the GPIO pin:

```
ESP32-C3 GPIO8 ──[22Ω]──── Speaker + (red wire)
                             Speaker − (black wire) ──── breadboard − rail (GND)
```

> For the simulation (Wokwi) the buzzer is connected directly.
> On real hardware with the 22Ω, you'll hear faint beeps — that's expected.
> For louder audio later: add a transistor (NPN 2N2222) using your spare 1kΩ as the base resistor.

---

### STEP 8 — Use the 3rd 470µF cap (optional but recommended)

Add one more 470µF cap across the GPS VCC-GND to absorb any GPS module spikes:

```
GPS VCC row ──── cap3 (+) ──── cap3 (−) ──── GPS GND row
```

---

### COMPLETE WIRING SUMMARY TABLE

| From | To | Via |
|---|---|---|
| ESP32 3V3 | + rail | direct |
| ESP32 GND | − rail | direct |
| + rail | SIM800L VCC | direct |
| − rail | SIM800L GND | direct |
| SIM800L VCC | 470µF cap1 + cap2 (+) | direct (caps to GND) |
| ESP32 GPIO4 | SIM800L TX | direct |
| ESP32 GPIO5 | SIM800L RX | via 1kΩ + 330Ω divider |
| + rail | GPS VCC | direct |
| − rail | GPS GND | direct |
| ESP32 GPIO6 | GPS TX | direct |
| ESP32 GPIO7 | GPS RX | direct |
| + rail | TTP223B VCC | direct |
| − rail | TTP223B GND | direct |
| ESP32 GPIO2 | TTP223B SIG | direct |
| + rail | Mic + | via 10kΩ bias resistor |
| ESP32 GPIO1 | Mic + (bias node) | direct |
| − rail | Mic − | direct |
| ESP32 GPIO8 | Speaker + | via 22Ω |
| − rail | Speaker − | direct |

---

---

## PART 2 — WOKWI SIMULATION (do this RIGHT NOW)

### ✅ Prerequisites — install once

1. Open **VS Code**
2. Press `Ctrl+Shift+X` (Extensions)
3. Search: **"Wokwi for VS Code"** → Install (by Wokwi)
4. After install, press `Ctrl+Shift+P` → type **"Wokwi: Request a License"** → Get a free licence (takes 30 seconds)

---

### Step 1 — Open the simulation project

In VS Code, open the folder:
```
c:\Users\joych\gps-safety-wearable\firmware\wokwi\
```

You'll see these files:
```
wokwi/
  diagram.json        ← the circuit schematic (all components + wires)
  sketch.ino          ← the firmware code
  libraries.txt       ← library list (TinyGPS++)
  wokwi.toml          ← tells Wokwi what to simulate
  BREADBOARD_WIRING.md
```

---

### Step 2 — Start the simulator

Option A (recommended): Click `diagram.json` → a **"Start Simulation"** green play button appears at the top right → click it.

Option B: Press `F1` → type **"Wokwi: Start Simulator"** → Enter.

> The simulator opens an interactive circuit view. You'll see:
> - ESP32-C3 board in the centre
> - GPS module (top left)
> - SIM800L (bottom left)
> - TTP223B touch chip (right)
> - Buzzer/speaker (bottom right)
> - Joystick (middle right — this is your microphone proxy)
> - Resistors and capacitors wired in

---

### Step 3 — Watch the boot sequence

Click the **Serial Monitor** tab (bottom of Wokwi, or the monitor icon).

You should see:
```
╔══════════════════════════════════════════════════════╗
║   SafeGuard GPS Safety Pendant — Wokwi Simulation   ║
║   ESP32-C3 Super Mini | Joy Kipkemboi, Strathmore   ║
╚══════════════════════════════════════════════════════╝
[GPS]  Serial1 ready (RX=GPIO6 TX=GPIO7)
[GSM]  Serial2 ready (RX=GPIO4 TX=GPIO5)
[GSM]  Initialising SIM800L V2...
[GSM]  Ready
Hardware:
  Touch  : TTP223B → GPIO2 (digital HIGH/LOW)
  Mic    : Electret condenser → GPIO1 (ADC)
  Speaker: 8Ω 1W mini speaker → GPIO8 (PWM)
Alert recipients on trigger:
  1. Personal contacts  (BLE-provisioned from app)
  2. Nisikilize GBV      1195 (free 24/7)
  3. Kenya Police        999 / 112
  4. Backend HTTP POST  via SIM800L GPRS
  5. BLE beacon         community responders ~30m

[STATE] → IDLE (waiting for double-tap or loud mic)
► Double-tap TTP223B chip to trigger alert.
► Move joystick VERT high (>73%) for 1.5s = mic shout trigger.
► Hold TTP223B >3s during cancel window to abort.
```

If you see this — **the simulation is working!** ✅

---

### Step 4 — Test the alert trigger (TTP223B double-tap)

In the Wokwi circuit view:

1. **Click the TTP223B chip once** (it lights up / changes state) — this is "tap 1"
2. **Click it again within 1.5 seconds** — this is "tap 2"

In the Serial Monitor you'll see:
```
[TOUCH] ⚡ Double-tap — 10s cancel window starting...
[STATE] → CANCEL WINDOW — 10s, hold touch to abort
[CANCEL] 10s remaining — hold touch to abort...
[CANCEL] 8s remaining — hold touch to abort...
[CANCEL] 6s remaining — hold touch to abort...
```

**Option A: Let it fire** — do nothing for 10 seconds.
```
[STATE] → SENDING ALL ALERTS
[GPS]  Waiting for satellite fix...
[GPS]  ⚠ Timeout — using Nairobi default

── CHANNEL 1: Personal Emergency Contacts ──
[SMS]  (sim) Would send to +254700000001
[SMS]  (sim) Would send to +254700000002
[SMS]  (sim) Would send to +254700000003

── CHANNEL 2: Nisikilize GBV Helpline (1195) ──
[SMS]  (sim) Would send to 1195

── CHANNEL 3: Kenya Police (999 + 112) ──
[SMS]  (sim) Would send to 999
[SMS]  (sim) Would send to 112

── CHANNEL 4: Backend HTTP POST (GPRS) ──
[HTTP] (sim) POST payload: {"device_id":"SafeGuard-Pendant","trigger":"pendant",...}

── CHANNEL 5: BLE Beacon → Community Responders ──
┌─────────────────────────────────────────────────────┐
│  BLE BEACON — Community Responder Broadcast          │
│  Service UUID : FFE0                                 │
│  Value        : 0x01  (SOS active)                  │
│  Lat: -1.292100  Lng: 36.821900                     │
│  SafeGuard app community responders notified (~30m) │
└─────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════╗
║   ✅  All 5 alert channels dispatched.               ║
╚══════════════════════════════════════════════════════╝
```

**Option B: Cancel** — during the countdown, **hold the TTP223B for 3+ seconds**:
```
[TOUCH] Long-press — ALERT CANCELLED.
[STATE] → IDLE (waiting for double-tap or loud mic)
```

---

### Step 5 — Test the microphone trigger

The electret mic is represented by the **joystick** in Wokwi.

1. Click and **drag the joystick upward** (VERT axis) past about 75%
2. **Hold it there for 1.5 seconds**

You'll see:
```
[MIC]   🎙 Sustained loud sound detected — alert triggered!
[STATE] → CANCEL WINDOW — 10s, hold touch to abort
```

Then the same 10-second countdown and full dispatch happens.

> This simulates someone shouting "MSAADA!" or "HELP!" into the mic.
> The real electret capsule will detect a shout at about 50–80cm distance.

---

### Step 6 — Things to notice in the diagram

While the simulation runs, look at the circuit:
- The **buzzer** should make a sound when the alert fires (3 beeps → confirmed 2-tone)
- The **capacitors** are shown across the SIM800L — this is the power decoupling
- The **resistor network** between GPIO5 and SIM800L RX is the voltage divider
- The **10kΩ** going from 3V3 to the joystick top pin = mic bias resistor

---

---

## PART 3 — CODE WALKTHROUGH
### Understanding sketch.ino section by section

---

### Section 1: Pin Definitions (lines 38–44)

```cpp
#define GPS_RX_PIN   6    // ESP32-C3 receives GPS sentences (NMEA data)
#define GPS_TX_PIN   7    // ESP32-C3 sends commands to GPS (rarely used)
#define GSM_RX_PIN   4    // ESP32-C3 receives AT command responses
#define GSM_TX_PIN   5    // ESP32-C3 sends AT commands to SIM800L
#define TOUCH_PIN    2    // TTP223B output — HIGH=touched, LOW=not
#define MIC_ADC_PIN  1    // Electret mic analog voltage (0–4095)
#define SPEAKER_PIN  8    // PWM output for tone() beeps
```

**Why these GPIO numbers?** The ESP32-C3 Super Mini only exposes certain pins. GPIO 0, 8, 9 have boot/strapping functions. We avoid those. GPIO 1 is ADC1_CH0 — the only ADC channel safe to use with WiFi active. GPIO 2 is a clean digital GPIO. GPIO 4/5/6/7 are the two hardware UART ports.

---

### Section 2: Timing Constants (lines 47–52)

```cpp
#define CANCEL_WINDOW_MS    10000UL  // 10 seconds to cancel after trigger
#define TOUCH_DOUBLE_PRESS_MS 1500UL // both taps must happen within 1.5s
#define LONG_PRESS_CANCEL_MS  3000UL // hold 3+ seconds = cancel command
#define GPS_TIMEOUT_MS       30000UL // wait up to 30s for satellite fix
```

The `UL` suffix = **Unsigned Long** — prevents integer overflow when comparing against `millis()` which returns a `uint32_t` (overflows after ~49 days).

**Why 10 seconds to cancel?** This is intentional UX. A survivor who accidentally triggers the device needs enough time to abort without panicking. But it's short enough that a genuine emergency dispatches quickly.

---

### Section 3: TTP223B Double-Tap State Machine (lines ~210–260)

This is the heart of the touch logic. It's a **Finite State Machine (FSM)** — it goes through states step by step:

```
T_IDLE → T_PRESSED_1 → T_RELEASED_1 → T_PRESSED_2 → fire alert
                                 ↓ (timeout)
                              T_IDLE
```

```cpp
// Every loop() iteration this runs:
void updateTouch() {
  bool isTouched = digitalRead(TOUCH_PIN) == HIGH;  // Read TTP223B

  // --- Long-press detection (for cancel) ---
  if (isTouched) {
    if (!prevTouch) holdStart = now;           // finger just arrived
    else if (now - holdStart > 3000) {
      cancelHoldFired = true;                  // held 3s → cancel flag
    }
  }

  // --- Double-tap FSM ---
  switch (touchState) {
    case T_IDLE:
      if (isTouched && !prevTouch)             // rising edge = first tap starts
        { touchState = T_PRESSED_1; }
      break;
    case T_PRESSED_1:
      if (!isTouched && prevTouch)             // finger lifted = tap 1 registered
        { touchState = T_RELEASED_1; }
      else if (timeout) touchState = T_IDLE;   // took too long → reset
      break;
    case T_RELEASED_1:
      if (isTouched && !prevTouch && within_time)  // second tap = FIRE
        { doubleTapFired = true; touchState = T_PRESSED_2; }
      break;
  }
  prevTouch = isTouched;                       // remember for next loop
}
```

**Key concept**: We track `prevTouch` so we can detect the **rising edge** (finger arrives) and **falling edge** (finger leaves). This prevents a held finger from counting as repeated taps.

---

### Section 4: Microphone ADC Detection (lines ~270–285)

```cpp
void updateMic() {
  int level = analogRead(MIC_ADC_PIN);  // 0 to 4095 (12-bit ADC)

  if (level > 3000) {                   // above threshold = loud sound
    if (micShoutStart == 0)
      micShoutStart = millis();         // start timing the shout
    else if (millis() - micShoutStart >= 1500) {
      micAlertFired = true;             // loud for 1.5s → trigger!
      micShoutStart = 0;
    }
  } else {
    micShoutStart = 0;                  // quiet → reset timer
  }
}
```

**Why require 1.5 seconds?** Prevents false triggers from door slams, passing vehicles, coughs. A genuine distress call (shouting) is sustained. This is a simple energy-threshold approach — the full app (`record_phrases.py` + ML model) will be smarter, using keyword detection.

**What is 3000 threshold?** The ADC returns 0–4095. The electret capsule at idle reads roughly 1500–2500 (mid-rail with bias). A shout pushes it toward 3000–4095. On real hardware you'll calibrate this in `config.h` (`MIC_SHOUT_THRESHOLD`).

---

### Section 5: The Alert State Machine (lines ~290–340)

```
STATE_IDLE
    │ double-tap OR mic shout
    ▼
STATE_CANCEL_WINDOW  ←── hold touch 3s → STATE_IDLE (cancelled)
    │ 10 seconds pass
    ▼
STATE_SENDING  (calls dispatchAlert())
    │
    ▼
STATE_CONFIRMED  → 5s → STATE_IDLE
```

This pattern (state machine) means the device is **never blocking** — it checks its state every loop cycle. The `changeState()` function records the timestamp (`stateEnter`) so the cancel window countdown works without using `delay()`.

**Why no `delay()`?** `delay()` freezes everything — the mic stops being checked, touch stops being read. A state machine using `millis()` lets all inputs stay responsive simultaneously.

---

### Section 6: GSM / SIM800L AT Commands (lines ~120–190)

The SIM800L is controlled by text commands called **AT commands** (Hayes command set, 1981):

```cpp
gsmWrite("AT");           // → SIM800L responds "OK" (ping/test)
gsmWrite("ATE0");         // → turns off echo (stops it repeating your commands)
gsmWrite("AT+CMGF=1");    // → sets SMS to text mode (not PDU binary)
gsmWrite("AT+CSQ");       // → returns signal quality, e.g. "+CSQ: 18,0"
```

**Sending an SMS:**
```cpp
gsmWrite("AT+CMGS=\"+254700000001\"");  // start SMS to this number
gsmWait(">");                            // SIM800L replies ">" meaning "send text now"
gsmSerial.print("EMERGENCY...");         // type the message
gsmSerial.write(26);                     // ASCII 26 = Ctrl+Z = "send it"
gsmWait("OK");                           // SIM800L confirms sent
```

In Wokwi, the SIM800L chip is simulated — it may not fully respond but the code logs what it would send. On real hardware with an active SIM card, the SMS goes out.

---

### Section 7: The 5-Channel Alert Dispatch (lines ~200–280)

The `dispatchAlert()` function runs the 5 channels in order:

```cpp
void dispatchAlert() {
  beepAlert();           // 🔊 speaker: 3 urgent beeps (SOS pattern)
  waitGpsFix(30000);     // 📍 try to get GPS coordinates for 30s

  // Build SMS body with map link
  char smsBody[] = "EMERGENCY! Location: https://maps.google.com/?q=-1.2921,36.8219";

  // Ch1: Personal contacts (provisioned via BLE from phone app)
  sendSms("+254700000001", smsBody);
  sendSms("+254700000002", smsBody);
  sendSms("+254700000003", smsBody);

  // Ch2: Nisikilize GBV helpline
  sendSms("1195", nisiSms);

  // Ch3: Police (both numbers, in case one has no airtime)
  sendSms("999", policeSms);
  sendSms("112", policeSms);   // 112 works without airtime on Safaricom

  // Ch4: HTTP POST to backend with JSON payload
  httpPostAlert(json);           // opens GPRS bearer, posts to API

  // Ch5: BLE beacon (simulated as Serial print in Wokwi)
  bleAdvertiseAlert(lat, lng);   // on real device: starts BLE advertising

  beepConfirmed();       // 🔊 speaker: rising 2-tone = "sent"
}
```

**Why Google Maps link in SMS?** Emergency contacts and police likely won't have the SafeGuard app. A raw Google Maps link opens immediately on any phone without installing anything.

---

### Section 8: GPS (lines ~95–120)

```cpp
TinyGPSPlus gpsParser;           // the GPS sentence parser library
HardwareSerial gpsSerial(1);     // UART1 hardware port

// In setup():
gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

// Every loop(), feed bytes to parser:
while (gpsSerial.available()) gpsParser.encode(gpsSerial.read());

// When you want coordinates:
double lat = gpsParser.location.lat();    // e.g. -1.2921
double lng = gpsParser.location.lng();    // e.g.  36.8219
```

The GPS module sends **NMEA sentences** continuously at 9600 baud. They look like:
```
$GPRMC,161229.487,A,-1.292100,S,036.821900,E,0.013,309.62,...
```

`TinyGPS++` parses these and extracts lat/lng, speed, satellites, etc. The `waitGpsFix()` function keeps looping until `gpsParser.location.isValid()` becomes true (or timeout after 30s).

---

### Summary: What to change before real deployment

| What | Where | Change |
|---|---|---|
| Personal emergency contacts | `sketch.ino` lines 61–65 | Replace `+254700000001` etc with real numbers |
| Backend URL | line 76 | Replace with your actual API endpoint |
| GSM APN | line 77 | `"safaricom"` → your SIM carrier APN |
| Mic threshold | line 57 | Tune `MIC_SHOUT_THRESHOLD` after testing with real capsule |
| Cancel window | line 47 | Adjust `CANCEL_WINDOW_MS` if 10s feels wrong |

---

## PART 4 — WHAT HAPPENS NEXT

After the Wokwi simulation works:

1. **Set up real hardware** on breadboard using Part 1 of this guide
2. **Insert a Safaricom SIM** into the SIM800L (nano-SIM, activated, with airtime)
3. **Flash the sketch** with Arduino IDE or PlatformIO targeting `esp32c3`
4. **Test outdoors** (clear sky for GPS fix)
5. **Connect the phone app** via BLE to provision real emergency contact numbers
6. **Test full chain**: trigger → SMS arrives on contact phone → GPS link opens correctly
