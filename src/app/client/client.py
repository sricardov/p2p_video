import socket
import threading
import pyaudio
import cv2
import time
import pickle
import struct

from environment.env import environment as env
from app.utils.console import Console
from app.utils.parser import Parser

class Client():

    def __init__(self, username):
        self._username = username
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._controlSocket = None
        self._videoSocket = None
        self._audioSocket = None
        self._controlPort = None
        self._videoPort = None
        self._audioPort = None
        self._ip = 'localhost'
    
    def getSocket(self):
        return self._socket
    
    def getControlSocket(self):
        return self._controlSocket
    
    def getUsername(self):
        return self._username
    
    def getControlPort(self):
        return self._controlPort
    
    def getVideoPort(self):
        return self._videoPort
    
    def getAudioPort(self):
        return self._audioPort

    def run(self):
        """ Client main loop. Tries to connect to the server with an username input. Must be unique.
        If the server accepts the connection, the client starts the command input loop """
        for controlPort in range(49152, 50152):
            try:
                self._controlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._controlSocket.bind(('localhost', controlPort))
                self._controlPort = controlPort
                Console.log(f"Control PORT: {self._controlPort}")
                break
            except:
                pass   
        for videoPort in range(50152, 51152):
            try:
                self._videoSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._videoSocket.bind(('localhost', videoPort))
                self._videoSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, env.BUFF_SIZE)
                self._videoPort = videoPort
                Console.log(f"Video PORT: {self._videoPort}")
                break
            except:
                pass
        for audioPort in range(51152, 52152):
            try:
                self._audioSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._audioSocket.bind(('localhost', audioPort))
                self._audioSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, env.BUFF_SIZE)
                self._audioPort = audioPort
                Console.log(f"Audio PORT: {self._audioPort}")
                break
            except:
                pass
        self.getSocket().connect((env.HOST_IP, env.HOST_PORT))
        self.startConnection(self.getUsername(), self.getControlPort(), self.getVideoPort(), self.getAudioPort())
        response = self.getSocket().recv(env.MSG_MAX_SIZE).decode(env.ENCODING)
        payload = Parser.parseMsg(response)
        Console.log(f"Received: {response}, payload: {payload}")
        if payload["command"] == "ERROR":
            socket.close()
            return
        controlListenThread = threading.Thread(target=self.handleControlListenThread)
        controlListenThread.start()
        while True:
            Console.box("- Select an option -\n1: View Connections\n2: Get Address by Username\n3: Call user\n4: Close")
            option = input()
            if option == "1":
                self.getConnections()
            elif option == "2":
                username = input(">>> Input Username: ")
                self.getConnection(username)
            elif option == "3":
                ip = input(">>> Input IP: ")
                port = input(">>> Input PORT: ")
                self.requestConnection(ip, int(port))
            elif option == "4":
                self.closeConnection()
                break


    # ############### #
    # Command methods #
    # ############### #

    def startConnection(self, username, controlPort, videoPort, audioPort):
        """ Connection request method. Uses username as primary key. Must be unique """
        msg = f"REQ/CONNECT/{username};{controlPort};{videoPort};{audioPort}"
        self.getSocket().send(bytes(msg, env.ENCODING))

    def getConnections(self):
        """ Connection index method. Lists all connected users' usernames """
        msg = f"REQ/CONNECTIONS"
        self.getSocket().send(bytes(msg, env.ENCODING))
        response = self.getSocket().recv(env.MSG_MAX_SIZE).decode(env.ENCODING)
        payload = Parser.parseMsg(response)
        connectionList = payload["args"]
        Console.log(f"{connectionList}")

    def getConnection(self, username):
        """ Connection getter method. Uses username as primary key. Display the client address associated with given username """
        msg = f"REQ/CONNECTION/{username}"
        self.getSocket().send(bytes(msg, env.ENCODING))
        response = self.getSocket().recv(env.MSG_MAX_SIZE).decode(env.ENCODING)
        payload = Parser.parseMsg(response)
        Console.log(f"{payload['args']}")

    def closeConnection(self):
        """ Close connection method """
        msg = "REQ/CLOSE"
        self.getSocket().send(bytes(msg, env.ENCODING))
        self.getSocket().close()

    def requestConnection(self, ip, port):
        """ Request connection with another client. Uses username as primary key """
        self._clientControlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._clientControlSocket.connect((ip, port))
        msg = f"REQ/CALL/{self.getUsername()};{self._ip}:{self._videoPort};{self._ip}:{self._audioPort}"
        self._clientControlSocket.send(bytes(msg, env.ENCODING))
        thread = threading.Thread(target=self.handleControlResponseThread)
        thread.start()


    # ############## #
    # Thread Methods #
    # ############## #  

    def handleControlListenThread(self):
        """ Listens to other clients call requests and opens other threads and sockets accordingly """
        self._controlSocket.listen()
        while True:
            connection, address = self._controlSocket.accept()
            Console.log(f"Accepted connection from {address[0]}:{address[1]}")
            msg = connection.recv(env.MSG_MAX_SIZE).decode(env.ENCODING)
            payload = Parser.parseMsg(msg)
            if payload['operation'] == 'REQ':
                if payload['command'] == 'CALL':
                    username = payload['args'].split(';')[0]
                    videoAddress = payload['args'].split(';')[1].split(':')
                    audioAddress = payload['args'].split(';')[2].split(':')
                    Console.box(f"- Call request from {username} -\ny: Accept\nn: Reject")
                    option = input()
                    if option == 'y':
                        resp = f"RESP/ACCEPT/{self.getUsername()};{self._ip}:{self._videoPort};{self._ip}:{self._audioPort}"
                        connection.send(bytes(resp, env.ENCODING))
                        Console.log('Connection accepted')
                        Console.log('Starting video conference...')
                        videoSendThread = threading.Thread(target=self.handleVideoSenderSocket, args=(videoAddress[0], int(videoAddress[1])))
                        audioSendThread = threading.Thread(target=self.handleAudioSenderSocket, args=(audioAddress[0], int(audioAddress[1])))
                        # videoRecvThread = threading.Thread(target=self.handleVideoRecieverSocket)
                        # audioRecvThread = threading.Thread(target=self.handleAudioRecieverSocket)
                        videoSendThread.start()
                        audioSendThread.start()
                        # videoRecvThread.start()
                        # audioRecvThread.start()
                    elif option == 'n':
                        resp = "RESP/REJECT"
                        connection.send(bytes(resp, env.ENCODING))
                        connection.close()
    
    def handleControlResponseThread(self):
        while True:
            msg = self._clientControlSocket.recv(env.MSG_MAX_SIZE).decode(env.ENCODING)
            payload = Parser.parseMsg(msg)
            if payload['operation'] == 'RESP':
                if payload['command'] == 'ACCEPT':
                    username = payload['args'].split(';')[0]
                    videoAddress = payload['args'].split(';')[1].split(':')
                    audioAddress = payload['args'].split(';')[2].split(':')
                    Console.log(f'Connection accepted by {username}')
                    Console.log('Starting video conference...')
                    # videoSendThread = threading.Thread(target=self.handleVideoSenderSocket, args=(videoAddress[0], int(videoAddress[1])))
                    # audioSendThread = threading.Thread(target=self.handleAudioSenderSocket, args=(audioAddress[0], int(audioAddress[1])))
                    videoRecvThread = threading.Thread(target=self.handleVideoRecieverSocket)
                    audioRecvThread = threading.Thread(target=self.handleAudioRecieverSocket)
                    # videoSendThread.start()
                    # audioSendThread.start()
                    videoRecvThread.start()
                    audioRecvThread.start()
                elif payload['command'] == 'REJECT':
                    Console.log(f'Connection rejected by {username}')
                    break
            elif payload['operation'] == 'ERROR':
                Console.log(f"{payload}")


    def handleVideoSenderSocket(self, ip, port):
        videoSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        videoSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, env.BUFF_SIZE)
        vid = cv2.VideoCapture(0)
        vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)
        while True:
            time.sleep(0.1)
            _, frame = vid.read()
            cv2.imshow("Sender's Video", frame)
            _, buffer = cv2.imencode('.jpeg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
            bytes = pickle.dumps(buffer)
            videoSocket.sendto(bytes, (ip, port))
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                videoSocket.close()
                break;
        cv2.destroyAllWindows()
        vid.release()

    def handleAudioSenderSocket(self, ip, port):
        audioSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        audioSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, env.BUFF_SIZE)
        p = pyaudio.PyAudio()
        stream = p.open(
            format= pyaudio.paInt16,
            channels= env.CHANNELS,
            rate= env.RATE,
            input= True,
            frames_per_buffer= env.AUDIO_CHUNK    
        )
        data = []
        while True:
            time.sleep(0.01)
            data.append(stream.read(env.AUDIO_CHUNK))
            if len(data) > 0:
                audioSocket.sendto(data.pop(0), (ip, port))


    def handleVideoRecieverSocket(self):
        while True:
            data, _ = self._videoSocket.recvfrom(100000000)
            data = pickle.loads(data)
            data = cv2.imdecode(data, cv2.IMREAD_COLOR)
            cv2.imshow('Video', data)
            if cv2.waitKey(10) == 13:
                break
        cv2.destroyAllWindows()           

    def handleAudioRecieverSocket(self):
        p = pyaudio.PyAudio()
        stream = p.open(
            format= pyaudio.paInt16,
            channels= env.CHANNELS,
            rate= env.RATE,
            output= True,
            frames_per_buffer= env.AUDIO_CHUNK
        )
        while True:
            audioData, _ = self._audioSocket.recvfrom(env.BUFF_SIZE)
            stream.write(audioData)
