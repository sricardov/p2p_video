import json

class Parser:
    def parseMsg(msg: str):
        _msg = msg.split("/")
        _json = json.dumps({
            'operation': _msg[0],
            'command': _msg[1],
            'payload': _msg[2]
        })
        return _json