from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import pandas as pd
from prophet import Prophet

app = FastAPI(title="Predicción de Stock - API")

# Definir cómo los datos deben llegar desde la API de C#
class DatoMensual(BaseModel):
    fecha: str  # "YYYY-MM-DD"
    cantidad: float

class PeticionPrediccion(BaseModel):
    historial: List[DatoMensual]
    meses_a_predecir: int = 1

#
# ENDPOINTS
#
@app.get("/")
def home():
    return {"mensaje": "API de Predicción de Stock activa"}

@app.post("/predict")
def predecir_stock(peticion: PeticionPrediccion):
    
    # Pasar los datos al formato que Prophet pueda entender
    datos = [{"ds": item.fecha, "y": item.cantidad} for item in peticion.historial]
    df = pd.DataFrame(datos)
    
    # Entrenar el modelo
    modelo = Prophet()
    modelo.fit(df)
    
    # Crear un calendario futuro para los próximos meses
    futuro = modelo.make_future_dataframe(periods=peticion.meses_a_predecir, freq='MS')
    
    # Ejecutar la prediccion
    pronostico = modelo.predict(futuro)
    
    # Extraer los meses a utilizar
    predicciones_futuras = pronostico[['ds', 'yhat']].tail(peticion.meses_a_predecir)
    
    # Devolver JSON
    resultado = []
    for _, fila in predicciones_futuras.iterrows():
        resultado.append({
            "fecha": fila['ds'].strftime('%Y-%m-%d'),
            "cantidad_estimada": round(fila['yhat'], 2)
        })
        
    return {"predicciones": resultado}
