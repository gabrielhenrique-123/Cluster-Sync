import socket  # Biblioteca para comunicação de rede usando sockets
import threading  # Biblioteca para executar múltiplas operações em paralelo (threads)
import time  # Biblioteca para trabalhar com tempo (ex: delay)
import random  # Biblioteca para gerar valores aleatórios (ex: simulação de tempo)
import json  # Biblioteca para trabalhar com JSON (serialização de dados)

# Fila de requisições de cada nó do Cluster Sync, onde ficam os pedidos pendentes
request_queue = []
# Lock para garantir que apenas uma thread por vez modifique a fila de requisições
lock = threading.Lock()

cluster_nodes_ack = []

# Lista de nós do cluster, que contém os IPs e portas dos outros nós no sistema
cluster_nodes = [
    ("cluster_node_1", 5001),  # Nó 1 (nome do serviço com porta 5001)
    ("cluster_node_2", 5002),  # Nó 2 (nome do serviço com porta 5002)
    ("cluster_node_4", 5004),  # Nó 4 (nome do serviço com porta 5004)
    ("cluster_node_5", 5005),  # Nó 5 (nome do serviço com porta 5005)
    # Este código será executado no Nó 3 (porta 5003)
]

# Lista para rastrear requisições já processadas (evitar duplicações)
processed_requests = set()

