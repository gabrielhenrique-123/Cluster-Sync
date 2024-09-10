import socket
import time
import random

# Lista de nós do Cluster Sync (IPs e portas)
cluster_nodes = [
    ("127.0.0.1", 5001),
    ("127.0.0.1", 5002),
    ("127.0.0.1", 5003),
    ("127.0.0.1", 5004),
    ("127.0.0.1", 5005)
]

def send_request(client_id):
    # Escolher um nó aleatório da lista
    cluster_node = random.choice(cluster_nodes)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(cluster_node)
        # Timestamp único baseado no tempo atual
        timestamp = int(time.time() * 1000)
        request = f"{client_id},{timestamp}"
        client_socket.sendall(request.encode())

        # Receber a resposta do Cluster Sync
        response = client_socket.recv(1024).decode()
        print(f"Cliente {client_id} recebeu resposta: {response}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    client_id = f"Client{random.randint(1, 1000)}"
    for _ in range(random.randint(10, 50)):  # Cliente faz entre 10 e 50 requisições
        send_request(client_id)
        # Cliente espera de 1 a 5 segundos antes de enviar outra requisição
        time.sleep(random.uniform(1, 5))
