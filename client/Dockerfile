# Usa uma imagem base do Python
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de código do cliente para o diretório de trabalho no container
COPY client.py .

# Atualize o pip para a versão mais recente
RUN pip install --upgrade pip

# Define a variável de ambiente para evitar buffers no output
ENV PYTHONUNBUFFERED=1

# Porta que o cliente pode utilizar (opcional)
EXPOSE 5006

# Comando para rodar o cliente
CMD ["python", "client.py"]