# Função para configurar o socket com Keep-Alive
def setup_socket():
    """
    Configura o socket com a opção de Keep-Alive ativada para garantir que a
    conexão seja mantida ativa.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # Habilitar Keep-Alive
    return s

# Função para enviar pedidos para outros nós do Cluster Sync
def propagate_to_cluster(request):
    """
    Propaga a requisição atual para os outros nós do Cluster Sync.
    Essa função se conecta aos outros nós listados e envia o pedido
    em formato JSON. Cada nó envia uma confirmação (ACK) após receber o pedido.
    """
    retries = 3  # Número de tentativas
    for node in cluster_nodes:
        attempt = 0
        while attempt < retries:
            node_socket = setup_socket()
            try:
                node_socket.settimeout(2)  # Timeout de 2 segundos
                node_socket.connect(node)
                node_socket.send(json.dumps(request).encode())  # Serializa e envia o pedido
                print(f"Confirmação de {node}")
                cluster_nodes_ack.append(node)
                break  # Conexão bem-sucedida, sai do loop de tentativas
            except socket.timeout:
                print(f"Timeout ao tentar conectar com {node}. Tentativa {attempt+1}/{retries}")
            except Exception as e:
                print(f"Falha ao conectar com {node}: {e}. Tentativa {attempt+1}/{retries}")
            finally:
                node_socket.close()
            attempt += 1
        else:
            print(f"Falha ao conectar com {node} após {retries} tentativas")
    print(cluster_nodes_ack)

# Função que simula o processamento na seção crítica
def process_critical_section(request):
    """
    Simula o tempo de processamento na seção crítica.
    Aqui, o processamento real seria feito, mas para simulação,
    usamos um tempo de espera aleatório para simular o acesso ao recurso.
    """
    time.sleep(random.uniform(0.2, 1))  # Simulação do tempo na seção crítica
    print(f"Processando seção crítica para: {request}")

# Função para processar requisições dos clientes
def handle_client_request(client_socket, address, local_node_id):
    """
    Lida com requisições de clientes. Recebe o pedido, verifica se já foi processado,
    adiciona à fila e propaga para os outros nós. Se o pedido já foi processado,
    ele é ignorado. Caso contrário, ele é processado.
    """
    global request_queue, processed_requests
    data = client_socket.recv(1024).decode()  # Recebe os dados da requisição
    
    # Verifica se é um JSON (requisição propagada) ou um pedido de cliente
    if data.startswith('{'):
        # Trata o dado como um JSON propagado de outro nó
        request = json.loads(data)
        client_id = request['client_id']
        timestamp = request['timestamp']
        node_id = request['node_id']
        print(f"Dados propagados recebidos de outro nó: {request}")
    else:
        # Trata como uma requisição direta de um cliente (formato client_id,timestamp)
        client_id, timestamp = data.split(',')
        timestamp = int(timestamp)
        node_id = local_node_id  # Define o nó local como origem
        print(f"Dados recebidos de cliente: {client_id}, {timestamp}")

    # Identificador único para cada requisição (para evitar duplicatas)
    request_id = f"{client_id}_{timestamp}"

    # Verifica se já processamos essa requisição
    with lock:
        if request_id in processed_requests:
            print(f"Requisição {request_id} já processada. Ignorando.")
            client_socket.close()
            return  # Ignora requisições duplicadas

        # Adiciona à fila de requisições local
        request_queue.append((client_id, timestamp))  # Adiciona o pedido à fila
        request_queue.sort(key=lambda x: x[1])  # Ordena por timestamp (ordem de chegada)
        print(f"\nFila de Requisições: {request_queue}\n")
        processed_requests.add(request_id)  # Marca a requisição como processada

    # Propagar o pedido para os outros nós do Cluster Sync (somente se for requisição direta de cliente)
    if node_id == local_node_id:
        request = {
            "client_id": client_id,
            "timestamp": timestamp,
            "node_id": local_node_id
        }
        propagate_to_cluster(request)  # Propaga o pedido para os outros nós

    client_socket.close()

# Função para tratar requisições propagadas de outros nós
def handle_propagated_request(request_data):
    """
    Lida com requisições propagadas de outros nós do cluster. Recebe os pedidos,
    verifica se já foram processados, e, se não, adiciona-os à fila e processa-os.
    """
    global request_queue, processed_requests
    request = json.loads(request_data)  # Decodifica os dados recebidos

    # Identificador único da requisição propagada
    request_id = f"{request['client_id']}_{request['timestamp']}"

    # Verifica se já processamos essa requisição
    with lock:
        if request_id in processed_requests:
            print(f"Requisição propagada {request_id} já processada. Ignorando.")
            return  # Ignora requisições duplicadas

        # Adicionar o pedido recebido à fila local
        request_queue.append((request['client_id'], request['timestamp']))
        request_queue.sort(key=lambda x: x[1])  # Ordena por timestamp
        processed_requests.add(request_id)  # Marca a requisição como processada

# Função para processar a fila de requisições
def process_queue():
    """
    Função que processa a fila de requisições em uma thread separada.
    """
    global request_queue
    while True:
        with lock:
            if request_queue:
                client_id, timestamp = request_queue.pop(0)
                process_critical_section(f"{client_id},{timestamp}")
        time.sleep(0.1)  # Evitar consumo excessivo de CPU

# Servidor Cluster Sync (que também recebe pedidos dos outros nós)
def cluster_sync_server(host, port, local_node_id):
    """
    Servidor principal que recebe requisições dos clientes. Ao receber um pedido,
    ele inicia uma thread separada para processá-lo e propagar para os outros nós.
    """
    server_socket = setup_socket()
    server_socket.bind((host, port))  # Liga o servidor ao IP e porta
    server_socket.listen(10)  # Aumenta o limite para 10 conexões simultâneas

    print(f"Nó do Cluster Sync rodando em {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()  # Aceita a conexão do cliente
        print(f"Conexão recebida de {addr}")

        # Criar uma thread para processar pedidos de clientes
        client_handler = threading.Thread(target=handle_client_request, args=(client_socket, addr, local_node_id))
        client_handler.start()

# Servidor para lidar com requisições de outros nós do Cluster Sync
def node_listener(host, port):
    """
    Ouvidor que escuta requisições propagadas dos outros nós do cluster.
    Quando recebe uma requisição, envia um ACK e processa a requisição.
    """
    listener_socket = setup_socket()
    listener_socket.bind((host, port))  # Liga o ouvidor ao IP e porta
    listener_socket.listen(10)  # Aumenta o limite para 10 conexões simultâneas

    print(f"Ouvidor de requisições de nós rodando em {host}:{port}")

    while True:
        node_socket, addr = listener_socket.accept()  # Aceita a conexão de outro nó
        print(f"Conexão recebida de {addr} (outro nó do Cluster)")

        # Recebe os dados da requisição propagada
        request_data = node_socket.recv(1024).decode()
        print(f"Requisição propagada recebida: {request_data}")

        # Envia confirmação de recebimento (ACK)
        node_socket.sendall(b"ACK")

        # Processa a requisição propagada em uma thread separada
        threading.Thread(target=handle_propagated_request, args=(request_data,)).start()

        node_socket.close()

if __name__ == "__main__":
    # Define o ID do nó local e o endereço IP
    local_node_id = 3  # Este script representa o nó 1
    host = "0.0.0.0"  # IP do servidor (aceita conexões de todas as interfaces)
    port = 5003  # Porta do servidor para o nó 1

    # Inicia o servidor principal em uma thread separada
    threading.Thread(target=cluster_sync_server, args=(host, port, local_node_id)).start()

    # Inicia o ouvidor para receber requisições propagadas dos outros nós em uma thread separada
    threading.Thread(target=node_listener, args=(host, port + 1000)).start()

    # Inicia a thread que processa a fila de requisições
    threading.Thread(target=process_queue).start()

