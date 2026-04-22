import os


def remove_duplicate_lines(file_path):
    try:
        # Создание временного файла для хранения уникальных строк
        temp_file_path = file_path + '.tmp'

        # Используем set для отслеживания уникальных строк
        seen_lines = set()

        with open(file_path, 'r', encoding='utf-8') as infile, open(temp_file_path, 'w', encoding='utf-8') as outfile:
            for line in infile:
                if line not in seen_lines:
                    outfile.write(line)
                    seen_lines.add(line)

        # Замена оригинального файла на временный
        os.replace(temp_file_path, file_path)

        print(f"Файл '{file_path}' успешно обновлён. Удалены дублирующиеся строки.")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


file_path = 'C:\\Users\\123\\Desktop\\Новая папка (9)\\valid (1).txt'
remove_duplicate_lines(file_path)
