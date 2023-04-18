import socket
import threading

SERVER_PORT = 7734

peers_lock = threading.Lock()
registered_peers = []

rfcs_lock = threading.Lock()
rfcs = []

def add_rfc(rfc_number: int, rfc_title: str, peer_hostname: str):
    with rfcs_lock:
        rfcs.append({
                'rfc_number': rfc_number, 
                'rfc_title': rfc_title,
                'peer_hostname': peer_hostname
            })

def remove_rfcs_by_hostname(peer_hostname: str):
    with rfcs_lock:
        for rfc in rfcs:
            if (rfc.peerhostname == peer_hostname):
                rfcs.remove(rfc)

def register_peer(peer_hostname: str, peer_port: int):
    with peers_lock:
        registered_peers.append({
                'peer_hostname': peer_hostname,
                'peer_port': peer_port
            })

def handle_client(client_socket: socket):
    request = client_socket.recv(1024).decode()
    if request.startswith('REGISTER'):
        # Register the peer
        peer_info = request.split('|')[1]
        print('Registered peer:', peer_info)
    elif request.startswith('QUERY'):
        # Respond with a list of registered peers
        peers = ['{}:{}'.format(addr[0], addr[1]) for addr in registered_peers]
        response = 'RESPONSE|' + '|'.join(peers)
        client_socket.send(response.encode())

def handle_upload_server():
    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # zero instead of a port number to tell the operating system to get a random available port
    peer_socket.bind((socket.gethostname(), 0))
    peer_socket.listen()

def start_peer():
    upload_server = threading.Thread(target=handle_upload_server)
    upload_server.start()
    
    while True:
        client_socket, client_addr = upload_server.accept()
        print('Received connection from:', client_addr)
        client_thread = threading.Thread(target=handle_upload_server)
        client_thread.start()