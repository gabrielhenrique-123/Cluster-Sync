import socket
import time
import random

# Lista de nós do Cluster Sync (cada nó tem um IP e uma porta para comunicação)
cluster_nodes = [
    ("cluster_node_1", 5001),
    ("cluster_node_2", 5002),
    ("cluster_node_3", 5003),
    ("cluster_node_4", 5004),
    ("cluster_node_5", 5005),
]

def send_request(client_id, nodes, timestamp, max_retries=3):
    """
    Envia uma requisição para um nó do cluster, escolhendo aleatoriamente um nó.
    Se a conexão falhar, tenta outro nó da lista até o número máximo de tentativas.
    """
    attempt = 0
    while attempt < max_retries and nodes:
        # Escolhe um nó aleatoriamente da lista para enviar a requisição
        cluster_node = random.choice(nodes)
        
        print(f"Nó escolhido foi: {cluster_node}")

        # Cria um socket para se conectar ao nó escolhido
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Tenta conectar ao nó escolhido
            client_socket.connect(cluster_node)
            # Monta a requisição no formato "ID do cliente, timestamp"
            request = f"{client_id},{timestamp}"
            print(f"A requisição sendo enviada para o nó é ClientId = {client_id} e Timestamp = {timestamp}\n")
            
            # Envia a requisição para o nó do Cluster Sync
            client_socket.sendall(request.encode())

            # Recebe a resposta do nó após o processamento
            response = client_socket.recv(1024).decode()
            print(f"Cliente {client_id} recebeu resposta: {response}")
            return  # Se a requisição for bem-sucedida, sai da função

        except (socket.gaierror, ConnectionRefusedError) as e:
            print(f"Erro ao conectar com o nó {cluster_node}: {e}")
            nodes.remove(cluster_node)  # Remove o nó falhado da lista
            attempt += 1
        finally:
            client_socket.close()
    
    if attempt >= max_retries:
        print(f"Falha ao conectar com todos os nós disponíveis após {max_retries} tentativas.")
    elif not nodes:
        print("Nenhum nó disponível para conexão.")

if __name__ == "__main__":
    client_id = f"Client{random.randint(1, 1000)}"
    
    # O cliente faz entre 10 e 50 requisições ao Cluster Sync
    for _ in range(random.randint(10, 50)):
        timestamp = int(time.time() * 1000)
        print(f"Timestamp gerado foi de {timestamp}\n")
        send_request(client_id, cluster_nodes, timestamp)
        
        # O cliente espera de 1 a 5 segundos antes de enviar a próxima requisição
        time.sleep(random.uniform(1, 5))
