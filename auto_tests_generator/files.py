import os
from pathlib import Path
import sys

from django.template import Context, Template

import autoflake
import black
import isort


class FilesHandler:

    __generated_tests_folder_name = 'auto_generated_tests'

    __permissions_path_name = 'permissions'
    __urls_path_name = 'urls'

    def __init__(self, tests_path, current_path, isort_settings_path) -> None:
        self.__tests_path = tests_path
        self.__current_path = current_path
        self.__isort_settings_path = isort_settings_path

        self.__generated_tests_path = Path(self.__tests_path) / self.__generated_tests_folder_name # noqa

        self.__utils_path = self.__generated_tests_path / 'utils'

        self.__permissions_path = self.__generated_tests_path / self.__permissions_path_name # noqa
        self.__urls_path = self.__generated_tests_path / self.__urls_path_name

        self.__templates_path = self.__current_path / 'templates' # noqa

    def prepare_tests_folder(self):
        self.__generate_tests_folder_structure()

    def __generate_tests_folder_structure(self):
        # Create generated tests Folder
        if not os.path.exists(self.__generated_tests_path):
            os.mkdir(self.__generated_tests_path)
            open(self.__generated_tests_path / "__init__.py", "x")

        # Create Utils Folder
        if not os.path.exists(self.__generated_tests_path):
            os.mkdir(self.__utils_path)
            open(self.__utils_path / "__init__.py", "x")

        # Create API permissions folder
        if not os.path.exists(self.__permissions_path):
            os.mkdir(self.__permissions_path)
            open(self.__permissions_path / "__init__.py", "x")

        # Create URLs folder
        if not os.path.exists(self.__urls_path):
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

        with open(_file_path, "w") as file:
            file.write(content)

        self.__isort_imports(_file_path)
        self.__use_autoflake(_file_path)

    ####################################
    # APIs Permissions File Operations #
    ####################################

    def generate_permissions_conftest_file(self, content):
        app_path = self.__permissions_path

        content = self.__use_black(content)

        with open(app_path / 'conftest.py', 'w') as file:
            file.write(content)

        self.__isort_imports(str(app_path / 'conftest.py'))
        self.__use_autoflake(str(app_path / 'conftest.py'))

    def generate_api_permissions_file(self, api, content):
        app_path = self.__permissions_path / api.__module__.split('.')[0]
        if not os.path.exists(app_path):
            os.mkdir(app_path)
            open(app_path / '__init__.py', "w")

        content = self.__use_black(content)

        with open(
                app_path / f'test_{api.__name__}_permissions.py', "x"
        ) as file:
            file.write(content)

        self.__isort_imports(
            str(app_path / f'test_{api.__name__}_permissions.py'))
        self.__use_autoflake(
            str(app_path / f'test_{api.__name__}_permissions.py'))

    def add_permissions_utils(self, file_name, content):
        file_path = self.__utils_path / file_name

        content = self.__use_black(content)

        with open(file_path, 'w') as file:
            file.write(content)

        self.__isort_imports(file_path)
        self.__use_autoflake(file_path)
