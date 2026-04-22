import os

# Указываем путь к директории, где нужно переименовать файлы
directory = "D:\\All_LOG\\SAVE\\Passwords"

# Новое имя для файлов
new_name = "pass_"

# Проходимся по всем файлам в директории
for count, filename in enumerate(os.listdir(directory), start=1):
    # Получаем расширение файла
    file_extension = os.path.splitext(filename)[1]

    # Формируем новое имя файла с номером и расширением
    new_filename = f"{new_name}_{count}{file_extension}"

    # Получаем полный путь старого и нового файлов
    old_file = os.path.join(directory, filename)
    new_file = os.path.join(directory, new_filename)

    # Проверяем, является ли объект файлом
    if os.path.isfile(old_file):
        # Переименовываем файл
        os.rename(old_file, new_file)
        print(f"Переименован: {old_file} -> {new_file}")
