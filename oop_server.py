import socket
import threading
import time
import itertools


server_clients = []
my_client_id = "-SERVER-"
interval_of_alive = 1

class ClientThread(threading.Thread):
    """a class that create a thread for each client to handle communication with it
    """
    #to give the client an initial id until receive the id from the client
    id_iter = itertools.count() 

    def __init__(self, clientAddress, clientsocket):
        """constructor of the class

        Args:
            clientAddress (tuple of HOST and IP)
            clientsocket (the socket of this client after accepting the connection)
        """
        threading.Thread.__init__(self)
        self.clientSocket = clientsocket
        self.clientAddress = clientAddress
        self.clientID = next(self.id_iter)
        self.timeStamp = time.time()
        self.status = "connecting"
        self.do_run = True
        print("New connection added: ", self.clientID, self.clientAddress)

    def run(self):
        self.receive_messages()

    def format_message(self, dest_id, tag, message):
        """this function format message in the required format 
        and the order of dest id , source id, tag, and message

        Args:
            dest_id (string)
            tag (string)
            message (string)
        """
        dest_id_length = len(dest_id)
        messages = []
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
        """this function handles the quit of the client. It will remove
        the client object from the list, and send Quit message to the client

        Args:
            clientId (string)
        """
        quit_message = self.format_message("{}".format(self.clientID), "Quit", "")
        self.send_to_client(None, quit_message[0])
        for c in server_clients:
            if(c.clientID == clientId):
                server_clients.remove(c)

    def add_alive_timestamp(self, contact):
        """this function update the timeStamp of each client
        when it send the alive message so it will not be considered as an offline client

        Args:
            contact (string): the if of the contact to be updated
        """
        for c in server_clients:
            if(c.clientID == int(contact.replace("\x00","").strip())):
                c.timeStamp = time.time()

    def send_to_client(self, c, message):
        """this function send the formatted message to a client

        Args:
            c (clientThread)
            message (string)
        """
        if(c != None):
            c.clientSocket.send(message.encode())
        else:
            self.clientSocket.send(message.encode())


    def receive_messages(self):
        """this function keep listening for client messages and pass them to the
        handle_received_message function
        """
        while True:
            try:
                message = self.clientSocket.recv(1024)
                if not message:
                    break;  
            except:
                break
            
            self.handle_received_message(message.decode())

    def handle_received_message(self, message):
        """this function split the message into its component
        and then deal with it based on its tag

        Args:
            message (string)
        """
        msg_dest_id = message[0:8]
        msg_source_id = message[8:16]
        msg_prefix = message[16:29].strip()
        msg_tag = msg_prefix.split("(")[1].split(")")[0]
        msg = message[29:256]
        if(msg_tag == "Connect"):
            alive_interval_message = self.format_message(
            msg_source_id, "alive", "{}".format(interval_of_alive))
            self.send_to_client(None,alive_interval_message[0])
            time.sleep(2)

            is_id_exist = self.is_clientid_duplicated(int(msg_source_id.replace("\x00", "").strip()))
            if is_id_exist:
                self.ask_for_new_clientid(msg_source_id)
            else:
                self.clientID = int(msg_source_id.replace("\x00", "").strip())
                server_clients.append(self)
                avid_message = self.format_message(msg_source_id, "AVID", "")
                self.send_to_client(None, avid_message[0])
                for c in server_clients:
                    c.send_list_to_client()


        elif(msg_tag == "General"):
            for c in server_clients:
                if(c.clientID == int(msg_dest_id.replace("\x00", "").strip())):
                    self.send_to_client(c,message)

        elif(msg_tag == "List"):
            self.send_list_to_client()
        elif(msg_tag == "Alive"):
            self.add_alive_timestamp(msg_source_id.strip())

        elif(msg_tag == "Quit"):
            self.handle_quit(msg_source_id.strip())
            
    def ask_for_new_clientid(self, dest_id):
        """if the client id is already exist it will ask the client
        to provide a new unique id

        Args:
            dest_id (string)
        """
        message = self.format_message(dest_id, "NVID", "")[0]
        self.send_to_client(None, message)
    
    def is_clientid_duplicated(self, c_id):
        """check if client id provided by the new client
        exist in the server_clients list

        Args:
            c_id (string)
        """
        for c in server_clients:
            if c.clientID == c_id:
                return True
        return False
    
    def send_list_to_client(self):
        """send the clients list to the client
        """
        contacts = ""
        msg_source_id = "{}".format(self.clientID).ljust(8, '\0')
        for c in server_clients:
            contacts += str(c.clientID).ljust(8, '\0')
        list_message = self.format_message(
            msg_source_id, "List", contacts)[0]
        self.send_to_client(None, list_message)




def remove_offline_clients():
    """check if time stamp of a client is > interval_of alive
    and remove it if so.
    """
    global server_clients
    for c in server_clients:
        if(time.time()-c.timeStamp > interval_of_alive):
            server_clients.remove(c)
            print("Client {} disconnected !".format(c.clientID))
            for c in server_clients:
                c.send_list_to_client()
        

def set_remove_offline_contacts_interval():
    """timer thread to check the clients alive timestamp periodically
    """

    def recursive_interval():
        set_remove_offline_contacts_interval()
        remove_offline_clients()
    created_thread = threading.Timer(interval_of_alive, recursive_interval)
    created_thread.start()
    return created_thread


def listen_to_connections(server):
    """keep listening for connection requests and accepted them,
    them create a new object of ClientThread class for each new connection
    """
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
