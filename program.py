import libscrc
import socket
import struct
import os
import time
import threading


corrupted = missing = 0

# zadanie ip adresy
def ip_input():
    ip_addr = input("Enter the IP adress of the receiver: ")
    while True:
        try:
            if socket.inet_aton(ip_addr):
                break
        except OSError:
            ip_addr = input("Please enter a valid IP address: ")

    return ip_addr



# posielac keep alive sprav, caka na ack ci je server respondivny
def keep_alive_sender(keep_alive_status, host_addr, host_port, c_socket):
    while keep_alive_status.isSet():
        c_socket.sendto("K".encode('utf-8'), (host_addr, host_port))
        data, addr = c_socket.recvfrom(2048)
        if data[0:1].decode('utf-8') == 'A':
            time.sleep(5)
        else:
            print("Server not responding")

 # osetrenie port vstupu
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

# inicializacia spojenia
def initialize_connection(host_addr, host_port, c_sock):
    i = 0
    init_packet = struct.pack(f"! c ", "I".encode())

    # klient sa pokusi 3x nadviazat spojenie, caka na taky isty packet co odoslal na server
    while i != 3:
        c_sock.settimeout(5)
        c_sock.sendto(init_packet, (host_addr, host_port))
        try:
            data, addr = c_sock.recvfrom(1500)
            if struct.unpack("! c", data[:1]):
                print(f"\nConnection initialized with {addr[0]} on port {addr[1]}")
                break

        # ak timeoutne, moze sa stat inicializacna sprava sa stratila, skusi sa znovu
        except socket.timeout:
            print(f"Connection not initialized for {i + 1}. time")
            i += 1
            if i == 3:
                client_init(0)
                return 0
    return 1

# nasekame byte_string na fragmenty o velkosti len(hlavicka) + data
def chop_data(byte_str, frag_size):
    fragments_q = []
    start = 0
    fragment_size = frag_size

    # ak je cely string po deleni s fragment size vacsi ako 65535 tak sa nezmesti do hlavicky 2B a tak
    # sa fragment size nastavi na najmensiu moznu hodnotu a podla neho naseka tento subor
    # vsetky ostatne subory/spravy ktore sa poslu po tomto subore budu mat defaultnu fragment size
    if len(byte_str) / frag_size > 65535:
        print("Number of fragments is larger than the max, that can fit into 2 bytes")
        print(f"The fragment size was set for this file to {len(byte_str) // 65535 + 1}")
        fragment_size = len(byte_str) // 65535 + 1

    end = fragment_size



    # postupna iteracia byte stringom a rozdelenim ho do fragmentov
    while True:
        if start + fragment_size > len(byte_str):
            end = len(byte_str)

            # ak je dlzka byte stringu MOD fragment_size 0, tak neukladaj
            if len(byte_str[start:end]) == 0:
                break
            fragments_q.append(byte_str[start:end])
            break
        else:
            fragments_q.append(byte_str[start:end])
            start += fragment_size
            end += fragment_size

    return fragments_q

# prida hlavicky na fragmenty
def add_headers(chopped_bytes, data_type):
    i = 0
    fragments = []

    for data in chopped_bytes:
        fragments.append(struct.pack("! c H", data_type.encode('utf-8'), i) + data)
        fragments[i] += struct.pack("! I", calculate_crc(fragments[i]))
        i += 1
    return fragments, i


def calculate_crc(fragment):
    return libscrc.fsc(fragment)

 # posle prvy fragment, ktore sluzia ako metadata pre posielane data
 # ak je prenasana sprava, posle sa typ M, pocet fragmentov kolko bude prenasanych
 # ak je prenasany subor, posle sa typ F, pocet fragmentvo a nazov suboru
def send_info_packet(host_addr, host_port, c_socket, data_type, frag_count, file_name):
    i = 0
    if data_type == 'M':
        info_packet = struct.pack("!c H", data_type.encode('utf-8'), frag_count)

    if data_type == 'F':
        info_packet = struct.pack("!c H", data_type.encode('utf-8'), frag_count) + file_name.encode('utf-8')

    i = 0


    # skusim trikrat poslat info packet, ak pride odpoved breaknem loop
    # ak nie, tak je moznost ze sa info packet stratil po ceste a tak ho skusim poslat znovu
    # ak sa trikrat neposlal, tak je spojenie nestabilne
    while i != 3:
        c_socket.settimeout(5)
        c_socket.sendto(info_packet, (host_addr, host_port))
        try:
            data, addr = c_socket.recvfrom(2048)
            if data[0:1].decode('utf-8') == 'A':
                print(f"{file_name} will be sent") if data_type == 'F' else print("A message will be sent")

                break
        except socket.timeout:
            i += 1
            if i == 3:
                print("Connection unstable")
                client_init(0)
                return 0
    return 1

