import socket
import select

from app.control_center.parsing import parsing_request, recv_full_request

def startsocket(state):
    ip_address = "0.0.0.0" # ip address for our socket so that clients can find it 
    port = 8080 

    server = socket.socket() # created a socket named server 
    server.bind((ip_address , port)) # binded/assighned the socket with the ip address and the port 
    server.listen() # the socket is listnening for the connection 

    server.setblocking(False)

    buffers = {} # buffer for handling multiple requests , buffers declared as dictionary for saving buffers of multiple clients 

    sockets = [server] # we create a list of sockets to be worked on 

    while True:
        readable, _, _ = select.select(sockets, [], [])   # this helps us to connect to multiple clients 

        for sock in readable:

            # New client connection
            if sock is server:
                client, addr = server.accept()
                client.setblocking(False)
                sockets.append(client)
                buffers[client] = b""
                print("Connected:", addr)

            # Existing client sent HTTP request
            else:
                try:
                    headers_text, body_text, new_buffer = recv_full_request( sock, buffers.get(sock, b"") )

                    # update buffer
                    buffers[sock] = new_buffer

                    if headers_text is None:
                        continue

                    # parse request
                    response = parsing_request(headers_text, body_text, state)

                    print(headers_text)

                    sock.sendall(response)

                except ConnectionResetError:
                    sockets.remove(sock)
                    buffers.pop(sock, None)
                    sock.close()

                    