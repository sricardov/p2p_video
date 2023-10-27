class Parser():

    def parseMsg(msg: str):
        _msg = msg.split("/")
        if len(_msg) == 2:
            payload = {
                'operation': _msg[0],
                'command': _msg[1],
            }
        elif len(_msg) == 3:
            payload = {
                'operation': _msg[0],
                'command': _msg[1],
                'args': _msg[2]
            }
        return payload