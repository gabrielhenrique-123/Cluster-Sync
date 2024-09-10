import socket
import threading
import time
import random
import json

# Fila de requisições de cada nó do Cluster Sync
request_queue = []
lock = threading.Lock()

# Lista de nós do cluster (IPs e portas dos outros nós do cluster)
cluster_nodes = [
    ("127.0.0.1", 5001),  # Node 1
    ("127.0.0.1", 5003),  # Node 3
    ("127.0.0.1", 5004),  # Node 4
    ("127.0.0.1", 5005)   # Node 5
    # Este código será rodado no Node 2 (5002)
]

# Função para enviar pedidos para outros nós do Cluster Sync
def propagate_to_cluster(request):
    for node in cluster_nodes:
        node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            node_socket.connect(node)
            node_socket.sendall(json.dumps(request).encode())
            # Recebe confirmação da propagação
            ack = node_socket.recv(1024).decode()
            print(f"Confirmação de {node}: {ack}")
        except Exception as e:
            print(f"Falha ao conectar com {node}: {e}")
        finally:
            node_socket.close()

# Função que simula o processamento na seção crítica
def process_critical_section(request):
    time.sleep(random.uniform(0.2, 1))  # Simulação do tempo na seção crítica
    print(f"Processando seção crítica para: {request}")

# Função para processar requisições dos clientes
def handle_client_request(client_socket, address, local_node_id):
    global request_queue
    data = client_socket.recv(1024).decode()
    client_id, timestamp = data.split(',')
    timestamp = int(timestamp)

    # Adicionar à fila de requisições local
    with lock:
        request_queue.append((client_id, timestamp))
        request_queue.sort(key=lambda x: x[1])  # Ordena por timestamp

    # Propagar o pedido para os outros nós do Cluster Sync
    request = {
        "client_id": client_id,
        "timestamp": timestamp,
        "node_id": local_node_id
    }
    propagate_to_cluster(request)

    # Simulação: Entrar na seção crítica para o menor timestamp
    with lock:
        if request_queue and request_queue[0][0] == client_id:  # Verifica se o cliente está na vez
            process_critical_section(data)
            # Remove o pedido processado da fila
            request_queue.pop(0)

    # Responder ao cliente
    client_socket.sendall(f"COMMITTED for {client_id} at timestamp {timestamp}".encode())
    client_socket.close()

# Função para tratar requisições propagadas de outros nós
def handle_propagated_request(request_data):
    global request_queue
    request = json.loads(request_data)

    # Adicionar o pedido recebido à fila local
    with lock:
        request_queue.append((request['client_id'], request['timestamp']))
        request_queue.sort(key=lambda x: x[1])  # Ordena por timestamp

# Servidor Cluster Sync (que também recebe pedidos dos outros nós)
def cluster_sync_server(host, port, local_node_id):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Nó do Cluster Sync rodando em {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Conexão recebida de {addr}")

        # Criar uma thread para processar pedidos de clientes
        client_handler = threading.Thread(target=handle_client_request, args=(client_socket, addr, local_node_id))
        client_handler.start()

# Servidor para lidar com requisições de outros nós do Cluster Sync
def node_listener(host, port):
    listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener_socket.bind((host, port))
    listener_socket.listen(5)

    print(f"Ouvidor de requisições de nós rodando em {host}:{port}")

    while True:
        node_socket, addr = listener_socket.accept()
        request_data = node_socket.recv(1024).decode()
        node_socket.sendall(b"ACK")  # Envia confirmação de recebimento
        node_socket.close()

        # Processar a requisição propagada por outro nó
        handle_propagated_request(request_data)

if __name__ == "__main__":
    local_node_id = "Peer2"  # Defina um ID único para este nó
    threading.Thread(target=cluster_sync_server, args=("127.0.0.1", 5002, local_node_id)).start()
    threading.Thread(target=node_listener, args=("127.0.0.1", 6002)).start()
