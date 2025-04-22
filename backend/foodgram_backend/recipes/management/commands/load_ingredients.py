import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from recipes.models import Ingredient


class Command(BaseCommand):
    """
    Management команда для загрузки ингредиентов из JSON или CSV файла.

    Ожидает файл в директории /app/fixtures/ внутри контейнера.
    Эта директория должна быть смонтирована из хост-системы
    (например, ./fixtures:/app/fixtures в docker-compose.yml).
    """
    help = (
        'Загружает ингредиенты из <filename>.json или <filename>.csv '
        'в /app/fixtures/ в базу данных'
    )

    FIXTURES_DIR = Path('/app/fixtures')

    def add_arguments(self, parser):
        parser.add_argument(
            'filename',
            type=str,
            help=(
                'Имя файла (например, ingredients.json или ingredients.csv) '
                'в директории /app/fixtures/'
            ),
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить таблицу Ingredient перед загрузкой новых данных.',
        )

    def handle(self, *args, **options):
        filename = options['filename']
        clear_table = options['clear']

        file_path = self.FIXTURES_DIR / filename

        self.stdout.write(
            f"Попытка загрузить данные из файла: {file_path}"
        )

        if not file_path.is_file():
            raise CommandError(
                f'Файл "{file_path}" не найден. Убедитесь, что он существует '
                f'в директории "{self.FIXTURES_DIR}" внутри контейнера '
                '(проверьте volume mount в docker-compose.yml).'
            )

        file_ext = file_path.suffix.lower()

        if clear_table:
            self._clear_ingredients_table()

        created_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(f"Обработка файла '{filename}'...")

        try:
            with transaction.atomic():
                if file_ext == '.json':
                    created_count, skipped_count, error_count = (
                        self._load_from_json(file_path)
                    )
                elif file_ext == '.csv':
                    created_count, skipped_count, error_count = (
                        self._load_from_csv(file_path)
                    )
                else:
                    raise CommandError(
                        f'Неподдерживаемый тип файла: "{file_ext}". '
                        'Используйте .json или .csv.'
                    )

        except IOError as e:
            raise CommandError(f'Ошибка чтения файла "{file_path}": {e}')
        except CommandError as e:
            raise e
        except Exception as e:
            raise CommandError(f'Непредвиденная ошибка во время загрузки: {e}')

        self._write_summary(
            filename, created_count, skipped_count, error_count
        )

    def _clear_ingredients_table(self):
        """Очищает таблицу Ingredient."""
        self.stdout.write(
            self.style.WARNING('Очистка таблицы Ingredient...')
        )
        try:
            with transaction.atomic():
                deleted_count, _ = Ingredient.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Удалено {deleted_count} ингредиентов.'
                )
            )
        except Exception as e:
            raise CommandError(f'Ошибка при очистке таблицы: {e}')

    def _load_from_json(self, file_path):
        """Загружает данные из JSON файла и возвращает статистику."""
        created_count = 0
        skipped_count = 0
        error_count = 0

        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError as e:
                raise CommandError(f'Ошибка декодирования JSON: {e}')

            if not isinstance(data, list):
                raise CommandError(
                    'JSON файл должен содержать список объектов.'
                )

        self.stdout.write(f"Найдено {len(data)} записей в JSON.")
        for item in data:
            if not isinstance(item, dict):
                self.stdout.write(self.style.WARNING(
                    f"Пропущен элемент (не словарь): {item}"
                ))
                skipped_count += 1
                continue

            name = item.get('name')
            unit = item.get('measurement_unit')

            if not self._validate_item(item, name, unit, 'JSON'):
                skipped_count += 1
                continue

            created, error = self._save_ingredient(name, unit)
            if error:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f"Ошибка сохранения JSON элемента {item}: {error}"
                ))
            elif created:
                created_count += 1
            else:
                skipped_count += 1

        return created_count, skipped_count, error_count

    def _load_from_csv(self, file_path):
        """Загружает данные из CSV файла и возвращает статистику."""
        created_count = 0
        skipped_count = 0
        error_count = 0

        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            if (
                not reader.fieldnames
                or 'name' not in reader.fieldnames
                or 'measurement_unit' not in reader.fieldnames
            ):
                raise CommandError(
                    "CSV файл должен содержать заголовки "
                    "'name' и 'measurement_unit'."
                )

            try:
                pass
            except Exception:
                pass

            for row_num, row in enumerate(reader, start=2):
                name = row.get('name')
                unit = row.get('measurement_unit')

                if not self._validate_item(row, name, unit, 'CSV', row_num):
                    skipped_count += 1
                    continue

                created, error = self._save_ingredient(name, unit)
                if error:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(
                        "Ошибка сохранения строки CSV"
                    ))
                elif created:
                    created_count += 1
                else:
                    skipped_count += 1

        return created_count, skipped_count, error_count

    def _validate_item(self, item, name, unit, source_type, line_num=None):
        """Проверяет корректность данных для одного ингредиента."""
        line_info = f" (строка {line_num})" if line_num else ""
        if not name or not isinstance(name, str):
            self.stdout.write(self.style.WARNING(
                f"Пропущен элемент {source_type}{line_info}:"
                f" некорректен 'name' в {item}"
            ))
            return False
        if not unit or not isinstance(unit, str):
            self.stdout.write(self.style.WARNING(
                f"Пропущен элемент {source_type}{line_info}: некорректен "
                f"'measurement_unit' в {item}"
            ))
            return False
        return True

    def _save_ingredient(self, name, unit):
        """
        Сохраняет или обновляет ингредиент.
        Возвращает (bool: created, str: error_message or None).
        """
        try:
            obj, created = Ingredient.objects.get_or_create(
                name=name.lower(),
                defaults={'measurement_unit': unit}
            )
            if not created and obj.measurement_unit != unit:
                obj.measurement_unit = unit
                obj.save()
                self.stdout.write(self.style.NOTICE(
                    f"Обновлена единица измерения для '{name.lower()}'"
                ))
            return created, None
        except Exception as e:
            return False, str(e)

    def _write_summary(self, filename, created, skipped, errors):
        """Выводит итоговую статистику."""
        summary = (
            f'Загрузка из "{filename}" завершена. '
            f'Добавлено новых: {created}, '
            f'Пропущено/Обновлено: {skipped}, '
            f'Ошибок при сохранении: {errors}.'
        )
        if errors > 0:
            self.stdout.write(self.style.ERROR(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
