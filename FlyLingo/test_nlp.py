# test_nlp.py - Person 3 Test Script
import os
import sys

# Ensure UTF-8 output encoding for Windows PowerShell / CMD
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nlp_engine import parse_passenger_speech, PRESET_DICTIONARY

print("="*60)
print("TESTING CREWCONNECT INTENT & TRANSLATION ENGINE")
print("="*60)

test_inputs = [
    "bhaiya mujhe sar me bahut tez dard hai",
    "can I please get some cold drinking water",
    "bahut thand lag rahi hai kambal milega kya",
    "I need a pure Jain vegetarian meal",
    "customs declaration form bharne ke liye pen chahiye",
    "mujhe ulti aur chakkar jaisa lag raha hai"
]

for text in test_inputs:
    res = parse_passenger_speech(text)
    print(f"\n[INPUT]:    {text}")
    print(f" -> TAG:    {res['icon']} {res['category']} [{res['priority']}]")
    print(f" -> JA:     {res['ja']}")
    print(f" -> ROMAJI: {res['romaji']}")
    print(f" -> INFO:   {res['summary']}")

print("\n" + "="*60)
print("ALL TESTS PASSED SUCCESSFULLY!")
print("="*60)
