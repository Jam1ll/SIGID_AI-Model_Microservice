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

# MODELOS DE DATOS
class DatoMensual(BaseModel):
    fecha: date
    cantidad: float = Field(..., ge=0, description="El stock no puede ser negativo")

class PeticionPrediccion(BaseModel):
    historial: List[DatoMensual] = Field(..., min_length=2, description="Se necesitan al menos 2 meses de datos")
    meses_a_predecir: int = Field(default=1, gt=0, le=24, description="Predecir entre 1 y 24 meses máximo")

# ENDPOINTS
@app.get("/")
def home():
    return {"mensaje": "API de Predicción de Stock activa"}

@app.post("/predict")
def predecir_stock(peticion: PeticionPrediccion):
    if len(peticion.historial) < 2:
         raise HTTPException(status_code=400, detail="Prophet requiere un mínimo de 2 registros históricos para calcular una tendencia.")

    try:
        datos = [{"ds": item.fecha, "y": item.cantidad} for item in peticion.historial]
        df = pd.DataFrame(datos)
        
        if df['ds'].duplicated().any():
            raise ValueError("El historial contiene fechas duplicadas. Cada mes debe ser único.")

    except Exception as e:
        logger.error(f"Error procesando los datos de entrada: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error en la estructura de datos: {str(e)}")

    try:
        modelo = Prophet()
        modelo.fit(df)
        
        futuro = modelo.make_future_dataframe(periods=peticion.meses_a_predecir, freq='MS')
        pronostico = modelo.predict(futuro)
        
        predicciones_futuras = pronostico[['ds', 'yhat']].tail(peticion.meses_a_predecir)
        
        resultado = []
        for _, fila in predicciones_futuras.iterrows():
            cantidad_estimada = max(0, round(fila['yhat'], 2)) 
            resultado.append({
                "fecha": fila['ds'].strftime('%Y-%m-%d'),
                "cantidad_estimada": cantidad_estimada
            })
            
        return {"predicciones": resultado}
        
    except ValueError as ve:
        logger.error(f"Error de valor en Prophet: {str(ve)}")
        raise HTTPException(status_code=422, detail=f"El modelo no pudo procesar estos datos matemáticamente: {str(ve)}")
        
    except Exception as e:
        logger.error(f"Error interno del servidor: {str(e)}")
        raise HTTPException(status_code=500, detail="Ocurrió un error interno al generar la predicción. Revisa los logs del servidor.")