import socket
import threading
import time
import itertools
id_iter = 2
my_client_id = "{}".format(id_iter).ljust(8, '\0')

SERVER = "127.0.0.1"
PORT = 8080
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# my_client_id = "1".ljust(8, '\0')
remaining_messages = 0
tag_of_last_received_message = ""
source_of_last_received_message = ""
current_message = ""
contacts_list = []
alive_interval = 0
sender_thread = ""
receiver_thread = ""
interval_thread = ""
app_quitted = False


def format_message(dest_id, tag, message):
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

    temp_message = "{}{}{}{}".format(
        dest_id, my_client_id, "({})".format(tag).ljust(12, '\0'), message)
    print(temp_message)
    messages.append(temp_message)
    return messages



def send_message(formatted_message):
    """send the formatted messages to the server
        
        Args:
        formatted_message (String): the formatted message
        
        return: nothing
    """
    client.send(formatted_message.encode())  # formatted_message.encode())


def handle_received_message(message):
    """collect messages and process them

        Args:
        message (String): the received message

        return: nothing
    """
    global sender_thread
    global current_message
    # global app_quitted
    msg_dest_id = message[0:8]
    msg_source_id = message[8:16]
    msg_prefix = message[16:28].strip()
    msg_tag = msg_prefix.split("(")[1].split(")")[0]
    msg = message[28:256]
    print("[{}]: {}".format(msg_source_id, msg))

    if(msg_tag == "NVID"):
        print("NVID [{}]: {}".format(msg_source_id, msg))
        ask_for_new_id()
    elif(msg_tag == "AVID"):
        print("AVID [{}]: {}".format(msg_source_id, msg))
        sender_thread = threading.Thread(target=show_available_options)
        sender_thread.start()
        sender_thread.do_run = True
        # sender_thread.join()
    elif(msg_tag == "List"):
        set_online_contact_list(msg)
    elif(msg_tag == "alive"):
        set_alive_interval(msg)
    elif(msg_tag == "error"):
        print("[{}][error]: {}".format(msg_source_id, msg))
    elif(msg_tag == "Quit"):
        app_quitted = True
        print("You have quitted the app")

def set_online_contact_list(list):
    """get contacts out of the message and set them in contacts_list, and print them

        Args:
        list (String): contacts in a string(everyone of them is 8 bytes)

        return: nothing
    """
    num_of_contacts = int(len(list)/8)
    contacts_list = []
    print("====================")
    print("Your contacts list :")
    print("you have {} contact/s".format(num_of_contacts))

    for c in range(num_of_contacts):
        start_index = c*8
        end_index = start_index + 8
        contact = list[start_index:end_index]
        contacts_list.append(contact.strip())
        print("{}. {}".format(c+1, contact))


def set_alive_interval(interval):
    """set the interval to send alive message

        Args:
        interval (String): the interval in string

        return: nothing
    """
    global interval_thread
    interval = int(interval)
    alive_interval = interval
    alive_message = format_message("-SERVER-", "Alive", "")
    # interval_thread.close()
    interval_thread = set_interval(
        send_message, alive_message[0], alive_interval)


def set_interval(send_alive, message, interval):
    """equivalence to setInterval but in python, it will call send_alive each interval

        Args:
        send_alive (function): the function to send alive message
        interval (number): the interval

        return: the thread that will work on sending alive messages
    """
    def recursive_interval():
        if(app_quitted == False):
            set_interval(send_alive, message, interval)
            send_alive(message)
    created_thread = threading.Timer(interval, recursive_interval)
    created_thread.start()
    return created_thread


def get_contacts_list():
    """send List message to the server

        Args:

        return: nothing
    """
    list_message = format_message("-SERVER-", "List", "")
    send_message(list_message[0])


def quit():
    """send Quit message to the server and stop the socket and the interval thread, also clear all variables

        Args:

        return: nothing
    """
    global sender_thread
    global receiver_thread
    global interval_thread
    global app_quitted
    quit_message = format_message("-SERVER-", "Quit", "")
    send_message(quit_message[0])
    # if(interval_thread != ""):
    # interval_thread.stop()
    # receiver_thread.close()
    # sender_thread.close()
    alive_interval = 0
    app_quitted = True
    interval_thread.cancel()
    sender_thread.do_run = False
    receiver_thread.do_run = False

    client.close
    remaining_messages = 0
    tag_of_last_received_message = ""
    source_of_last_received_message = ""
    current_message = ""
    contacts_list = []


def send_message_to_client(message, dest_id):
    """format the message and the send the message/s to the server with the client_id,
        tag = General

        Args:
            dest_id (String): the id of the destination
            message (String): the message itself


        return: nothing
    """
    messages = format_message(dest_id, "General", message)
    for m in messages:
        send_message(m)


def handle_user_command(command):
    """handle the commands written by the user

        Args:
            command (String): the user input


        return: nothing
    """
    if(command == "@List"):
        get_contacts_list()
    elif(command == "@Quit"):
        quit()
    elif(command == "@help"):
        show_help()
    elif(command == "@message"):
        client_id = input("Enter the destination client id : ")
        message = input("Enter the message : ")
        send_message_to_client(message, client_id)
    else:
        print("The inserted command is not correct, to get help write @help")
    if(getattr(sender_thread,"do_run", True)):
        show_available_options()


def show_help():
    """show the list of commands that the user can use,

        Args:
            

        return: nothing
    """
    print("Welcome to chatClient helper \n you can enter one of the following commands:")
    print("1- @List - to get the list of online contacts")
    print("2- @Quit - to quit the app")
    print("3- @help - to get this message")


def receive_messages():
    while getattr(receiver_thread,"do_run", True):
        message = client.recv(1024)
        print("to test receive")
        handle_received_message(message.decode())
    client.close()

def show_available_options():
    print("=============")
    print("1- to get the contact list enter @List")
    print("2- to quit the app enter @Quit")
    print("3- send message to a client enter @message")
    choice = input("Enter your selected option : ")
    handle_user_command(choice)


def ask_for_new_id():
    global id_iter
    global my_client_id
    print("==========================")
    print("Error: the selected id is not accepted, ")
    id_iter = int(input("Enter a new id as a digit : "))
    my_client_id = "{}".format(id_iter).ljust(8, '\0')
    connect_message = format_message("-SERVER-", "Connect", "")
    send_message(connect_message[0])



client.connect((SERVER, PORT))
connect_message = format_message("-SERVER-", "Connect", "")
send_message(connect_message[0])
# while True:
#   in_data = client.recv(1024)
#   print("From Server :", in_data.decode())
#   out_data = input()
# #   client.sendall(bytes(out_data, 'UTF-8'))
#   if out_data == 'bye':
#     break
receiver_thread = threading.Thread(target=receive_messages)
# sender_thread = threading.Thread(target=show_available_options)
receiver_thread.start()
# sender_thread.start()
receiver_thread.do_run = True
# sender_thread.do_run = True
# sender_thread.join()
# receiver_thread.join()



