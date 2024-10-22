import pathlib

from auto_tests_generator.files import FilesHandler
from auto_tests_generator.permissions.handler import PermissionsHandler
from auto_tests_generator.urls.handler import URLHandler
from auto_tests_generator.signals.handler import SignalsHandler


class AutoTestsGenerator:
    """
        Auto Tests Generator
    """

    def __init__(
        self, configs,
        tests_path, isort_settings_path, root_urlconfig,
        apps, permissions, roles
    ):
        self.__configs = {
            'permissions': {
                'generate_tests': False,
                'apps': 'all',
            },
            'urls': {
                'generate_tests': False
            },
            'signals': {
                'generate_tests': False,
                'apps': 'all',
            }
        }
        self.__configs.update(**configs)

        # Tests/Templates Files Handler
        self.__files_handler = FilesHandler(
            tests_path=tests_path,
            current_path=pathlib.Path(__file__).parent.resolve(),
            isort_settings_path=isort_settings_path,
        )

        # Permissions Tests Generator Handler
        if self.__configs['permissions']['generate_tests']:
            _apps = []
            if self.__configs['permissions']['apps'] == 'all':
                _apps = apps
            else:
                _apps = self.__configs['permissions']['apps'].split(',')
                for _app in _apps:
                    if _app not in apps:
                        raise Exception(f"No app with name {_app} was found")

            self.__permissions_handler = PermissionsHandler(
                files_handler=self.__files_handler,
                apps=_apps,
                permissions=permissions,
                roles=roles,
            )

        # Urls Tests Generator Handler
        if self.__configs['urls']['generate_tests']:
            self.__urls_handler = URLHandler(
                files_handler=self.__files_handler,
                root_urlconfig=root_urlconfig
            )

        # Signals Tests Generator Handler
        if self.__configs['signals']['generate_tests']:
            _apps = []
            if self.__configs['signals']['apps'] == 'all':
                _apps = apps
            else:
                _apps = self.__configs['signals']['apps'].split(',')
                for _app in _apps:
                    if _app not in apps:
                        raise Exception(f"No app with name {_app} was found")

            self.__signals_handler = SignalsHandler(
                files_handler=self.__files_handler,
                apps=_apps
            )

    def prepare(self):
        """
            Prepare Tests Conditions And Load Configurations
        """
        self.__files_handler.prepare_tests_folder()

        if self.__configs['permissions']['generate_tests']:
            self.__permissions_handler.load_permissions()
            self.__permissions_handler.check_permissions()

        if self.__configs['urls']['generate_tests']:
            self.__urls_handler.load_urls()

        if self.__configs['signals']['generate_tests']:
            self.__signals_handler.load_models()

    def generate_tests(self):
        """
            Generate Tests
        """
        if self.__configs['permissions']['generate_tests']:
            self.__permissions_handler.generate_tests()

        if self.__configs['urls']['generate_tests']:
            self.__urls_handler.generate_tests()

        if self.__configs['signals']['generate_tests']:
            self.__signals_handler.generate_tests()
