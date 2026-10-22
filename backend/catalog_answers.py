"""Render simple product facts from the mock catalog without model-generated claims."""

import re

from langchain_core.messages import HumanMessage

from llm.language import ReplyLanguage, prepare_language


PRODUCT_TERMS = {
    "P001": ("tv", "television"),
    "P002": ("ac", "air conditioner"),
    "P003": ("fridge", "refrigerator"),
    "P004": ("headphones", "headphone"),
    "P005": ("iphone", "phone", "phones"),
    "P006": ("washing machine",),
    "P007": ("laptop", "laptops", "लैपटॉप", "ల్యాప్‌టాప్", "ল্যাপটপ", "மடிக்கணினி", "লেপটপ", "लॅपटॉप"),
    "P008": ("microwave",),
    "P009": ("soundbar",),
    "P010": ("router",),
}

COPY = {
    "english": (
        "Demo catalog — mock data, not a live offer.",
        "Mock price", "Demo warranty", "months",
        "These are the only details recorded in the catalog. Further specifications and stock availability are not provided.",
        "I cannot offer an extra discount or place an order in this demo.",
    ),
    "hindi": (
        "डेमो कैटलॉग — यह उदाहरण के लिए बनाया गया डेटा है, वास्तविक ऑफ़र नहीं।",
        "डेमो कीमत", "डेमो वारंटी", "महीने",
        "कैटलॉग में केवल यही जानकारी दर्ज है। अन्य विशेषताओं और स्टॉक की उपलब्धता की जानकारी नहीं दी गई है।",
        "इस डेमो में मैं अतिरिक्त छूट नहीं दे सकता और ऑर्डर नहीं कर सकता।",
    ),
    "telugu": (
        "డెమో కేటలాగ్ — ఇది నమూనా సమాచారం మాత్రమే, నిజమైన ఆఫర్ కాదు.",
        "డెమో ధర", "డెమో వారంటీ", "నెలలు",
        "కేటలాగ్‌లో ఈ వివరాలు మాత్రమే ఉన్నాయి. ఇతర సాంకేతిక వివరాలు మరియు స్టాక్ లభ్యత సమాచారం ఇవ్వలేదు.",
        "ఈ డెమోలో నేను అదనపు తగ్గింపు ఇవ్వలేను లేదా ఆర్డర్ చేయలేను.",
    ),
    "bengali": (
        "ডেমো ক্যাটালগ — এটি নমুনা তথ্য, প্রকৃত অফার নয়।",
        "ডেমো দাম", "ডেমো ওয়ারেন্টি", "মাস",
        "ক্যাটালগে শুধু এই তথ্য রয়েছে। অন্যান্য বৈশিষ্ট্য এবং স্টকের তথ্য দেওয়া নেই।",
        "এই ডেমোতে আমি অতিরিক্ত ছাড় দিতে বা অর্ডার করতে পারি না।",
    ),
    "tamil": (
        "டெமோ பட்டியல் — இது மாதிரித் தகவல் மட்டுமே, உண்மையான சலுகை அல்ல.",
        "டெமோ விலை", "டெமோ உத்தரவாதம்", "மாதங்கள்",
        "பட்டியலில் இந்த விவரங்கள் மட்டுமே உள்ளன. பிற தொழில்நுட்ப விவரங்களும் இருப்புத் தகவலும் வழங்கப்படவில்லை.",
        "இந்த டெமோவில் கூடுதல் தள்ளுபடி வழங்கவோ ஆர்டர் செய்யவோ முடியாது.",
    ),
    "assamese": (
        "ডেমো কেটেলগ — এইটো নমুনা তথ্য, প্ৰকৃত অফাৰ নহয়।",
        "ডেমো মূল্য", "ডেমো ৱাৰেণ্টী", "মাহ",
        "কেটেলগত কেৱল এই তথ্য আছে। অন্য বৈশিষ্ট্য আৰু ষ্টকৰ উপলব্ধতাৰ তথ্য দিয়া হোৱা নাই।",
        "এই ডেমোত মই অতিৰিক্ত ৰেহাই দিব বা অৰ্ডাৰ কৰিব নোৱাৰোঁ।",
    ),
    "marathi": (
        "डेमो कॅटलॉग — ही नमुना माहिती आहे, प्रत्यक्ष ऑफर नाही.",
        "डेमो किंमत", "डेमो वॉरंटी", "महिने",
        "कॅटलॉगमध्ये फक्त हीच माहिती आहे. इतर वैशिष्ट्ये आणि उपलब्ध साठ्याची माहिती दिलेली नाही.",
        "या डेमोमध्ये मी अतिरिक्त सवलत देऊ शकत नाही किंवा ऑर्डर करू शकत नाही.",
    ),
}

FACT_REQUEST = re.compile(
    r"\b(?:price|cost|warranty|specs?|specifications?|details?|features?|stock|available|availability|"
    r"discount|dscound|buy|purchase|show|tell|more|about|batao|bataiye|bataiyein|keemat|kimat)\b"
    r"|कीमत|जानकारी|बताओ|बताइए|ధర|వివరాలు|দাম|তথ্য|விலை|விவரம்|মূল্য|किंमत|माहिती",
    re.IGNORECASE,
)

FOLLOWUP = re.compile(
    r"^\s*(?:please\s+)?(?:tell me more(?: about (?:it|this|that))?|more details|more specifications|"
    r"(?:what is|what about|show me) (?:its|the) (?:price|cost|warranty|specifications|details)|"
    r"(?:mujhe\s+)?iske\s+(?:bare|baare)\s+(?:me|mein)\s+(?:aur\s+)?(?:batao|bataiye)|"
    r"इसके बारे में (?:और )?बताओ)[?.!]*\s*$",
    re.IGNORECASE,
)


def product_ids(text: str, products: list[dict]) -> set[str]:
    explicit = set(re.findall(r"\bp\d{3}\b", text.lower()))
    if explicit:
        return {identifier.upper() for identifier in explicit}
    matches = set()
    for product in products:
        terms = (*PRODUCT_TERMS.get(product["id"], ()), product["name"])
        if any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.IGNORECASE) for term in terms):
            matches.add(product["id"])
    return matches


def catalog_answer(message: str, history: list[dict], language: ReplyLanguage, products: list[dict]) -> str | None:
    if re.search(
        r"\b(?:compare|versus|vs|track|status|cancel|return|repair|broken|error|install|"
        r"recommend|best|better|under|budget|translate|translation|calculate|why|how)\b"
        r"|\b(?:ord|sr|resq)-\d+\b",
        message, re.IGNORECASE,
    ):
        return None
    if not FACT_REQUEST.search(message) and not re.fullmatch(r"\s*p\d{3}\s*[?.!]?\s*", message, re.IGNORECASE):
        return None
    matches = product_ids(message, products)
    if not matches and FOLLOWUP.search(message):
        for item in reversed(history):
            if item.get("role") == "user":
                matches = product_ids(item.get("content", ""), products)
                if matches:
                    break
    if len(matches) != 1:
        return None
    product = next((row for row in products if row["id"] in matches and row.get("is_mock") is True), None)
    if product is None:
        return None
    _, target = prepare_language([HumanMessage(message)], reply_language=language)
    if target not in COPY:
        return None
    heading, price, warranty, months, missing, limitations = COPY[target]
    return (
        f"{heading}\n\n"
        f"**{product['name']} ({product['id']})**\n"
        f"- {price}: {product['price']}\n"
        f"- {warranty}: {product['warranty_months']} {months}\n\n"
        f"{missing}\n\n{limitations}"
    )
