from src.networking.connection import MinecraftConnection
from src.networking.listen_thread import ListenThread
from src.networking.auth import Auth

import argparse


parser = argparse.ArgumentParser(add_help=True)
parser.add_argument('--ip', help='The ip address of the server to connect to (e.g localhost)')
parser.add_argument('--port', default=25565, help='The port of the server to connect to (default=25565)')
parser.add_argument('--protocol', default=340, type=int, help='The protocol version of the server to connect to (default=340)')
parser.add_argument('--username', help='Your Mojang account username (an email or legacy name)')
parser.add_argument('--password', help='Your Mojang account password')
parser.add_argument('--dport', default=1337, type=int, help='The port to connect to with mcidle (default=1337)')
args = parser.parse_args()


def update_credentials(username, password):
    if not Auth.has_credentials():
        if username is None or username is None:
            raise ValueError("Please provide both your username and password.")

        auth = Auth()
        Auth.save_to_disk(auth.authenticate(username=username, password=password))

def try_auth(username, password):
    update_credentials(args.username, args.password)

    credentials = Auth.read_from_disk()
    auth = Auth().assign_profile(credentials)

    if not auth.validate():
        Auth.delete_credentials()
        return None # Invalid credentials
    else:
        print("Credentials are valid!", flush=True)
    return credentials
        
def init():
    if args.ip is None:
        raise RuntimeError("Please specify an ip address!")

    # We use this to listen for incoming connections
    listen_thread = ListenThread(address=('localhost', args.dport))
    listen_thread.start()

    # We do this loop because the session information may be invalidated at any point
    # Due to restarting the Minecraft client over and over
    # So when we reconnect we need to generate potentially new credentials to avoid session errors
    import time
    while True:
        credentials = try_auth(args.username, args.password) # Make sure we can still auth
        if credentials:
            listen_thread.set_server(None)
            conn = MinecraftConnection(ip=args.ip, port=args.port, server_port=args.dport, protocol=args.protocol, \
                                       username=credentials['selectedProfile']['name'], profile=credentials, \
                                       listen_thread=listen_thread)
            conn.run_handler()
            print("Disconnected..reconnecting in 5 seconds", flush=True)
            time.sleep(5)
            print("Reconnecting..", flush=True)
        else:
            if not args.username or not args.password:
                print("Can't re-auth user because no user or password provided!", flush=True)
                return
            print("Trying to auth again", flush=True)
            time.sleep(3)

if __name__ == '__main__':
    init()