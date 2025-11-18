import socket

def start_server(port=9999):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(1)

        print(f"Server Start... Port : {port}")
        print("Waiting Messages...\n")

        while True:
                try:
                        client_socket, addr = server_socket.accept()
                        message = client_socket.recv(1024).decode('utf-8')
                        print(f"[{addr[0]}] {message}")

                        client_socket.send("OK".encode('utf-8'))
                        client_socket.close()

                except KeyboardInterrupt:
                        print("\nServer stop...")
                        break
                except Exception as e:
                        print(f"Error : {e}")

        server_socket.close()

if __name__ == '__main__':
        import sys
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 9999
        start_server(port)