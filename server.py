import socket
import struct
import libscrc

def check_crc(fragment):
    return True if libscrc.fsc(fragment) == 0 else False


def unpack_data(fragment):
    data_len = len(fragment) - 7
    frag_type, frag_count, data, crc = struct.unpack(f"! c h {data_len}c I",fragment)
    return frag_type,frag_count,data,crc

def server_listen(port, s_socket):

    s_socket.settimeout(None)
    while True:
        print(f"\n######## SERVER IS LISTENING ON PORT {port} ########")

        while True:
            try:

                data, addr = s_socket.recvfrom(1500)

                processed_packet_type = struct.unpack("! c", data[:1])[0]
                if processed_packet_type.decode('utf-8') == "I":
                    print(f"Connection initialized by {addr[0]}")
                    s_socket.sendto(data, addr)

                if processed_packet_type.decode('utf-8') == 'M':
                    frag_type = "M"
                    frag_count = struct.unpack("!H",data[1:3])[0]
                    print(f"A message will be received consisting of {frag_count} fragments")
                    s_socket.sendto("A".encode('utf-8'),addr)
                    break

                if processed_packet_type.decode('utf-8') == 'F':
                    frag_type = "F"
                    frag_count = struct.unpack("!H",data[1:3])[0]
                    file_name = data[3:].decode('utf-8')
                    s_socket.sendto("A".encode('utf-8'), addr)
                    print(f"A file {file_name} will be received consisting of {frag_count} fragments")
                    break

                if processed_packet_type.decode('utf-8') == 'K':
                    print("The connection is alive")

            except socket.timeout:
                print("No traffic, closing")
                s_socket.close()
                return

        received_fragments = {}.fromkeys(range(frag_count))
        received_num = 0


        # ak 4 sekundy nepride z klienta packet, tak sa berie, že je zatúlany
        s_socket.settimeout(10)
        while received_num != frag_count:
            try:
                data, addr = s_socket.recvfrom(2048)
                key = struct.unpack("! h", data[1:3])[0]
                if check_crc(data):
                    received_fragments[key] = data[3:-4]
                    s_socket.sendto('A'.encode('utf-8'),addr)
                    received_num+=1
                else:
                    print(f"Corrupted data on fragment {received_num}")
                    s_socket.sendto('A'.encode('utf-8')+key.to_bytes(2, "big"), addr)
                    continue

            except socket.timeout:
                print(f"Connection unstable")

        if frag_type == 'F':
            message = reconstruct_file(received_fragments,file_name)
            print(f"File was saved to {message}")

        if frag_type == 'M':
            message = reconstruct_message(received_fragments)
            print(f"Message: {message}")

        s_socket.settimeout(30)




def reconstruct_file(received_fragments, file_name):
    file = open(f"Download/{file_name}", "wb")
    b_string = b''
    values = received_fragments.values()
    for value in values:
        try:
            b_string += value
        except TypeError:
            break
    file.write(b_string)
    file.close()
    return f"Downloads/{file_name}"

def reconstruct_message(received_fragments):
    values = received_fragments.values()
    message = b''
    for value in values:
        message += value
    return message.decode('utf-8')



def server_init():
    host = socket.gethostname()  #
    port = int(input("Please input the server port: "))

    # ipv4 family, udp
    s_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s_socket.bind((host, port))

    print(f"A UDP socket was created")

    server_listen(port, s_socket)


if __name__ == "__main__":
    server_init()
