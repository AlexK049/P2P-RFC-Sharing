import socket
import threading
import parsing
from rfc import RFC
import platform
import datetime
import signal
import socket_helper

SERVER_PORT = 7734
SERVER_HOST = 'localhost'

class Peer:
    #version of p2p system that this peer is implemented on
    P2P_VERSION = "P2P-CI/1.0"

    def __init__(self, rfcs: list[RFC]):
        self.rfcs = rfcs

        ##create variables to manage stopping upload server if/when it is started
        self.stop_requested = False
        self.stop_requested_lock = threading.Lock()
        ##create the upload server socket
        self.upload_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.upload_socket.bind(("localhost", 0)) #zero means get a random available port
        (self.upload_socket_host, self.upload_socket_port) = self.upload_socket.getsockname()
        ##connect to server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((SERVER_HOST, SERVER_PORT))
        msg = "INIT - {}\nHost: {}\nPort: {}\n".format(self.P2P_VERSION, self.upload_socket_host, self.upload_socket_port)
        self.server_socket.send(msg.encode())
    
    def __del__(self):
        self.upload_socket.close()
        self.server_socket.close()

    #this creates a peer with the given number of random rfcs
    @classmethod
    def with_random_rfcs(cls, num_rfcs):
        rfcs = []
        for _ in range(num_rfcs):
            rfcs.append(RFC.generate_random_rfc())
        return cls(rfcs)
    
    def start_upload_server(self):
        ##start upload server in another thread
        upload_server_thread = threading.Thread(target=self._run_upload_server, args=(self.upload_socket,))
        upload_server_thread.daemon = True #exit when main program exits
        
        ##set stop reqested to false to allow the upload server thread's infinite loop to run
        self.stop_requested_lock.acquire()
        self.stop_requested = False
        self.stop_requested_lock.release()

        upload_server_thread.start()

    def stop_upload_server(self):
        self.stop_requested_lock.acquire()
        self.stop_requested = True
        self.stop_requested_lock.release()
    
    def _run_upload_server(self, upload_socket: socket):
        upload_socket.listen()
        while not self.stop_requested:
            peer_socket, peer_addr = upload_socket.accept()
            print('\nReceived connection from: {}\ncmd>'.format(peer_addr))
            client_thread = threading.Thread(target=self._handle_peer, args=(peer_socket,))
            client_thread.daemon = True
            client_thread.start()
        self.upload_socket.close()
    
    def _handle_peer(self, peer_socket: socket):
        try:
            request = parsing.parse_peer_request(peer_socket.recv(4096).decode())
            if request.version != self.P2P_VERSION:
                peer_socket.send(self._res_msg(self.P2P_VERSION, 505, "P2P-CI Version Not Supported").encode())
                return
            
            retrieved_rfc = None
            for rfc in self.rfcs:
                if rfc.rfc_number == request.rfc_number:
                    retrieved_rfc = rfc
                    break

            if retrieved_rfc == None:
                peer_socket.send(self._res_msg(self.P2P_VERSION, 404, "Not Found").encode())
            else:
                peer_socket.send(self._res_msg(self.P2P_VERSION, 200, "OK", retrieved_rfc).encode())
        except:
            peer_socket.send(self._res_msg(self.P2P_VERSION, 400, "Bad Request").encode())
        
        peer_socket.close()

    #this does not add any headers about file information
    @staticmethod
    def _res_msg(version: str, status_code: int, phrase: str, rfc: RFC = None):
        current_date = datetime.datetime.now(datetime.timezone.utc)
        rfc_date = current_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        msg = "{} {} {}\nDate: {}\nOS: {}\n".format(version, status_code, phrase, rfc_date, platform.platform())
        if (rfc is not None):
            msg += "Last-Modified: {}\nContent-Length: {}\nContent-Type: {}\n\n{}\n".format(rfc.last_modified, rfc.content_length, rfc.content_type, rfc.content)
        return msg
    
    def add_cmd(self, rfc: str, title: str):
        msg = "ADD {} {}\nHost: {}\nPort: {}\nTitle: {}\n".format(rfc, self.P2P_VERSION, self.upload_socket_host, self.upload_socket_port, title)
        self.server_socket.send(msg.encode())

        res = self.server_socket.recv(4096).decode()
        return res

    def lookup_cmd(self, rfc: str, title: str):
        msg = "LOOKUP {} {}\nHost: {}\nPort: {}\nTitle: {}\n".format(rfc, self.P2P_VERSION, self.upload_socket_host, self.upload_socket_port, title)
        self.server_socket.send(msg.encode())

        res = self.server_socket.recv(4096).decode()
        return res
    
    def list_cmd(self):
        msg = "LIST ALL {}\nHost: {}\nPort: {}\n".format(self.P2P_VERSION, self.upload_socket_host, self.upload_socket_port)
        self.server_socket.send(msg.encode())

        res = self.server_socket.recv(4096).decode()
        return res
    
    def list_local(self):
        retVal = ""
        for rfc in self.rfcs:
            retVal += "{} {}\n".format(rfc.rfc_number, rfc.title)
        
        if retVal == "":
            return "No RFC Files are stored locally"
        else:
            return retVal

    def get_cmd(self, rfc_number: str, host: str):
        #get info from the server on who has the rfc
        server_res = parsing.parse_s2p_response(self.lookup_cmd(rfc_number, ""))
        if server_res.status_code != "200":
            return self._res_msg(self.P2P_VERSION, server_res.status_code, server_res.phrase)

        rfc = next(filter(lambda r: r.hostname == host, server_res.rfcs), None)
        if rfc == None:
            return self._res_msg(self.P2P_VERSION, 404, "Not Found")
        
        upload_port_number = rfc.upload_port_number
        msg = "GET {} {}\nHost: {}\nOS: {}\n".format(rfc_number, self.P2P_VERSION, host, platform.platform())

        #connect to peer's upload server
        upload_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upload_server_socket.connect((host, int(upload_port_number)))
        upload_server_socket.send(msg.encode())

        #recieve response, close socket, and return response
        response_str = socket_helper.recv_all(upload_server_socket).decode()
        res = parsing.parse_p2p_reponse(response_str)
        rfc = RFC(rfc_number, rfc.rfc_title, res.headers["Last-Modified"], res.headers["Content-Length"], res.headers["Content-Type"], res.data)
        self.rfcs.append(rfc)
        upload_server_socket.close()
        return response_str
    
    def exit_cmd(self):
        msg = "EXIT - {}\nHost: {}\nPort: {}\n".format(self.P2P_VERSION, self.upload_socket_host, self.upload_socket_port)
        self.server_socket.send(msg.encode())

