import socket  # Importa a biblioteca de sockets para comunicação entre máquinas
import time  # Biblioteca para trabalhar com tempo (espera, timestamp, etc.)
import random  # Biblioteca para gerar números aleatórios

# Lista de nós do Cluster Sync (cada nó tem um nome de serviço e uma porta para comunicação)
cluster_nodes = [
    ("cluster_node_1", 5001),  # Nó 1 (nome do serviço com porta 5001)
    ("cluster_node_2", 5002),  # Nó 1 (nome do serviço com porta 5001)
    ("cluster_node_3", 5003),  # Nó 1 (nome do serviço com porta 5001)
    ("cluster_node_4", 5004),  # Nó 1 (nome do serviço com porta 5001)
    ("cluster_node_5", 5005),  # Nó 1 (nome do serviço com porta 5001)
]

# Função que simula o envio de uma requisição de um cliente para um nó do cluster
def send_request(client_id, timestamp):
    # Escolhe um nó aleatoriamente da lista para enviar a requisição
    cluster_node = random.choice(cluster_nodes)
    
    print(f"Nó escolhido foi: {cluster_node}")

    # Cria um socket para se conectar ao nó escolhido
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Tenta conectar ao nó escolhido
        client_socket.connect(cluster_node)        
        # Monta a requisição no formato "ID do cliente, timestamp"
        request = f"{client_id},{timestamp}"
        print(f"A requisição sendo enviado para o nó é ClientId = {client_id} e Timestamp = {timestamp}\n")
        
        # Envia a requisição para o nó do Cluster Sync
        client_socket.send(request.encode())

        # Recebe a resposta do nó após o processamento
        response = client_socket.recv(1024).decode()
        print(f"Cliente {client_id} recebeu resposta: {response}")  # Exibe a resposta
    
    except ConnectionRefusedError as e:
        print(f"Conexão recusada com o nó {cluster_node}\n")
        client_socket.close()
        send_request(client_id, timestamp)

    finally:
        # Fecha o socket para encerrar a conexão
        client_socket.close()

# Função principal (executada quando o script é rodado)
if __name__ == "__main__":
    # Gera um ID único para o cliente (ex: "Client123")
    client_id = f"Client{random.randint(1, 1000)}"
    
    # O cliente faz entre 10 e 50 requisições ao Cluster Sync
    for _ in range(random.randint(10, 50)):
        # Gera um timestamp único baseado no tempo atual (em milissegundos)
        timestamp = int(time.time() * 1000)
        print(f"Timestamp gerado foi de {timestamp}\n")
        send_request(client_id, timestamp)  # Envia uma requisição para o cluster
        
        # O cliente espera de 1 a 5 segundos antes de enviar a próxima requisição
        time.sleep(random.uniform(1,5))
