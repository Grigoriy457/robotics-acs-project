import socket
from _thread import start_new_thread


HOST = "10.10.10.58"  # Standard loopback interface address (localhost)
PORT = 5001           # Port to listen on (non-privileged ports are > 1023)


def new_connection(connection, addres):
    print("Send callback")
    connection.send("Connected! (from server)".encode("utf-8"))
    while True:
        try:
            data = connection.recv(1024)
        except ConnectionResetError:
            print('Bye (1)')
            break

        if not data:
            print('Bye (2)')
            break
        connection.send(data)
        print(addres, data.decode("utf-8"))
    connection.close()


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print("socket is listening")

    # a forever loop until client wants to exit
    while True:
        # establish connection with client
        connection, addres = s.accept()
        print('Connected to :', addres[0], ':', addres[1])

        # Start a new thread and return its identifier
        start_new_thread(new_connection, (connection, addres))
    s.close()


if __name__ == "__main__":
    main()