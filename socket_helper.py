import socket

#this makes it so that all data is received from a socket
def recv_all(socket: socket):
    socket.settimeout(0.25)
    response = b""
    while True:
        try:
            chunk = socket.recv(1024)
        except:
            break

        if not chunk: # break the loop if no more data is received
            break
        response += chunk
    socket.settimeout(None)
    return response