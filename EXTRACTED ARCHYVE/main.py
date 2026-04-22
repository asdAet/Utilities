import os
import zipfile
import rarfile
import subprocess
import py7zr
import shutil  # Импортируем модуль shutil для работы с файлами
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from os import cpu_count

rarfile.UNRAR_TOOL = r"C:\Program Files\WinRAR\UnRAR.exe"
seven_zip_path = r"C:\Program Files\7-Zip\7z.exe"

# Установите директорию с архивами и директорию для сохранения извлеченных файлов
ARCHIVE_FOLDER = r'D:\All_LOG\DLOGS'
EXTRACT_DIRECTORY = r'D:\All_LOG\SAVE'

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
    '@LOGS_CENTER',
    '@Cloud',
    '@SunCloudVip',
]


def extract_7z_with_external_tool(archive_path, extract_to, password=None):
    """Извлекает архив 7z с использованием заданного пароля, если он есть"""
    temp_dir = os.path.join(extract_to, "temp")  # Временная папка для извлечения архива
    os.makedirs(temp_dir, exist_ok=True)

    command = [seven_zip_path, 'x', archive_path, f'-o{temp_dir}', '-y']
    if password:
        command += ['-p' + password]

    try:
        subprocess.run(command, check=True)
        print(f'Файл {archive_path} успешно извлечён.')

        for file_name in file_list:
            file_path = os.path.join(temp_dir, file_name)
            if os.path.exists(file_path):
                dest_dir = os.path.join(extract_to, file_name)
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy(file_path, os.path.join(dest_dir, f"{file_name}.txt"))
                print(f'Файл {file_name} скопирован в {dest_dir}')
            else:
                print(f'Файл {file_name} не найден в архиве {archive_path}')
    except subprocess.CalledProcessError:
        print(f'Не удалось извлечь архив {archive_path} с паролем {password}.')
    finally:
        shutil.rmtree(temp_dir)

def extract_and_save(file_path, source, extract_to, index, password=None):
    """Извлекает файл и сохраняет его в подкаталог с уникальным именем с номером по порядку"""
    file_name = os.path.basename(file_path)
    if file_name in file_list:
        directory = os.path.join(extract_to, file_name)
        os.makedirs(directory, exist_ok=True)
        destination_file = os.path.join(directory, f"{file_name}_{index}.txt")

        try:
            with source.open(file_path, pwd=password) as src_file:
                content = src_file.read()
                try:
                    decoded_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    print(f"Ошибка декодирования файла |{file_path}|, пропускаем этот файл.")
                    return

                with open(destination_file, 'w', encoding='utf-8') as dest_file:
                    dest_file.write(decoded_content)

            print(f'Извлечён файл |{file_path}| в {destination_file}')
        except Exception as e:
            print(f'Ошибка сохранения файла |{file_path}|: {e}')

def try_passwords(archive, extract_func, extract_to):
    """Пытается подобрать пароль для архива из списка паролей поочередно"""
    for password in password_list:
        try:
            extract_func(archive, extract_to, password)
            print(f'Пароль подобран: {password} для |{archive}|')
            return
        except (zipfile.BadZipFile, rarfile.Error, py7zr.ArchiveError):
            continue
        except UnicodeDecodeError:
            print(f'Ошибка декодирования содержимого в архиве |{archive}|. Пропускаем.')
            return
        except Exception as e:
            print(f'Ошибка при подборе пароля для |{archive}|: {e}')
    print(f'Не удалось подобрать пароль для |{archive}|')

def extract_zip(zip_path, extract_to, password=None):
    """Извлекает только нужные файлы из zip архива и сохраняет их в соответствующих подкаталогах"""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        with ThreadPoolExecutor() as executor:
            futures = []
            for index, file in enumerate(zip_ref.namelist()):
                if os.path.basename(file) in file_list:
                    futures.append(executor.submit(extract_and_save, file, zip_ref, extract_to, index, password.encode() if password else None))
            for future in futures:
                future.result()

def extract_rar(rar_path, extract_to, password=None):
    """Извлекает только нужные файлы из rar архива и сохраняет их в соответствующих подкаталогах"""
    with rarfile.RarFile(rar_path, 'r') as rar_ref:
        with ThreadPoolExecutor() as executor:
            futures = []
            for index, file in enumerate(rar_ref.namelist()):
                if os.path.basename(file) in file_list:
                    futures.append(executor.submit(extract_and_save, file, rar_ref, extract_to, index, password))
            for future in futures:
                future.result()

def extract_7z(archive_path, extract_to, password=None):
    """Извлекает только нужные файлы из 7z архива и сохраняет их в соответствующих подкаталогах"""
    try:
        with py7zr.SevenZipFile(archive_path, 'r', password=password) as archive_ref:
            with ThreadPoolExecutor() as executor:
                futures = []
                for index, file in enumerate(archive_ref.getnames()):
                    if os.path.basename(file) in file_list:
                        futures.append(executor.submit(extract_and_save, file, archive_ref, extract_to, index, password))
                for future in futures:
                    future.result()
    except EOFError:
        print(f'Ошибка чтения данных из архива: {archive_path}. Возможно, файл повреждён.')
    except py7zr.ArchiveError as e:
        print(f'Ошибка распаковки 7z файла {archive_path}: {e}')

def process_archive(archive_path):
    """Функция для обработки одного архива"""
    extract_to = EXTRACT_DIRECTORY
    if archive_path.endswith('.zip'):
        try_passwords(archive_path, extract_zip, extract_to)
    elif archive_path.endswith('.rar'):
        try_passwords(archive_path, extract_rar, extract_to)
    elif archive_path.endswith('.7z'):
        try_passwords(archive_path, extract_7z, extract_to)

def main():
    archive_paths = [os.path.join(ARCHIVE_FOLDER, f) for f in os.listdir(ARCHIVE_FOLDER) if f.endswith(('.zip', '.rar', '.7z'))]
    with ProcessPoolExecutor(max_workers=cpu_count() // 2) as executor:
        executor.map(process_archive, archive_paths)

if __name__ == "__main__":
    main()