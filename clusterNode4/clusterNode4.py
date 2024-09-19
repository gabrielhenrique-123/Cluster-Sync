import socket
import threading
import time
import random
import json

# Fila de requisições do Cluster Sync
request_queue = []
lock = threading.Lock()

# Lista de nós do cluster, contendo IPs e portas
cluster_nodes = [
    ("cluster_node_1", 6001),  # Nó 2
    ("cluster_node_2", 6002),  # Nó 2
    ("cluster_node_3", 6003),  # Nó 2
    ("cluster_node_5", 6005),  # Nó 2
]

# Lista para rastrear requisições já processadas
processed_requests = set()

# Fila separada de requisições por cliente
client_request_queues = {}
client_locks = {}

def propagate_to_cluster(request):
    """
    Propaga a requisição atual para os outros nós do Cluster Sync.
    """
    oks_received = 0
    for node in cluster_nodes:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as node_socket:
            try:
                node_socket.connect(node)
                node_socket.sendall(json.dumps(request).encode())
                ack = node_socket.recv(1024).decode()
                print(f"Confirmação de {node}: {ack}")
                oks_received = oks_received + 1
            except Exception as e:
                print(f"Falha ao conectar com {node}: {e}")
    
    return oks_received

def process_critical_section(request):
    """
    Simula o processamento na seção crítica.
    """
    time.sleep(random.uniform(0.2, 1))  # Simulação do tempo de processamento
    print(f"Processando seção crítica para: {request}")

def wait_for_oks(request_id, oks_received):
    """
    Aguarda a recepção de todos os "OKs" dos nós do Cluster Sync.
    """
    while True:
        with lock:
            if oks_received == len(cluster_nodes):
                break
        time.sleep(0.1)
    
    print(f"Todos os 'OKs' recebidos para a requisição {request_id}. Entrando na seção crítica...\n\n")

    
def process_request_queue(client_id, local_node_id):
    """
    Processa a fila de requisições de um cliente.
    """
    global request_queue
    while True:
        with client_locks[client_id]:  # Bloqueia o cliente para processar uma requisição por vez
            if client_request_queues[client_id]:
                # Pega a próxima requisição da fila do cliente
                request_data = client_request_queues[client_id].pop(0)
                handle_client_request_internal(request_data, local_node_id)

            time.sleep(0.1)  # Pausa para não sobrecarregar o loop

def handle_client_request(client_socket, address, local_node_id):
    """
    Processa requisições dos clientes e propaga para o cluster.
    """
    data = client_socket.recv(1024).decode()

    # Se a requisição é JSON, ela foi propagada de outro nó
    if data.startswith('{'):
        request = json.loads(data)
        client_id = request['client_id']
        timestamp = request['timestamp']
        node_id = request['node_id']
    else:
        client_id, timestamp = data.split(',')
        timestamp = int(timestamp)
        node_id = local_node_id

    # Cria uma chave única para a requisição
    request_id = f"{client_id}_{timestamp}"

    # Adiciona o cliente na fila se ele ainda não estiver
    if client_id not in client_request_queues:
        client_request_queues[client_id] = []
        client_locks[client_id] = threading.Lock()
        # Inicia uma thread para processar a fila desse cliente
        threading.Thread(target=process_request_queue, args=(client_id, local_node_id)).start()

    # Adiciona a requisição na fila do cliente
    client_request_queues[client_id].append({
        "client_socket": client_socket,
        "client_id": client_id,
        "timestamp": timestamp,
        "node_id": node_id,
        "request_id": request_id
    })

def handle_client_request_internal(request_data, local_node_id):
    """
    Lógica interna para processar a requisição de um cliente após ser tirada da fila.
    """
    global request_queue, processed_requests

    client_socket = request_data['client_socket']
    client_id = request_data['client_id']
    timestamp = request_data['timestamp']
    node_id = request_data['node_id']
    request_id = request_data['request_id']

    with lock:
        if request_id in processed_requests:
            print(f"Requisição {request_id} já processada. Ignorando.")
            client_socket.close()
            return

        request_queue.append((client_id, timestamp))
        request_queue.sort(key=lambda x: x[1])
        processed_requests.add(request_id)

    if node_id == local_node_id:
        request = {
            "client_id": client_id,
            "timestamp": timestamp,
            "node_id": local_node_id
        }
        oks_received = propagate_to_cluster(request)
    
    print(f"Oks recebidos: {oks_received}")

    wait_for_oks(request_id, oks_received)

    with lock:
        if request_queue and request_queue[0][0] == client_id:
            process_critical_section(f"Cliente {client_id}, timestamp {timestamp}")
            request_queue.pop(0)

    if node_id == local_node_id:
        client_socket.sendall(f"COMMITTED for {client_id} at timestamp {timestamp}".encode())

    client_socket.close()

def handle_propagated_request(request_data):
    """
    Processa requisições propagadas de outros nós do cluster.
    """
    global request_queue, processed_requests
    request = json.loads(request_data)
    request_id = f"{request['client_id']}_{request['timestamp']}"

    with lock:
        if request_id in processed_requests:
            print(f"Requisição propagada {request_id} já processada. Ignorando.")
            return

        request_queue.append((request['client_id'], request['timestamp']))
        request_queue.sort(key=lambda x: x[1])
        processed_requests.add(request_id)

def cluster_sync_server(host, port, local_node_id):
    """
    Servidor principal que recebe requisições dos clientes.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Nó do Cluster Sync rodando em {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Conexão recebida de {addr}")

        client_handler = threading.Thread(target=handle_client_request, args=(client_socket, addr, local_node_id))
        client_handler.start()

def node_sync_server(host, port, local_node_id):
    """
    Servidor que lida com requisições propagadas de outros nós do Cluster Sync.
    """
    node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    node_socket.bind((host, port))
    node_socket.listen(5)

    print(f"Servidor de sincronização do nó rodando em {host}:{port}")

    while True:
        node_conn, addr = node_socket.accept()
        print(f"Conexão de sincronização recebida de {addr}")

        request_data = node_conn.recv(1024).decode()
        handle_propagated_request(request_data)

        node_conn.sendall("OK".encode())
        node_conn.close()


if __name__ == "__main__":
    node_id = 4  # Definido como o nó 1
    threading.Thread(target=cluster_sync_server, args=("cluster_node_4", 5004, node_id)).start()
    threading.Thread(target=node_sync_server, args=("cluster_node_4", 6004, node_id)).start()
