
from pathlib import Path
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit import IndicProcessor

PROJECT_DIR = Path(__file__).resolve().parent.parent
FORWARD_DIR = PROJECT_DIR / "offline_translation"
REVERSE_DIR = PROJECT_DIR / "offline_translation_reverse"


LANGUAGES = {
    "Assamese": "asm_Beng",
    "Bengali": "ben_Beng",
    "Bodo": "brx_Deva",
    "Dogri": "doi_Deva",
    "English": "eng_Latn",
    "Gujarati": "guj_Gujr",
    "Hindi": "hin_Deva",
    "Kannada": "kan_Knda",
    "Kashmiri (Arabic)": "kas_Arab",
    "Kashmiri (Devanagari)": "kas_Deva",
    "Konkani": "gom_Deva",
    "Maithili": "mai_Deva",
    "Malayalam": "mal_Mlym",
    "Manipuri (Bengali)": "mni_Beng",
    "Manipuri (Meitei)": "mni_Mtei",
    "Marathi": "mar_Deva",
    "Nepali": "npi_Deva",
    "Odia": "ory_Orya",
    "Punjabi": "pan_Guru",
    "Sanskrit": "san_Deva",
    "Santali": "sat_Olck",
    "Sindhi (Arabic)": "snd_Arab",
    "Sindhi (Devanagari)": "snd_Deva",
    "Tamil": "tam_Taml",
    "Telugu": "tel_Telu",
    "Urdu": "urd_Arab",
}


class OfflineTranslator:
    def __init__(self):
        print("Loading Indic-to-English model...")
        self.forward_tokenizer = AutoTokenizer.from_pretrained(
            str(FORWARD_DIR), trust_remote_code=True, local_files_only=True
        )
        self.forward_model = AutoModelForSeq2SeqLM.from_pretrained(
            str(FORWARD_DIR), trust_remote_code=True, local_files_only=True
        )
        self.forward_model.eval()

        print("Loading English-to-Indic model...")
        self.reverse_tokenizer = AutoTokenizer.from_pretrained(
            str(REVERSE_DIR), trust_remote_code=True, local_files_only=True
        )
        self.reverse_model = AutoModelForSeq2SeqLM.from_pretrained(
            str(REVERSE_DIR), trust_remote_code=True, local_files_only=True
        )
        self.reverse_model.eval()

        self.processor = IndicProcessor(inference=True)
        print("Both translation models are ready.")

    def _translate(self, text, source_code, target_code, tokenizer, model):
        batch = self.processor.preprocess_batch(
            [text], src_lang=source_code, tgt_lang=target_code
        )
        inputs = tokenizer(
            batch, truncation=True, padding="longest", return_tensors="pt"
        )
        with torch.no_grad():
            generated = model.generate(**inputs, max_length=128, num_beams=5)
        decoded = tokenizer.batch_decode(generated, skip_special_tokens=True)
        return self.processor.postprocess_batch(decoded, lang=target_code)[0]

    def translate_to_english(self, text: str, source_language: str) -> str:
        if source_language not in LANGUAGES:
            raise ValueError(f"Unsupported language: {source_language}")
        if source_language == "English":
            return text
        return self._translate(
            text, LANGUAGES[source_language], "eng_Latn",
            self.forward_tokenizer, self.forward_model
        )

    def translate_from_english(self, text: str, target_language: str) -> str:
        if target_language not in LANGUAGES:
            raise ValueError(f"Unsupported language: {target_language}")
        if target_language == "English":
            return text
        return self._translate(
            text, "eng_Latn", LANGUAGES[target_language],
            self.reverse_tokenizer, self.reverse_model
        )
