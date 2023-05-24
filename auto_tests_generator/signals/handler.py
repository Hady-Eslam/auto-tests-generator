import sys
import inspect
from django.db.models import Model
from auto_tests_generator.files import FilesHandler
from typing import List
import faker
from django.db.models import (
    URLField, JSONField, TextField, CharField, IntegerField, DateField,
    BooleanField, FloatField, DecimalField, DateTimeField, EmailField,
    UUIDField,
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
                            "module": model.__module__
                        }
                    }
                )
            )

    def __generate_conftest(self):
        self.__files_handler.generate_signals_contest_file(
            self.__files_handler.import_template(
                "signals/conftest.txt", self.__get_model_info()
            )
        )

    def __get_model_info(self):
        models_info = []

        for model in self.__models:
            if model._meta.abstract:
                continue

            _info = {
                "name": model.__name__,
                "module": model.__module__,
                "fields": []
            }

            for field in model._meta.get_fields():

                if isinstance(field, URLField):
                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": '_faker.url()'
                    })

                elif isinstance(field, JSONField):
                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": "_faker.json(data_columns={'ID': 'pyint', 'Details': {'Name': 'name', 'Address': 'address'} })" # noqa
                    })

                elif isinstance(field, TextField):
                    value = "_faker.paragraph(nb_sentences=5)"
                    if field.choices:
                        value = f"_faker.random_element(elemnts={model.__name__}._meta.get_field('{field.name}').choices)" # noqa

                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": value
                    })

                elif isinstance(field, EmailField):
                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": '_faker.email()'
                    })

                elif isinstance(field, CharField):
                    value = "_faker.word()"
                    if field.choices:
                        value = f"_faker.random_element(elemnts={model.__name__}._meta.get_field('{field.name}').choices)" # noqa

                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": value
                    })

                elif isinstance(field, IntegerField):
                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": "_faker.pyint()"
                    })

                elif isinstance(field, DateTimeField):
                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": "_faker.date_time()"
                    })

                elif isinstance(field, DateField):
                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": "_faker.date()"
                    })

                elif isinstance(field, BooleanField):
                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": "_faker.pybool()"
                    })

                elif isinstance(field, FloatField):
                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": "_faker.pyfloat()"
                    })

                elif isinstance(field, DecimalField):
                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": "_faker.pydecimal()"
                    })

                elif isinstance(field, UUIDField):
                    _info['model']['fields'].append({
                        "name": field.name,
                        "value": "_faker.uuid4()"
                    })

            models_info.append(_info)

        return models_info
