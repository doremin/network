import sys
from socket import *
import os

from django.db import connection

HTTP_STATUS_CODE = {
    404: "NOT FOUND",
    200: "OK"
}

def decode_header(raw_string):
    result = {}
    header_list = list(filter(lambda x: x != "", map(lambda x: x.decode("utf-8"), raw_string)))
    splitted_header_list = list(map(lambda x: x.split(":", 1), header_list))
    headers_list = list(filter(lambda x: len(x) > 1, splitted_header_list))
    
    for item in headers_list:
        result[item[0]] = item[1].lstrip()

    return result

def make_response_header(status_code, content_length, content_type):
    response_header = f"HTTP/1.0 {status_code} {HTTP_STATUS_CODE[status_code]}\r\nConnection: close\r\nContent-Length: {content_length}\r\nContent-Type: {content_type}\r\n\r\n"
    return response_header

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 20171585.py --port")
        exit(0)

    port = int(sys.argv[1])

    print("Student ID : 20171585")
    print("Name : Domin Kim")

    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', port))
    server_socket.listen(1)

    while True:
        connection_socket, address = server_socket.accept()
        request_message = connection_socket.recv(1024)
        request_method = request_message.split(b' ')[0].decode('utf-8')
        request_endpoint = request_message.split(b' ')[1].decode('utf-8')
        request_http_version = request_message.split(b' ')[2].decode('utf-8').split("\n")[0]
        request_header = decode_header(request_message.split(b'\r\n')[:-1])
        print(f'Connection : Host IP {address[0]}, Port {address[1]}, socket {connection_socket.fileno()}')
        print(f'{request_method} {request_endpoint} {request_http_version}')
        print(f'User-Agent: {request_header["User-Agent"]}')
        print(f'{len(request_header)} headers')
        sys.stdout.flush()

        file_size = 0
        try:
            file_size = os.path.getsize(f'.{request_endpoint}')   
        except os.error:
            response_message = make_response_header(404, 0, "text/html")
            connection_socket.sendall(response_message.encode())
            connection_socket.close()
            continue
        
        content_type = "text/html" if request_endpoint.split(".")[-1] == "html" else "image/jpeg"
        response_header = make_response_header(200, file_size, content_type)
        connection_socket.send(bytes(response_header, 'utf-8'))
        print(content_type)
        sys.stdout.flush()
        with open(f'.{request_endpoint}', 'rb') as f:
            response_body = f.readline()
            while True:
                line = f.readline()
                if not line: break
                else: response_body += line
            sended_byte = connection_socket.send(response_body)
            print(f"finish {sended_byte} {file_size}")
            sys.stdout.flush()
        connection_socket.close()

if __name__ == '__main__':
    main()
