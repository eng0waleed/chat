import socket
import threading
import time
import itertools


server_clients = []
my_client_id = "-SERVER-"
interval_of_alive = 1

class ClientThread(threading.Thread):
    id_iter = itertools.count()

    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.clientSocket = clientsocket
        self.clientAddress = clientAddress
        self.clientID = next(self.id_iter)
        self.timeStamp = time.time()
        self.status = "connecting"
        self.do_run = True
        print("New connection added: ", self.clientID)

    def run(self):
        print("Connection from : ", self.clientAddress)
        self.receive_messages()

    def format_message(self, dest_id, tag, message):
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

        temp_message = "{}{}{}{}".format(
            dest_id, my_client_id, "({})".format(tag).ljust(12, '\0'), message)
        messages.append(temp_message)
        return messages

    def handle_quit(self, clientId):
        quit_message = self.format_message("{}".format(self.clientID), "Quit", "")
        self.send_to_client(None, quit_message[0])
        

        for c in server_clients:
            if(c.clientID == clientId):
                server_clients.remove(c)

    def add_alive_timestamp(self, contact):
        print(int(contact.replace("\x00", "").strip()))
        for c in server_clients:
            if(c.clientID == int(contact.replace("\x00","").strip())):
                c.timeStamp = time.time()

    def send_to_client(self, c, message):
        if(c != None):
            print("sending to "+str(c.clientAddress))
            c.clientSocket.send(message.encode())
        else:
            print("sending to "+str(self.clientAddress))
            self.clientSocket.send(message.encode())


    def receive_messages(self):
        while True:
            try:
                message = self.clientSocket.recv(1024)
                if not message:
                    break;  
            except:
                break
            
            self.handle_received_message(message.decode())

    def handle_received_message(self, message):
        #@Todo: handle duplicated client_id
        print(message)
        msg_dest_id = message[0:8]
        msg_source_id = message[8:16]
        msg_prefix = message[16:29].strip()
        msg_tag = msg_prefix.split("(")[1].split(")")[0]
        print(msg_tag)
        msg = message[29:256]
        if(msg_tag == "Connect"):
            alive_interval_message = self.format_message(
            msg_source_id, "alive", "{}".format(interval_of_alive))
            print(alive_interval_message[0])
            self.send_to_client(None,alive_interval_message[0])
            time.sleep(2)

            is_id_exist = self.is_clientid_duplicated(int(msg_source_id.replace("\x00", "").strip()))
            print("is_id_exist : ",is_id_exist)
            if is_id_exist:
                self.ask_for_new_clientid(msg_source_id)
            else:
                self.clientID = int(msg_source_id.replace("\x00", "").strip())
                server_clients.append(self)
                avid_message = self.format_message(msg_source_id, "AVID", "")
                self.send_to_client(None, avid_message[0])

        elif(msg_tag == "General"):
            for c in server_clients:
                if(c.clientID == int(msg_dest_id.replace("\x00", "").strip())):
                    # dest_address = c.clientAddress
                    self.send_to_client(c,message)

        elif(msg_tag == "List"):
            contacts = ""
            for c in server_clients:
                contacts += str(c.clientID).ljust(8, '\0')
            list_message = self.format_message(msg_source_id, "List", contacts)[0]
            self.send_to_client(None,list_message)

        elif(msg_tag == "Alive"):
            self.add_alive_timestamp(msg_source_id.strip())

        elif(msg_tag == "Quit"):
            self.handle_quit(msg_source_id.strip())
            
    def ask_for_new_clientid(self, dest_id):
        message = self.format_message(dest_id, "NVID", "")[0]
        self.send_to_client(None, message)
    
    def is_clientid_duplicated(self, c_id):
        for c in server_clients:
            if c.clientID == c_id:
                return True
        return False



def remove_offline_clients():
    for c in server_clients:
        if(time.time()-c.timeStamp > interval_of_alive):
            server_clients.remove(c)
            print("Client {} disconnected !".format(c.clientID))

def set_remove_offline_contacts_interval():

    def recursive_interval():
        set_remove_offline_contacts_interval()
        remove_offline_clients()
    created_thread = threading.Timer(interval_of_alive, recursive_interval)
    created_thread.start()
    return created_thread


def listen_to_connections(server):
    while True:
        server.listen(1)
        clientsock, clientAddress = server.accept()
        newthread = ClientThread(clientAddress, clientsock)
        newthread.start()


if __name__ == '__main__':
    LOCALHOST = "127.0.0.1"
    PORT = 8080
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LOCALHOST, PORT))
    print("Server started")
    print("Waiting for client request..")

    set_remove_offline_contacts_interval()
    listen_to_connections(server)
