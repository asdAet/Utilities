import os
import zipfile
import rarfile
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import datetime

now = datetime.datetime.now()
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# CYAN = "\033[96m"
# RESET = "\033[0m"

# Инициализация глобального счетчика и блокировки
extracted_count = 0
lock = threading.Lock()

def get_unique_filename(directory, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = f"{base}{ext}"
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
    return new_filename

def extract_password_txt_from_zip(zip_path, output_dir):
    global extracted_count
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith(extracted_file):
                    unique_filename = get_unique_filename(output_dir, os.path.basename(file))
                    temp_extract_path = os.path.join(output_dir, unique_filename)
                    with zip_ref.open(file) as source, open(temp_extract_path, 'wb') as target:
                        target.write(source.read())
                    with lock:
                        extracted_count += 1
                        print(f'Извлечен {file}. Всего извлечено: {extracted_count}, {current_time}')
    except Exception as e:
        print(f"Ошибка извлечения {zip_path}: {e}")

def extract_password_txt_from_rar(rar_path, output_dir):
    global extracted_count
    try:
        with rarfile.RarFile(rar_path, 'r') as rar_ref:
            for file in rar_ref.namelist():
                if file.endswith(extracted_file):
                    unique_filename = get_unique_filename(output_dir, os.path.basename(file))
                    temp_extract_path = os.path.join(output_dir, unique_filename)
                    with rar_ref.open(file) as source, open(temp_extract_path, 'wb') as target:
                        target.write(source.read())
                    with lock:
                        extracted_count += 1
                        print(f'Извлечен {file}. Всего извлечено: {extracted_count}, {current_time}')
    except Exception as e:
        print(f"Ошибка извлечения {rar_path}: {e}")

async def process_file(file, root, output_dir, executor):
    if file.endswith('.zip'):
        zip_path = os.path.join(root, file)
        await asyncio.get_event_loop().run_in_executor(executor, extract_password_txt_from_zip, zip_path, output_dir)
    elif file.endswith('.rar'):
        rar_path = os.path.join(root, file)
        await asyncio.get_event_loop().run_in_executor(executor, extract_password_txt_from_rar, rar_path, output_dir)

async def main(archives_dir, output_dir):
    if not os.path.exists(archives_dir):
        print(f"Ошибка: Указанная директория архивов '{archives_dir}' не существует. {current_time}")
        return
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    executor = ThreadPoolExecutor(max_workers=2048)
    tasks = []

    for root, _, files in os.walk(archives_dir):
        for file in files:
            tasks.append(process_file(file, root, output_dir, executor))

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    archives_dir = r'D:\All_LOG\DLOGS'  # Путь к директории, содержащей архивы
    output_dir = r'D:\All_LOG\Token'  # Путь к директории, куда будут сохраняться извлеченные файлы
    extracted_file = 'full_tokens.txt'
    #extracted_file = 'Passwords.txt'
    asyncio.run(main(archives_dir, output_dir))