# This is Project 1 for CSC401

## General Info
I can guarantee that this project works on Python version 3.11.0 as this was the version that it was tested on.

To run the server enter 'python server.py' in the terminal
To run the peer enter 'python peer.py' in the terminal

The server will run indefinitely or until it is halted.

Peers will run until they receive an exit command or they are halted with a Keyboard Interrupt.

Once the peer is running, a line with 'cmd>' on it will appear. Commands can be entered to interact with the system. The API is detailed in a section below.

## API:
### list
- this will list all RFC's available in the server index
list --local
- this will list all RFC's available locally to that peer. RFC's are not actually files but python objects with the required fields (with these fields being filled with randomly generated information). Once a peer exits, all RFC's associated with this peer will be lost.

### get rfc host
- rfc: The RFC number that you want to get from a remote host, for example: "RFC 123"
- host: the host that the rfc is located on. This will probably just be localhost

### add rfc title
- rfc: The RFC number to add to the server index, for example: "RFC 123"
- title: The title of the RFC to add to the server index, for example: "A Preferred Official ICP".

note: the rfc number and title entered have to be available locally to the peer

### lookup rfc title
- rfc: The RFC number to find from the server index, for example: "RFC 123"
- title: The title of the RFC to find from the server index, for example: "A Preferred Official ICP".

### details what
- what: the thing that you want details of. This can either be 'self' or an RFC number. 

note: If self is entered as the what argument, the host and the port of that instance of peer is printed. If anything else is entered, you are essentially asking the peer to print the info of an RFC with an RFC number equal to what was entered. So for example, if you type 'details "RFC 123"', details related to that rfc will be printed.

### help
enter this get help with what commands you can enter

### exit
If you enter this, the following will happen:

1. The server will acknowledge this request by printing a message to the terminal
2. The server will close the socket associated with that peer
3. The server will remove all data related to that peer from the rfc index list as well as the registered peers list
4. The peer will close its server socket and its upload socket and quit
