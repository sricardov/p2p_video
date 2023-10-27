class Connection:
    def __init__(self, client_ip, client_port, username) -> None:
        self.client_username = username
        self.client_ip = client_ip
        self.client_port = client_port