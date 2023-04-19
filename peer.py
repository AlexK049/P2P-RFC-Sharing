import socket
import threading
import parsing
from rfc import RFC
import os
import random

SERVER_PORT = 7734
P2P_VERSION = "P2P-CI/1.0"

class Peer:
    def __init__(self, rfcs: list[RFC]):
        self.rfcs = rfcs
        
    #this creates a peer with the given number of random rfcs
    @classmethod
    def with_random_rfcs(cls, num_rfcs):
        rfcs = []
        for _ in range(num_rfcs):
            rfcs.append(RFC.generate_random_rfc())
        return cls(rfcs)
    
    

def add_cmd(socket: socket, rfc: str, host: str, port: str, title: str):
    msg = "ADD " + rfc + " " + P2P_VERSION + "\n"
    msg += "Host: " + host + "\n"
    msg += "Port: " + port + "\n"
    msg += "Title: " + title + "\n"
    socket.send(msg.encode())

    res = socket.recv(1024).decode()
    return parsing.parse_s2p_response(res)

def lookup_cmd(socket: socket, rfc: str, host: str, port: str, title: str):
    msg = "LOOKUP " + rfc + " " + P2P_VERSION + "\n"
    msg += "Host: " + host + "\n"
    msg += "Port: " + port + "\n"
    msg += "Title: " + title + "\n"
    socket.send(msg.encode())

    res = socket.recv(1024).decode()
    return parsing.parse_s2p_response(res)

def list_cmd(socket: socket, host: str, port: str):
    msg = "LIST ALL " + P2P_VERSION + "\n"
    msg += "Host: " + host + "\n"
    msg += "Port: " + port + "\n"
    socket.send(msg.encode())

    res = socket.recv(1024).decode()
    return parsing.parse_s2p_response(res)

def get_cmd(port: str, rfc: str, host: str):
    msg = "GET " + rfc + " " + P2P_VERSION + "\n"
    msg += "Host: " + host + "\n"
    msg += "OS: " + os.name + "\n"

    #connect to peer's upload server
    upload_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    upload_server_socket.connect(('localhost', port))
    upload_server_socket.send(msg.encode())

    #recieve response, close socket, and return response
    res = upload_server_socket.recv(1024).decode()
    upload_server_socket.close()
    return parsing.parse_p2p_reponse(res)

def handle_upload_client(peer_socket: socket):
    peer_socket.send()
    print('hi')

def start_upload_server(upload_socket: socket):
    upload_socket.listen()
    while True:
        peer_socket, peer_addr = upload_socket.accept()
        print('Received connection from:', peer_addr)
        client_thread = threading.Thread(target=handle_upload_client, args=(peer_socket))
        client_thread.start()

def start_peer():
    ##create the upload server socket
    upload_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    upload_socket.bind(("0.0.0.0", 0)) #zero means get a random available port
    (upload_socket_host, upload_socket_port) = upload_socket.getsockname()

    ##start upload server in another thread
    upload_server_thread = threading.Thread(target=start_upload_server, args=(upload_socket))
    upload_server_thread.daemon = True #exit when main program exits
    upload_server_thread.start()

    ##connect to server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect(('localhost', SERVER_PORT))
    
    ##handle commands from client
    while True:
        userCmd = input("cmd> ")
        args = parsing.parse_user_cmd(userCmd)
        
        response = ""
        if args.command == "add":
            response = add_cmd(server_socket, args.rfc, upload_socket_host, upload_socket_port, args.title)
        elif args.command == "lookup":
            response = lookup_cmd(server_socket, args.rfc, upload_socket_host, upload_socket_port, args.title)
        elif args.command == "list":
            response = list_cmd(args.rfc, upload_socket_host, upload_socket_port)
        elif args.command == "get":
            response = get_cmd()
        elif args.command == "help" or args.command == "h":
            parsing.user_cmd_parser.print_help()
        elif args.command == "":
            continue #do nothing if the user just hits enter
        elif args.command == "exit":
            upload_socket.close()
            server_socket.close()
            quit()
        else:
            print("Invalid Command.")
        
        #print response from peer/server
        if response != "":
            print(response)
        