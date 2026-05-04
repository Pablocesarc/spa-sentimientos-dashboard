from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from deep_translator import GoogleTranslator
import joblib
import os
import re
import numpy as np
from collections import Counter


MODEL_PATH = "modelo_sentimientos_pet_groomers.pkl"

app = FastAPI(
    title="API de Análisis de Sentimientos - Spa de Mascotas",
    description="Predice polaridad, emoción aproximada, keywords en español y datos para dashboard.",
    version="2.1.0"
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
        "inseguro", "insegura", "emergencia"
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

    probabilities_dict = {
        str(label): round(float(prob), 4)
        for label, prob in zip(classes, probabilities)
    }

    confidence = round(float(max(probabilities)), 4)

    emotion_scores, emotion_words = score_emotions(original_text, text_for_model)
    emotion = choose_emotion(emotion_scores, str(prediction))

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
    top_words_for_prediction = TOP_WORDS_BY_SENTIMENT.get(str(prediction), [])

    interpretation = build_interpretation(str(prediction), emotion, confidence)
    recommendation = build_recommendation(str(prediction), emotion)

    return {
        "original_text": original_text,
        "text_used_by_model": text_for_model,
        "was_translated": was_translated,

        "sentiment": str(prediction),
        "confidence": confidence,
        "probabilities": probabilities_dict,

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
        "version": "2.1.0",
        "endpoints": ["/predict", "/predict-batch", "/model-info"]
    }


@app.get("/model-info")
def model_info():
    return {
        "classes": list(map(str, modelo.classes_)),
        "top_words_by_sentiment_en": TOP_WORDS_BY_SENTIMENT,
        "note": "Las keywords visibles se extraen del comentario original en español. Las palabras técnicas del modelo pueden estar en inglés porque el modelo fue entrenado con reseñas en inglés."
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