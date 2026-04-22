import requests


def check_token(token):
    url = "https://discord.com/api/v9/users/@me"
    headers = {
        "Authorization": token
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True
    else:
        return False


# Путь к файлу с токенами
file_path = 'path_to_your_file_with_tokens.txt'

# Считывание токенов из файла
with open(file_path, 'r') as file:
    tokens = file.readlines()

# Проверка каждого токена
for token in tokens:
    token = token.strip()
    if check_token(token):
        print(f'Token {token} is valid.')
    else:
        print(f'Token {token} is invalid or expired.')

print('Token check completed.')
