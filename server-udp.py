from socket import *
import threading

HOST = 'localhost'
PORT = 5000
s = socket(AF_INET, SOCK_DGRAM)
s.bind((HOST, PORT))
# while True:                # forever


test_clients = []
test_client = {"clientId": "", "clientAddress": ""}


def receive_messages():
    while True:
        message, addr = s.recvfrom(1024)
        handle_received_message(message, addr)


def handle_received_message(message, address):
    """collect messages and process them

        Args:
        message (String): the received message

        return: nothing
    """
    #@Todo: handle duplicated client_id
    msg_dest_id = message[0:8]
    msg_source_id = message[8:16]
    msg_prefix = message[16:29].strip().split("-")
    msg_tag = msg_prefix[0]
    msg_num = int(msg_prefix[1].split("/")[0])
    msg_total = int(msg_prefix[1].split("/")[1])
    msg = message[29:256]
    
    if(msg_tag == "Connect"):
      test_client = {"clientID": msg_source_id, "clientAddress": address}
      test_clients = test_clients.append(test_client)
      client_thread = threading.Thread(target=receive_messages)
      client_thread.start()
      client_thread.join()
      
    elif(msg_tag == "General"):
      for c in test_clients :
         if(c.clientId == msg_dest_id):
           dest_address =  c.clientAddress
      send_to_client(dest_address, message)
      
      
def send_to_client(client, message):
   s.sendto(message.encode(), client)


receive_messages()



print("received: "+data.decode())
