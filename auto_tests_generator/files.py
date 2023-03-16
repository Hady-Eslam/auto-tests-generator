import os
from pathlib import Path
import shutil
import sys

from django.template import Context, Template

import autoflake
import black
import isort


class FilesHandler:

    __generated_tests_folder_name = 'auto_generated_tests'

    __urls_path_name = 'urls'

    def __init__(self, tests_path, current_path, isort_settings_path) -> None:
        self.__tests_path = tests_path
        self.__current_path = current_path
        self.__isort_settings_path = isort_settings_path

        self.__generated_tests_path = \
            Path(self.__tests_path) / self.__generated_tests_folder_name

        self.__urls_path = self.__generated_tests_path / self.__urls_path_name

        self.__templates_path = self.__current_path / 'auto_tests_generator' / 'templates' # noqa

    def prepare_tests_folder(self):
        self.__remove_old_folder()
        self.__generate_tests_folder_structure()

    def __remove_old_folder(self):
        """
            Remove Old auto_generated_tests Folder
        """
        shutil.rmtree(self.__generated_tests_path) if os.path.exists(
            self.__generated_tests_path) else None

    def __generate_tests_folder_structure(self):
        # Create generated tests Folder
        os.mkdir(self.__generated_tests_path)
        open(self.__generated_tests_path / "__init__.py", "x")

        # Create URLs folder
        os.mkdir(self.__urls_path)
        open(self.__urls_path / "__init__.py", "x")

    def import_template(self, template_path, context):
        """
            Import Template And Render The Template WIth Context Value
        """
        with open(self.__templates_path / template_path) as file:
            template = Template(file.read()).render(Context(context))
            return template

    def __isort_imports(self, file_path):
        """
            Use Isort On This File Path
        """
        isort.SortImports(
            file_path=file_path,
            settings_path=self.__isort_settings_path
        )

    def __use_black(self, content):
        _content = black.format_str(
            src_contents=content,
            mode=black.Mode(line_length=79)
        )
        return _content

    def __use_autoflake(self, file_path):
        argv = [
            'autoflake', '-i', '--remove-all-unused-imports', str(file_path)]
        autoflake._main(
            argv=argv,
            standard_out=None,
            standard_error=sys.stderr,
            standard_input=sys.stdin,
        )

    ########################
    # Urls File Operations #
    ########################

    def add_urls_tests(self, content):
        """
            Create Urls Tests File And Dump into it the Tests Content
        """
        _file_path = self.__urls_path / 'test_urls.py'

        content = self.__use_black(content)

        with open(_file_path, "x") as file:
            file.write(content)

        self.__isort_imports(_file_path)
        self.__use_autoflake(_file_path)