def main():
    peer = Peer.with_random_rfcs(4)

    def sigint_handler(signum, frame):
        peer.exit_cmd()
        peer.stop_upload_server()
        peer.server_socket.close()
        print("\nCtrl-c was pressed. All RFC's stored locally and known by the server have been deleted.")
        exit(1)

    signal.signal(signal.SIGINT, sigint_handler)

    peer.start_upload_server()

    ##handle commands from client
    while True:
        userCmd = input("cmd> ")
        try:
            args = parsing.parse_user_cmd(userCmd)
        except parsing.ArgumentParserError as ex:
            print(ex)
            continue

        response = ""
        if args.command == "add":
            response = peer.add_cmd(args.rfc, args.title)
        elif args.command == "lookup":
            response = peer.lookup_cmd(args.rfc, args.title)
        elif args.command == "list":
            if args.local:
                response = peer.list_local()
            else:
                response = peer.list_cmd()
        elif args.command == "get":
            response = peer.get_cmd(args.rfc, args.host)
        elif args.command == "help":
            parsing.user_cmd_parser.print_help()
        elif args.command == "details": #print info about this peer
            if args.what == "self":
                response = "Upload Server Host: {}\nUpload Server Port: {}\n".format(peer.upload_socket_host, peer.upload_socket_port)
            else:
                for rfc in peer.rfcs:
                    if rfc.rfc_number == args.what:
                       response = rfc.__str__()
                if response == "": #no rfc found
                    response = "The RFC specified does not exist"
        elif args.command == "exit":
            peer.exit_cmd()
            peer.server_socket.close()
            peer.upload_socket.close()
            quit()
        else:
            print("Unsupported Command.")
        
        #print response from peer/server
        if response != "":
            print(response)

if __name__ == '__main__':
    main()
        