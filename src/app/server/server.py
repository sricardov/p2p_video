import socket
import threading

from environment.env import environment as env
from app.server.connection import Connection
from app.utils.console import Console
from app.utils.parser import Parser

class Server():

    def __init__(self):
        self._ip = env.HOST_IP
        self._port = env.HOST_PORT
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connections: list[Connection] = []

    def getIp(self):
        return self._ip
    
    def getPort(self):
        return self._port
    
    def getSocket(self):
        return self._socket
    
    def getConnections(self):
        return self._connections

    def run(self):
        """ Server main loop. The server listen for connection messages and rejects any other message from clients that are not registered """
        try:
            socket = self.getSocket()
            socket.bind((self.getIp(), self.getPort()))
            socket.listen()
            Console.box(f"Server running. Listening on: {self.getIp()}:{self.getPort()}")

            while True:
                clientSocket, clientAddress = socket.accept()
                Console.log(f"Accepted connection from {clientAddress[0]}:{clientAddress[1]}")
                request = clientSocket.recv(env.MSG_MAX_SIZE).decode(env.ENCODING)
                payload = Parser.parseMsg(request)
                Console.log(f"Received: {request}, payload: {payload}")
                command = payload["command"]

                if command == "CONNECT":
                    username = payload["args"]
                    valid = True
                    for connection in self.getConnections():
                        if connection.client_username == username:
                            valid = False
                    
                    if valid:
                        self.registerClient(clientAddress[0], clientAddress[1], username)
                        thread = threading.Thread(target=self.handleClient, args=(clientSocket, clientAddress))
                        thread.start()
                        response = "RESP/SUCCESS/Connection successful"
                        clientSocket.send(bytes(response, env.ENCODING))
                    else:
                        response = "RESP/ERROR/Username already taken"
                        clientSocket.send(bytes(response, env.ENCODING))
                else:
                    response = "RESP/ERROR/Invalid request"
                    clientSocket.send(bytes(response, env.ENCODING))

        except Exception as e:
            Console.log(f"Error: {e}")
        finally:
            socket.close()

    def handleClient(self, clientSocket, clientAddress):
        """ Client thread method. The server listens for request messages from registered clients and denies any other messages """
        try:
            while True:
                request = clientSocket.recv(env.MSG_MAX_SIZE).decode(env.ENCODING)
                payload = Parser.parseMsg(request)
                Console.log(f"Received: {request}, payload: {payload}")
                command = payload["command"]
                if command == "CLOSE":
                    self.closeConnection(clientSocket, clientAddress)
                elif command == "CONNECTIONS":
                    self.listConnections(clientSocket)
                elif command == "CONNECTION":
                    self.getConnectionAddress(clientSocket, payload["args"])
                else:
                    response = "RESP/ERROR/Invalid request"
                    clientSocket.send(bytes(response, env.ENCODING))

        except Exception as e:
            Console.log(f"Error while hanlding client: {e}")
        finally:
            clientSocket.close()
            Console.log(f"Connection to client {clientAddress[0]}:{clientAddress[1]} closed")


    # ############### #
    # Command methods #
    # ############### #

    def registerClient(self, ip, port, username):
        """ Appends the client connection in the server connection list """
        self.getConnections().append(Connection(ip, port, username))

    def closeConnection(self, clientSocket, clientAddress):
        """ Close connection command method. The server searches for the connected client and removes the connection from the connection list if it exists """
        connectionList = self.getConnections()
        for i in range(len(connectionList)):
            if connectionList[i].client_ip == clientAddress[0] and connectionList[i].client_port == clientAddress[1]:
                del self.getConnections()[i]
        response = "RESP/SUCCESS/Ending connection"
        clientSocket.send(bytes(response, env.ENCODING))
    
    def listConnections(self, clientSocket):
        """ Connection index method """
        userList = []
        for connection in self.getConnections():
            userList.append(connection.client_username)
        response = f"RESP/SUCCESS/{userList}"
        clientSocket.send(bytes(response, env.ENCODING))
    
    def getConnectionAddress(self, clientSocket, username):
        """ Connection getter method. Uses username as primary key """
        address = ""
        for connection in self.getConnections():
            if connection.client_username == username:
                address = f"{connection.client_ip}:{connection.client_port}"
        response = ""
        if address == "":
            response = "RESP/ERROR/User not found"
        else:
            response = f"RESP/SUCCESS/{address}"
        clientSocket.send(bytes(response, env.ENCODING))
