# nlp_engine.py - Person 1: Speech & Translation Engine
# Handles intent categorization, Indian accent acoustic normalization, and Japanese translation.

PRESET_DICTIONARY = {
    "water": {
        "hi": "कृपया मुझे एक गिलास पीने का पानी चाहिए।",
        "en": "Can I please get a glass of drinking water?",
        "ja": "お水を一杯いただけますでしょうか？",
        "romaji": "Omizu o ippai itadakemasu deshō ka?",
        "category": "COMFORT",
        "priority": "NORMAL",
        "icon": "💧"
    },
    "blanket": {
        "hi": "मुझे ठंड लग रही है, क्या एक कंबल मिल सकता है?",
        "en": "I am feeling cold, could I please get a blanket?",
        "ja": "寒気を感じますので、毛布を一枚いただけますか？",
        "romaji": "Samuke o kanjimasu node, mōfu o ichimai itadakemasu ka?",
        "category": "COMFORT",
        "priority": "NORMAL",
        "icon": "🛏️"
    },
    "headache": {
        "hi": "मेरे सिर में बहुत तेज़ दर्द है, क्या कोई दवाई मिल सकती है?",
        "en": "I have a severe headache, is there any medicine available?",
        "ja": "激しい頭痛がします。頭痛薬はありますでしょうか？",
        "romaji": "Hageshii zutsū ga shimasu. Zutsūyaku wa arimasu deshō ka?",
        "category": "MEDICAL",
        "priority": "HIGH",
        "icon": "💊"
    },
    "nausea": {
        "hi": "मुझे चक्कर आ रहे हैं और उल्टी जैसा लग रहा है, सिक बैग चाहिए।",
        "en": "I feel dizzy and nauseous, I need an airsickness bag.",
        "ja": "吐き気とめまいがします。エチケット袋をいただけますか？",
        "romaji": "Hakike to memai ga shimasu. Etiketto-bukuro o itadakemasu ka?",
        "category": "MEDICAL",
        "priority": "HIGH",
        "icon": "🤢"
    },
    "veg_meal": {
        "hi": "क्या मुझे शुद्ध शाकाहारी / जैन भोजन मिल सकता है?",
        "en": "Can I please get a pure vegetarian / Jain meal?",
        "ja": "ベジタリアン（菜食）またはジャイナ教の食事はございますか？",
        "romaji": "Bejitarian matawa Jaina-kyō no shokuji wa gozaimasu ka?",
        "category": "DIETARY",
        "priority": "NORMAL",
        "icon": "🍽️"
    },
    "customs": {
        "hi": "जापान इमिग्रेशन और कस्टम्स डिक्लेरेशन फॉर्म भरने में मदद चाहिए।",
        "en": "I need assistance filling out the Japan Customs / Immigration card.",
        "ja": "日本の入国カード・税関申告書の記入を手伝っていただけますか？",
        "romaji": "Nihon no nyūkoku kādo, zeikan shinkokusho no kinyū o tetsudatte itadakemasu ka?",
        "category": "ASSISTANCE",
        "priority": "NORMAL",
        "icon": "📝"
    },
    "baby": {
        "hi": "बच्चे के लिए थोड़ा गुनगुना पानी या दूध चाहिए।",
        "en": "I need some warm water or milk for my baby.",
        "ja": "赤ちゃん用にぬるま湯、またはミルクをいただけますでしょうか？",
        "romaji": "Akachan-yō ni nurumayu, matawa miruku o itadakemasu deshō ka?",
        "category": "ASSISTANCE",
        "priority": "NORMAL",
        "icon": "🍼"
    },
    "lavatory": {
        "hi": "मुझे वॉशरूम जाने के लिए सहारे की आवश्यकता है।",
        "en": "I need assistance walking to the lavatory.",
        "ja": "お手洗いへの移動をサポートしていただけますでしょうか？",
        "romaji": "Otearai e no idō o sapōto shite itadakemasu deshō ka?",
        "category": "ASSISTANCE",
        "priority": "NORMAL",
        "icon": "♿"
    }
}

