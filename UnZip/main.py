import zipfile
import rarfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools

# Перечень файлов, которые нужно извлечь
file_list = [
    'full_tokens.txt',
    'Passwords.txt',
    'passwords.txt',
    'tokens.txt',
    'Tokens.txt',
    'discord.txt',
    'All Passwords.txt',
    '_AllPasswords_list.txt',
    'logins.json',
    'DiscordTokens.txt'
]

# Список паролей
password_list = [
    '',
]

# Функция для генерации уникального имени файла
def get_unique_filename(directory, base_name):
    """Возвращает уникальное имя файла, добавляя суффикс к имени"""
    base, ext = os.path.splitext(base_name)
    for i in itertools.count(1):
        unique_name = f"{base}_{i}{ext}"
        if not os.path.exists(os.path.join(directory, unique_name)):
            return unique_name

def extract_and_save(file_path, source, extract_to):
    """Извлекает файл и сохраняет его в подкаталог с уникальным именем"""
    file_name = os.path.basename(file_path)
    if file_name in file_list:
        directory = os.path.join(extract_to, file_name)
        os.makedirs(directory, exist_ok=True)
        destination_file = os.path.join(directory, get_unique_filename(directory, file_name))

        # Открываем исходный файл в архиве и записываем его содержимое в файл
        with source.open(file_path) as src_file:
            with open(destination_file, 'w', encoding='utf-8') as dest_file:
                content = src_file.read().decode('utf-8')
                dest_file.write(content)
        print(f'Извлечён файл {file_path} в {destination_file}')

def try_passwords(archive, extract_func, extract_to):
    """Пытается подобрать пароль для архива из списка паролей"""
    for password in password_list:
        try:
            extract_func(archive, extract_to, password)
            print(f'Пароль подобран: {password} для {archive}')
            return
        except (zipfile.BadZipFile, rarfile.Error):
            continue  # Пробуем следующий пароль
        except Exception as e:
            print(f'Ошибка при подборе пароля для {archive}: {e}')
    print(f'Не удалось подобрать пароль для {archive}')

def extract_zip(zip_path, extract_to, password=None):
    """Извлекает только нужные файлы из zip архива и сохраняет их в соответствующих подкаталогах"""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if os.path.basename(file) in file_list:
                try:
                    if password:
                        zip_ref.setpassword(password.encode('utf-8'))
                    extract_and_save(file, zip_ref, extract_to)
                except RuntimeError as e:
                    print(f'Ошибка извлечения {file} из {zip_path}: {e}')

def extract_rar(rar_path, extract_to, password=None):
    """Извлекает только нужные файлы из rar архива и сохраняет их в соответствующих подкаталогах"""
    with rarfile.RarFile(rar_path, 'r') as rar_ref:
        for file in rar_ref.namelist():
            if os.path.basename(file) in file_list:
                try:
                    if password:
                        rar_ref.setpassword(password)
                    extract_and_save(file, rar_ref, extract_to)
                except rarfile.BadRarFile as e:
                    print(f'Ошибка извлечения {file} из {rar_path}: {e}')

def process_archives(archive_folder, extract_to):
    """Обрабатывает архивы параллельно с использованием многопоточности"""
    # Получаем все файлы в папке, которые являются zip или rar архивами
    archive_paths = [os.path.join(archive_folder, f) for f in os.listdir(archive_folder) if
                     f.endswith(('.zip', '.rar'))]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for archive_path in archive_paths:
            if archive_path.endswith('.zip'):
                futures.append(executor.submit(try_passwords, archive_path, extract_zip, extract_to))
            elif archive_path.endswith('.rar'):
                futures.append(executor.submit(try_passwords, archive_path, extract_rar, extract_to))

        # Ожидание завершения всех потоков
        for future in as_completed(futures):
            try:
                future.result()  # Проверяем на исключения
            except Exception as e:
                print(f"Ошибка при обработке архива: {e}")


# Пример использования
archive_folder = r'D:\All_LOG\DLOGS'  # Папка, в которой находятся архивы
extract_directory = r'D:\All_LOG\SAVE'  # Укажи путь, куда будут извлекаться файлы

# Запуск многопоточной обработки
process_archives(archive_folder, extract_directory)
