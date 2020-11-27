















def main():
    controller = 0
    while controller != 3:
        print("1 - odosielatel\n2 - prijmatel\n3 - koniec")

        controller = int(input("Zadaj vyber: "))
        if controller == 1:
            continue
        if controller == 2:
            continue

def generate_random_number():
    return 42069

if __name__ == "__main__":
    print(f"Random port number is: {generate_random_number()}")