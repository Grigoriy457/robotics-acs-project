import socket
import config

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("10.10.10.58", 5001))  # Ваш IPv4 адрес и порт который вы указали в файле server.py
# print(client.recv(1024).decode('utf8'))

while True:
    text = input('>>> ')
    if text != "":
        client.send(text.encode("utf-8"))
        print("<<<", client.recv(1024).decode("utf-8"))

        if text == "exit":
            break

client.close()