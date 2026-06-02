from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Comentario,
    ResumenDiario,
    Recomendacion,
    Alerta,
    TemaFrecuente
)


router = APIRouter(
    prefix="/api/agente",
    tags=["Agente Inteligente"]
)


def serializar_comentario(comentario: Comentario):
    return {
        "id": comentario.id,
        "texto": comentario.texto,
        "fecha": comentario.fecha,
        "sentimiento": comentario.sentimiento,
        "emocion": comentario.emocion,
        "confianza": float(comentario.confianza) if comentario.confianza is not None else None,
        "creado_en": comentario.creado_en
    }


def serializar_resumen_completo(resumen: ResumenDiario):
    return {
        "id": resumen.id,
        "fecha": resumen.fecha,
        "total_comentarios": resumen.total_comentarios,
        "positivos": resumen.positivos,
        "neutrales": resumen.neutrales,
        "negativos": resumen.negativos,
        "emocion_principal": resumen.emocion_principal,
        "tema_principal": resumen.tema_principal,
        "nivel_satisfaccion": float(resumen.nivel_satisfaccion) if resumen.nivel_satisfaccion is not None else None,
        "resumen": resumen.resumen,
        "creado_en": resumen.creado_en,
        "recomendaciones": [
            {
                "id": recomendacion.id,
                "tipo": recomendacion.tipo,
                "descripcion": recomendacion.descripcion,
                "prioridad": recomendacion.prioridad,
                "creado_en": recomendacion.creado_en
            }
            for recomendacion in resumen.recomendaciones
        ],
        "alertas": [
            {
                "id": alerta.id,
                "tipo": alerta.tipo,
                "mensaje": alerta.mensaje,
                "nivel": alerta.nivel,
                "activa": alerta.activa,
                "creado_en": alerta.creado_en
            }
            for alerta in resumen.alertas
        ],
        "temas_frecuentes": [
            {
                "id": tema.id,
                "tema": tema.tema,
                "cantidad": tema.cantidad,
                "sentimiento_asociado": tema.sentimiento_asociado,
                "creado_en": tema.creado_en
            }
            for tema in resumen.temas
        ]
    }


class RecomendacionRequest(BaseModel):
    tipo: str
    descripcion: str
    prioridad: str = "media"


class AlertaRequest(BaseModel):
    tipo: str
    mensaje: str
    nivel: str = "medio"
    activa: bool = True


class TemaFrecuenteRequest(BaseModel):
    tema: str
    cantidad: int = 1
    sentimiento_asociado: Optional[str] = None


class ResumenDiarioRequest(BaseModel):
    fecha: date
    total_comentarios: int
    positivos: int
    neutrales: int
    negativos: int
    emocion_principal: Optional[str] = None
    tema_principal: Optional[str] = None
    nivel_satisfaccion: Optional[float] = None
    resumen: str
    recomendaciones: List[RecomendacionRequest] = []
    alertas: List[AlertaRequest] = []
    temas_frecuentes: List[TemaFrecuenteRequest] = []


@router.get("/comentarios")
def listar_comentarios(limit: int = 200, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 1000))
    comentarios = db.query(Comentario).order_by(Comentario.creado_en.desc()).limit(limit).all()
    return [serializar_comentario(comentario) for comentario in comentarios]


@router.get("/base-datos")
def obtener_base_datos(limit: int = 200, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 1000))

    comentarios = db.query(Comentario).order_by(Comentario.creado_en.desc()).limit(limit).all()
    resumenes = db.query(ResumenDiario).order_by(ResumenDiario.fecha.desc()).limit(limit).all()
    recomendaciones = db.query(Recomendacion).order_by(Recomendacion.creado_en.desc()).limit(limit).all()
    alertas = db.query(Alerta).order_by(Alerta.creado_en.desc()).limit(limit).all()
    temas = db.query(TemaFrecuente).order_by(TemaFrecuente.creado_en.desc()).limit(limit).all()

    return {
        "conteos": {
            "comentarios": db.query(Comentario).count(),
            "resumenes_diarios": db.query(ResumenDiario).count(),
            "recomendaciones": db.query(Recomendacion).count(),
            "alertas": db.query(Alerta).count(),
            "temas_frecuentes": db.query(TemaFrecuente).count()
        },
        "comentarios": [serializar_comentario(comentario) for comentario in comentarios],
        "resumenes_diarios": [serializar_resumen_completo(resumen) for resumen in resumenes],
        "recomendaciones": [
            {
                "id": recomendacion.id,
                "resumen_id": recomendacion.resumen_id,
                "tipo": recomendacion.tipo,
                "descripcion": recomendacion.descripcion,
                "prioridad": recomendacion.prioridad,
                "creado_en": recomendacion.creado_en
            }
            for recomendacion in recomendaciones
        ],
        "alertas": [
            {
                "id": alerta.id,
                "resumen_id": alerta.resumen_id,
                "tipo": alerta.tipo,
                "mensaje": alerta.mensaje,
                "nivel": alerta.nivel,
                "activa": alerta.activa,
                "creado_en": alerta.creado_en
            }
            for alerta in alertas
        ],
        "temas_frecuentes": [
            {
                "id": tema.id,
                "resumen_id": tema.resumen_id,
                "tema": tema.tema,
                "cantidad": tema.cantidad,
                "sentimiento_asociado": tema.sentimiento_asociado,
                "creado_en": tema.creado_en
            }
            for tema in temas
        ]
    }


