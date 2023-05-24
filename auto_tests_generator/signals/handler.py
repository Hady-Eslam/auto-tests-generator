import sys
import inspect
from django.db.models import Model
from auto_tests_generator.files import FilesHandler
from typing import List


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
