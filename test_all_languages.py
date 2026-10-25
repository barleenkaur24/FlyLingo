
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# One sample phrase per language; replace with native-script text.
SAMPLES = {
    "Assamese": "মোক পানী লাগে",
    "Bengali": "আমার পানি চাই",
    "Bodo": "आंनो दै नांगौ",
    "Dogri": "मिगी पानी चाहिदा ऐ",
    "Gujarati": "મને પાણી જોઈએ છે",
    "Hindi": "मुझे पानी चाहिए",
    "Kannada": "ನನಗೆ ನೀರು ಬೇಕು",
    "Kashmiri (Arabic)": "مےٚ پانی چھِیہ",
    "Kashmiri (Devanagari)": "म्योन पानी चाही",
    "Konkani": "म्हाका उदक जाय",
    "Maithili": "हमरा पानि चाही",
    "Malayalam": "എനിക്ക് വെള്ളം വേണം",
    "Manipuri (Bengali)": "ঐগী ঈশিং পাম্বি",
    "Manipuri (Meitei)": "ꯑꯩꯒꯤ ꯏꯁꯤꯡ ꯄꯥꯝꯕꯤ",
    "Marathi": "मला पाणी हवे आहे",
    "Nepali": "मलाई पानी चाहिन्छ",
    "Odia": "ମୋତେ ପାଣି ଦରକାର",
    "Punjabi": "ਮੈਨੂੰ ਪਾਣੀ ਚਾਹੀਦਾ ਹੈ",
    "Sanskrit": "मम जलम् आवश्यकम्",
    "Santali": "ᱤᱧ ᱫᱟᱜ ᱞᱟᱹᱠᱛᱤ",
    "Sindhi (Arabic)": "مون کي پاڻي گهرجي",
    "Sindhi (Devanagari)": "मांखे पाणी घुरजे",
    "Tamil": "எனக்கு தண்ணீர் வேண்டும்",
    "Telugu": "నాకు నీళ్లు కావాలి",
    "Urdu": "مجھے پانی چاہیے",
}

for language, sample in SAMPLES.items():
    try:
        r = requests.post(
            f"{BASE_URL}/api/translate",
            json={"text": sample, "language": language},
            timeout=120,
        )
        if r.status_code == 200:
            print(f"PASS | {language}: {r.json()['translated_text']}")
        else:
            print(f"FAIL | {language}: HTTP {r.status_code} {r.text}")
    except Exception as e:
        print(f"ERROR | {language}: {e}")
