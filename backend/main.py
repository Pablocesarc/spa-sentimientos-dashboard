from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from deep_translator import GoogleTranslator
import joblib
import os
import re
import numpy as np
from collections import Counter


MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelo_sentimientos_pet_groomers.pkl")

app = FastAPI(
    title="API de Análisis de Sentimientos - Spa de Mascotas",
    description="Predice polaridad, emoción aproximada, keywords en español y datos para dashboard.",
    version="2.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"No se encontró el modelo '{MODEL_PATH}'. "
        "Copia modelo_sentimientos_pet_groomers.pkl dentro de la carpeta backend."
    )

modelo = joblib.load(MODEL_PATH)


class SentimentRequest(BaseModel):
    text: str
    translate_to_english: bool = True


class BatchSentimentRequest(BaseModel):
    texts: list[str]
    translate_to_english: bool = True


SPANISH_STOPWORDS = {
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con",
    "contra", "cual", "cuando", "de", "del", "desde", "donde", "durante",
    "e", "el", "ella", "ellas", "ellos", "en", "entre", "era", "erais",
    "eran", "eras", "eres", "es", "esa", "esas", "ese", "eso", "esos",
    "esta", "estaba", "estaban", "estado", "estais", "estamos", "estan",
    "estar", "estará", "estas", "este", "esto", "estos", "estoy", "fue",
    "fueron", "fui", "fuimos", "ha", "haber", "habia", "hacia", "han",
    "hasta", "hay", "he", "hemos", "la", "las", "le", "les", "lo", "los",
    "me", "mi", "mis", "mucho", "muchos", "muy", "más", "mas", "nada",
    "ni", "nos", "nosotros", "o", "otra", "otras", "otro", "otros", "para",
    "pero", "poco", "por", "porque", "que", "se", "sea", "ser", "si", "sí",
    "sin", "sobre", "son", "su", "sus", "tambien", "también", "te", "tiene",
    "tienen", "todo", "todos", "tu", "tus", "un", "una", "unas", "uno",
    "unos", "y", "ya", "yo"
}

# Se conservan negaciones: son importantes para sentimientos.
NEGATIONS_ES = {"no", "nunca", "jamás", "tampoco"}


EMOTION_LEXICON_ES = {
    "Alegría": [
        "excelente", "feliz", "contento", "contenta", "encantado", "encantada",
        "maravilloso", "maravillosa", "perfecto", "perfecta", "genial",
        "increíble", "recomiendo", "amable", "bonito", "hermoso", "hermosa",
        "limpio", "limpia", "satisfecho", "satisfecha", "agradable", "fantástico",
        "fantástica", "amor", "cariño", "bien", "bueno", "buena", "mejor"
    ],
    "Tristeza": [
        "triste", "decepcionado", "decepcionada", "decepción", "lamentable",
        "pena", "dolor", "mal", "malo", "mala", "pésimo", "pésima",
        "terrible", "lastimado", "lastimada", "descuidado", "descuidada",
        "abandonado", "abandonada", "perdido", "perdida"
    ],
    "Enojo": [
        "enojado", "enojada", "molesto", "molesta", "furioso", "furiosa",
        "horrible", "grosero", "grosera", "maleducado", "maleducada",
        "peor", "nunca", "queja", "reclamo", "estafa", "caro", "abusivo",
        "abusiva", "irresponsable", "maltrato", "maltrataron", "ignoraron",
        "impuntual", "tardaron", "tarde"
    ],
    "Miedo": [
        "miedo", "preocupado", "preocupada", "riesgo", "peligro", "peligroso",
        "peligrosa", "asustado", "asustada", "nervioso", "nerviosa",
        "inseguro", "insegura", "emergencia", "somnoliento", "somnolienta",
        "adormecido", "adormecida", "decaído", "decaída", "irritado", "irritada",
        "hinchado", "hinchada", "herido", "herida", "vomitó", "vomito"
    ],
    "Confianza": [
        "confianza", "confiable", "profesional", "profesionales", "seguro",
        "segura", "cuidado", "cuidadoso", "cuidadosa", "experto", "experta",
        "responsable", "atento", "atenta", "calidad", "puntual", "recomendado",
        "recomendada"
    ],
    "Asco": [
        "sucio", "sucia", "apestoso", "apestosa", "olor", "asqueroso",
        "asquerosa", "higiene", "pulgas", "infectado", "infectada"
    ],
    "Sorpresa": [
        "sorpresa", "sorprendido", "sorprendida", "inesperado", "inesperada",
        "wow", "impresionante", "sorprendentemente"
    ]
}

