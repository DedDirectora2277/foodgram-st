import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from recipes.models import Ingredient


class Command(BaseCommand):
    help = (
        'Загружает ингредиенты из файла'
        '../../data/ingredients.json '
        '(относительно manage.py) в базу данных'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
        )

    def handle(self, *args, **options):
        clear_table = options['clear']

        try:
            manage_py_dir = settings.BASE_DIR.parent
            project_root_dir = manage_py_dir.parent
            data_dir = project_root_dir / 'data'
            file_path = data_dir / 'ingredients.json'
            absolute_file_path = file_path.resolve()
        except AttributeError:
            raise CommandError(
                "Не удалось определить путь к файлу. "
                "Проверьте переменную BASE_DIR в settings.py."
            )

        self.stdout.write(
            f"Попытка загрузить данные из локального файла: "
            f"{absolute_file_path}"
        )

        if not absolute_file_path.is_file():
            error_message = (
                f'Файл "{absolute_file_path}" не найден. '
                'Убедитесь, что он существует по пути '
                '"../../data/ingredients.json"'
                'относительно директории, '
                'где находится manage.py.'
            )
            raise CommandError(error_message)

        if clear_table:
            self._clear_ingredients_table()

        created_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write("Обработка файла ...")

        try:
            with transaction.atomic():
                created_count, skipped_count, error_count = (
                    self._load_from_json(absolute_file_path)
                )

        except IOError as e:
            raise CommandError(
                f'Ошибка чтения файла "{absolute_file_path}": {e}'
            )
        except CommandError as e:
            raise e
        except Exception as e:
            raise CommandError(
                f'Непредвиденная ошибка во время загрузки: {e}'
            )

        self._write_summary(
            absolute_file_path.name,
            created_count,
            skipped_count,
            error_count
        )

    def _clear_ingredients_table(self):
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

            if not name or not isinstance(name, str):
                self.stdout.write(self.style.WARNING(
                    f"Пропущен элемент: некорректен 'name' в {item}"
                ))
                skipped_count += 1
                continue
            if not unit or not isinstance(unit, str):
                self.stdout.write(self.style.WARNING(
                    "Пропущен элемент: некорректен "
                    f"'measurement_unit' в {item}"
                ))
                skipped_count += 1
                continue

            created, error = self._save_ingredient(name, unit)
            if error:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f"Ошибка сохранения JSON элемента: {error}"
                ))
            elif created:
                created_count += 1
            else:
                skipped_count += 1

        return created_count, skipped_count, error_count

    def _save_ingredient(self, name, unit):
        try:
            obj, created = Ingredient.objects.get_or_create(
                name=name.lower(),
                defaults={'measurement_unit': unit}
            )
            if not created and obj.measurement_unit != unit:
                obj.measurement_unit = unit
                obj.save()
            return created, None
        except Exception as e:
            return False, str(e)

    def _write_summary(self, filename, created, skipped, errors):
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
