from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from datetime import date
import pandas as pd
from prophet import Prophet
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Predicción de Stock - API")

# CONFIGURACIÓN CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DatoMensual(BaseModel):
    fecha: date
    cantidad: float = Field(..., ge=0, description="El stock no puede ser negativo")

class ProductoHistorial(BaseModel):
    producto: str = Field(..., description="Nombre o ID del producto (ej. Coca Cola)")
    historial: List[DatoMensual] = Field(..., min_length=2, description="Mínimo 2 meses")

class PeticionPrediccionBatch(BaseModel):
    productos: List[ProductoHistorial]
    meses_a_predecir: int = Field(default=1, gt=0, le=24)


@app.get("/")
def home():
    return {"mensaje": "API de Predicción de Stock activa"}

@app.post("/predict")
def predecir_stock_batch(peticion: PeticionPrediccionBatch):
    resultados_finales = []

    for item in peticion.productos:
        nombre_producto = item.producto
        
        try:
            datos = [{"ds": dato.fecha, "y": dato.cantidad} for dato in item.historial]
            df = pd.DataFrame(datos)
            
            if df['ds'].duplicated().any():
                resultados_finales.append({
                    "producto": nombre_producto,
                    "error": "Fechas duplicadas en el historial"
                })
                continue

            modelo = Prophet()
            modelo.fit(df)
            
            futuro = modelo.make_future_dataframe(periods=peticion.meses_a_predecir, freq='MS')
            pronostico = modelo.predict(futuro)
            
            predicciones_futuras = pronostico[['ds', 'yhat']].tail(peticion.meses_a_predecir)
            
            predicciones_limpias = []
            for _, fila in predicciones_futuras.iterrows():
                cantidad_estimada = max(0, round(fila['yhat'], 2)) 
                predicciones_limpias.append({
                    "fecha": fila['ds'].strftime('%Y-%m-%d'),
                    "cantidad_estimada": cantidad_estimada
                })
                
            resultados_finales.append({
                "producto": nombre_producto,
                "predicciones": predicciones_limpias
            })
            
        except Exception as e:
            logger.error(f"Error procesando {nombre_producto}: {str(e)}")
            resultados_finales.append({
                "producto": nombre_producto,
                "error": f"Fallo en predicción: {str(e)}"
            })

    return {"resultados": resultados_finales}