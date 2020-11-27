import socket
import struct


def server_listen(port, s_socket):
    BUF_SIZE = 1500

    connected_user = False

    while True:
        print(f"######## SERVER IS LISTENING ON PORT {port} ########")
        s_socket.settimeout(100)

        try:

            data, addr = s_socket.recvfrom(1500)

            processed_packet_type = struct.unpack("! c", data[:1])[0]
            if processed_packet_type.decode('ascii') == "I":
                print(f"Connection initialized by {addr[0]}")
                s_socket.sendto(data, addr)


        except socket.timeout:
            print("No client initialised a connection, closing port")
            return

        data, addr = s_socket.recvfrom(1500)
        print(f"{data}")


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
