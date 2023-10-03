class Connection:
    def __init__(self, host_ip, host_port, client_ip, client_port) -> None:
        self.host_ip = host_ip
        self.host_port = host_port
        self.client_ip = client_ip
        self.client_port = client_port