import os


# расположение файла локализации
translations_file_dir = os.path.dirname(__file__)


# открываем файл локализации
with open(os.path.join(translations_file_dir, 'translations.txt'), encoding='utf-8') as localization_file:
    lines = localization_file.read().splitlines()
total = tuple()
for line in lines:
    packages = list()
    for phrases in line.split('|~|~|~|'):  # разделитель языков
        the_phrase = list()
        for text in phrases.split('|<=>|'):  # разделитель вариантов фразы внутри языка
            exec(f'the_phrase.append("{text}")')
        packages += [the_phrase[0] if len(the_phrase) == 1 else tuple(the_phrase)]
    total += (tuple(packages), ) if len(packages) != 1 else tuple(packages)
total = total[0] if len(total) == 2 and total[1] == '' else total

# переменные локализации (их число должно совпадать с числом строк в соответствующем файле)
start_or_help_command, about_bot_command, feedback_messages, lang_button, language_changing, processing_phrase, \
    feedback_report, length_limit, prompt, response_lang, bot_error, cancel, command_error, ban = total
