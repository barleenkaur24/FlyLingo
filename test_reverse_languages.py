import requests

BASE_URL = "http://127.0.0.1:8000"

LANGUAGES = [
    "Assamese", "Bengali", "Bodo", "Dogri", "Gujarati",
    "Hindi", "Kannada", "Kashmiri (Arabic)",
    "Kashmiri (Devanagari)", "Konkani", "Maithili", "Malayalam",
    "Manipuri (Bengali)", "Manipuri (Meitei)", "Marathi", "Nepali",
    "Odia", "Punjabi", "Sanskrit", "Santali",
    "Sindhi (Arabic)", "Sindhi (Devanagari)", "Tamil", "Telugu", "Urdu"
]

for language in LANGUAGES:
    try:
        response = requests.post(
            f"{BASE_URL}/api/translate-reply",
            json={
                "text": "Your request has been received. We will bring you water shortly.",
                "language": language
            },
            timeout=120
        )

        if response.status_code == 200:
            print(f"PASS | {language}: {response.json()['translated_text']}")
        else:
            print(f"FAIL | {language}: HTTP {response.status_code} {response.text}")

    except Exception as error:
        print(f"ERROR | {language}: {error}")
        