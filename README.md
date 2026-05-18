# The Verifier v2.0 — Automotive AI Hallucination Detection

## Run in 5 steps

1. `pip install fastapi uvicorn groq scikit-learn numpy python-dotenv streamlit requests`
2. `cd backend` → create `.env` file with `GROQ_API_KEY=your_key`
3. `python build_index.py` (run once)
4. `python server.py` (Terminal 1)
5. `streamlit run dashboard.py` (Terminal 2)

Load Chrome extension: chrome://extensions → Developer mode → Load unpacked → select extension/

## What it detects

- Wrong VSS signal paths (vehicle.speed.current, Vehicle.Engine.RPM, etc.)
- Non-existent ASIL levels (ASIL E, ASIL Z, ASIL 5, etc.)
- ASIL assigned without HARA
- ABS timing outside 50-150ms range
- Wrong OBD-II addresses (0x7FF instead of 0x7DF)
- CAN bus claimed to have encryption
- ara::com used with Classic AUTOSAR
- Adaptive Platform on bare-metal
- Fake ISO 26262 clause numbers
- SOTIF confused with ISO 26262
- Absolute impossible claims (100% accurate, guaranteed, never fails)

## What scores correctly (should be 0%)

- Vehicle.Speed, Vehicle.Powertrain.TractionBattery.StateOfCharge.Current
- ASIL A/B/C/D with HARA mentioned
- ABS timing 50-150ms
- 100% MC/DC coverage for ASIL D (legitimate test requirement)
- OBD-II address 0x7DF
- CAN described as lacking security
- ara::com with Adaptive Platform
- SOTIF as complementary to ISO 26262
