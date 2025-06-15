from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import threading
import time
import logging


UP = 'up'
DOWN = 'down'
FORCE_UP = 'force_up'
FORCE_DOWN = 'force_down'

http_logger = logging.getLogger('http_server')


def open_door():
    http_logger.warning("open door not initialized")


def close_door():
    http_logger.warning("close door not initialized")


actions = {UP: {'function': open_door, "active": True},
           DOWN: {'function': close_door, "active": True},
           FORCE_UP: {'function': open_door, "active": True},
           FORCE_DOWN: {'function': close_door, "active": True}}


def get_command(name: str) -> any:
    """get function according to action name

    Args:
        name (str): the name of action, UP, DOWN, FORCE_UP, FORCE_DOWN

    Returns:
        any: None if not found
    """
    if name is None:
        return None
    try:
        action = actions[name]
        if action['active']:
            return action['function']
    except KeyError:
        pass
    return None


def update_function(name: str, function: str =None) -> bool:
    """update default function according to its name

    Args:
        name (str): the name of action, UP, DOWN, FORCE_UP, FORCE_DOWN
        function (str, optional): the new function. Defaults to None.

    Returns:
        bool: True if update is ok
    """
    if function is None:
        return False
    try:
        action = actions[name]
        if action['active']:
            action['function'] = function
        return True
    except KeyError:
        return False


class CommandRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, token: str = None, **kwargs):
        self.token = token
        super().__init__(*args, **kwargs)

    def do_POST(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or auth_header != self.token:
            self.send_response(401)
            self.end_headers()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        data = parse_qs(post_data.decode())

        try:
            action = data['action'][0]
        except KeyError:
            self.send_response(400)
            self.end_headers()
            return

        command = get_command(action)

        if command is not None:
            thread = threading.Timer(0.5, command)
            thread.start()
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(400)
            self.end_headers()
            return


class ApiHttpServer:
    def __init__(self, port: str, token: str, up = None, down = None, force_up = None, force_down = None):
        """http server

        Args:
            port (str): port to use
            token (str): authentication token
            up (optional): function to launch for this keyword. Defaults to None.
            down (optional): function to launch for this keyword. Defaults to None.
            force_up (optional): function to launch for this keyword. Defaults to None.
            force_down (optional): function to launch for this keyword. Defaults to None.
        """
        self.port = port
        self.token = token
        self.server = None
        self.thread = None
        update_function(UP, up)
        update_function(DOWN, down)
        update_function(FORCE_UP, force_up)
        update_function(FORCE_DOWN, force_down)
        self.is_running = False

    def start(self):
        handler = lambda *args, **kwargs: CommandRequestHandler(*args, token=self.token, **kwargs)
        self.server = HTTPServer(('localhost', self.port), handler)
        self.is_running = True
        self.thread = threading.Thread(target=self._run_server)
        # stop thread when main program is stopped
        self.thread.daemon = True
        http_logger.info(f'Server starts on port {self.port}')
        self.thread.start()

    def _run_server(self):
        while self.is_running:
            self.server.handle_request()

    def stop(self):
        self.is_running = False
        if self.server:
            self.server.server_close()
        if self.thread:
            self.thread.join()
        http_logger.info('Server is stopped')

# Example
def up_test():
    print("open door updated")


def down_test():
    print("close door updated")


if __name__ == '__main__':
    server = ApiHttpServer(8000, 'secret-token', up_test, down_test)
    server.start()

    try:
        while True:
            print("Programme principal en cours d'exécution...")
            time.sleep(50)
    except KeyboardInterrupt:
        server.stop()