EMOTION_LEXICON_EN = {
    "Alegría": [
        "excellent", "happy", "amazing", "wonderful", "perfect", "great",
        "awesome", "fantastic", "love", "lovely", "recommend", "friendly",
        "clean", "beautiful", "satisfied", "nice", "best", "good"
    ],
    "Tristeza": [
        "sad", "disappointed", "disappointment", "poor", "bad", "terrible",
        "awful", "hurt", "pain", "neglected", "lost", "unhappy"
    ],
    "Enojo": [
        "angry", "mad", "upset", "furious", "horrible", "rude", "worst",
        "never", "complaint", "scam", "expensive", "irresponsible",
        "ignored", "late", "abuse", "abusive"
    ],
    "Miedo": [
        "fear", "afraid", "worried", "risk", "danger", "dangerous",
        "scared", "nervous", "unsafe", "emergency"
    ],
    "Confianza": [
        "trust", "reliable", "professional", "safe", "care", "careful",
        "expert", "responsible", "attentive", "quality", "punctual"
    ],
    "Asco": [
        "dirty", "smelly", "smell", "disgusting", "hygiene", "fleas",
        "infected", "filthy"
    ],
    "Sorpresa": [
        "surprise", "surprised", "unexpected", "wow", "impressive",
        "surprisingly"
    ]
}



NEUTRAL_PATTERNS_ES = [
    r"\bnormal\b",
    r"\bregular\b",
    r"\baceptable\b",
    r"\bpasable\b",
    r"\bmas o menos\b",
    r"\bm[aá]s o menos\b",
    r"\bmeh\b",
    r"\bok\b",
    r"\bmejorable\b",
    r"\bpuede mejorar\b",
    r"\bpodria mejorar\b",
    r"\bpodr[ií]a mejorar\b",
    r"\bpodria ser mejor\b",
    r"\bpodr[ií]a ser mejor\b",
    r"\bno fue lo que esperaba\b",
    r"\bno era lo que esperaba\b",
    r"\bno es lo que esperaba\b",
    r"\besperaba algo mejor\b",
    r"\besperaba algo mucho mejor\b",
    r"\besperaba mucho mejor\b",
    r"\besperaba mas\b",
    r"\besperaba m[aá]s\b",
    r"\besperaba mejor\b",
    r"\bpor\s+[a-z0-9\s]{0,20}\s+esperaba\b",
]

NEUTRAL_PATTERNS_EN = [
    r"\bneutral\b",
    r"\bnormal\b",
    r"\bregular\b",
    r"\baverage\b",
    r"\bok\b",
    r"\bmeh\b",
    r"\bcould be better\b",
    r"\bcan improve\b",
    r"\bexpected better\b",
    r"\bexpected something better\b",
    r"\bexpected something much better\b",
    r"\bnot what i expected\b",
]

