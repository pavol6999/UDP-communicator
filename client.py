import libscrc
import socket
import struct
import os


from crcmod import crcmod


def ip_input():
    ip_addr = input("Enter the IP adress of the receiver: ")
    valid = False
    while True:
        try:
            if socket.inet_aton(ip_addr):
                break
        except OSError:
            ip_addr = input("Please enter a valid IP address: ")

    return ip_addr

def port_input():
    port = int(input("Enter port: "))
    while True:
        try:
            if 1 <= port <= 65535:
                break
            else:
                port = int(input("Enter a valid port number (1 - 65535): "))
        except ValueError:
            port = int(input("Please enter a valid port nubmer: "))
    return port

def initialize_connection(host_addr, host_port, frag_size, c_sock):
    i = 0
    init_packet = struct.pack(f"! c ", "I".encode())


    # klient sa pokusi 3x nadviazat spojenie, caka na taky isty packet co odoslal na server
    while i != 3:
        c_sock.settimeout(5)
        c_sock.sendto(init_packet, (host_addr, host_port))
        try:
            data, addr = c_sock.recvfrom(1500)
            if struct.unpack("! c", data[:1]):
                print(f"Connection initialized with {addr[0]} on port {addr[1]}")
                break
        except socket.timeout:

            print(f"Connection not initialized for {i+1}. time")
            i += 1
            if i == 3:
                client_init()
                return 0
    return 1

def chop_data(byte_str, frag_size):
    fragments_q = []
    start = 0
    end = frag_size
    while True:
        if start + frag_size > len(byte_str):
            end = len(byte_str)

            # ak je dlzka byte stringu MOD fragment_size 0, tak neukladaj
            if len(byte_str[start:end]) == 0:
                break
            fragments_q.append(byte_str[start:end])
            break
        else:
            fragments_q.append(byte_str[start:end])
            start += frag_size
            end += frag_size
    return fragments_q

def add_headers(chopped_bytes, data_type):


    i = 0
    fragments = []

    for data in chopped_bytes:
        fragments.append(struct.pack("! c h", data_type.encode('ascii'), i+1) + data)
        fragments[i] += struct.pack("! I", calculate_crc(fragments[i]))
        i+=1
    return fragments, i


def calculate_crc(fragment):
    return libscrc.fsc(fragment)


def send_info_packet(host_addr,host_port, c_socket, data_type, frag_count, file_name):
    i = 0
    if data_type == 'M':
        info_packet = struct.pack("!c h", data_type.encode('ascii'), frag_count)

    if data_type == 'F':
        info_packet = struct.pack("!c h", data_type.encode('ascii'), frag_count) + file_name.encode('ascii')

    i = 0

    while i != 3:
        c_socket.settimeout(5)
        c_socket.sendto(info_packet,(host_addr,host_port))
        try:
            data, addr = c_socket.recvfrom(2048)
            if struct.unpack("! c",data[0]) == 'A':
                print(f"Bude odoslany subor {file_name}") if data_type == 'F' else print("Bude odoslana sprava")
                break
        except socket.timeout:
            i+=1
            if i == 3:
                print("Connection unstable")
                client_init()
                return 0
    return 1




def transmit_data(host_addr, host_port, frag_size, data_type, c_socket):

    file_name = 0

    if data_type.upper() == "M":
        data_type=data_type.upper()
        byte_str = input("Enter the message you want to send: ").encode('ascii')


    if data_type.upper() == "F":
        data_type=data_type.upper()
        file_path = input_file_path()
        file_name = os.path.basename(file_path)
        print(f"File {file_name} is going to be send to the receiver")
        byte_str = open(file_path, "rb").read()

    chopped_data = chop_data(byte_str,frag_size)

    fragments,frag_count = add_headers(chopped_data, data_type)


    init = initialize_connection(host_addr, host_port, frag_size, c_socket)


    #ak sa podarilo ndviazat spojenie
    if init != 0:
        send_info_packet(host_addr, host_port, c_socket,data_type, frag_count,file_name)

    for fragment in fragments:
        c_socket.sendto(fragment, (host_addr, host_port))


def input_file_path():
    file_path = input("Enter the file path: ")

    while True:
        if os.path.isfile(file_path):
            break
        else:
            file_path = input("Enter valid file path: ")

    return file_path

def client_init():

    host_addr = ip_input()
    host_port = port_input()

    frag_size = int(input("Fragment size: "))
    data_type = input("Message or File (m - f): ")  # TODO check data type



    c_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    transmit_data(host_addr, host_port, frag_size, data_type, c_sock)


if __name__ == "__main__":
    client_init()
