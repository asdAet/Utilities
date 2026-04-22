import os
import glob
import sys

# Функция для чтения списка слов из файла
def read_word_list(file_name):
    # Получение пути к директории, где находится исполняемый файл
    current_directory = os.path.dirname(sys.argv[0])
    file_path = os.path.join(current_directory, file_name)
    if os.path.isfile(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return [word.strip() for word in file.readlines()]
    else:
        print(f"Файл '{file_name}' не найден в текущей директории.")
        return []

# Остальная часть программы остается без изменений


# Функция для парсинга слов из текстовых файлов
def parse_text_files(word_list, directory, extensions, log_file):
    result = {}
    files = []
    for extension in extensions:
        current_files = glob.glob(os.path.join(directory, f'*.{extension}'))
        if current_files:
            with open(log_file, 'a', encoding='utf-8') as log:
                log.write(f"Найдены файлы с расширением {extension} - {len(current_files)}:\n")
                for file_path in current_files:
                    log.write(f"- Файл с расширением {os.path.basename(file_path)} - {file_path}\n")
                    files.append(file_path)
                log.write("\n")
    for file_path in files:
        print("Обрабатываем файл:", os.path.basename(file_path))  # Убран полный путь к файлу
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for line_number, line in enumerate(lines, 1):
                for word in word_list:
                    if word.lower() in line.lower():
                        if file_path not in result:
                            result[file_path] = {}
                        if word not in result[file_path]:
                            result[file_path][word] = []
                        result[file_path][word].append((line_number, line.find(word) + 1))
    return result

# Функция для записи результата в файл log
def write_log(log_file, message):
    with open(log_file, 'a', encoding='utf-8') as file:
        file.write(message + '\n')

# Функция для выбора расширений из списка
def choose_extensions():
    print("Введите расширения файлов через запятую (например: txt, json, cfg) или 'Выход' для завершения:")
    extensions_input = input("Расширения файлов: ").strip().lower()
    if extensions_input == 'выход':
        return None
    else:
        return [ext.strip() for ext in extensions_input.split(',')]

# Основная программа
if __name__ == "__main__":
    # Получение текущей директории, где находится исполняемый файл
    current_directory = os.path.dirname(__file__)

    # Ввод пути к папке, в которой нужно искать файлы
    search_directory = input("Введите путь к папке, в которой нужно искать: ")

    # Ввод пути к общей директории для сохранения результата
    output_directory = os.path.join(current_directory, "output")
    os.makedirs(output_directory, exist_ok=True)

    # Путь к файлу для записи лога
    log_file = os.path.join(output_directory, 'log.txt')

    while True:
        # Выбор расширений
        extensions = choose_extensions()
        if extensions is None:
            break  # Выход из программы, если возвращено None

        # Запись в лог информации о найденных файлах
        parse_text_files([], search_directory, extensions, log_file)

        # Чтение списка слов
        words_to_search = read_word_list("search.txt")

        # Парсинг файлов и поиск слов
        search_result = parse_text_files(words_to_search, search_directory, extensions, log_file)

        # Вывод в консоль
        print("Поиск завершен. Результат записан в", output_directory)

        # Запись результата в файл
        output_file = os.path.join(output_directory, 'result.txt')
        with open(output_file, 'w', encoding='utf-8') as file:
            if not search_result:
                file.write("Результат поиска пустой.\n")
            else:
                for file_path, words_count in search_result.items():
                    file.write(f"Путь к файлу: {file_path}\n")
                    file.write(f"Найдено в файле: {os.path.basename(file_path)}\n")
                    file.write("Все найденные слова:\n")
                    for word, positions in words_count.items():
                        file.write(f"{word} - {len(positions)}\n")
                        for position in positions:
                            file.write(f"  - Строка {position[0]}, Позиция в строке {position[1]}\n")
                    file.write("\n")
