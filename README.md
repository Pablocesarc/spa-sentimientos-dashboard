# Spa Sentimientos Dashboard V2

Versión mejorada para análisis de sentimientos con dashboard. Incluye corrección híbrida para frases ambiguas o falsos positivos del modelo.

## Cambios principales

- Las palabras clave visibles ahora salen en español.
- Se mantiene la traducción a inglés internamente para que el modelo original funcione.
- Se agregó carga masiva de comentarios desde CSV.
- El dashboard acumula resultados en el navegador.
- Se puede exportar el historial a CSV.
- Se agregó una capa híbrida de reglas para corregir baja confianza y frases como “esperaba algo mucho mejor”.

## Estructura esperada del CSV

La página buscará automáticamente una columna llamada:

- comentario
- comentarios
- texto
- text
- comment
- review
- reseña
- opinion

Si no encuentra una columna clara, usa la primera columna.

## Uso

1. Copia tu modelo:

```txt
backend/modelo_sentimientos_pet_groomers.pkl
```

2. Ejecuta backend:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

3. Ejecuta frontend:

```bash
cd frontend
python -m http.server 5500
```

4. Abre:

```txt
http://127.0.0.1:5500
```

## Nota

La predicción principal usa tu modelo real y una capa de corrección: Positivo / Neutral / Negativo.

Las emociones y palabras clave son una capa interpretativa adicional para enriquecer el dashboard.
