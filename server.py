import socket
import threading
import parsing
from jsobject import JSObject

P2P_VERSION = "P2P-CI/1.0"
SERVER_PORT = 7734
SERVER_HOST = 'localhost'

#stores registered peers with lock for thread safety
peers_lock = threading.Lock()
registered_peers = []

#index of rfsc with lock for thread safety
rfcs_lock = threading.Lock()
rfcs = []

#add an rfc to the index
def add_rfc(rfc_number: str, rfc_title: str, peer_hostname: str, peer_port):
    with rfcs_lock:
        rfcs.append(JSObject(**{
                'rfc_number': rfc_number,
                'rfc_title': rfc_title,
                'peer_hostname': peer_hostname,
                'peer_port': peer_port
            }))

#remove all records of a peer from the system based on the hostname and peer port
def remove_peer_from_system(peer_hostname: str, peer_port: int):
    with rfcs_lock:
        for rfc in rfcs:
            if (rfc.peer_hostname == peer_hostname and rfc.peer_port == peer_port):
                rfcs.remove(rfc)
    with peers_lock:
        for peer in registered_peers:
            if peer.peer_hostname == peer_hostname and peer.peer_port == peer_port:
                registered_peers.remove(peer)

#add a peer to to the registered peers list
def register_peer(peer_hostname: str, peer_port: int):
    with peers_lock:
        registered_peers.append(JSObject(**{
                'peer_hostname': peer_hostname,
                'peer_port': peer_port
            }))

#handle each client concurrently until they exit
def handle_client(client_socket: socket):
    init_msg = parsing.parse_peer_request(client_socket.recv(1024).decode())
    client_host = init_msg.headers["Host"]
    client_port = init_msg.headers["Port"]
    register_peer(client_host, client_port)
    print('Received connection from host: {} port: {}'.format(client_host, client_port))
    
    while True:
        request = client_socket.recv(1024).decode()
        req =  parsing.parse_peer_request(request)
        
        response = ""
        if req.version != P2P_VERSION:
            print("Received request from an incompatible version from host: {} port: {}\nRequest:\n{}\n".format(client_host, client_port, request))
            response = P2P_VERSION + " " + "505 P2P-CI Version Not Supported\n\n"
        elif req.command == "ADD":
            print("Received ADD request:\n{}\n".format(request))
            add_rfc(req.rfc_number,
                    req.headers["Title"], 
                    req.headers["Host"], 
                    req.headers["Port"])
            response = "{} 200 OK\n\n{} {} {} {}\n".format(P2P_VERSION, req.rfc_number, req.headers["Title"], req.headers["Host"], req.headers["Port"])
        elif req.command == "LOOKUP":
            print("Received LOOKUP request:\n{}\n".format(request))
            for rfc in rfcs:
                if rfc.rfc_number == req.rfc_number and (rfc.rfc_title == req.headers["Title"] or req.headers["Title"] == ""):
                    response += "{} {} {} {}\n".format(rfc.rfc_number, rfc.rfc_title, rfc.peer_hostname, rfc.peer_port)
            if response == "":
                response = P2P_VERSION + " " + "404 Not Found\n\n"
            else:
                response = P2P_VERSION + " " + "200 OK\n\n" + response
        elif req.command == "LIST":
            print("Received LIST request:\n{}\n".format(request))
            response = P2P_VERSION + " " + "200 OK\n\n"
            for rfc in rfcs:
                response += "{} {} {} {}\n".format(rfc.rfc_number, rfc.rfc_title, rfc.peer_hostname, rfc.peer_port)
            if len(rfcs) == 0:
                response += "No RFCs in index."
        elif req.command == "EXIT":
            print("Received EXIT request.\n{}\n".format(request))
            client_socket.close()
            remove_peer_from_system(req.headers["Host"], req.headers["Port"])
            break
        else:
            print("Received a malformed request from host: {} port: {}\nRequest:\n{}\n".format(client_host, client_port, request))
            response = P2P_VERSION + " " + "400 Bad Request\n\n"
        client_socket.send(response.encode())

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen()
    print("Listening on port " + str(SERVER_PORT))

    while True:
        client_socket, client_addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.daemon = True
        client_thread.start()

def main():
    start_server()

if __name__ == '__main__':
    main()
        