from socket import *
import threading

HOST = 'localhost'
PORT = 5000
my_socket = socket(AF_INET, SOCK_DGRAM)

my_client_id = "1".ljust(8, '\0')
remaining_messages = 0
tag_of_last_received_message = ""
source_of_last_received_message = ""
current_message = ""
contacts_list = []
alive_interval = 0


def dummy():
    return


interval_thread = threading.Timer(10000, dummy)
sender_thread = threading.Thread()
receiver_thread = threading.Thread()


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


def send_message(formatted_message):
    """send the formatted messages to the server
        
        Args:
        formatted_message (String): the formatted message
        
        return: nothing
    """
    my_socket.sendto(formatted_message.encode(), (HOST, PORT))


def handle_received_message(message):
    """collect messages and process them

        Args:
        message (String): the received message

        return: nothing
    """
    msg_dest_id = message[0:8]
    msg_source_id = message[8:16]
    msg_prefix = message[16:29].strip().split("-")
    msg_tag = msg_prefix[0][1:]
    # msg_num = int(msg_prefix[1].strip().split("/")[0])
    # msg_total = int(msg_prefix[1].strip().split("/")[1])
    msg = message[28:256]
    print("[{}]: {}".format(msg_source_id, msg))

    tag_of_last_received_message = msg_tag
    source_of_last_received_message = msg_source_id
    remaining_messages = 0

    # if(msg_num == 1):
    #     current_message = msg
    # else:
    #     current_message += msg

    # if(msg_num < msg_total):
    #     remaining_messages = msg_total - msg_num
    # elif(msg_total - msg_num == 0):
    #     print("[{}][{}]:{}".format(msg_source_id, msg_tag, current_message))

    if(msg_tag == "list"):
        set_online_contact_list(current_message)
    elif(msg_tag == "aliveT"):
        set_alive_interval(msg)
    elif(msg_tag == "error"):
        print("[{}][error]: {}".format(msg_source_id, msg))
    # else:
        # print("[{}][unknown type of message]: {}".format(msg_source_id, msg))


def set_online_contact_list(list):
    """get contacts out of the message and set them in contacts_list, and print them

        Args:
        list (String): contacts in a string(everyone of them is 8 bytes)

        return: nothing
    """
    num_of_contacts = list/8
    contacts_list = []
    print("====================")
    print("Your contacts list :")

    for c in num_of_contacts:
        start_index = c*8
        end_index = start_index + 8
        contact = list[start_index:end_index]
        contacts_list.append(contact)
        print(c+". "+contact)


def set_alive_interval(interval):
    """set the interval to send alive message

        Args:
        interval (String): the interval in string

        return: nothing
    """
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
        set_interval(send_alive, message, interval)
        send_alive(message)
    created_thread = threading.Timer(interval, recursive_interval)
    created_thread.start()
    return created_thread


def connect_to_server():
    """create socket and send connect message to the server

        Args:

        return: nothing
    """
    my_socket = socket(AF_INET, SOCK_DGRAM)
    connect_message = format_message("-SERVER-", "Connect", "")
    send_message(connect_message[0])


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

    quit_message = format_message("-SERVER-", "Quit", "")
    send_message(quit_message[0])
    # if(interval_thread != ""):
    interval_thread.stop()
    receiver_thread.close()
    sender_thread.close()
    my_socket.close
    remaining_messages = 0
    tag_of_last_received_message = ""
    source_of_last_received_message = ""
    current_message = ""
    contacts_list = []
    alive_interval = 0
    interval_thread = ""
    sender_thread = ""
    receiver_thread = ""
    print("You have quitted the app")


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
    while True:
        message, address = my_socket.recvfrom(1024)
        handle_received_message(message.decode())


def show_available_options():
    print("=============")
    print("1- to get the contact list enter @List")
    print("2- to quit the app enter @Quit")
    print("3- send message to a client enter @message")
    choice = input("Enter your selected option : ")
    handle_user_command(choice)


# def main():
connect_to_server()
print("You are connected to the server now!")

receiver_thread = threading.Thread(target=receive_messages)
sender_thread = threading.Thread(target=show_available_options)

receiver_thread.start()
sender_thread.start()
sender_thread.join()
receiver_thread.join()
# choice = input("to get the contact list enter @List /n")

# if __name__ == "__main__":
#     main()
