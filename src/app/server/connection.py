class Connection:
    def __init__(self, client_ip, client_port, username, client_control_port, client_video_port, client_audio_port) -> None:
        self.client_username = username
        self.client_ip = client_ip
        self.client_port = client_port
        self.client_control_port = client_control_port
        self.client_video_port = client_video_port
        self.client_audio_port = client_audio_port