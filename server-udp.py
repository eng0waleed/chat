from socket import *
import threading

HOST = 'localhost'
PORT = 5000
s = socket(AF_INET, SOCK_DGRAM)
s.bind((HOST, PORT))
# while True:                # forever


test_clients = []
test_client = {"clientID": "", "clientAddress": ""}


def receive_messages():
    while True:
        message, addr = s.recvfrom(1024)
        handle_received_message(message.decode(), addr)


def handle_received_message(message, address):
    """collect messages and process them

        Args:
        message (String): the received message

        return: nothing
    """
    #@Todo: handle duplicated client_id
    print(message)
    msg_dest_id = message[0:8]
    msg_source_id = message[8:16]
    msg_prefix = message[16:29].strip().split("-")
    msg_tag = msg_prefix[0][1:]
    msg_num = msg_prefix[1].split("/")[0]
    msg_total = msg_prefix[1].split("/")[1]
    msg = message[29:256]
    if(msg_tag == "Connect"):
      test_client = {"clientID": msg_source_id, "clientAddress": address}
      test_clients.append(test_client)
      
    elif(msg_tag == "General"):
      for c in test_clients :
         if(c["clientID"].strip() == msg_dest_id):
           dest_address = c["clientAddress"]
           send_to_client(dest_address, message)
      
      
def send_to_client(client, message):
  print("sending to "+str(client))
  s.sendto(message.encode(), client)


client_thread = threading.Thread(target=receive_messages)
client_thread.start()
client_thread.join()
