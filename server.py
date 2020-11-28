import socket
import struct


def unpack_data(fragment):
    data_len = len(fragment) - 7
    frag_type, frag_count, data, crc = struct.unpack(f"! c h {data_len}c I",fragment)
    return frag_type,frag_count,data,crc

def server_listen(port, s_socket):
    BUF_SIZE = 1500

    connected_user = False

    while True:
        print(f"######## SERVER IS LISTENING ON PORT {port} ########")
        s_socket.settimeout(100)
        while True:
            try:

                data, addr = s_socket.recvfrom(1500)

                processed_packet_type = struct.unpack("! c", data[:1])[0]
                if processed_packet_type.decode('ascii') == "I":
                    print(f"Connection initialized by {addr[0]}")
                    s_socket.sendto(data, addr)

                if processed_packet_type.decode('ascii') == 'M':
                    frag_type = "M"
                    frag_count = struct.unpack("!h",data[1:3])
                    print(f"A message will be received consisting of {frag_count[0]} fragments")
                    s_socket.sendto("A".encode('ascii'),addr)
                    break

                if processed_packet_type.decode('ascii') == 'F':
                    frag_type = "F"
                    frag_count = struct.unpack("!h",data[1:3])
                    file_name = data[3:].decode('ascii')
                    s_socket.sendto("A".encode('ascii'), addr)
                    print(f"A file {file_name} will be received consisting of {frag_count[0]} fragments")
                    break

            except socket.timeout:
                print("Connection unstable, closing")
                return


        while True:
            data, addr = s_socket.recvfrom(2048)
            s_socket.sendto("A".encode('ascii'),addr)
            print(data[3:-4].decode('ascii'))



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
