















def main():
    controller = 0
    while controller != 3:
        print("1 - odosielatel\n2 - prijmatel\n3 - koniec")

        controller = int(input("Zadaj vyber: "))
        if controller == 1:
            transmitter()
        if controller == 2:
            receiver()


if __name__ == "__main__":
    main()