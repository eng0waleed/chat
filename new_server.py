import socket
import threading
import time
import os 

HOST = 'localhost'
PORT = 5000

serverSocket = ""
test_clients = []
test_client = {"clientID": "", "clientAddress": "",
               "timeStamp": "", "clientThread": ""}
my_client_id = "-SERVER-"
interval_of_alive = 10

def startServer():
    serverSocket = socket.socket()
    serverSocket.bind((HOST, PORT))
    serverSocket.listen()
    print("Main PID {}".format(os.getpid()))
    print("Main PID {}".format(threading.get_native_id()))
    while True:
        (clientConnection, clientAddress) = serverSocket.accept()    
        client_t = threading.Thread(
            target=maintain_client_connection, args=(clientAddress, clientConnection))
        client_t.start()
        # client_t.join()

def maintain_client_connection(address, connection):
    print("client PID {}{}".format(os.getpid(), address))
    print("client PID {}{}".format(threading.get_native_id(), address))
    while True:
      message= connection.recv(1024)
      message = message.decode()
      print("from rcv maintain_client_connection  hi"+message)
      msg_dest_id = message[0:8]
      msg_source_id = message[8:16]
      msg_prefix = message[16:29].strip().split("-")
      msg_tag = msg_prefix[0][1:]
      if msg_tag == "Quit" :
        break
      else:
        handle_received_message(message, address)
        break


def remove_offline_clients():
  print("remove_offline_clients")
  for c in test_clients:
    if(time.time()-c["timeStamp"] > interval_of_alive):
      print(test_clients)
      test_clients.remove(c)
      print(test_clients)


def handle_quit(clientId):
  for c in test_clients:
    if(c["clientID"] == clientId):
      print(test_clients)
      test_clients.remove(c)
      print(test_clients)


def format_message(dest_id, tag, message):
    """formatting the message to be "dest_idMy_id(tag-1/1)message\0" with length of 256 bytes  
        
        Args:
        dest_id (String): the id of the destination
        tag (String): the tag refer to the type of the message
        message (String): the message itself
        
        return: list of generated messages
    """
    message_length = len(message)
    dest_id_length = len(dest_id)
    tag_length = len(tag)
    messages = []
    chunk_length = 227  # 239-12 for prefix (tag-msg_num/total)
    number_of_chunks = 0

    if(dest_id):
        if(dest_id_length > 8):  # throw a very large length exception
            raise Exception(
                "length error: destination id length is more than 8 bytes")
        elif(dest_id_length < 8):  # padding the dest_id to be 8 bytes
            # auto padding, see https://docs.python.org/3/library/stdtypes.html#str.ljust
            dest_id = dest_id.ljust(8, '\0')
    else:  # throw a no destination exception
        raise Exception("destination error: destination id is required")

    if(message_length > chunk_length):
        number_of_chunks = message_length / chunk_length
        current_index = 0

        for i in number_of_chunks:
            temp_message = ""
            message_prefix = "({}-{}/{})".format(tag, i,
                                                 number_of_chunks).ljust(12, '\0')
            next_index = current_index + chunk_length

            if(current_index >= message_length):
                break
            elif((current_index + chunk_length) > message_length):
                temp_message = (
                    "{}{}{}{}".format(dest_id, my_client_id, message_prefix,
                                      message[current_index:message_length])
                ).ljust(256, '\0')
            else:
                temp_message = temp_message = (
                    "{}{}{}{}".format(dest_id, my_client_id, message_prefix,
                                      message[current_index:next_index])
                ).ljust(256, '\0')

            messages.append(temp_message)
    else:
        temp_message = "{}{}{}{}".format(
            dest_id, my_client_id, "({}-{}/{})".format(tag, 1, 1).ljust(12, '\0'), message)
        messages.append(temp_message)

    return messages


def handle_received_message(message, address):
    """collect messages and process them

        Args:
        message (String): the received message

        return: nothing
    """
    #@Todo: handle duplicated client_id
    print(message)
    # msg_dest_id = message[0:8]
    # msg_source_id = message[8:16]
    # msg_prefix = message[16:29].strip().split("-")
    # msg_tag = msg_prefix[0][1:]
    # msg_num = msg_prefix[1].split("/")[0]
    # msg_total = msg_prefix[1].split("/")[1]
    # msg = message[29:256]
    # if(msg_tag == "Connect"):
    #   print("new connection")
    #   maintain_client_thread = threading.Thread(
    #       target=maintain_client_connection, args=(address, s))
    #   test_client = {"clientID": msg_source_id, "clientAddress": address,
    #                  "timeStamp": time.time(), "clientThread": maintain_client_thread}
    #   test_clients.append(test_client)
    #   maintain_client_thread.start()
    #   maintain_client_thread.join()
    #   alive_interval_message = format_message(
    #       msg_source_id, "aliveT", "{}".format(interval_of_alive))
    #   print(alive_interval_message[0])
    #   send_to_client(address, alive_interval_message[0])

    # elif(msg_tag == "General"):
    #   for c in test_clients:
    #      if(c["clientID"].strip() == msg_dest_id):
    #        dest_address = c["clientAddress"]
    #        send_to_client(dest_address, message)

    # elif(msg_tag == "@List"):
    #   contacts = ""
    #   for c in test_clients:
    #     contacts += c["clientID"].strip().ljust(8, '\0')
    #   list_message = format_message(msg_source_id, "List", contacts)[0]
    #   send_to_client(address, list_message)

    # elif(msg_tag == "Alive"):
    #   add_alive_timestamp(msg_source_id.strip())

    # elif(msg_tag == "Quit"):
    #   handle_quit(msg_source_id.strip())


def add_alive_timestamp(contact):
  new_contact = ""
  for c in test_clients:
    if(c["clientID"].strip() == contact):
      print(c["timeStamp"])
      c["timeStamp"] = time.time()
      print(c["timeStamp"])


def send_to_client(client, message):
  print("sending to "+str(client))
  s.sendto(message.encode(), client)


def set_remove_offline_contacts_interval():
    def recursive_interval():
      set_remove_offline_contacts_interval()
      remove_offline_clients()
    created_thread = threading.Timer(interval_of_alive, recursive_interval)
    created_thread.start()
    return created_thread


if __name__ == '__main__':
    startServer()