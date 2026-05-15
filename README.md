# Spa Sentimientos Dashboard V2

Versión mejorada para análisis de sentimientos con dashboard. Incluye corrección híbrida para frases ambiguas o falsos positivos del modelo, carga masiva desde CSV y análisis por fecha.

## Cambios principales

- Las palabras clave visibles salen en español.
- Se mantiene la traducción a inglés internamente para que el modelo original funcione.
- Se agregó carga masiva de comentarios desde CSV.
- Se agregó soporte de fechas para comentarios individuales y para CSV.
- Se agregó el gráfico **Estado de ánimo por fecha**, que muestra cuántos comentarios positivos, neutrales y negativos hubo por día.
- El dashboard acumula resultados en el navegador.
- Se puede exportar el historial a CSV con fecha, comentario, sentimiento, emoción y confianza.
- Se agregó una capa híbrida de reglas para corregir baja confianza y frases como “esperaba algo mucho mejor”.

## Estructura esperada del CSV

El CSV recomendado debe tener estas columnas:

```csv
fecha,comentario
2026-05-10,"El baño quedó muy bien, mi perrito salió limpio y tranquilo."
2026-05-11,"Tardaron más de lo indicado y nadie me avisó."
```

La página buscará automáticamente una columna de comentarios llamada:

- comentario
- comentarios
- texto
- text
- comment
- review
- reseña
- opinion

También buscará automáticamente una columna de fecha llamada:

- fecha
- date
- día
- dia
- fecha_comentario
- created_at
- timestamp

Formatos de fecha aceptados:

- `2026-05-10`
- `10/05/2026`
- `10-05-2026`

Si no encuentra una fecha válida, usará la fecha actual.

## Uso local

1. Ejecuta backend:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

2. Ejecuta frontend en otra terminal:

```bash
cd frontend
python -m http.server 5500
```

3. Abre:

```txt
http://127.0.0.1:5500
```

## Deploy

El frontend detecta automáticamente si está en local o desplegado:

- Local: usa `http://127.0.0.1:8000`
- Producción: usa `https://spa-sentimientos-dashboard.onrender.com`

Si tu backend de Render tiene otra URL, cambia la constante `API_BASE_URL` en `frontend/app.js`.

## Nota

La predicción principal usa tu modelo real y una capa de corrección: Positivo / Neutral / Negativo.

Las emociones y palabras clave son una capa interpretativa adicional para enriquecer el dashboard.