STRONG_NEGATIVE_PATTERNS_ES = [
    r"\bp[eé]simo\b", r"\bp[eé]sima\b", r"\bterrible\b", r"\bhorrible\b",
    r"\bmaltrato\b", r"\bestafa\b", r"\bno recomiendo\b", r"\bnunca volver[ií]a\b",
    r"\birresponsable\b", r"\babusivo\b", r"\babusiva\b", r"\bmalo\b", r"\bmala\b",
    r"\bsomnoliento\b", r"\bsomnolienta\b", r"\badormecido\b", r"\badormecida\b",
    r"\bdecaido\b", r"\bdecaida\b", r"\birritado\b", r"\birritada\b",
    r"\bhinchado\b", r"\bhinchada\b", r"\bherido\b", r"\bherida\b",
    r"\bvomito\b", r"\bvomito\b", r"\bdolor\b",
]

STRONG_NEGATIVE_PATTERNS_EN = [
    r"\bawful\b", r"\bterrible\b", r"\bhorrible\b", r"\bworst\b", r"\bscam\b",
    r"\babuse\b", r"\babusive\b", r"\bdo not recommend\b", r"\bnever again\b",
    r"\bbad\b", r"\bpoor\b",
]

STRONG_POSITIVE_PATTERNS_ES = [
    r"\bexcelente\b", r"\bperfecto\b", r"\bperfecta\b", r"\bgenial\b",
    r"\bincre[ií]ble\b", r"\bmaravilloso\b", r"\bmaravillosa\b",
    r"\bme encant[oó]\b", r"\brecomiendo\b", r"\bmuy bueno\b", r"\bmuy buena\b",
]

STRONG_POSITIVE_PATTERNS_EN = [
    r"\bexcellent\b", r"\bperfect\b", r"\bgreat\b", r"\bamazing\b", r"\bwonderful\b",
    r"\bawesome\b", r"\bfantastic\b", r"\blove\b", r"\brecommend\b", r"\bvery good\b",
]

NEGATIVE_PATTERNS_ES = [
    r"\bmal\b", r"\bmalo\b", r"\bmala\b", r"\bcaro\b", r"\bcara\b", r"\btarde\b",
    r"\bdemora\b", r"\bdemoraron\b", r"\bmolesto\b", r"\bmolesta\b",
    r"\bdecepcionado\b", r"\bdecepcionada\b", r"\btriste\b", r"\bqueja\b",
    r"\breclamo\b", r"\bsucio\b", r"\bsucia\b", r"\bimpuntual\b",
]

NEGATIVE_PATTERNS_EN = [
    r"\bbad\b", r"\bpoor\b", r"\bexpensive\b", r"\blate\b", r"\bdelay\b", r"\bupset\b",
    r"\bdisappointed\b", r"\bsad\b", r"\bcomplaint\b", r"\bdirty\b", r"\bunpunctual\b",
]

POSITIVE_PATTERNS_ES = [
    r"\bbien\b", r"\bbueno\b", r"\bbuena\b", r"\bbonito\b", r"\bbonita\b",
    r"\bamable\b", r"\blimpio\b", r"\blimpia\b", r"\bprofesional\b",
    r"\bconfiable\b", r"\batento\b", r"\batenta\b", r"\bcalidad\b",
]

POSITIVE_PATTERNS_EN = [
    r"\bgood\b", r"\bnice\b", r"\bfriendly\b", r"\bclean\b", r"\bprofessional\b",
    r"\breliable\b", r"\battentive\b", r"\bquality\b",
]


def normalize_for_rules(text: str) -> str:
    """Normalización más estable para reglas: minúsculas, sin tildes y espacios limpios."""
    import unicodedata

    text = str(text).lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_pattern_matches(patterns: list[str], text: str) -> int:
    return sum(1 for pattern in patterns if re.search(pattern, text))