@router.get("/comentarios-dia")
def obtener_comentarios_del_dia(fecha: date, db: Session = Depends(get_db)):
    comentarios = db.query(Comentario).filter(
        Comentario.fecha == fecha
    ).all()

    return {
        "fecha": fecha,
        "total": len(comentarios),
        "comentarios": [
            {
                "id": comentario.id,
                "texto": comentario.texto,
                "sentimiento": comentario.sentimiento,
                "emocion": comentario.emocion,
                "confianza": float(comentario.confianza) if comentario.confianza is not None else None
            }
            for comentario in comentarios
        ]
    }


@router.post("/resumen-diario")
def guardar_resumen_diario(data: ResumenDiarioRequest, db: Session = Depends(get_db)):
    resumen_existente = db.query(ResumenDiario).filter(
        ResumenDiario.fecha == data.fecha
    ).first()

    if resumen_existente:
        db.delete(resumen_existente)
        db.commit()

    nuevo_resumen = ResumenDiario(
        fecha=data.fecha,
        total_comentarios=data.total_comentarios,
        positivos=data.positivos,
        neutrales=data.neutrales,
        negativos=data.negativos,
        emocion_principal=data.emocion_principal,
        tema_principal=data.tema_principal,
        nivel_satisfaccion=data.nivel_satisfaccion,
        resumen=data.resumen
    )

    db.add(nuevo_resumen)
    db.commit()
    db.refresh(nuevo_resumen)

    for recomendacion in data.recomendaciones:
        db.add(Recomendacion(
            resumen_id=nuevo_resumen.id,
            tipo=recomendacion.tipo,
            descripcion=recomendacion.descripcion,
            prioridad=recomendacion.prioridad
        ))

    for alerta in data.alertas:
        db.add(Alerta(
            resumen_id=nuevo_resumen.id,
            tipo=alerta.tipo,
            mensaje=alerta.mensaje,
            nivel=alerta.nivel,
            activa=alerta.activa
        ))

    for tema in data.temas_frecuentes:
        db.add(TemaFrecuente(
            resumen_id=nuevo_resumen.id,
            tema=tema.tema,
            cantidad=tema.cantidad,
            sentimiento_asociado=tema.sentimiento_asociado
        ))

    db.commit()

    return {
        "mensaje": "Resumen diario guardado correctamente",
        "resumen_id": nuevo_resumen.id
    }


@router.get("/resumenes")
def listar_resumenes(db: Session = Depends(get_db)):
    resumenes = db.query(ResumenDiario).order_by(
        ResumenDiario.fecha.desc()
    ).all()

    return [
        {
            "id": resumen.id,
            "fecha": resumen.fecha,
            "total_comentarios": resumen.total_comentarios,
            "positivos": resumen.positivos,
            "neutrales": resumen.neutrales,
            "negativos": resumen.negativos,
            "emocion_principal": resumen.emocion_principal,
            "tema_principal": resumen.tema_principal,
            "nivel_satisfaccion": float(resumen.nivel_satisfaccion) if resumen.nivel_satisfaccion is not None else None,
            "resumen": resumen.resumen,
            "creado_en": resumen.creado_en
        }
        for resumen in resumenes
    ]


@router.get("/resumenes/{resumen_id}")
def obtener_resumen_por_id(resumen_id: int, db: Session = Depends(get_db)):
    resumen = db.query(ResumenDiario).filter(
        ResumenDiario.id == resumen_id
    ).first()

    if not resumen:
        raise HTTPException(status_code=404, detail="Resumen no encontrado")

    return {
        "id": resumen.id,
        "fecha": resumen.fecha,
        "total_comentarios": resumen.total_comentarios,
        "positivos": resumen.positivos,
        "neutrales": resumen.neutrales,
        "negativos": resumen.negativos,
        "emocion_principal": resumen.emocion_principal,
        "tema_principal": resumen.tema_principal,
        "nivel_satisfaccion": float(resumen.nivel_satisfaccion) if resumen.nivel_satisfaccion is not None else None,
        "resumen": resumen.resumen,
        "recomendaciones": [
            {
                "id": recomendacion.id,
                "tipo": recomendacion.tipo,
                "descripcion": recomendacion.descripcion,
                "prioridad": recomendacion.prioridad
            }
            for recomendacion in resumen.recomendaciones
        ],
        "alertas": [
            {
                "id": alerta.id,
                "tipo": alerta.tipo,
                "mensaje": alerta.mensaje,
                "nivel": alerta.nivel,
                "activa": alerta.activa
            }
            for alerta in resumen.alertas
        ],
        "temas_frecuentes": [
            {
                "id": tema.id,
                "tema": tema.tema,
                "cantidad": tema.cantidad,
                "sentimiento_asociado": tema.sentimiento_asociado
            }
            for tema in resumen.temas
        ]
    }