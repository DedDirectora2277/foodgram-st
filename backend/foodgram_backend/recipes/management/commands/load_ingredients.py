import json
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):
    """
    Management команда для загрузки ингредиентов из JSON файла.

    Загружает данные из файла, расположенного по пути:
    <корень_проекта>/data/ingredients.json
    где <корень_проекта> - это директория, содержащая папку backend.
    """
    help = 'Загружает ингредиенты из data/ingredients.json в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',

            help=(
                'Очистить таблицу Ingredient перед загрузкой '
                'новых данных.'
            )
        )

    def handle(self, *args, **options):
        project_root = Path(settings.BASE_DIR).resolve().parent.parent
        data_dir = project_root / 'data'
        data_file_path = data_dir / 'ingredients.json'

        self.stdout.write(
            f"Проверка наличия файла: {data_file_path}"
        )

        if not data_file_path.is_file():

            raise CommandError(
                f'Файл "{data_file_path}" не найден или не файл.'
            )

        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Очистка таблицы Ingredient...')
            )
            deleted_count, _ = Ingredient.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Удалено {deleted_count} ингредиентов.'
                )
            )

        self.stdout.write("Чтение JSON файла...")
        try:
            with open(data_file_path, 'r', encoding='utf-8') as file:
                ingredients_data = json.load(file)
            if not isinstance(ingredients_data, list):
                raise CommandError(
                    'JSON файл должен содержать список объектов.'
                )
        except json.JSONDecodeError as e:

            raise CommandError(
                f'Ошибка декодирования JSON в файле "{data_file_path}": {e}'
            )
        except IOError as e:

            raise CommandError(
                f'Ошибка чтения файла "{data_file_path}": {e}'
            )
        except Exception as e:
            raise CommandError(f'Непредвиденная ошибка: {e}')

        self.stdout.write("Загрузка ингредиентов в базу данных...")
        created_count = 0
        skipped_count = 0
        error_count = 0

        for item in ingredients_data:
            if not isinstance(item, dict):

                self.stdout.write(self.style.WARNING(
                    f"Пропущен элемент: не является словарем ({type(item)})"
                ))
                skipped_count += 1
                continue

            name = item.get('name')
            measurement_unit = item.get('measurement_unit')

            if not name or not isinstance(name, str):

                self.stdout.write(self.style.WARNING(
                    "Пропущен элемент: отсутствует или некорректен 'name' в "
                    f"{item}"
                ))
                skipped_count += 1
                continue
            if not measurement_unit or not isinstance(measurement_unit, str):

                self.stdout.write(self.style.WARNING(
                    "Пропущен элемент: отсутствует или некорректен "
                    f"'measurement_unit' в {item}"
                ))
                skipped_count += 1
                continue

            try:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name.lower(),
                    measurement_unit=measurement_unit,
                )

                if created:
                    created_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Ошибка при обработке {item}: {e}"
                ))
                error_count += 1

        summary = (
            f'Загрузка завершена. '
            f'Добавлено новых: {created_count}, '
            f'Пропущено (уже существовали или некорректные данные): {skipped_count}, '
            f'Ошибок при сохранении: {error_count}.'
        )

        if error_count > 0:
            self.stdout.write(self.style.ERROR(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
