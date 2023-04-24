import argparse
import shlex
from jsobject import JSObject

# source: https://stackoverflow.com/questions/14728376/i-want-python-argparse-to-throw-an-exception-rather-than-usage
class ArgumentParserError(Exception): pass
class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)

###########################
### User Command Parser ###
###########################
user_cmd_parser = ThrowingArgumentParser()
subparsers = user_cmd_parser.add_subparsers(dest="command", required=True)

#parser for the "ADD" command
add_parser = subparsers.add_parser("add", help="add a locally available RFC to the server's index")
add_parser.add_argument("rfc", help='The RFC number, for example: "RFC 123"')
add_parser.add_argument("title", help='The title of the RFC, for example: "A Preferred Official ICP"')

#parser for the "LOOKUP" command
lookup_parser = subparsers.add_parser("lookup", help="find peers that have the specified RFC")
lookup_parser.add_argument("rfc", help='The RFC number, for example: "RFC 123"')
lookup_parser.add_argument("title", help='The title of the RFC, for example: "A Preferred Official ICP"')

#parser for "LIST" command
list_parser = subparsers.add_parser("list", help="request the whole index of RFCs from the server")
list_parser.add_argument("--local", action="store_true", help="Specify this flag if you only wish to see RFC files that are stored locally")

#parser for "get" command
get_parser = subparsers.add_parser("get", help="get an RFC from the specified peer")
get_parser.add_argument("rfc", help='The RFC number you are requesting, for example: "RFC 123"')
get_parser.add_argument("host", help="The host that the specified RFC is located on")

#parser for "details" command
details_parser = subparsers.add_parser("details", help="view host and port of this process or details of an rfc")
details_parser.add_argument("what", help="The thing that you want details for. Can be either 'self' or an RFC number located on your system. ex: 'RFC 456'")

#parser for "help" command
help_parser = subparsers.add_parser("help", help="view help menu")

#parser for "exit" command (to end peer)
exit_parser = subparsers.add_parser("exit", help="exit out of this peer and all upload process, remove all associated entries from server index")

def parse_user_cmd(cmd_str: str):
    return user_cmd_parser.parse_args(shlex.split(cmd_str))


###########################
### P2P Response Parser ###
###########################
def parse_p2p_reponse(peer_response: str):
    #split the response message into lines
    lines = peer_response.split("\n")

    #parse version, status code, and phrase. note: phrase can have spaces in it so split doesn't work
    status_line = lines[0]
    first_space_index = status_line.find(' ')
    second_space_index = status_line.find(' ', first_space_index + 1)
    version = status_line[:first_space_index]
    status_code = status_line[first_space_index + 1:second_space_index]
    phrase = status_line[second_space_index + 1:]

    # Parse the headers
    headers = {}
    for line in lines[1:]:
        if line.strip() == "":
            break
        name, value = line.split(":", 1)
        headers[name.strip()] = value.strip()

    # Get the response body (rfc file data)
    data = "\n".join(lines[len(headers)+2:]).strip()

    ret_obj = JSObject(**{
        'version': version, 
        'status_code': status_code, 
        'phrase': phrase,
        'headers': headers,
        'data': data
    })
    return ret_obj


###########################
### S2P Response Parser ###
###########################
def parse_s2p_response(server_message: str):
    #split the response message into lines
    lines = server_message.split("\n")

    #parse version, status code, and phrase
    status_line = lines[0]
    first_space_index = status_line.find(' ')
    second_space_index = status_line.find(' ', first_space_index + 1)
    version = status_line[:first_space_index]
    status_code = status_line[first_space_index + 1:second_space_index]
    phrase = status_line[second_space_index + 1:]

    #parse the rfcs
    i = 2 #it is 2 in order to skip the empty line
    rfcs = []
    while i < len(lines) and lines[i].strip() != "":
        rfc_line = lines[i]
        second_space_index = rfc_line.find(' ', rfc_line.find(' ') + 1)
        last_space_index = rfc_line.rfind(' ')
        second_last_space_index = rfc_line.rfind(' ', 0, rfc_line.rfind(' '))

        rfc_number = rfc_line[:second_space_index]
        rfc_title = rfc_line[second_space_index + 1:second_last_space_index]
        hostname = rfc_line[second_last_space_index + 1:last_space_index]
        upload_port = rfc_line[last_space_index + 1:]
        rfcs.append(JSObject(**{
            "rfc_number": rfc_number,
            "rfc_title": rfc_title,
            "hostname": hostname,
            "upload_port_number": upload_port
        }))
        i += 1
    ret_obj = JSObject(**{
        'version': version, 
        'status_code': status_code, 
        'phrase': phrase,
        'rfcs': rfcs
    })
    return ret_obj
    

###########################
### Peer Request Parser ###
# (works for requests to peers and server) #
###########################
def parse_peer_request(peer_request: str):
    #split the response message into lines
    lines = peer_request.split("\n")

    #parse command, rfc_number, and version. note: rfc_number can have spaces
    status_line = lines[0]
    first_space_index = status_line.find(' ')
    last_space_index = status_line.rfind(' ')
    command = status_line[:first_space_index]
    rfc_number = status_line[first_space_index + 1:last_space_index]
    version = status_line[last_space_index + 1:]

    # Parse the headers
    headers = {}
    for line in lines[1:]:
        if line.strip() == "":
            break
        name, value = line.split(":", 1)
        headers[name.strip()] = value.strip()

    ret_obj = JSObject(**{
        'command': command,
        'rfc_number': rfc_number,
        'version': version,
        'headers': headers,
    })
    return ret_obj
