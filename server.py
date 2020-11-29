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
    BUF_SIZE = 1500

    connected_user = False
    s_socket.settimeout(None)
    while True:
        print(f"######## SERVER IS LISTENING ON PORT {port} ########")

        while True:
            try:

                data, addr = s_socket.recvfrom(1500)

                processed_packet_type = struct.unpack("! c", data[:1])[0]
                if processed_packet_type.decode('ascii') == "I":
                    print(f"Connection initialized by {addr[0]}")
                    s_socket.sendto(data, addr)

                if processed_packet_type.decode('ascii') == 'M':
                    frag_type = "M"
                    frag_count = struct.unpack("!h",data[1:3])[0]
                    print(f"A message will be received consisting of {frag_count} fragments")
                    s_socket.sendto("A".encode('ascii'),addr)
                    break

                if processed_packet_type.decode('ascii') == 'F':
                    frag_type = "F"
                    frag_count = struct.unpack("!h",data[1:3])[0]
                    file_name = data[3:].decode('ascii')
                    s_socket.sendto("A".encode('ascii'), addr)
                    print(f"A file {file_name} will be received consisting of {frag_count} fragments")
                    break

                if processed_packet_type.decode('ascii') == 'K':
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
                    s_socket.sendto('A'.encode('ascii'),addr)
                    received_num+=1
                else:
                    s_socket.sendto('A'.encode('ascii')+key.to_bytes(2, "big"), addr)
                    continue

            except socket.timeout:
                print(f"Connection unstable")


        s_socket.settimeout(30)
        print("")







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
