import sys
import inspect
from django.db.models import Model
from auto_tests_generator.files import FilesHandler
from typing import List
import faker
from celery import _state
from django.contrib.postgres.fields import ArrayField
from django.db.models import (
    URLField, JSONField, TextField, CharField, IntegerField, DateField,
    BooleanField, FloatField, DecimalField, DateTimeField, EmailField,
    UUIDField, ForeignKey
)

_faker = faker.Faker()


class SignalsHandler:

    def __init__(self, files_handler: FilesHandler, apps) -> None:
        self.__models: List[Model] = []
        self.__files_handler = files_handler
        self.__apps = apps

    def load_models(self):
        for name in list(sys.modules):
            module = sys.modules[name]
            if name.startswith(tuple(self.__apps)):
                for member in inspect.getmembers(module, inspect.isclass):
                    member[0]
                    _member_class = member[1]
                    if issubclass(_member_class, Model) and \
                            _member_class.__module__ == name:
                        self.__models.append(_member_class)

        self.__rearrange_models()

    def __rearrange_models(self):
        _models = []
        _models_with_not_null_forien_keys = []

        for model in self.__models:
            tricky = False
            for field in model._meta.get_fields():
                if isinstance(field, ForeignKey) and not field.null:
                    tricky = True

            if tricky:
                _models_with_not_null_forien_keys.append(model)
            else:
                _models.append(model)

        self.__models: List[Model] = [
            *_models,
            *_models_with_not_null_forien_keys
        ]

    def generate_tests(self):
        self.__generate_conftest()

        for model in self.__models:
            if model._meta.abstract:
                continue

            self.__files_handler.generate_signals_tests_file(
                model.__name__,
                self.__files_handler.import_template(
                    "signals/test_signals.txt", {
                        "model": {
                            "name": model.__name__,
                            "module": model.__module__,
                            "forien_keys": self.__get_model_forien_keys(model)
                        }
                    }
                )
            )

    def __get_model_forien_keys(self, model: Model):
        _fields = []
        for field in model._meta.get_fields():
            if not field.auto_created and isinstance(field, ForeignKey):
                _fields.append({
                    'name': field.name,
                    'can_import': field.related_model.__name__ != model.__name__, # noqa
                    'module': field.related_model.__module__,
                    'model': field.related_model.__name__,
                })

        return _fields

    def __generate_conftest(self):
        self.__files_handler.generate_signals_contest_file(
            self.__files_handler.import_template(
                "signals/conftest.txt", {
                    "models": self.__get_models_info(),
                    "celery_tasks": self.__get_celery_tasks()
                }
            )
        )

    def __get_celery_tasks(self):
        _tasks = []
        for task_name, task in _state.get_current_app().tasks.items():
            _split_task_name = task_name.split('.')
            if _split_task_name[0] not in self.__apps:
                continue
            _tasks.append({
                'module': '.'.join(_split_task_name[:-1]),
                'name': _split_task_name[-1],
                'fullname': task_name,
            })
        return _tasks

    def __get_models_info(self):
        models_info = []

        for model in self.__models:
            if model._meta.abstract:
                continue

            _info = {
                "name": model.__name__,
                "module": model.__module__,
                "variable_name": f"_{model.__name__.lower()}",
                "fields": []
            }

            for field in model._meta.get_fields():

                if field.auto_created:
                    continue

                elif isinstance(field, URLField):
                    _info['fields'].append({
                        "name": field.name,
                        "value": '_faker.url()'
                    })

                elif isinstance(field, JSONField):
                    _info['fields'].append({
                        "name": field.name,
                        "value": "_faker.json(data_columns={'ID': 'pyint', 'Details': {'Name': 'name', 'Address': 'address'} })" # noqa
                    })

                elif isinstance(field, TextField):
                    value = "_faker.paragraph(nb_sentences=5)"
                    if field.choices:
                        value = f"_faker.random_element(elements={model.__name__}._meta.get_field('{field.name}').choices)" # noqa

                    _info['fields'].append({
                        "name": field.name,
                        "value": value
                    })

                elif isinstance(field, EmailField):
                    _info['fields'].append({
                        "name": field.name,
                        "value": '_faker.email()'
                    })

                elif isinstance(field, CharField):
                    value = f"_faker.word()[:{field.max_length}]"
                    if field.choices:
                        value = f"_faker.random_element(elements={model.__name__}._meta.get_field('{field.name}').choices)" # noqa

                    _info['fields'].append({
                        "name": field.name,
                        "value": value
                    })

                elif isinstance(field, IntegerField):
                    _info['fields'].append({
                        "name": field.name,
                        "value": "_faker.pyint()"
                    })

                elif isinstance(field, DateTimeField):
                    _info['fields'].append({
                        "name": field.name,
                        "value": "_faker.date_time()"
                    })

                elif isinstance(field, DateField):
                    _info['fields'].append({
                        "name": field.name,
                        "value": "_faker.date()"
                    })

                elif isinstance(field, BooleanField):
                    _info['fields'].append({
                        "name": field.name,
                        "value": "_faker.pybool()"
                    })

                elif isinstance(field, FloatField):
                    _info['fields'].append({
                        "name": field.name,
                        "value": "_faker.pyfloat()"
                    })

                elif isinstance(field, DecimalField):
                    right_digits = field.decimal_places
                    left_digits = field.max_digits - field.decimal_places
                    _info['fields'].append({
                        "name": field.name,
                        "value": f"_faker.pydecimal(left_digits={left_digits}, right_digits={right_digits})" # noqa
                    })

                elif isinstance(field, UUIDField):
                    _info['fields'].append({
                        "name": field.name,
                        "value": "_faker.uuid4()"
                    })

                elif isinstance(field, ArrayField):
                    _info['fields'].append({
                        "name": field.name,
                        "value": "[]"
                    })

                elif isinstance(field, ForeignKey) and not field.null:
                    _info['fields'].append({
                        "name": field.name,
                        "value": f"_{field.related_model.__name__.lower()}"
                    })

            models_info.append(_info)

        return models_info
