import importlib

from django.conf import settings
from django.urls import URLPattern, URLResolver

from auto_tests_generator.files import FilesHandler


class URLHandler:
    """
        URLs Tests Handler
    """

    def __init__(self, files_handler: FilesHandler, root_urlconfig):
        self.__files_handler = files_handler
        self.__root_urlconfig = root_urlconfig
        self.__urls = []

    def __get_urls(self, _url_list=[], append=[]):
        """
            Get All URLs
        """
        for _url in _url_list:

            # If URL is URLResolver The Call The Same URL With The URLs List
            if isinstance(_url, URLResolver):
                self.__get_urls(
                    _url.url_patterns, append + [str(_url.pattern)])

            # If Url is URLPattern Then Append The URL to URLs Array
            # And Add The Path Of The URL
            elif isinstance(_url, URLPattern):
                self.__urls.append({
                    'path': append + [str(_url.pattern)],
                    'url': _url
                })

    def load_urls(self):
        """
            Load All URLs In The System
        """
        # Load urlconf file from settings ROOT_URLCONF
        old_value = None
        settings.DEBUG = old_value
        settings.DEBUG = False

        urlconf = importlib.import_module(self.__root_urlconfig)
        urlconf = importlib.reload(urlconf)

        # Load Urls
        self.__get_urls(urlconf.urlpatterns)

        settings.DEBUG = old_value
        urlconf = importlib.import_module(self.__root_urlconfig)
        urlconf = importlib.reload(urlconf)

    def __filter_url(self, url: str):
        """
            Filter Url With underscore ( _ ) so we can use it as to use it as
        """
        return url.replace('/', '_').replace('<', '_')\
            .replace(':', '_').replace('>', '_').replace('^', '_')\
            .replace('(', '_').replace(')', '_').replace('|', '_')\
            .replace('?', '_').replace('*', '_').replace('$', '_')\
            .replace('.', '_').replace('-', '_').replace('[', '_')\
            .replace(']', '_').replace('+', '_').replace('\\', '_')

    def __get_url_info(self, _url, _index):
        """
            Return URL Info TO Be Used In Templates
        """
        _url_path = ''.join(_url['path'])
        _filtered_url_path = self.__filter_url(_url_path)

        _callback = ''
        _callback_view = ''
        _callback_import = f"from {_url['url'].callback.__module__} import {_url['url'].callback.__name__}" # noqa
        _callback_is_model_view_set = False
        _view_set_actions = ''
        if hasattr(_url['url'].callback, 'cls'):
            _callback = f"{_url['url'].callback.__name__}"
            _callback_view = ".cls"
            if hasattr(_url['url'].callback, 'actions'):
                _callback_is_model_view_set = True
                _view_set_actions = _url['url'].callback.actions
        elif hasattr(_url['url'].callback, 'view_class'):
            _callback = f"{_url['url'].callback.__name__}"
            _callback_view = ".view_class"
        else:
            _callback = f"{_url['url'].callback.__name__}"

        return {
            'url': {
                'filtered_path': _filtered_url_path + '_url',
                'index': _index,
                'path': f"'{_url_path}'",
                'callback_import': _callback_import,
                'callback_view': _callback_view,
                'callback': _callback,
                'name_is_none': False if _url['url'].name else True, # noqa
                'name': f"'{_url['url'].name}'" if _url['url'].name else 'None', # noqa
                'callback_is_model_view_set': _callback_is_model_view_set, # noqa
                'actions': _view_set_actions,
            }
        }

    def generate_tests(self):
        _tests = []
        _index = 0

        for _url in self.__urls:
            _url_info: dict = self.__get_url_info(_url, _index)

            _tests.append(
                self.__files_handler.import_template(
                    'urls/url_test.txt', _url_info
                )
            )
            _index += 1

        _tests = self.__files_handler.import_template(
            'urls/base_class.txt', {
                'urls_count': _index,
                'tests': _tests,
            }
        )

        self.__files_handler.add_urls_tests(_tests)
