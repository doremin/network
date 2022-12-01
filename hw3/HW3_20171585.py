from select import select
import sys
from socket import *
from typing import List, Tuple

message_buffer = []
peers: List[socket] = []
sequence_number = 0
find_buffer = []
pre_printed = []

class CommandArguments:
    def __init__(self, raw_command: str, raw_arguments: str):
        if raw_command == "@connect":
            self.peer_id = None
            self.target_host = raw_arguments[0].strip()
            self.target_port = int(raw_arguments[1].strip())
        elif raw_command == "@query":
            self.peer_id = raw_arguments[0].strip()
            self.target_host = None
            self.target_port = None
        elif raw_command == "@quit":
            self.peer_id = None
            self.target_host = None
            self.target_port = None

class UserInfo:
    def __init__(self, host: str, port: int, user_id: str, username: str):
        self.host = host
        self.port = port
        self.user_id = user_id
        self.username = username

class Query:
    def __init__(self, raw_query: str):
        splitted_query = raw_query.strip().split(" ")
        if len(splitted_query) != 5:
            print(f'invalid query: {raw_query}')
            return
        self.sender_id = splitted_query[1]
        self.sequence_number = int(splitted_query[2])
        self.hop = int(splitted_query[3])
        self.peer_id = splitted_query[4]
    
    def __eq__(self, other) -> bool:
        return (self.sender_id == other.sender_id) and (self.sequence_number == other.sequence_number) and (self.peer_id == other.peer_id)

    def __str__(self) -> str:
        return f"QUERY {self.sender_id} {self.sequence_number} {self.hop} {self.peer_id}\r\n"

def connect(command_arguments: CommandArguments, _):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((command_arguments.target_host, command_arguments.target_port))
    peers.append(client_socket)

def query(command_arguments: CommandArguments, user_info: UserInfo):
    global sequence_number
    global find_buffer
    if command_arguments.peer_id == user_info.user_id:
        print(f"PeerInfo src {user_info.user_id} target {command_arguments.peer_id} {user_info.username} IP 127.0.0.1 port {user_info.port} hop 0")
        return

    for peer in peers:
        peer.sendall(bytes(f"QUERY {user_info.user_id} {sequence_number} {1} {command_arguments.peer_id}\r\n", 'utf-8'))
        print(f'{user_info.port} -> send to {peer.getpeername()[1]}')
    
    sequence_number += 1
    flag = False

    count = 0
    
    while True:
        print("in query select")
        readable, _, _ = select(peers, [], [], 0.2)
        if len(readable) == 0:
            count += 1
            if count >= 4:
                return
            continue
        for r in readable:
            try:
                response = r.recv(1024).decode('utf-8')
            except ConnectionResetError:
                break
            for res in response.split("\r\n"):
                if res == "" or res.isspace():
                    continue
                elif res.startswith("FIND"):
                    splitted_response = res.split(" ")
                    target_username = splitted_response[1]
                    target_ip = splitted_response[2]
                    target_port = splitted_response[3]
                    hop = splitted_response[4]
                    find_buffer.append(f'PeerInfo src {user_info.user_id} target {command_arguments.peer_id} name {target_username} IP {target_ip} port {target_port} hop {hop}')
                    return
            if flag:
                break
        if flag:
            break

def flood(raw_query: str, sender: socket, user_info: UserInfo):
    query = Query(raw_query)
    if query.peer_id == user_info.user_id:
        sender.send(bytes(f"FIND {user_info.username} 127.0.0.1 {user_info.port} {query.hop}\r\n", 'utf-8'))
        return

    if query in message_buffer:
        return

    message_buffer.append(query)
    query.hop += 1

    for peer in peers:
        if peer.getpeername() != sender.getpeername():
            peer.send(bytes(str(query), 'utf-8'))
            print(f'{user_info.port} -> send to {peer.getpeername()[1]}')

    flag = False
    count = 0
    error_count = 0

    while True:
        print("in flood select")
        readable, _, _ = select(list(filter(lambda x: x != sender, peers)), [], [], 0.1)
        if len(readable) == 0:
            count += 1
            if count >= 4:
                return
        for r in readable:
            try:
                response = r.recv(1024).decode('utf-8')
            except ConnectionResetError:
                error_count += 1
                if error_count > 10:
                    return
                break
            for res in response.split("\r\n"):
                if res == "" or res.isspace():
                    continue
                elif res.startswith("FIND"):
                    sender.send(bytes(res.strip(), 'utf-8'))
                    flag = True
                    return
            if flag:
                break
        if flag:
            break
    
def quit(_, __):
    pairs = []

    for f in find_buffer:
        splitted_f = f.split(" ")
        src = splitted_f[2]
        target = splitted_f[4]
        if (src, target) not in pairs:
            pairs.append((src, target))
    
    for pair in pairs:
        min_hop = 9999
        min_f = ""
        for f in find_buffer:
            splitted_f = ""
            if "QUERY" in f:
                splitted_f = f[:-5].split(" ")
            else:
                splitted_f = f.split(" ")
            src = splitted_f[2]
            target = splitted_f[4]
            hop = int(splitted_f[-1])

            if pair[0] == src and pair[1] == target:
                if hop < min_hop:
                    min_hop = hop
                    min_f = f
        print(min_f)

    for peer in peers:
        peer.close()
    exit(0)

COMMANDS = {
    "@connect": connect,
    "@query": query,
    "@quit": quit
}

def main():
    global find_buffer
    global message_buffer

    if len(sys.argv) < 4:
        print("Usage: python3 20171585.py --port --userid --username")
        exit(0)

    print("Student ID : 20171585")
    print("Name : Domin Kim")

    port = int(sys.argv[1])
    user_id = sys.argv[2]
    username = sys.argv[3]

    user_info = UserInfo('', port, user_id, username)

    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((user_info.host, user_info.port))
    server_socket.listen(1)

    while True:
        readable, _, _ = select(peers + [sys.stdin, server_socket], [], [], 0.5)
        for r in readable:
            if r == sys.stdin:
                raw_command = sys.stdin.readline().strip()
                command = raw_command.split(" ")[0].strip()
                raw_arguments = raw_command.split(" ")[1:]
                command_arguments = CommandArguments(command, raw_arguments)

                if command in COMMANDS.keys():
                    COMMANDS[command](command_arguments, user_info)
                elif command == "@quit":
                    quit("", "")
                else:
                    print(f"Invalid Command: {raw_command}")
            elif r == server_socket:
                connection, address = server_socket.accept()
                peers.append(connection)
                print(f'new connection detected: {address}')
            elif r in peers:
                try:
                    response = r.recv(1024).decode('utf-8')
                except ConnectionResetError:
                    pass
                # sender_address = r.getpeername()
                for res in response.split("\r\n"):
                    if res == "" or res.isspace():
                        continue
                    elif res.startswith("FIND"):
                        splitted_response = res.split(" ")
                        target_username = splitted_response[1]
                        target_ip = splitted_response[2]
                        target_port = splitted_response[3]
                        hop = splitted_response[4]
                        find_buffer.append(f'PeerInfo src {user_info.user_id} target {command_arguments.peer_id} name {target_username} IP {target_ip} port {target_port} hop {hop}')
                    else:
                        flood(res.strip(), r, user_info)

                

if __name__ == '__main__':
    main()
