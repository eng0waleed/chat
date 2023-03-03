from socket import *
HOST = 'localhost'
PORT = 5000
s = socket(AF_INET, SOCK_DGRAM)
s.sendto(''.encode(), (HOST, PORT))  # send some data
data = s.recvfrom(1024)     # receive the response
print(data[0].decode())              # print the result