def recalibrate_probabilities(probabilities: dict, corrected_sentiment: str, min_confidence: float = 0.55):
    """
    Ajusta la distribución cuando una regla corrige la predicción.
    No finge 99%; solo hace que la clase corregida sea la más probable y mantiene incertidumbre.
    """
    labels = ["Negativo", "Neutral", "Positivo"]
    probs = {label: float(probabilities.get(label, 0.0)) for label in labels}

    if corrected_sentiment not in probs:
        return probabilities, round(max(probs.values()) if probs else 0.0, 4)

    current_winner = max(probs, key=probs.get)
    if current_winner == corrected_sentiment and probs[corrected_sentiment] >= min_confidence:
        return {k: round(v, 4) for k, v in probs.items()}, round(probs[corrected_sentiment], 4)

    target = max(float(min_confidence), probs[corrected_sentiment], max(probs.values()) + 0.03)
    target = min(target, 0.85)

    other_labels = [label for label in labels if label != corrected_sentiment]
    old_other_total = sum(probs[label] for label in other_labels)
    remaining = max(0.0, 1.0 - target)

    new_probs = {corrected_sentiment: target}

    if old_other_total <= 0:
        share = remaining / len(other_labels)
        for label in other_labels:
            new_probs[label] = share
    else:
        for label in other_labels:
            new_probs[label] = remaining * (probs[label] / old_other_total)

    # Corrige posibles diferencias por redondeo.
    total = sum(new_probs.values())
    if total > 0:
        new_probs = {label: value / total for label, value in new_probs.items()}

    return {label: round(float(new_probs[label]), 4) for label in labels}, round(float(new_probs[corrected_sentiment]), 4)


def apply_sentiment_corrections(original_text: str, text_for_model: str, prediction: str, probabilities: dict):
    """
    Capa híbrida encima del modelo.
    El modelo base viene de reseñas en inglés; por eso frases como
    'esperaba algo mucho mejor' pueden verse falsamente positivas por la palabra 'better'.
    Esta capa corrige casos de baja confianza y frases neutrales/ambiguas en español.
    """
    clean_es = normalize_for_rules(original_text)
    clean_en = normalize_for_rules(text_for_model)

    neutral_hits = count_pattern_matches(NEUTRAL_PATTERNS_ES, clean_es) + count_pattern_matches(NEUTRAL_PATTERNS_EN, clean_en)
    strong_neg_hits = count_pattern_matches(STRONG_NEGATIVE_PATTERNS_ES, clean_es) + count_pattern_matches(STRONG_NEGATIVE_PATTERNS_EN, clean_en)
    strong_pos_hits = count_pattern_matches(STRONG_POSITIVE_PATTERNS_ES, clean_es) + count_pattern_matches(STRONG_POSITIVE_PATTERNS_EN, clean_en)
    neg_hits = strong_neg_hits + count_pattern_matches(NEGATIVE_PATTERNS_ES, clean_es) + count_pattern_matches(NEGATIVE_PATTERNS_EN, clean_en)
    pos_hits = strong_pos_hits + count_pattern_matches(POSITIVE_PATTERNS_ES, clean_es) + count_pattern_matches(POSITIVE_PATTERNS_EN, clean_en)

    corrected = str(prediction)
    reason = "modelo_base"
    original_confidence = max(float(v) for v in probabilities.values()) if probabilities else 0.0
    min_confidence = original_confidence

    # 1) Palabras fuertemente negativas/positivas ganan sobre el modelo.
    # 2) Frases tipo "esperaba algo mucho mejor" son reclamos leves/ambiguos: Neutral.
    # 3) Si el modelo no llega a 55%, se muestra Neutral salvo que exista evidencia fuerte.
    if strong_neg_hits > 0 and strong_neg_hits >= strong_pos_hits:
        corrected = "Negativo"
        reason = "regla_negativa_fuerte"
        min_confidence = 0.70
    elif strong_pos_hits > 0 and strong_pos_hits > strong_neg_hits:
        corrected = "Positivo"
        reason = "regla_positiva_fuerte"
        min_confidence = 0.70
    elif neutral_hits > 0 and strong_neg_hits == 0 and strong_pos_hits == 0:
        corrected = "Neutral"
        reason = "regla_neutral_contextual"
        min_confidence = 0.55
    elif neg_hits >= pos_hits + 2:
        corrected = "Negativo"
        reason = "regla_lexico_negativo"
        min_confidence = 0.62
    elif pos_hits >= neg_hits + 2:
        corrected = "Positivo"
        reason = "regla_lexico_positivo"
        min_confidence = 0.62
    elif original_confidence < 0.55:
        corrected = "Neutral"
        reason = "baja_confianza_modelo"
        min_confidence = 0.55
    elif corrected == "Positivo" and neg_hits > pos_hits and probabilities.get("Positivo", 0) - probabilities.get("Negativo", 0) < 0.20:
        corrected = "Neutral"
        reason = "positivo_debil_con_senales_negativas"
        min_confidence = 0.55
    elif corrected == "Negativo" and pos_hits > neg_hits and probabilities.get("Negativo", 0) - probabilities.get("Positivo", 0) < 0.20:
        corrected = "Neutral"
        reason = "negativo_debil_con_senales_positivas"
        min_confidence = 0.55

    calibrated_probabilities, confidence = recalibrate_probabilities(probabilities, corrected, min_confidence)

    return {
        "sentiment": corrected,
        "confidence": confidence,
        "probabilities": calibrated_probabilities,
        "correction_reason": reason,
        "signals": {
            "neutral_hits": neutral_hits,
            "negative_hits": neg_hits,
            "positive_hits": pos_hits,
            "original_prediction": str(prediction),
            "original_confidence": round(original_confidence, 4)
        }
    }

