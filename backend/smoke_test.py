"""
Smoke test for The Verifier — run AFTER starting server.py.
    python smoke_test.py
Sends 7 known inputs and checks the scores make sense.
"""
import requests

API = "http://localhost:8000"

TESTS = [
    # (name, text, expect_hallucinated)
    ("Dense hallucination (3 critical errors)",
     "The vehicle.speed.current signal gives wheel speed. The ABS responds in 1 ms. ASIL Z is the highest safety level.",
     True),
    ("Clean correct text",
     "Vehicle.Speed provides wheel-based speed in km/h per COVESA VSS 4.0. ABS responds in 80 ms. ASIL D is the highest level.",
     False),
    ("False-positive check: 'uncertainly'",
     "The sensor behaves uncertainly in fog conditions.",
     False),
    ("False-positive check: 'absolute' is not ABS",
     "The absolute maximum rating is 5 ms for the relay.",
     False),
    ("CAN security claim",
     "The CAN bus includes encryption and built-in authentication for all frames.",
     True),
    ("Homoglyph attack (Cyrillic 'с')",
     "The vehiсle.speed.current path gives speed.",
     True),
    ("ASIL without HARA",
     "We assigned ASIL D without conducting a formal HARA because it obviously qualifies.",
     True),
]

def main():
    try:
        h = requests.get(f"{API}/health", timeout=5).json()
    except Exception:
        print("Server not reachable. Start it first:  cd backend && python server.py")
        return
    print(f"Server OK | Groq: {h['groq']} | KB chunks: {h['chunks']}\n")

    passed = 0
    for name, text, expect_bad in TESTS:
        r = requests.post(f"{API}/verify", json={"text": text}, timeout=30).json()
        got_bad = r["score"] >= 50
        ok = (got_bad == expect_bad)
        passed += ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}")
        print(f"       score={r['score']}  issues={[i['pattern'] for i in r['issues']]}  time={r['time_ms']}ms\n")

    print(f"{passed}/{len(TESTS)} tests passed.")
    if h["groq"]:
        print("\nRe-verify demo:")
        rv = requests.post(f"{API}/reverify", json={
            "original":  "ASIL Z is the highest level and ABS responds in 1 ms.",
            "corrected": "ASIL D is the highest level per ISO 26262 and ABS responds in 50-150 ms."
        }, timeout=60).json()
        print(f"  {rv['original_score']}% -> {rv['corrected_score']}%  ({rv['message']})")

if __name__ == "__main__":
    main()
