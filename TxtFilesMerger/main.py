import os

# Корневая директория для поиска текстовых файлов
root_source_dir = r'C:\Users\root\Desktop\discord\DiscordTokens'

# Целевая директория для объединенного файла
target_dir = r'C:\Users\root\Desktop\discord'

# Имя объединенного файла
output_file_name = 'combined.txt'

# Полный путь к целевому файлу
output_file_path = os.path.join(target_dir, output_file_name)

# Создаем целевую директорию, если она не существует
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

# Строки, которые нужно фильтровать
filter_strings = [
    "",
]

# Счетчики для отладки
files_scanned = 0
raw_lines_count = 0

print("\nНачинаем копирование и первичную фильтрацию")
try:
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        # Рекурсивно перебираем все файлы и поддиректории в корневой директории
        for root, dirs, files in os.walk(root_source_dir):
            for file_name in files:
                if file_name.endswith('.txt'):
                    files_scanned += 1
                    print(f"\rСканирую файл {files_scanned}/{len(files)}: {file_name}", end='')
                    try:
                        with open(os.path.join(root, file_name), 'r', encoding='utf-8') as input_file:
                            for line in input_file:
                                # Фильтрация пустых и по подстрокам
                                if line.strip() and all(fs not in line for fs in filter_strings):
                                    output_file.write(line)
                                    raw_lines_count += 1
                            # Разделитель между файлами
                            output_file.write('\n')
                    except Exception as e:
                        print(f"Ошибка при обработке {file_name}: {e}")
    # print(f"\nФайлов обработано: {files_scanned}")
    # print(f"Строк записано после первичной фильтрации: {raw_lines_count}\n")
except Exception as e:
    print(f"Ошибка при открытии выходного файла: {e}")
    exit(1)

# Убираем пустые строки
print("\n\n———————————————————————————————————————————")
print("Убираем пустые строки")
with open(output_file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
empty_filtered = [line for line in lines if line.strip()]
empty_removed = len(lines) - len(empty_filtered)
# print(f"Удалено пустых строк: {empty_removed}")
with open(output_file_path, 'w', encoding='utf-8') as f:
    f.writelines(empty_filtered)

# Удаляем строки, превышающие 100 символов
print("Удаляем строки длиной более 100 символов")
with open(output_file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
long_filtered = [line for line in lines if len(line) <= 100]
long_removed = len(lines) - len(long_filtered)
# print(f"Удалено длинных строк (>100): {long_removed}")
with open(output_file_path, 'w', encoding='utf-8') as f:
    f.writelines(long_filtered)

# Убираем повторяющиеся строки, сохраняя порядок
print("Удаляем дублирующиеся строки")
print("———————————————————————————————————————————\n")
with open(output_file_path, 'r', encoding='utf-8') as f:
    seen = set()
    unique_lines = []
    for line in f:
        if line not in seen:
            unique_lines.append(line)
            seen.add(line)
duplicates_removed = len(long_filtered) - len(unique_lines)
# print(f"Удалено дубликатов: {duplicates_removed}\n")

# Запись финального файла и итоговые показатели
with open(output_file_path, 'w', encoding='utf-8') as f:
    f.writelines(unique_lines)

print("===========================================")
print(f"Файлов обработано: {files_scanned}")
print(f"Исходных строк после первичной фильтрации: {raw_lines_count}")
print(f"Удалено пустых строк: {empty_removed}")
print(f"Удалено длинных строк (>100): {long_removed}")
print(f"Удалено дубликатов: {duplicates_removed}")
print(f"Итоговое количество строк: {len(unique_lines)}")
print(f"Объединенный файл сохранен: {output_file_path}")
print("===========================================")