def normalize_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"[^a-záéíóúñü\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def translate_text_to_english(text: str) -> str:
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception:
        return text


def score_emotions(text_es: str, text_en: str):
    clean_es = normalize_text(text_es)
    clean_en = normalize_text(text_en)

    scores = {}
    detected_words = {}

    for emotion in EMOTION_LEXICON_ES.keys():
        words_es = EMOTION_LEXICON_ES.get(emotion, [])
        words_en = EMOTION_LEXICON_EN.get(emotion, [])

        found_es = [w for w in words_es if w in clean_es]
        found_en = [w for w in words_en if w in clean_en]

        score = len(found_es) + len(found_en)

        scores[emotion] = score
        detected_words[emotion] = sorted(list(set(found_es + found_en)))

    return scores, detected_words


def choose_emotion(scores: dict, sentiment: str):
    max_score = max(scores.values()) if scores else 0

    if max_score == 0:
        if sentiment == "Positivo":
            return "Alegría"
        if sentiment == "Negativo":
            return "Enojo"
        return "Neutral"

    candidates = [emo for emo, score in scores.items() if score == max_score]
    return candidates[0]


def extract_spanish_keywords(text: str, top_n: int = 10):
    """
    Extrae palabras clave visibles en español desde el comentario original.
    No usa el TF-IDF del modelo porque ese vocabulario está en inglés.
    """
    clean = normalize_text(text)
    raw_tokens = clean.split()

    tokens = []
    for token in raw_tokens:
        if token in NEGATIONS_ES:
            tokens.append(token)
        elif len(token) > 2 and token not in SPANISH_STOPWORDS:
            tokens.append(token)

    if not tokens:
        return []

    emotion_words_es = set()
    for words in EMOTION_LEXICON_ES.values():
        emotion_words_es.update(words)

    scores = Counter()

    # Unigramas
    for token in tokens:
        score = 1.0
        if token in emotion_words_es:
            score += 2.0
        if len(token) >= 7:
            score += 0.5
        scores[token] += score

    # Bigramas simples: ayudan a mostrar frases como "mala atención", "servicio excelente".
    for i in range(len(tokens) - 1):
        w1, w2 = tokens[i], tokens[i + 1]
        if w1 in SPANISH_STOPWORDS or w2 in SPANISH_STOPWORDS:
            continue

        phrase = f"{w1} {w2}"
        phrase_score = 1.5

        if w1 in emotion_words_es or w2 in emotion_words_es:
            phrase_score += 2.0

        # Priorizamos frases cortas útiles.
        if len(w1) > 2 and len(w2) > 2:
            scores[phrase] += phrase_score

    top = scores.most_common(top_n)

    return [
        {
            "word": word,
            "score": round(float(score), 4),
            "language": "es"
        }
        for word, score in top
    ]


