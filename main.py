import json
import socket
from enum import Enum


class WcpMessageType(Enum):
    COMMAND = "command"
    RESPONSE = "response"
    EVENT = "event"
    GREETING = "greeting"
    ERROR = "error"

    @classmethod
    def from_str(cls, label: str):
        try:
            return cls(label.lower())
        except ValueError:
            return None


class WcpSocket:
    def __init__(self, host="localhost", port=54321):
        self.host = host
        self.port = port
        self.sock = None
        self._buffer = b""

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def send_json(self, data):
        if not self.sock:
            raise ConnectionError("Not connected to the WCP server")
        message = json.dumps(data) + "\0"
        self.sock.sendall(message.encode("utf-8"))

    def receive_json(self):
        if not self.sock:
            raise ConnectionError("Not connected to the WCP server")
        while b"\0" not in self._buffer:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise EOFError("Connection has been closed by the server")
            self._buffer += chunk
        message, self._buffer = self._buffer.split(b"\0", 1)
        return json.loads(message.decode("utf-8"))

    def close(self):
        if self.sock:
            self.sock.close()


class WcpClient:
    def __init__(self, sock: WcpSocket):
        self.sock = sock

    def start(self):
        self.sock.connect()
        init = self.send_greeting()
        if WcpMessageType.from_str(init["type"]) == WcpMessageType.ERROR:
            raise ConnectionError(init["message"])

    def close(self):
        self.sock.close()

    def send_greeting(self):
        data = {"type": "greeting", "version": "0", "commands": []}
        self.sock.send_json(data)
        return self.sock.receive_json()


def main():
    try:
        client = WcpClient(WcpSocket())
        client.start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
