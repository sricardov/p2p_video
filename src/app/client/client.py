import socket
import threading
import os
import sys

from environment.env import environment as env
from app.server.connection import Connection
from app.utils.console import Console
from app.utils.parser import Parser

class Client():

    def __init__(self, username):
        self._username = username
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def getSocket(self):
        return self._socket
    
    def getUsername(self):
        return self._username

    def run(self):
        socket = self.getSocket()
        socket.connect((env.HOST_IP, env.HOST_PORT))
        self.startConnection(self.getUsername())
        response = socket.recv(env.MSG_MAX_SIZE).decode(env.ENCODING)
        payload = Parser.parseMsg(response)
        Console.log(f"Received: {response}, payload: {payload}")
        if payload["command"] == "ERROR":
            socket.close()
            return

        while True:
            Console.box("- Select an option -\n1: View Connections\n2: Get Address by Username\n3: Close")
            option = input()

            if option == "1":
                self.getConnections()
            elif option == "2":
                username = input(">>> Input Username: ")
                self.getConnection(username)
            elif option == "3":
                self.closeConnection()
                break

    def startConnection(self, username):
        socket = self.getSocket()
        msg = f"REQ/CONNECT/{username}"
        socket.send(bytes(msg, env.ENCODING))

    def getConnections(self):
        socket = self.getSocket()
        msg = f"REQ/CONNECTIONS"
        socket.send(bytes(msg, env.ENCODING))
        response = socket.recv(env.MSG_MAX_SIZE).decode(env.ENCODING)
        payload = Parser.parseMsg(response)
        connectionList = payload["args"]
        Console.log(f"{connectionList}")

    def getConnection(self, username):
        socket = self.getSocket()
        msg = f"REQ/CONNECTION/{username}"
        socket.send(bytes(msg, env.ENCODING))
        response = socket.recv(env.MSG_MAX_SIZE).decode(env.ENCODING)
        payload = Parser.parseMsg(response)
        Console.log(f"{payload['args']}")

    def closeConnection(self):
        socket = self.getSocket()
        msg = "REQ/CLOSE"
        socket.send(bytes(msg, env.ENCODING))
        socket.close()