def get_top_model_words_by_class(top_n=12):
    """
    Extrae palabras representativas desde el modelo.
    Estas salen del vocabulario del modelo y por eso pueden estar en inglés.
    No se muestran como keywords principales; se conservan como explicación técnica.
    """
    try:
        vectorizer = modelo.named_steps["tfidf"]
        clf = modelo.named_steps["clf"]

        feature_names = np.array(vectorizer.get_feature_names_out())
        classes = clf.classes_

        result = {}

        for i, cls in enumerate(classes):
            coef = clf.coef_[i]
            top_idx = np.argsort(coef)[-top_n:][::-1]

            result[str(cls)] = [
                {
                    "word": str(feature_names[idx]),
                    "weight": round(float(coef[idx]), 4),
                    "language": "en"
                }
                for idx in top_idx
            ]

        return result

    except Exception:
        return {}


def get_keywords_from_model(text_for_model: str, top_n=8):
    """
    Palabras importantes para el modelo. Pueden estar en inglés.
    """
    try:
        vectorizer = modelo.named_steps["tfidf"]
        transformed = vectorizer.transform([text_for_model])
        feature_names = np.array(vectorizer.get_feature_names_out())

        row = transformed.toarray()[0]
        nonzero = np.where(row > 0)[0]

        if len(nonzero) == 0:
            return []

        top_idx = nonzero[np.argsort(row[nonzero])[-top_n:][::-1]]

        return [
            {
                "word": str(feature_names[idx]),
                "score": round(float(row[idx]), 4),
                "language": "en"
            }
            for idx in top_idx
        ]

    except Exception:
        return []


TOP_WORDS_BY_SENTIMENT = get_top_model_words_by_class(top_n=15)


def build_interpretation(sentiment: str, emotion: str, confidence: float):
    if confidence >= 0.75:
        security = "alta"
    elif confidence >= 0.55:
        security = "media"
    else:
        security = "baja"

    if sentiment == "Positivo":
        base = "El comentario transmite una experiencia favorable del servicio."
    elif sentiment == "Negativo":
        base = "El comentario refleja una experiencia desfavorable o una queja."
    else:
        base = "El comentario no muestra una inclinación emocional fuerte."

    return f"{base} La emoción predominante detectada es {emotion}. La seguridad del modelo es {security}."


def build_recommendation(sentiment: str, emotion: str):
    if sentiment == "Positivo":
        return "Usar este comentario como evidencia de buena atención y reforzar los puntos positivos mencionados."
    if sentiment == "Negativo":
        if emotion == "Enojo":
            return "Revisar con prioridad la causa de molestia: trato, demora, precio o mala atención."
        if emotion == "Miedo":
            return "Revisar protocolos de seguridad, confianza y cuidado de la mascota."
        if emotion == "Asco":
            return "Revisar limpieza, higiene del ambiente y presentación del servicio."
        return "Analizar la queja y responder al cliente con una solución concreta."
    return "Monitorear el comentario. Puede servir para detectar puntos neutrales que necesitan mejorar."


