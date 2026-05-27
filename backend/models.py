from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Comentario(Base):
    __tablename__ = "comentarios"

    id = Column(Integer, primary_key=True, index=True)
    texto = Column(Text, nullable=False)
    fecha = Column(Date, nullable=False)
    sentimiento = Column(String(20))
    emocion = Column(String(50))
    confianza = Column(Numeric(5, 2))
    creado_en = Column(DateTime, server_default=func.now())


class ResumenDiario(Base):
    __tablename__ = "resumenes_diarios"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, unique=True)
    total_comentarios = Column(Integer, default=0)
    positivos = Column(Integer, default=0)
    neutrales = Column(Integer, default=0)
    negativos = Column(Integer, default=0)
    emocion_principal = Column(String(50))
    tema_principal = Column(String(100))
    nivel_satisfaccion = Column(Numeric(5, 2))
    resumen = Column(Text)
    creado_en = Column(DateTime, server_default=func.now())

    recomendaciones = relationship("Recomendacion", back_populates="resumen", cascade="all, delete")
    alertas = relationship("Alerta", back_populates="resumen", cascade="all, delete")
    temas = relationship("TemaFrecuente", back_populates="resumen", cascade="all, delete")


class Recomendacion(Base):
    __tablename__ = "recomendaciones"

    id = Column(Integer, primary_key=True, index=True)
    resumen_id = Column(Integer, ForeignKey("resumenes_diarios.id", ondelete="CASCADE"))
    tipo = Column(String(30), nullable=False)
    descripcion = Column(Text, nullable=False)
    prioridad = Column(String(20), default="media")
    creado_en = Column(DateTime, server_default=func.now())

    resumen = relationship("ResumenDiario", back_populates="recomendaciones")


class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    resumen_id = Column(Integer, ForeignKey("resumenes_diarios.id", ondelete="CASCADE"))
    tipo = Column(String(50), nullable=False)
    mensaje = Column(Text, nullable=False)
    nivel = Column(String(20), default="medio")
    activa = Column(Boolean, default=True)
    creado_en = Column(DateTime, server_default=func.now())

    resumen = relationship("ResumenDiario", back_populates="alertas")


class TemaFrecuente(Base):
    __tablename__ = "temas_frecuentes"

    id = Column(Integer, primary_key=True, index=True)
    resumen_id = Column(Integer, ForeignKey("resumenes_diarios.id", ondelete="CASCADE"))
    tema = Column(String(100), nullable=False)
    cantidad = Column(Integer, default=1)
    sentimiento_asociado = Column(String(20))
    creado_en = Column(DateTime, server_default=func.now())

    resumen = relationship("ResumenDiario", back_populates="temas")