def add_error():
    missing = corrupted = False
    controller = input("Do you want to simulate error (y - n): ")
    if controller == 'y':
        missing = input("Missing first fragment (y - n): ")

        if missing.upper() == 'Y':
            missing = True
        else:
            missing = False

        corrupted = input("Corrupted first fragment (y - n): ")

        if corrupted.upper() == 'Y':
            corrupted = True
        else:
            corrupted = False

    return missing, corrupted


# hlavna funkcia, ktora prenasa udaje
def transmit_data(host_addr, host_port, frag_size, data_type, client_socket):

    # ak este nebol  nastaveny socket tak sa vytvori novy
    if client_socket == 0:
        c_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # ak uz bol spraveny socket, tak sa pouzije ten
    # tato podmienka plati ak sa switchnu endpointy
    else:
        c_socket = client_socket
    file_name = 0

    # zavedenie chyby do prenosu
    # premenne ktore predstavuju pocet chyb
    missing, corrupted = add_error()



    # ak chceme poslat spravu, tak zadame spravu
    if data_type.upper() == "M":
        data_type = data_type.upper()
        byte_str = input("Enter the message you want to send: ").encode('utf-8')


    # ak chceme poslat subor, tak zadame nazov suboru
    if data_type.upper() == "F":
        data_type = data_type.upper()
        file_path = input_file_path()
        file_name = os.path.basename(file_path)
        print(f"File {file_name} is going to be sent to the receiver")
        byte_str = open(file_path, "rb").read()

    # posekame string na fragmenty
    chopped_data = chop_data(byte_str, frag_size)

    # pridame fragmentom hlavicky
    fragments, frag_count = add_headers(chopped_data, data_type)

    # ak spojenie este nebolo nadviazane
    if client_socket == 0:
        initialize_connection(host_addr, host_port, c_socket)

    # ak sa podarilo ndviazat spojenie

    send_info_packet(host_addr, host_port, c_socket, data_type, frag_count, file_name)

    num_of_tries = 0

    # pokial su fragmenty ktore treba odoslat, odoslem ich
    while len(fragments) != 0:
        fragment = fragments.pop(0)

        # klient sa pokusi poslat fragment na server
        while num_of_tries != 3:
            c_socket.settimeout(3)

            if missing:
                missing = False
                time.sleep(6)

            elif corrupted and int.from_bytes(fragment[1:3], "big") == 1:
                corrupted_fragment = bytearray(fragment)
                try:
                    corrupted_fragment[-1] += 1
                except:
                    corrupted_fragment[-1] -=1
                corrupted_fragment = bytes(corrupted_fragment)
                c_socket.sendto(corrupted_fragment, (host_addr, host_port))
                corrupted = False

            else:
                c_socket.sendto(fragment, (host_addr, host_port))

            # ak prisla odpoved zo servera
            try:
                data, addr = c_socket.recvfrom(2048)

                # ak to bolo ack tak pozrieme ci bolo chybne alebo nie
                if data[0:1].decode('utf-8') == 'A':

                    num_of_tries = 0
                    c_socket.settimeout(None)
                    break
                elif data[0:1].decode('utf-8') == 'E':
                    print("The fragment was corrupted or lost, resending fragment")
                    continue

            # ak klient timeoutne, takze fragment sa stratil, tak pokusi poslat fragment este raz
            except socket.timeout:
                num_of_tries += 1

                if num_of_tries == 3:
                    print("Connection unstable, disconnecting")
                    client_init(0)
                print(f"Retransmitting fragment for the {num_of_tries}. time")


    # po ukonceni posielania suboru/spravy, vytvorim novy thread, ktory posiela keep alive spravy
    keep_alive_status = threading.Event()
    keep_alive_status.set()
    ka_thread = threading.Thread(target=keep_alive_sender, args=(keep_alive_status, host_addr, host_port, c_socket),
                                 daemon=True)
    ka_thread.start()

    end_transmission(host_addr, host_port, keep_alive_status, c_socket)

# zadanie validnej cesty k suboru
def input_file_path():
    file_path = input("Enter the file path: ")

    while True:
        if os.path.isfile(file_path):
            break
        else:
            file_path = input("Enter valid file path: ")

    return file_path

# koniec prenosu suboru, otvori sa menu ci chce klient stale posielat subory na server alebo chce so serverom switchnut role
def end_transmission(host_addr, host_port, keep_alive_status, c_socket):
    controller = input("1 - Keep sending data to server \n2 - Change to server")
    if controller == '1':
        frag_size = int(input("Fragment size: "))
        data_type = input("Message or File (m - f): ")
        keep_alive_status.clear()
        transmit_data(host_addr, host_port, frag_size, data_type, c_socket)
    else:
        keep_alive_status.clear()
        switch_role(c_socket, host_addr, host_port)

# odosle sa na server sprava S - switch, tne spracuje spravu a nastavi sa na odosielanie
# klient sa pripravi na odosielanie
def switch_role(c_socket, host_addr, host_port):
    c_socket.sendto("S".encode('utf-8'), (host_addr, host_port))

    server_init(c_socket)

