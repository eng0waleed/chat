from socket import *
HOST = 'localhost'
PORT = 5000
my_socket = socket(AF_INET, SOCK_DGRAM)
my_socket.sendto(''.encode(), (HOST, PORT))  # send some data
data = my_socket.recvfrom(1024)     # receive the response
print(data[0].decode())              # print the result

my_client_id = "1".ljust(8, '\0')
remaining_messages = 0
tag_of_last_received_message = ""
source_of_last_received_message = ""
current_message = ""

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
            message_prefix = "({}-{}/{})".format(tag, i, number_of_chunks).ljust(12, '\0')
            next_index = current_index + chunk_length
            
            if(current_index >= message_length):
                break;
            elif((current_index + chunk_length) > message_length):
                temp_message = (
                    dest_id+my_client_id+message_prefix +
                    message[current_index:message_length]
                ).ljust(256, '\0')
            else:
                temp_message = temp_message = (
                    dest_id+my_client_id+message_prefix +
                    message[current_index:next_index]
                ).ljust(256, '\0')
                
            messages.append(temp_message)
    else:
        temp_message = dest_id + my_client_id + "({}-{}/{})".format(tag, 1, 1).ljust(12, '\0') + message
        messages.append(temp_message);
    
    return messages            


def send_message(formatted_message):
    """send the formatted messages to the server
        
        Args:
        formatted_message (String): the formatted message
        
        return: nothing
    """
    my_socket.sendto(''.encode(), (HOST, PORT))
    

def handle_received_message(message):
    """collect messages and process them

        Args:
        message (String): the received message

        return: nothing
    """
    msg_dest_id = message[0:8]
    msg_source_id = message[8:16]
    msg_prefix = message[16:29].strip().split("-")
    msg_tag = msg_prefix[0]
    msg_num = msg_prefix[1].split("/")[0]
    msg_total = msg_prefix[1].split("/")[1]
    msg = message[29:256]
    
    tag_of_last_received_message = msg_tag
    source_of_last_received_message = msg_source_id
    remaining_messages = 0
    
    if(msg_num == 1):
        current_message = msg
    else:
        current_message += msg

    if(msg_num < msg_total):
        remaining_messages = msg_total - msg_num
    elif(msg_total - msg_num == 0):
        print("[{}][{}]:{}".format(msg_source_id, msg_tag, current_message))
        
        if(msg_tag == "list"):
            set_online_contact_list(current_message)
        elif(msg_tag == "aliveT"):
            set_alive_interval(msg)
        elif(msg_tag == "error"):
            handle_received_error(msg)
        else:
            print("[{}][unknown type of message]: {}".format(msg_source_id, msg))
    

