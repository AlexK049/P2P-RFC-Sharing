import argparse

###########################
### User Command Parser ###
###########################
user_cmd_parser = argparse.ArgumentParser()
subparsers = user_cmd_parser.add_subparsers(dest="command", required=True)

#parser for the "ADD" command
add_parser = subparsers.add_parser("add", help="add a locally available RFC to the server's index")
add_parser.add_argument("rfc", help='The RFC number, for example: "RFC 123"')
add_parser.add_argument("title", help='The title of the RFC, for example: "A Proferred Official ICP"')

#parser for the "LOOKUP" command
lookup_parser = subparsers.add_parser("lookup", help="find peers that have the specified RFC")
lookup_parser.add_argument("rfc", help='The RFC number, for example: "RFC 123"')
lookup_parser.add_argument("title", help='The title of the RFC, for example: "A Proferred Official ICP"')

#parser for "LIST" command
list_parser = subparsers.add_parser("list", help="request the whole index of RFCs from the server")

#parser for "exit" command (to end peer)
exit_parser = subparsers.add_parser("exit", help="exit out of this peer and all upload process")

def parse_user_cmd(cmd_str: str):
    return user_cmd_parser.parse_args(cmd_str)


###########################
### P2P Response Parser ###
###########################
def parse_p2p_reponse(peer_response: str):
    #split the response message into lines
    lines = peer_response.split("\n")

    #parse version, status code, and phrase
    status_line = lines[0]
    version, status_code, phrase = status_line.split(" ", 2)

    # Parse the headers
    headers = {}
    for line in lines[1:]:
        if line.strip() == "":
            break
        name, value = line.split(":", 1)
        headers[name.strip()] = value.strip()

    # Get the response body (rfc file data)
    data = "\n".join(lines[len(headers)+2:]).strip()

    return {
                'version': version, 
                'status_code': status_code, 
                'phrase': phrase,
                'headers': headers,
                'data': data
            }


###########################
### S2P Response Parser ###
###########################
def parse_s2p_response(server_message: str):
    #split the response message into lines
    lines = server_message.split("\n")

    #parse version, status code, and phrase
    status_line = lines[0]
    version, status_code, phrase = status_line.split(" ", 2)

    #parse the rfcs
    i = 2 #it is 2 in order to skip the empty line
    rfcs = []
    while i < len(lines) and lines[i].strip() != "":
        rfc_line = lines[i]
        rfc_number, rfc_title, hostname, upload_port = rfc_line.split(" ", 3)
        rfcs.append({
            "rfc_number": rfc_number,
            "rfc_title": rfc_title,
            "hostname": hostname,
            "upload_port_number": upload_port
        })
        i += 1

    return {
                'version': version, 
                'status_code': status_code, 
                'phrase': phrase,
                'rfcs': rfcs
            }

###########################
### Peer Request Parser ###
# (works for requests to peers and server) #
###########################
def parse_peer_request(peer_request: str):
    #split the response message into lines
    lines = peer_request.split("\n")

    #parse version, status code, and phrase
    status_line = lines[0]
    version, status_code, phrase = status_line.split(" ", 2)

    # Parse the headers
    headers = {}
    for line in lines[1:]:
        if line.strip() == "":
            break
        name, value = line.split(":", 1)
        headers[name.strip()] = value.strip()

    return {
                'version': version, 
                'status_code': status_code, 
                'phrase': phrase,
                'headers': headers,
            }