# priprava klienta, zada sa ip adresa a port na ktory chceme posielat subory/spravy
def client_init(client_socket):
    host_addr = ip_input()
    host_port = port_input()

    frag_size = int(input("Fragment size: "))
    data_type = input("Message or File (m - f): ")
    transmit_data(host_addr, host_port, frag_size, data_type, client_socket)


def check_crc(fragment):
    return True if libscrc.fsc(fragment) == 0 else False







# hlavna funkcia pre server
def server_listen(port, s_socket):

    # ak prvykrat nastavime socket server a zapneme tak pocuva,
    # timeout nepotrebuje lebo este nikto nie je pripojeny
    s_socket.settimeout(None)
    while True:
        print(f"\n######## SERVER IS LISTENING ON PORT {port} ########")

        # loopuj ak chodia jednoduche spravy ako je Keep Alive alebo inicializacna sprava
        while True:
            try:

                data, addr = s_socket.recvfrom(1500)


                # ak sa chce pripojit klient
                processed_packet_type = struct.unpack("! c", data[:1])[0]
                if processed_packet_type.decode('utf-8') == "I":
                    print(f"Connection initialized by {addr[0]}")
                    s_socket.sendto(data, addr)

                # ak pride sprava
                if processed_packet_type.decode('utf-8') == 'M':
                    frag_type = "M"
                    frag_count = struct.unpack("!H", data[1:3])[0]
                    print(f"A message will be received consisting of {frag_count} fragments")
                    s_socket.sendto("A".encode('utf-8'), addr)
                    break

                # ak pride subor
                if processed_packet_type.decode('utf-8') == 'F':
                    frag_type = "F"
                    frag_count = struct.unpack("!H", data[1:3])[0]
                    file_name = data[3:].decode('utf-8')
                    s_socket.sendto("A".encode('utf-8'), addr)
                    print(f"A file {file_name} will be received consisting of {frag_count} fragments")
                    break

                # ak pride keep alive packet
                if processed_packet_type.decode('utf-8') == 'K':
                    print("The connection is alive")
                    s_socket.sendto("A".encode('utf-8'),addr)

                # ked pride switch tak sa server pusti funckiu client_init na pripravu na prijmanie suborov
                if processed_packet_type.decode('utf-8') == 'S':
                    print("\nSwitching to client")
                    client_init(s_socket)



            except socket.timeout:
                print("No traffic, closing")
                s_socket.close()
                return

        # slovnik, ktory udrzuje nase fragmenty
        received_fragments = {}.fromkeys(range(frag_count))
        received_num = 0

        # ak 5 sekund nepride od klienta packet, tak sa berie, že je zatúlany
        s_socket.settimeout(5)

        # ak je pocet prijatych fragmentov rovny celkovemu poctu fragmentov co sa ma prijat, skonci
        while received_num != frag_count:
            try:
                data, addr = s_socket.recvfrom(2048)
                key = struct.unpack("! h", data[1:3])[0]

                # ak su data neposkodene, tak ulozim fragment a odoslem prazdne ack
                if check_crc(data):
                    received_fragments[key] = data[3:-4]
                    s_socket.sendto('A'.encode('utf-8'), addr)
                    received_num += 1
                # ak su data poskodene, tak neulozim fragment a odoslem ack s cislom poskodeneho fragmentu
                else:
                    print(f"Corrupted data on fragment {received_num}")
                    s_socket.sendto('E'.encode('utf-8'),addr)
                    continue

            except socket.timeout:
                print(f"Connection unstable, a packet was lost")
                s_socket.sendto('E'.encode('utf-8'),addr)


        # dalej sa rozhodujem ci ulozim subor, alebo zobrazim spravu
        if frag_type == 'F':
            message = reconstruct_file(received_fragments, file_name)
            print(f"File was saved to {message}")



        if frag_type == 'M':
            message = reconstruct_message(received_fragments)
            print(f"Message: {message}")

        s_socket.settimeout(30)

# rekonstrukcia suboru, vrati cestu k ulozenemu suboru
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

# rekonstrukcia spravy
def reconstruct_message(received_fragments):
    values = received_fragments.values()
    message = b''
    for value in values:
        message += value
    return message.decode('utf-8')

# priprava serveru, ak je server_socket 0, teda este nenastaveny tak sa nastavi novy, ak uz socket bol
# spraveny, vyuzije sa ten
def server_init(server_socket):
    if server_socket == 0:
        host = socket.gethostname()  #
        port = int(input("Please input the server port: "))

        # ipv4 family, udp
        s_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_socket.bind((host, port))
        server_listen(port, s_socket)
    else:
        server_listen(server_socket.getsockname()[1], server_socket)


def main():
    controller = 0
    while controller != 3:
        print("1 - odosielatel\n2 - prijmatel\n3 - koniec")

        controller = int(input("Zadaj vyber: "))
        if controller == 1:
            client_init(0)
        if controller == 2:
            server_init(0)


if __name__ == "__main__":
    main()
