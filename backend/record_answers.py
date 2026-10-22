"""Order and service-ticket lookups answered straight from the mock records, with no model involved.

A found record reports only the stored status, issue, product and amount (never the customer name). An ID that
does not exist gets an explicit "no record" reply, so status and delivery details can never be invented.
Status values are shown as stored; they are data, not translated text. Wording outside English and Hindi
should be reviewed by fluent speakers.
"""

import re

COPY = {
    # heading, order, ticket, status, product, mock amount, issue, limits, not found
    "english": (
        "Demo record — mock data, not a real customer order or ticket.",
        "Order", "Ticket", "Status", "Product", "Mock amount", "Issue",
        "Delivery dates, tracking and other updates are not recorded in this demo, and I cannot change or cancel anything.",
        "No record with this ID exists in the demo data, so I cannot give a status. Please check the ID.",
    ),
    "hindi": (
        "डेमो रिकॉर्ड — यह उदाहरण डेटा है, किसी वास्तविक ग्राहक का ऑर्डर या टिकट नहीं।",
        "ऑर्डर", "टिकट", "स्थिति", "उत्पाद", "डेमो राशि", "समस्या",
        "इस डेमो में डिलीवरी की तारीख, ट्रैकिंग और अन्य अपडेट दर्ज नहीं हैं, और मैं कुछ भी बदल या रद्द नहीं कर सकता।",
        "इस आईडी का कोई रिकॉर्ड डेमो डेटा में नहीं है, इसलिए मैं स्थिति नहीं बता सकता। कृपया आईडी जाँच लें।",
    ),
    "telugu": (
        "డెమో రికార్డ్ — ఇది నమూనా డేటా, నిజమైన కస్టమర్ ఆర్డర్ లేదా టికెట్ కాదు.",
        "ఆర్డర్", "టికెట్", "స్థితి", "ఉత్పత్తి", "డెమో మొత్తం", "సమస్య",
        "ఈ డెమోలో డెలివరీ తేదీలు, ట్రాకింగ్ మరియు ఇతర అప్‌డేట్‌లు నమోదు కాలేదు, మరియు నేను ఏదీ మార్చలేను లేదా రద్దు చేయలేను.",
        "ఈ ID తో ఎలాంటి రికార్డ్ డెమో డేటాలో లేదు, కాబట్టి నేను స్థితిని చెప్పలేను. దయచేసి IDని సరిచూడండి.",
    ),
    "bengali": (
        "ডেমো রেকর্ড — এটি নমুনা তথ্য, প্রকৃত গ্রাহকের অর্ডার বা টিকিট নয়।",
        "অর্ডার", "টিকিট", "অবস্থা", "পণ্য", "ডেমো পরিমাণ", "সমস্যা",
        "এই ডেমোতে ডেলিভারির তারিখ, ট্র্যাকিং ও অন্যান্য আপডেট নথিভুক্ত নেই, এবং আমি কিছু পরিবর্তন বা বাতিল করতে পারি না।",
        "এই আইডির কোনো রেকর্ড ডেমো ডেটায় নেই, তাই আমি অবস্থা জানাতে পারছি না। অনুগ্রহ করে আইডি যাচাই করুন।",
    ),
    "tamil": (
        "டெமோ பதிவு — இது மாதிரித் தரவு, உண்மையான வாடிக்கையாளர் ஆர்டர் அல்லது டிக்கெட் அல்ல.",
        "ஆர்டர்", "டிக்கெட்", "நிலை", "பொருள்", "டெமோ தொகை", "சிக்கல்",
        "இந்த டெமோவில் டெலிவரி தேதிகள், கண்காணிப்பு மற்றும் பிற புதுப்பிப்புகள் பதிவு செய்யப்படவில்லை, மேலும் என்னால் எதையும் மாற்றவோ ரத்து செய்யவோ முடியாது.",
        "இந்த ID க்கான பதிவு டெமோ தரவில் இல்லை, எனவே நிலையைச் சொல்ல முடியாது. தயவுசெய்து IDஐச் சரிபார்க்கவும்.",
    ),
    "assamese": (
        "ডেমো ৰেকৰ্ড — এইটো নমুনা তথ্য, প্ৰকৃত গ্ৰাহকৰ অৰ্ডাৰ বা টিকট নহয়।",
        "অৰ্ডাৰ", "টিকট", "অৱস্থা", "পণ্য", "ডেমো পৰিমাণ", "সমস্যা",
        "এই ডেমোত ডেলিভাৰীৰ তাৰিখ, ট্ৰেকিং আৰু অন্য আপডেট নথিভুক্ত নাই, আৰু মই একো সলনি বা বাতিল কৰিব নোৱাৰোঁ।",
        "এই আইডিৰ কোনো ৰেকৰ্ড ডেমো তথ্যত নাই, গতিকে মই অৱস্থা ক'ব নোৱাৰোঁ। অনুগ্ৰহ কৰি আইডি পৰীক্ষা কৰক।",
    ),
    "marathi": (
        "डेमो रेकॉर्ड — ही नमुना माहिती आहे, प्रत्यक्ष ग्राहकाची ऑर्डर किंवा तिकीट नाही.",
        "ऑर्डर", "तिकीट", "स्थिती", "उत्पादन", "डेमो रक्कम", "समस्या",
        "या डेमोमध्ये डिलिव्हरीच्या तारखा, ट्रॅकिंग आणि इतर अपडेट नोंदलेले नाहीत, आणि मी काहीही बदलू किंवा रद्द करू शकत नाही.",
        "या आयडीची कोणतीही नोंद डेमो डेटामध्ये नाही, त्यामुळे मी स्थिती सांगू शकत नाही. कृपया आयडी तपासा.",
    ),
}

ORDER_ID = re.compile(r"\b(?:ord-\d+|rd\d+)\b", re.IGNORECASE)
TICKET_ID = re.compile(r"\b(?:sr|resq)-\d+\b", re.IGNORECASE)
ACTION_OR_COMPARISON = re.compile(
    r"\b(?:cancel|return|refund|replace|modify|change|update|edit|reschedule|escalate|complain|compare|versus|vs|"
    r"repair|fix|why|how)\b",
    re.IGNORECASE,
)


def record_answer(message: str, language: str, products: list[dict], orders: list[dict], tickets: list[dict]) -> str | None:
    if ACTION_OR_COMPARISON.search(message):
        return None
    order_ids = {match.upper() for match in ORDER_ID.findall(message)}
    ticket_ids = {match.upper() for match in TICKET_ID.findall(message)}
    if len(order_ids) + len(ticket_ids) != 1 or language not in COPY:
        return None
    heading, order, ticket, status, product, amount, issue, limits, not_found = COPY[language]
    is_order = bool(order_ids)
    identifier = next(iter(order_ids or ticket_ids))
    rows = orders if is_order else tickets
    record = next((row for row in rows if row["id"].upper() == identifier and row.get("is_mock") is True), None)
    label = order if is_order else ticket
    if record is None:
        return f"{heading}\n\n**{label} {identifier}**\n\n{not_found}"
    item = next((row for row in products if row["id"] == record["product_id"]), None)
    lines = [f"- {status}: {record['status']}"]
    if item is not None:
        lines.append(f"- {product}: {item['name']} ({item['id']})")
    if is_order and record.get("amount"):
        lines.append(f"- {amount}: {record['amount']}")
    if not is_order and record.get("issue"):
        lines.append(f"- {issue}: {record['issue']}")
    return f"{heading}\n\n**{label} {record['id']}**\n" + "\n".join(lines) + f"\n\n{limits}"
