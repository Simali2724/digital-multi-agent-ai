"""Approved, localized application messages.

Every customer-visible string the application itself produces (boundary statements, refusals,
clarifications, handoff prefixes and error texts) lives here so it follows the resolved reply language.
Wording outside English and Hindi should be reviewed by fluent speakers before production use.
"""

LANGUAGES = ("english", "hindi", "telugu", "bengali", "tamil", "assamese", "marathi")

MESSAGES: dict[str, dict[str, str]] = {
    # One brief boundary plus one relevant direction for unrelated programming requests.
    "scope_code": {
        "english": "I can help with Reliance Digital products and support. If you're choosing a laptop for programming, share your budget and requirements.",
        "hindi": "मैं Reliance Digital के उत्पादों और सहायता में मदद कर सकता हूँ। अगर आप प्रोग्रामिंग के लिए लैपटॉप चुन रहे हैं, तो अपना बजट और ज़रूरतें बताइए।",
        "telugu": "నేను Reliance Digital ఉత్పత్తులు మరియు సపోర్ట్‌లో సహాయం చేయగలను. మీరు ప్రోగ్రామింగ్ కోసం ల్యాప్‌టాప్ ఎంచుకుంటున్నట్లయితే, మీ బడ్జెట్ మరియు అవసరాలను తెలియజేయండి.",
        "bengali": "আমি Reliance Digital-এর পণ্য ও সহায়তায় সাহায্য করতে পারি। আপনি প্রোগ্রামিংয়ের জন্য ল্যাপটপ বেছে নিলে আপনার বাজেট ও প্রয়োজনের কথা জানান।",
        "tamil": "நான் Reliance Digital பொருட்கள் மற்றும் ஆதரவில் உதவ முடியும். நிரலாக்கத்திற்கு மடிக்கணினி தேர்ந்தெடுக்கிறீர்கள் என்றால், உங்கள் பட்ஜெட் மற்றும் தேவைகளைப் பகிருங்கள்.",
        "assamese": "মই Reliance Digital-ৰ পণ্য আৰু সহায়ত সহায় কৰিব পাৰোঁ। আপুনি প্ৰগ্ৰেমিঙৰ বাবে লেপটপ বাছনি কৰিলে আপোনাৰ বজেট আৰু প্ৰয়োজনীয়তা জনাওক।",
        "marathi": "मी Reliance Digital ची उत्पादने आणि सपोर्ट यांमध्ये मदत करू शकतो. तुम्ही प्रोग्रामिंगसाठी लॅपटॉप निवडत असाल, तर तुमचे बजेट आणि गरजा सांगा.",
    },
    "scope_general": {
        "english": "I can help with Reliance Digital products and support. Tell me what you're shopping for or what needs support.",
        "hindi": "मैं Reliance Digital के उत्पादों और सहायता में मदद कर सकता हूँ। बताइए आप क्या खरीदना चाहते हैं या किस चीज़ में सहायता चाहिए।",
        "telugu": "నేను Reliance Digital ఉత్పత్తులు మరియు సపోర్ట్‌లో సహాయం చేయగలను. మీరు ఏమి కొనాలనుకుంటున్నారో లేదా దేనిలో సహాయం కావాలో చెప్పండి.",
        "bengali": "আমি Reliance Digital-এর পণ্য ও সহায়তায় সাহায্য করতে পারি। আপনি কী কিনতে চান বা কোন বিষয়ে সহায়তা দরকার তা জানান।",
        "tamil": "நான் Reliance Digital பொருட்கள் மற்றும் ஆதரவில் உதவ முடியும். நீங்கள் என்ன வாங்க விரும்புகிறீர்கள் அல்லது எதில் உதவி வேண்டும் என்று சொல்லுங்கள்.",
        "assamese": "মই Reliance Digital-ৰ পণ্য আৰু সহায়ত সহায় কৰিব পাৰোঁ। আপুনি কি কিনিব বিচাৰে বা কিহত সহায় লাগে জনাওক।",
        "marathi": "मी Reliance Digital ची उत्पादने आणि सपोर्ट यांमध्ये मदत करू शकतो. तुम्हाला काय खरेदी करायचे आहे किंवा कशात मदत हवी आहे ते सांगा.",
    },
    # Request to reveal instructions, credentials or other protected material.
    "disclosure": {
        "english": "I can't share internal instructions or private details. I can help with Reliance Digital products and support.",
        "hindi": "मैं आंतरिक निर्देश या निजी जानकारी साझा नहीं कर सकता। मैं Reliance Digital के उत्पादों और सहायता में मदद कर सकता हूँ।",
        "telugu": "నేను అంతర్గత సూచనలు లేదా ప్రైవేట్ వివరాలను పంచుకోలేను. నేను Reliance Digital ఉత్పత్తులు మరియు సపోర్ట్‌లో సహాయం చేయగలను.",
        "bengali": "আমি অভ্যন্তরীণ নির্দেশনা বা ব্যক্তিগত তথ্য শেয়ার করতে পারি না। আমি Reliance Digital-এর পণ্য ও সহায়তায় সাহায্য করতে পারি।",
        "tamil": "உள் வழிமுறைகள் அல்லது தனிப்பட்ட விவரங்களை என்னால் பகிர முடியாது. நான் Reliance Digital பொருட்கள் மற்றும் ஆதரவில் உதவ முடியும்.",
        "assamese": "মই আভ্যন্তৰীণ নিৰ্দেশনা বা ব্যক্তিগত তথ্য শ্বেয়াৰ কৰিব নোৱাৰোঁ। মই Reliance Digital-ৰ পণ্য আৰু সহায়ত সহায় কৰিব পাৰোঁ।",
        "marathi": "मी अंतर्गत सूचना किंवा खाजगी माहिती शेअर करू शकत नाही. मी Reliance Digital ची उत्पादने आणि सपोर्ट यांमध्ये मदत करू शकतो.",
    },
    # Pure instruction-override attempt (ignore rules, admin mode, role spoofing).
    "injection": {
        "english": "I can't follow that request. I can help with Reliance Digital products and support.",
        "hindi": "मैं उस अनुरोध का पालन नहीं कर सकता। मैं Reliance Digital के उत्पादों और सहायता में मदद कर सकता हूँ।",
        "telugu": "నేను ఆ అభ్యర్థనను పాటించలేను. నేను Reliance Digital ఉత్పత్తులు మరియు సపోర్ట్‌లో సహాయం చేయగలను.",
        "bengali": "আমি সেই অনুরোধ মানতে পারি না। আমি Reliance Digital-এর পণ্য ও সহায়তায় সাহায্য করতে পারি।",
        "tamil": "அந்தக் கோரிக்கையை என்னால் பின்பற்ற முடியாது. நான் Reliance Digital பொருட்கள் மற்றும் ஆதரவில் உதவ முடியும்.",
        "assamese": "মই সেই অনুৰোধ পালন কৰিব নোৱাৰোঁ। মই Reliance Digital-ৰ পণ্য আৰু সহায়ত সহায় কৰিব পাৰোঁ।",
        "marathi": "मी ती विनंती पाळू शकत नाही. मी Reliance Digital ची उत्पादने आणि सपोर्ट यांमध्ये मदत करू शकतो.",
    },
    # Prefix when only the legitimate part of a mixed request is answered.
    "prefix_scope": {
        "english": "I can't help with the unrelated part of your request. Here is help with the Reliance Digital part:",
        "hindi": "आपके अनुरोध के असंबंधित हिस्से में मैं मदद नहीं कर सकता। Reliance Digital से जुड़े हिस्से के लिए जानकारी यह है:",
        "telugu": "మీ అభ్యర్థనలో సంబంధం లేని భాగంలో నేను సహాయం చేయలేను. Reliance Digital కు సంబంధించిన భాగానికి సమాధానం ఇది:",
        "bengali": "আপনার অনুরোধের অপ্রাসঙ্গিক অংশে আমি সাহায্য করতে পারি না। Reliance Digital সংক্রান্ত অংশের উত্তর এখানে:",
        "tamil": "உங்கள் கோரிக்கையின் தொடர்பில்லாத பகுதியில் என்னால் உதவ முடியாது. Reliance Digital தொடர்பான பகுதிக்கான பதில் இதோ:",
        "assamese": "আপোনাৰ অনুৰোধৰ অসম্পৰ্কিত অংশত মই সহায় কৰিব নোৱাৰোঁ। Reliance Digital সম্পৰ্কীয় অংশৰ উত্তৰ তলত:",
        "marathi": "तुमच्या विनंतीतील असंबंधित भागात मी मदत करू शकत नाही. Reliance Digital शी संबंधित भागासाठी उत्तर हे आहे:",
    },
    "prefix_internal": {
        "english": "I can't follow or share internal instructions. Here is help with your product question:",
        "hindi": "मैं आंतरिक निर्देशों का पालन या उन्हें साझा नहीं कर सकता। आपके उत्पाद संबंधी प्रश्न का उत्तर यह है:",
        "telugu": "నేను అంతర్గత సూచనలను పాటించలేను లేదా పంచుకోలేను. మీ ఉత్పత్తి ప్రశ్నకు సమాధానం ఇది:",
        "bengali": "আমি অভ্যন্তরীণ নির্দেশনা মানতে বা শেয়ার করতে পারি না। আপনার পণ্য সংক্রান্ত প্রশ্নের উত্তর এখানে:",
        "tamil": "உள் வழிமுறைகளை என்னால் பின்பற்றவோ பகிரவோ முடியாது. உங்கள் பொருள் தொடர்பான கேள்விக்கான பதில் இதோ:",
        "assamese": "মই আভ্যন্তৰীণ নিৰ্দেশনা পালন বা শ্বেয়াৰ কৰিব নোৱাৰোঁ। আপোনাৰ পণ্য সম্পৰ্কীয় প্ৰশ্নৰ উত্তৰ তলত:",
        "marathi": "मी अंतर्गत सूचनांचे पालन किंवा त्या शेअर करू शकत नाही. तुमच्या उत्पादनाविषयीच्या प्रश्नाचे उत्तर हे आहे:",
    },
    # Uncertain classification: ask instead of guessing.
    "clarify_programming": {
        "english": "Do you want help choosing a laptop or device for programming, or something else? I can only help with Reliance Digital products and support.",
        "hindi": "क्या आप प्रोग्रामिंग के लिए लैपटॉप या डिवाइस चुनने में मदद चाहते हैं, या कुछ और? मैं केवल Reliance Digital के उत्पादों और सहायता में मदद कर सकता हूँ।",
        "telugu": "మీరు ప్రోగ్రామింగ్ కోసం ల్యాప్‌టాప్ లేదా పరికరం ఎంచుకోవడంలో సహాయం కోరుతున్నారా, లేక మరేదైనా? నేను Reliance Digital ఉత్పత్తులు మరియు సపోర్ట్‌లో మాత్రమే సహాయం చేయగలను.",
        "bengali": "আপনি কি প্রোগ্রামিংয়ের জন্য ল্যাপটপ বা ডিভাইস বেছে নিতে সাহায্য চান, নাকি অন্য কিছু? আমি শুধু Reliance Digital-এর পণ্য ও সহায়তায় সাহায্য করতে পারি।",
        "tamil": "நிரலாக்கத்திற்கு மடிக்கணினி அல்லது சாதனம் தேர்ந்தெடுக்க உதவி வேண்டுமா, அல்லது வேறு ஏதாவதா? நான் Reliance Digital பொருட்கள் மற்றும் ஆதரவில் மட்டுமே உதவ முடியும்.",
        "assamese": "আপুনি প্ৰগ্ৰেমিঙৰ বাবে লেপটপ বা ডিভাইচ বাছনি কৰাত সহায় বিচাৰে নেকি, নে অন্য কিবা? মই কেৱল Reliance Digital-ৰ পণ্য আৰু সহায়ত সহায় কৰিব পাৰোঁ।",
        "marathi": "तुम्हाला प्रोग्रामिंगसाठी लॅपटॉप किंवा डिव्हाइस निवडण्यात मदत हवी आहे का, की आणखी काही? मी फक्त Reliance Digital ची उत्पादने आणि सपोर्ट यांमध्ये मदत करू शकतो.",
    },
    # An answer quoted an amount that is not in the demo data or derivable from the customer's own numbers.
    "price_unverified": {
        "english": "I can only quote prices from the demo catalog, and I couldn't confirm that amount. Please ask about a specific product to see its mock price.",
        "hindi": "मैं केवल डेमो कैटलॉग की कीमतें बता सकता हूँ और उस राशि की पुष्टि नहीं कर सका। किसी विशेष उत्पाद की डेमो कीमत देखने के लिए उसके बारे में पूछिए।",
        "telugu": "నేను డెమో కేటలాగ్‌లోని ధరలను మాత్రమే చెప్పగలను, ఆ మొత్తాన్ని నిర్ధారించలేకపోయాను. ఒక నిర్దిష్ట ఉత్పత్తి డెమో ధర చూడటానికి దాని గురించి అడగండి.",
        "bengali": "আমি শুধু ডেমো ক্যাটালগের দাম বলতে পারি এবং সেই অঙ্কটি নিশ্চিত করতে পারিনি। কোনো নির্দিষ্ট পণ্যের ডেমো দাম জানতে তার সম্পর্কে জিজ্ঞাসা করুন।",
        "tamil": "நான் டெமோ பட்டியலிலுள்ள விலைகளை மட்டுமே சொல்ல முடியும், அந்தத் தொகையை உறுதிப்படுத்த முடியவில்லை. ஒரு குறிப்பிட்ட பொருளின் டெமோ விலையை அறிய அதைப் பற்றி கேளுங்கள்.",
        "assamese": "মই কেৱল ডেমো কেটেলগৰ দাম ক'ব পাৰোঁ আৰু সেই পৰিমাণ নিশ্চিত কৰিব নোৱাৰিলোঁ। কোনো নিৰ্দিষ্ট পণ্যৰ ডেমো দাম জানিবলৈ তাৰ বিষয়ে সোধক।",
        "marathi": "मी फक्त डेमो कॅटलॉगमधील किमती सांगू शकतो आणि ती रक्कम खात्रीशीर करू शकलो नाही. विशिष्ट उत्पादनाची डेमो किंमत पाहण्यासाठी त्याबद्दल विचारा.",
    },
    # Application-generated error texts, one per failure class.
    "error_busy": {
        "english": "The assistant is busy right now. Please try again in a minute.",
        "hindi": "सहायक अभी व्यस्त है। कृपया एक मिनट बाद फिर कोशिश करें।",
        "telugu": "అసిస్టెంట్ ఇప్పుడు బిజీగా ఉంది. దయచేసి ఒక నిమిషం తర్వాత మళ్లీ ప్రయత్నించండి.",
        "bengali": "সহায়ক এখন ব্যস্ত আছে। অনুগ্রহ করে এক মিনিট পরে আবার চেষ্টা করুন।",
        "tamil": "உதவியாளர் இப்போது பிஸியாக உள்ளது. ஒரு நிமிடம் கழித்து மீண்டும் முயற்சிக்கவும்.",
        "assamese": "সহায়ক এতিয়া ব্যস্ত আছে। অনুগ্ৰহ কৰি এক মিনিটৰ পিছত আকৌ চেষ্টা কৰক।",
        "marathi": "सहाय्यक सध्या व्यस्त आहे. कृपया एका मिनिटाने पुन्हा प्रयत्न करा.",
    },
    "error_timeout": {
        "english": "The assistant took too long to reply. Please try again.",
        "hindi": "सहायक ने जवाब देने में बहुत समय लिया। कृपया फिर कोशिश करें।",
        "telugu": "అసిస్టెంట్ సమాధానం ఇవ్వడానికి చాలా సమయం తీసుకుంది. దయచేసి మళ్లీ ప్రయత్నించండి.",
        "bengali": "সহায়ক উত্তর দিতে অনেক সময় নিয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
        "tamil": "உதவியாளர் பதிலளிக்க அதிக நேரம் எடுத்தது. மீண்டும் முயற்சிக்கவும்.",
        "assamese": "সহায়কে উত্তৰ দিবলৈ বহুত সময় ললে। অনুগ্ৰহ কৰি আকৌ চেষ্টা কৰক।",
        "marathi": "सहाय्यकाने उत्तर देण्यास खूप वेळ घेतला. कृपया पुन्हा प्रयत्न करा.",
    },
    "error_network": {
        "english": "The assistant service could not be reached. Please try again shortly.",
        "hindi": "सहायक सेवा से संपर्क नहीं हो सका। कृपया थोड़ी देर बाद फिर कोशिश करें।",
        "telugu": "అసిస్టెంట్ సేవను చేరుకోలేకపోయాం. దయచేసి కొద్దిసేపటి తర్వాత మళ్లీ ప్రయత్నించండి.",
        "bengali": "সহায়ক পরিষেবায় যোগাযোগ করা যায়নি। অনুগ্রহ করে কিছুক্ষণ পরে আবার চেষ্টা করুন।",
        "tamil": "உதவியாளர் சேவையை அணுக முடியவில்லை. சிறிது நேரம் கழித்து மீண்டும் முயற்சிக்கவும்.",
        "assamese": "সহায়ক সেৱালৈ সংযোগ কৰিব পৰা নগ'ল। অনুগ্ৰহ কৰি অলপ পিছত আকৌ চেষ্টা কৰক।",
        "marathi": "सहाय्यक सेवेशी संपर्क होऊ शकला नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.",
    },
    "error_config": {
        "english": "The assistant is not configured correctly right now. Please contact support.",
        "hindi": "सहायक अभी सही तरह से कॉन्फ़िगर नहीं है। कृपया सहायता से संपर्क करें।",
        "telugu": "అసిస్టెంట్ ప్రస్తుతం సరిగ్గా కాన్ఫిగర్ చేయబడలేదు. దయచేసి సపోర్ట్‌ను సంప్రదించండి.",
        "bengali": "সহায়ক এখন সঠিকভাবে কনফিগার করা নেই। অনুগ্রহ করে সহায়তা দলের সঙ্গে যোগাযোগ করুন।",
        "tamil": "உதவியாளர் தற்போது சரியாக கட்டமைக்கப்படவில்லை. ஆதரவைத் தொடர்புகொள்ளவும்.",
        "assamese": "সহায়ক এতিয়া শুদ্ধকৈ কনফিগাৰ কৰা হোৱা নাই। অনুগ্ৰহ কৰি সহায়ৰ সৈতে যোগাযোগ কৰক।",
        "marathi": "सहाय्यक सध्या योग्यरित्या कॉन्फिगर केलेले नाही. कृपया सपोर्टशी संपर्क साधा.",
    },
    "error_invalid": {
        "english": "That request could not be processed. Please rephrase it and try again.",
        "hindi": "यह अनुरोध संसाधित नहीं हो सका। कृपया इसे दूसरे शब्दों में लिखकर फिर कोशिश करें।",
        "telugu": "ఆ అభ్యర్థనను ప్రాసెస్ చేయలేకపోయాం. దయచేసి వేరే విధంగా రాసి మళ్లీ ప్రయత్నించండి.",
        "bengali": "অনুরোধটি প্রক্রিয়া করা যায়নি। অনুগ্রহ করে অন্যভাবে লিখে আবার চেষ্টা করুন।",
        "tamil": "அந்தக் கோரிக்கையை செயலாக்க முடியவில்லை. வேறு வார்த்தைகளில் எழுதி மீண்டும் முயற்சிக்கவும்.",
        "assamese": "অনুৰোধটো প্ৰক্ৰিয়া কৰিব পৰা নগ'ল। অনুগ্ৰহ কৰি অন্যধৰণে লিখি আকৌ চেষ্টা কৰক।",
        "marathi": "ती विनंती प्रक्रिया करता आली नाही. कृपया वेगळ्या शब्दांत लिहून पुन्हा प्रयत्न करा.",
    },
    "error_generic": {
        "english": "The assistant could not answer right now. Please try again.",
        "hindi": "सहायक अभी उत्तर नहीं दे सका। कृपया फिर कोशिश करें।",
        "telugu": "అసిస్టెంట్ ఇప్పుడు సమాధానం ఇవ్వలేకపోయింది. దయచేసి మళ్లీ ప్రయత్నించండి.",
        "bengali": "সহায়ক এখন উত্তর দিতে পারেনি। অনুগ্রহ করে আবার চেষ্টা করুন।",
        "tamil": "உதவியாளரால் இப்போது பதிலளிக்க முடியவில்லை. மீண்டும் முயற்சிக்கவும்.",
        "assamese": "সহায়কে এতিয়া উত্তৰ দিব নোৱাৰিলে। অনুগ্ৰহ কৰি আকৌ চেষ্টা কৰক।",
        "marathi": "सहाय्यक सध्या उत्तर देऊ शकले नाही. कृपया पुन्हा प्रयत्न करा.",
    },
}

REFERENCE_LABEL = {
    "english": "Reference",
    "hindi": "संदर्भ",
    "telugu": "రిఫరెన్స్",
    "bengali": "রেফারেন্স",
    "tamil": "குறிப்பு எண்",
    "assamese": "ৰেফাৰেন্স",
    "marathi": "संदर्भ",
}

# Failure code (see llm.factory.failure_code) -> message key. Unknown codes use the generic text.
ERROR_KEYS = {
    "rate_limit": "error_busy",
    "temporary_connection": "error_network",
    "timeout": "error_timeout",
    "authentication": "error_config",
    "not_configured": "error_config",
    "invalid_request": "error_invalid",
}


def message(key: str, language: str) -> str:
    texts = MESSAGES[key]
    return texts.get(language, texts["english"])


def error_message(code: str, language: str, reference: str | None = None) -> str:
    text = message(ERROR_KEYS.get(code, "error_generic"), language)
    if reference:
        text += f" ({REFERENCE_LABEL.get(language, REFERENCE_LABEL['english'])}: {reference})"
    return text
