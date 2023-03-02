import socket
import threading
import time
import itertools


test_clients = []
my_client_id = "-SERVER-"
interval_of_alive = 10

class ClientThread(threading.Thread):
    id_iter = itertools.count()

    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.clientSocket = clientsocket
        self.clientAddress = clientAddress
        self.clientID = next(self.id_iter)
        self.timeStamp = time.time()
        print("New connection added: ", self.clientID)

    def run(self):
        print("Connection from : ", self.clientAddress)
        #self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        # msg = ''
        # while True:
        #     data = self.csocket.recv(2048)
        #     msg = data.decode()
        #     if msg == 'bye':
        #       break
        #     print("from client", msg)
        #     self.csocket.send(bytes(msg, 'UTF-8'))
        self.receive_messages()
        print("Client at ", self.clientAddress, " disconnected...")

    def format_message(self, dest_id, tag, message):
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
        my_client_id = "-SERVER-"

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

    def handle_quit(self, clientId):
        for c in test_clients:
            if(c["clientID"] == clientId):
                print(test_clients)
                test_clients.remove(c)
                print(test_clients)

    def add_alive_timestamp(self, contact):
        print(contact)
        for c in test_clients:
            if(c.clientID == int(contact)):
                print(c.timeStamp)
                c.timeStamp = time.time()
                print(c.timeStamp)

    def send_to_client(self, message):
        print("sending to "+str(self.clientAddress))
        self.clientSocket.send(message.encode())

    def receive_messages(self):
        while True:
            message = self.clientSocket.recv(1024)
            self.handle_received_message(message.decode())

    def handle_received_message(self, message):
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
            test_clients.append(self)
            alive_interval_message = self.format_message(
                msg_source_id, "aliveT", "{}".format(9))
            print(alive_interval_message[0])
            self.send_to_client(alive_interval_message[0])

        elif(msg_tag == "General"):
            for c in test_clients:
                if(c.clientID == msg_dest_id):
                    # dest_address = c.clientAddress
                    self.send_to_client(message)

        elif(msg_tag == "@List"):
            contacts = ""
            for c in test_clients:
                contacts += str(c.clientID).ljust(8, '\0')
            list_message = self.format_message(
                msg_source_id, "List", contacts)[0]
            self.send_to_client(list_message)

        elif(msg_tag == "Alive"):
            self.add_alive_timestamp(msg_source_id.strip())

        elif(msg_tag == "Quit"):
            self.handle_quit(msg_source_id.strip())
            


LOCALHOST = "127.0.0.1"
PORT = 8080
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))
print("Server started")
print("Waiting for client request..")


def remove_offline_clients():
    for c in test_clients:
        if(time.time()-c.timeStamp > interval_of_alive):
            print(test_clients)
            test_clients.remove(c)
            print(test_clients)

def set_remove_offline_contacts_interval():

    def recursive_interval():
        set_remove_offline_contacts_interval()
        remove_offline_clients()
    created_thread = threading.Timer(interval_of_alive, recursive_interval)
    created_thread.start()
    return created_thread


set_remove_offline_contacts_interval()
while True:
    server.listen(1)
    clientsock, clientAddress = server.accept()
    newthread = ClientThread(clientAddress, clientsock)
    newthread.start()