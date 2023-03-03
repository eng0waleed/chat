import socket
import threading
import time

my_client_id = "1".ljust(8, '\0')
my_socket = socket.socket()
sender_thread = threading.Thread()
receiver_thread = threading.Thread()


def connect_to_server():
    """create socket and send connect message to the server

        Args:

        return: nothing
    """
    HOST = 'localhost'
    PORT = 5000
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        my_socket.connect((HOST, PORT))
    except socket.error as e:
        print(str(e))
    
    my_socket.setblocking(True)
    time.sleep(2)
    connect_message = format_message("-SERVER-", "Connect", "")
    send_message(my_socket, connect_message[0])
    receiver_thread = threading.Thread(
        target=receive_messages, args=(my_socket,))
    receiver_thread.start()


def receive_messages(connection):
    while True:
        print(connection)
        message = connection.recv(1024)
        if not message:
          connection.close()

        handle_received_message(message.decode())


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


def send_message(connection , formatted_message):
    """send the formatted messages to the server
        
        Args:
        formatted_message (String): the formatted message
        
        return: nothing
    """
    connection.send(formatted_message.encode())


def handle_received_message(message):
    """collect messages and process them

        Args:
        message (String): the received message

        return: nothing
    """
    print("[{}]:".format(message))


if __name__ == '__main__':
    connect_to_server()
