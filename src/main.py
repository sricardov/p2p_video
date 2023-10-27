from app.server.server import Server
from app.client.client import Client
from app.utils.console import Console

Console.box("- Select an option -\n1: Run Server\n2: Run Client")
option = input(">>> ")

if option == "1":
    server = Server()
    server.run()

elif option == "2":
    username = input(">>> Please, enter your username: ")
    client = Client(username)
    client.run()