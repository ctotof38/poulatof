
from http.server import BaseHTTPRequestHandler, HTTPServer
import http.client
import threading
import socket
import logging
import time
from datetime import datetime


http_logger = logging.getLogger('http_server')


def open_door():
    http_logger.warning("open door not initialized")


def close_door():
    http_logger.warning("close door not initialized")


# do nothing, just here to not return error when server stopped
def stop_server():
    http_logger.info("stop HTTP server")


actions = [{'command': 'UP', 'function': open_door, "active": True},
           {'command': 'DOWN', 'function': close_door, "active": True},
           {'command': 'STOP', 'function': stop_server, "active": True}]


# get function according to action nane, None if not found
def get_command(name):
    for action in actions:
        if action['active'] and action['command'] in name:
            try:
                return action['function']
            except KeyError:
                pass
    return None


def update_function(name, function):
    for action in actions:
        if action['active'] and action['command'] in name:
            action['function'] = function


# specific HTTP server which accept standard parameters (server_address and handler)
# and two specifics : open_door_callback, close_door_callback
class ApiHttpServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(args) > 2:
            if len(args[2]) > 0:
                update_function('UP', args[2][0])
            if len(args[2]) > 1:
                update_function('DOWN', args[2][1])
        self.running = False
        self.count = 0
        self.current_date = datetime.now()
        server = threading.Timer(0.5, self.serve_forever)
        server.start()

    def serve_forever(self):
        self.running = True
        while self.running:
            self.check_attack()
            self.handle_request()

    def stop_server(self):
        self.running = False
        try:
            conn = http.client.HTTPConnection("localhost", self.server_port, timeout=1)
            conn.request("GET", "/STOP")
        except socket.timeout:
            pass
        finally:
            conn.close()

    # if 5 requests received with less than 2 seconds between them,
    # consider attack, so stop http server
    def check_attack(self):
        date = datetime.now()
        if (date - self.current_date).seconds < 2:
            self.count += 1
        else:
            self.count = 0
        self.current_date = date
        if self.count > 5:
            server = threading.Timer(0.5, self.stop_server)
            server.start()


class CommandRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            command = get_command(str(self.path))
            if command:
                thread = threading.Timer(0.5, command)
                thread.start()
                self.send_response(200)
                self.end_headers()
            else:
                self.send_error(400)
                self.end_headers()
        except BrokenPipeError:
            # can appear when stop server
            pass


# --------------- just for test ---------------
def up_test():
    print("open door updated")


def down_test():
    print("close door updated")


if __name__ == "__main__":
    server_address = ('localhost', 8000)
    httpd = ApiHttpServer(server_address, CommandRequestHandler, (up_test, down_test))

    for i in range(100):
        time.sleep(1)
        print(str(i) + "-", end='', flush=True)
        if i > 99:
            httpd.stop_server()

    print("\nend of test")
