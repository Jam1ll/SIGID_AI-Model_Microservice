from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from datetime import date
import pandas as pd
from prophet import Prophet

app = FastAPI(title="Predicción de Stock - API")

class DatoMensual(BaseModel):
    fecha: date
    cantidad: float = Field(..., ge=0)

class PeticionPrediccion(BaseModel):
    historial: List[DatoMensual] = Field(..., min_length=2)
    meses_a_predecir: int = Field(default=1, gt=0)

@app.get("/")
def home():
    return {"mensaje": "API de Predicción de Stock activa"}

@app.post("/predict")
def predecir_stock(peticion: PeticionPrediccion):
    
    datos = [{"ds": item.fecha, "y": item.cantidad} for item in peticion.historial]
    df = pd.DataFrame(datos)
    
    try:
        modelo = Prophet()
        modelo.fit(df)
        
        # Crear calendario futuro
        futuro = modelo.make_future_dataframe(periods=peticion.meses_a_predecir, freq='MS')
        
        # Ejecutar predicción
        pronostico = modelo.predict(futuro)
        
        # Extraer resultados
        predicciones_futuras = pronostico[['ds', 'yhat']].tail(peticion.meses_a_predecir)
        
        resultado = []
        for _, fila in predicciones_futuras.iterrows():
            # 4. Evitar stock negativo con max(0, valor)
            cantidad_estimada = max(0, round(fila['yhat'], 2)) 
            
            resultado.append({
                "fecha": fila['ds'].strftime('%Y-%m-%d'),
                "cantidad_estimada": cantidad_estimada
            })
            
        return {"predicciones": resultado}
        
    except Exception as e:
        # Devolver un error 500 controlado si Prophet falla
        raise HTTPException(status_code=500, detail=f"Error al procesar la predicción: {str(e)}")