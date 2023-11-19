import datetime
import json
import logging
import mimetypes
import pathlib
import socket
import urllib.parse

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_HOST = '0.0.0.0'
HTTP_PORT = 3000
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000


class LearningServer(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))
        client_sever = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_sever.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_sever.close()
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


def save_form(data, db):
    parse_data = urllib.parse.unquote_plus(data.decode()).replace('\r\n', '\n')
    try:
        parse_dict = {key: value for key, value in [el.split('=', 1) for el in parse_data.split('&', 1)]}
        with open(db, 'r', encoding='utf-8') as file:
            load_dict = json.load(file)
            load_dict[datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')] = parse_dict
        with open(db, 'w', encoding='utf-8') as file:
            json.dump(load_dict, file, ensure_ascii=False, indent=4)
    except (ValueError, OSError) as erroor:
        logging.error(erroor)


def run_socket(host, port, db):
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_server.bind((host, port))
    logging.info('Starting socket server')
    try:
        while True:
            data, *_ = socket_server.recvfrom(BUFFER_SIZE)
            save_form(data, db)
    finally:
        socket_server.close()


def run_server(host, port):
    httpserver = HTTPServer((host, port), LearningServer)
    logging.info('Starting http server')
    try:
        httpserver.serve_forever()
    except KeyboardInterrupt:
        httpserver.server_close()


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s: %(message)s')
    db = pathlib.Path(__file__).joinpath('storage/data.json')
    db.parent.mkdir(exist_ok=True)
    if not db.exists() or not db.stat().st_size:
        with open(db, 'w', encoding='utf-8') as fh:
            json.dump({}, fh)
    server_http = Thread(target=run_server, args=(HTTP_HOST, HTTP_PORT))
    server_http.start()
    server_socket = Thread(target=run_socket, args=(SOCKET_HOST, SOCKET_PORT, db))
    server_socket.start()


if __name__ == '__main__':
    main()