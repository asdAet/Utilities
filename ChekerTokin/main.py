import time
import requests

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def check_token(token):
    url = "https://discord.com/api/v9/users/@me"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при проверке токена: {e}")
        return False


def read_tokens(file_path):
    with open(file_path, "r") as file:
        tokens = file.readlines()
    return [token.strip() for token in tokens]


def write_valid_token(token, output_file_path):
    with open(output_file_path, "a") as file:
        file.write(token + "\n")


def main(input_file_path, output_file_path):
    tokens = read_tokens(input_file_path)

    for token in tokens:
        if check_token(token):
            print(f"{GREEN}Токен валиден: {token}{RESET}")
            write_valid_token(token, output_file_path)
        else:
            print(f"{RED}Токен не валиден: {token}{RESET}")

        time.sleep(0.2)  # Пауза на 0.4 секунды между запросами, чтобы избежать блокировки

    print(f"Проверка завершена. Валидные токены сохранены в {output_file_path}")


if __name__ == "__main__":
    input_file = r"C:\Users\root\Desktop\discord\combined.txt"  # Файл с токенами для проверки
    output_file = r"C:\Users\root\Desktop\discord\valid.txt"  # Файл для сохранения валидных токенов
    main(input_file, output_file)
