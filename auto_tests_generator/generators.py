import pathlib

from auto_tests_generator.files import FilesHandler
from auto_tests_generator.urls.handler import URLHandler


class AutoTestsGenerator:
    """
        Auto Tests Generator
    """

    def __init__(self, tests_path):
        # Tests/Templates Files Handler
        self.__files_handler = FilesHandler(
            tests_path=tests_path,
            current_path=pathlib.Path(__file__).parent.resolve()
        )

        # Urls Tests Generator Handler
        self.__urls_handler = URLHandler(
            files_handler=self.__files_handler,
        )

    def prepare(self):
        """
            Prepare Tests Conditions And Load Configurations
        """
        self.__files_handler.prepare_tests_folder()

        self.__urls_handler.load_urls()

    def generate_tests(self):
        """
            Generate Tests
        """
        self.__urls_handler.generate_tests()