def parse_passenger_speech(text: str) -> dict:
    t = text.lower().strip()

    # Indian Pharma Brand Lookup
    if "vertin" in t:
        return {
            "category": "MEDICAL",
            "priority": "HIGH",
            "icon": "💊",
            "ja": "【乗客携行薬】Vertin 16mg（ベタヒスチン / Betahistine - めまい治療薬）服用希望。白湯の提供が必要です。",
            "romaji": "Vertin: Betahisuchin (Memai chiryōyaku). Sayu ga hitsuyō desu.",
            "summary": "Carrying Indian Medicine: Vertin (Betahistine / Anti-vertigo)"
        }
    if any(k in t for k in ["dolo", "crocin", "calpol"]):
        return {
            "category": "MEDICAL",
            "priority": "HIGH",
            "icon": "💊",
            "ja": "【乗客携行薬】Dolo-650/Crocin（アセトアミノフェン / Paracetamol - 解熱鎮痛薬）服用希望。水が必要です。",
            "romaji": "Dolo/Crocin: Asetoaminofen. Mizu ga hitsuyō desu.",
            "summary": "Carrying Indian Medicine: Dolo/Crocin (Paracetamol / Fever Relief)"
        }
    if any(k in t for k in ["pan d", "pan-d", "pantocid"]):
        return {
            "category": "MEDICAL",
            "priority": "HIGH",
            "icon": "💊",
            "ja": "【乗客携行薬】Pan-D（パントプラゾール＋ドンペリドン - 逆流性食道炎・制酸薬）服用希望。白湯が必要です。",
            "romaji": "Pan-D: Pantopurazōru (Seisanyaku). Sayu ga hitsuyō desu.",
            "summary": "Carrying Indian Medicine: Pan-D (PPI & Antacid)"
        }
    if "telma" in t:
        return {
            "category": "MEDICAL",
            "priority": "HIGH",
            "icon": "💊",
            "ja": "【乗客携行薬】Telma-40（テルミサルタン / Telmisartan - 降圧薬）の服用確認と水分補給要請です。",
            "romaji": "Telma: Terumisarutan (Kōatsuyaku). Suibun hokyū.",
            "summary": "Carrying Indian Medicine: Telma (Telmisartan / High BP)"
        }
    if any(k in t for k in ["asthalin", "inhaler"]):
        return {
            "category": "MEDICAL",
            "priority": "HIGH",
            "icon": "🫁",
            "ja": "【緊急・呼吸器】Asthalin 吸入薬（サルブタモール / Salbutamol - 気管支拡張薬）使用。温水スチームと酸素確認要。",
            "romaji": "Asthalin: Sarubutamōru kyūnyū (Kikanshū kakuchōyaku).",
            "summary": "Carrying Inhaler: Asthalin (Salbutamol Bronchodilator)"
        }
    if "glycomet" in t:
        return {
            "category": "MEDICAL",
            "priority": "HIGH",
            "icon": "🩸",
            "ja": "【乗客携行薬】Glycomet（メトホルミン / Metformin - 糖尿病薬）服用。低血糖予防のため食事配慮要。",
            "romaji": "Glycomet: Metohorumin (Tōnyōbyōyaku). Teikettō yobō.",
            "summary": "Carrying Indian Medicine: Glycomet (Metformin / Diabetes)"
        }


    # -------------------------------------------------------------
    # In-Flight Complaints & Cabin Issues (100% Offline Parsing)
    # -------------------------------------------------------------
    # IFE Screen / Monitor Frozen / Touch issue
    if any(k in t for k in ["screen", "monitor", "display", "touch", "frozen", "hang", "black screen", "nahi chal", "chalta nahi", "स्क्रीन", "ਸਕ੍ਰੀਨ", "திரை", "స్క్రీన్", "স্ক্রিন"]):
        return {
            "category": "COMPLAINT",
            "priority": "HIGH",
            "icon": "📺",
            "ja": "【機内不具合】座席モニター（IFE画面）がフリーズし、操作できません。遠隔再起動または席での点検が必要です。",
            "romaji": "Zaseki monitaa (IFE) ga furiizu shite orimasu. Enkaku saikidou yoo.",
            "summary": "IFE Screen Frozen / Unresponsive"
        }

    # Headphone / Audio Jack
    if any(k in t for k in ["headphone", "earphone", "audio", "jack", "sound", "aawaz", "awaj", "distort", "हेडफोन", "ਹੈੱਡਫੋਨ", "ఆవాజ్", "ஆடியோ", "শব্দ", "आवाज", "ਆਵਾਜ਼"]):
        return {
            "category": "COMPLAINT",
            "priority": "NORMAL",
            "icon": "🎧",
            "ja": "【機内不具合】ヘッドホンまたは音声ジャックの接触不良・音が出ない状態です。新品ヘッドホンとの交換が必要です。",
            "romaji": "Heddohon / onsei jakku no fuguai desu. Shinpin heddohon kōkan.",
            "summary": "Headphone / Audio Jack Issue"
        }

    # Seat Recline / Tray Table stuck
    if any(k in t for k in ["recline", "seat stuck", "seat jam", "tray table", "table loose", "seat nahi", "seat peeche"]):
        return {
            "category": "COMPLAINT",
            "priority": "NORMAL",
            "icon": "💺",
            "ja": "【機内不具合】座席リクライニングまたはテーブル機構が作動しません。席での点検・手動解除が必要です。",
            "romaji": "Zaseki rikurainingu / teeburu kikō no fuguai desu.",
            "summary": "Seat Recline / Tray Table Stuck"
        }

    # Special Instruction: Do Not Disturb for meal / sleep (Evaluated before disturbance)
    if any(k in t for k in ["do not disturb", "dont disturb", "sone do", "mat jagana", "sleep", "disturb mat", "मत जगाना", "ਨਾ ਜਗਾਉਣਾ", "தூங்க", "నిద్ర", "ডাকবেন না"]):
        return {
            "category": "INSTRUCTION",
            "priority": "NORMAL",
            "icon": "😴",
            "ja": "【特別ご要望】睡眠中のため、お食事サービス時の声かけ不要（起こさないでください）とのご要望です。",
            "romaji": "Suimin-chū no tame, oshokuji-ji okosanaide kudasai to no go-yōbō desu.",
            "summary": "Do Not Disturb for Meal / Sleep"
        }

    # Cabin Noise / Passenger Disturbance
    if any(k in t for k in ["noise", "loud", "shor", "kicking", "rowdy", "shouting"]) or ("disturb" in t and "do not disturb" not in t and "dont disturb" not in t):
        return {
            "category": "COMPLAINT",
            "priority": "HIGH",
            "icon": "🤫",
            "ja": "【客室環境苦情】周囲の騒音・座席への衝撃に関する苦情です。客室乗務員による状況確認とマナー案内が必要です。",
            "romaji": "Shūi no sōon ni kansuru kujō desu. Joumuin ni yoru koe kake yō.",
            "summary": "Cabin Noise / Disturbance Complaint"
        }

    # Reading light
    if any(k in t for k in ["reading light", "light broken", "light nahi", "batti"]):
        return {
            "category": "COMPLAINT",
            "priority": "NORMAL",
            "icon": "💡",
            "ja": "【機内不具合】読書灯が点灯しない、または消灯できない状態です。",
            "romaji": "Dokushotō ga tentō shinai fuguai desu.",
            "summary": "Reading Light Not Working"
        }

    # -------------------------------------------------------------
    # Special Passenger Flight Instructions (100% Offline Parsing)
    # -------------------------------------------------------------
    # Wake me up before landing
    if any(k in t for k in ["wake me", "jaga dena", "landing", "before landing", "uthana"]):
        return {
            "category": "INSTRUCTION",
            "priority": "NORMAL",
            "icon": "⏰",
            "ja": "【特別ご要望】着陸の45分前に起こしてほしい（服薬・身支度等のため）とのご要望です。",
            "romaji": "Chakuriku mae ni okoshite hoshii to no go-yōbō desu.",
            "summary": "Wake Up Before Landing Instruction"
        }

    # Wheelchair Assistance
    if any(k in t for k in ["wheelchair", "wheel chair", "chalne me"]):
        return {
            "category": "INSTRUCTION",
            "priority": "HIGH",
            "icon": "♿",
            "ja": "【特別ご要望】羽田空港到着時の車いす・地上移動サポートのご要望です。",
            "romaji": "Haneda tōchaku-ji kurumaisu sapōto no go-yōbō desu.",
            "summary": "Wheelchair Assistance on Arrival"
        }

    # Check 1: Medical Emergency (Highest Priority)
    medical_keywords = ["dard", "headache", "pain", "chakkar", "chakkkar", "dizzy", "vomit", "sick", "sar dard", "stomach", "pet dard", "dawai", "medicine", "doctor", "fever", "bukhar", "chest", "दर्द", "ਦਰਦ", "चक्कर", "ਚੱਕਰ", "दवाई", "ਦਵਾਈ", "उल्टी", "தலைவலி", "తలనొప్పి", "ব্যথা"]
    if any(k in t for k in medical_keywords):
        if any(k in t for k in ["vomit", "sick", "nausea", "ulti"]):
            return {
                "category": "MEDICAL",
                "priority": "HIGH",
                "icon": "🤢",
                "ja": "吐き気・気分の悪さを訴えていらっしゃいます。エチケット袋とお手拭きが必要です。",
                "romaji": "Hakike / kibun no warusa o uttaete irasshaimasu.",
                "summary": "Nausea / Air Sickness Alert"
            }
        return {
            "category": "MEDICAL",
            "priority": "HIGH",
            "icon": "💊",
            "ja": "激しい頭痛または痛みを訴えていらっしゃいます。状態確認が必要です。",
            "romaji": "Hageshii zutsū matawa itami o uttaete irasshaimasu.",
            "summary": "Pain / Medication Request"
        }

    # Check 2: Water / Drinks
    if any(k in t for k in ["water", "pani", "paani", "पानी", "ਪਾਣੀ", "জল", "தண்ணீர்", "నీళ్లు", "omizu", "mizu", "お水", "drink", "juice", "chai", "tea", "coffee"]):
        if any(k in t for k in ["chai", "tea"]):
            return {
                "category": "COMFORT",
                "priority": "NORMAL",
                "icon": "☕",
                "ja": "温かいお茶（チャイ）をご希望です。",
                "romaji": "Atatakai ocha (chai) o go-kibō desu.",
                "summary": "Warm Tea Request"
            }
        return {
            "category": "COMFORT",
            "priority": "NORMAL",
            "icon": "💧",
            "ja": "お水またはお飲み物をご希望です。",
            "romaji": "Omizu matawa onomimono o go-kibō desu.",
            "summary": "Drinking Water Request"
        }

    # Check 3: Blanket / Cold
    if any(k in t for k in ["blanket", "kambal", "cold", "thand", "thandi", "pillow", "takiya", "कंबल", "ਕੰਬਲ", "ठंड", "ਠੰਢ", "குளிர்", "చలి", "ঠান্ডা", "mōfu", "毛布"]):
        return {
            "category": "COMFORT",
            "priority": "NORMAL",
            "icon": "🛏️",
            "ja": "寒気を感じており、毛布（または枕）をご希望です。",
            "romaji": "Samuke o kanjite ori, mōfu o go-kibō desu.",
            "summary": "Blanket / Comfort Item Request"
        }

    # Check 4: Food / Meal / Dietary
    if any(k in t for k in ["food", "khana", "meal", "veg", "jain", "roti", "rice", "lunch", "dinner", "breakfast"]):
        return {
            "category": "DIETARY",
            "priority": "NORMAL",
            "icon": "🍽️",
            "ja": "お食事（菜食・食事のタイミング等）に関するご要望です。",
            "romaji": "Oshokuji ni kansuru go-yōbō desu.",
            "summary": "Meal / Dietary Request"
        }

    # Check 5: Immigration / Customs
    if any(k in t for k in ["form", "custom", "immigration", "japan form", "card", "pen"]):
        return {
            "category": "ASSISTANCE",
            "priority": "NORMAL",
            "icon": "📝",
            "ja": "入国書類・税関申告書の記入サポート、またはペンの貸出をご希望です。",
            "romaji": "Nyūkoku shorui no kinyū sapōto o go-kibō desu.",
            "summary": "Customs Form Assistance"
        }

    # Default fallback
    return {
        "category": "ASSISTANCE",
        "priority": "NORMAL",
        "icon": "💬",
        "ja": f"お客様からの音声伝言: 「{text}」",
        "romaji": "Okyakusama kara no onsei dengon.",
        "summary": "Custom Passenger Request"
    }
