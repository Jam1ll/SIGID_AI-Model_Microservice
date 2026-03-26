# 1. Usamos una imagen oficial de Python 3.11 basada en Linux
FROM python:3.11

# 2. Le decimos a Docker que trabaje dentro de la carpeta /app
WORKDIR /app

# 3. Copiamos el archivo de requerimientos a la carpeta /app
COPY requirements.txt .

# 4. Instalamos las herramientas matemáticas necesarias para Linux y luego las librerías
# (Prophet necesita algunas herramientas de compilación en Linux, aquí nos aseguramos de tenerlas)
RUN apt-get update && apt-get install -y build-essential
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos tu código (main.py) al contenedor
COPY . .

# 6. Exponemos el puerto donde vivirá FastAPI
EXPOSE 8000

# 7. El comando para encender el servidor cuando el contenedor arranque
# Nota: Usamos 0.0.0.0 para que sea accesible desde fuera del contenedor (tu PC o C#)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]