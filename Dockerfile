FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y build-essential
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 7. El comando para encender el servidor cuando el contenedor arranque
# Nota: Usamos 0.0.0.0 para que sea accesible desde fuera del contenedor (tu PC o C#)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]