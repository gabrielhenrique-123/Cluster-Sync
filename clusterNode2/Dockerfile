# Dockerfile para Cluster Sync
FROM python:3.10-slim

# Definir o diretório de trabalho
WORKDIR /app

# Copiar os arquivos do Cluster Sync para o container
COPY . /app

# Atualize o pip para a versão mais recente
RUN pip install --upgrade pip

# Expor a porta do servidor (por exemplo, 5001)
EXPOSE 5002

# Comando para rodar o script do Cluster Sync 
CMD ["python", "clusterNode2.py"]