def analyze_text(original_text: str, translate_to_english: bool = True):
    original_text = str(original_text).strip()

    if not original_text:
        return {"error": "Comentario vacío."}

    if translate_to_english:
        text_for_model = translate_text_to_english(original_text)
        was_translated = True
    else:
        text_for_model = original_text
        was_translated = False

    prediction = modelo.predict([text_for_model])[0]

    probabilities = modelo.predict_proba([text_for_model])[0]
    classes = modelo.classes_

    raw_probabilities_dict = {
        str(label): round(float(prob), 4)
        for label, prob in zip(classes, probabilities)
    }

    correction = apply_sentiment_corrections(
        original_text,
        text_for_model,
        str(prediction),
        raw_probabilities_dict
    )

    final_sentiment = correction["sentiment"]
    probabilities_dict = correction["probabilities"]
    confidence = correction["confidence"]

    emotion_scores, emotion_words = score_emotions(original_text, text_for_model)

    if final_sentiment == "Neutral":
        emotion = "Neutral"
    else:
        emotion = choose_emotion(emotion_scores, final_sentiment)

        # Evita contradicciones visuales tipo: sentimiento negativo con emoción Alegría.
        if final_sentiment == "Negativo" and emotion == "Alegría":
            emotion = "Enojo" if emotion_scores.get("Enojo", 0) >= emotion_scores.get("Tristeza", 0) else "Tristeza"
        elif final_sentiment == "Positivo" and emotion in {"Enojo", "Tristeza", "Asco", "Miedo"}:
            emotion = "Alegría"

    total_emotion_score = sum(emotion_scores.values())
    if total_emotion_score > 0:
        emotion_percentages = {
            emo: round(score / total_emotion_score, 4)
            for emo, score in emotion_scores.items()
        }
    else:
        emotion_percentages = {
            emo: 0 for emo in emotion_scores.keys()
        }

    keywords_es = extract_spanish_keywords(original_text, top_n=10)
    model_keywords_en = get_keywords_from_model(text_for_model, top_n=8)
    top_words_for_prediction = TOP_WORDS_BY_SENTIMENT.get(final_sentiment, [])

    interpretation = build_interpretation(final_sentiment, emotion, confidence)
    recommendation = build_recommendation(final_sentiment, emotion)

    return {
        "original_text": original_text,
        "text_used_by_model": text_for_model,
        "was_translated": was_translated,

        "sentiment": final_sentiment,
        "confidence": confidence,
        "probabilities": probabilities_dict,
        "raw_model_sentiment": str(prediction),
        "raw_model_confidence": correction["signals"]["original_confidence"],
        "correction_reason": correction["correction_reason"],
        "correction_signals": correction["signals"],

        "dominant_emotion": emotion,
        "emotion_scores": emotion_scores,
        "emotion_percentages": emotion_percentages,
        "emotion_words_detected": emotion_words,

        # Principal para mostrar en la web
        "keywords_from_comment_es": keywords_es,

        # Técnico, por si quieres explicar qué vio el modelo
        "model_keywords_en": model_keywords_en,
        "top_words_for_predicted_sentiment_en": top_words_for_prediction,
        "top_words_by_sentiment_en": TOP_WORDS_BY_SENTIMENT,

        "interpretation": interpretation,
        "recommendation": recommendation
    }


@app.get("/")
def home():
    return {
        "message": "API funcionando correctamente",
        "version": "2.2.0",
        "endpoints": ["/predict", "/predict-batch", "/model-info"]
    }


@app.get("/model-info")
def model_info():
    return {
        "classes": list(map(str, modelo.classes_)),
        "top_words_by_sentiment_en": TOP_WORDS_BY_SENTIMENT,
        "note": "Las keywords visibles se extraen del comentario original en español. La predicción usa el modelo base y una capa híbrida de reglas para baja confianza, frases neutrales y falsos positivos por traducción."
    }


@app.post("/predict")
def predict_sentiment(request: SentimentRequest):
    return analyze_text(request.text, request.translate_to_english)


@app.post("/predict-batch")
def predict_batch(request: BatchSentimentRequest):
    texts = [str(t).strip() for t in request.texts if str(t).strip()]

    if len(texts) == 0:
        return {"error": "No se recibieron comentarios válidos."}

    if len(texts) > 200:
        return {
            "error": "Máximo 200 comentarios por lote. Divide el CSV en lotes más pequeños."
        }

    results = [
        analyze_text(text, request.translate_to_english)
        for text in texts
    ]

    return {
        "total": len(results),
        "results": results
    }