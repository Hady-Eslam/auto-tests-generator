import inspect
import sys

from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
import requests
import json

from auto_tests_generator.cmd import cmd
from auto_tests_generator.files import FilesHandler


class PermissionsHandler:

    def __init__(
            self, files_handler: FilesHandler,
            apps, permissions, auth0_credentials):

        self.__files_handler = files_handler
        self.__apps = apps
        self.__roles = ['anonymous', 'un-identified-role']
        self.__apis = {}
        self.__initial_permissions = permissions
        self.__auth0_credentials = auth0_credentials

        cmd.info("Start Generating Permissions Tests...")
        cmd.new_line()

    def __get_token(self):
        parameters = {
            "client_id": self.__auth0_credentials['AUTH0_CLIENT_ID'],
            "client_secret": self.__auth0_credentials['AUTH0_CLIENT_SECRET'],
            "audience": self.__auth0_credentials['AUTH0_AUDIENCE'],
            "grant_type": "client_credentials"
        }
        headers = {'content-type': "application/json"}
        response = requests.post(
            self.__auth0_credentials['AUTH0_APP_TOKEN_URL'],
            data=json.dumps(parameters),
            headers=headers
        )
        return response.json()['access_token']

    def load_roles(self):
        headers = {
            'Authorization': f"Bearer {self.__get_token()}",
            'Content-Type': "application/json"
        }
        url = f"{self.__auth0_credentials['AUTH0_URL']}roles"
        response = requests.get(url, headers=headers)

        if response.status_code == status.HTTP_200_OK:
            self.__roles += [role['name'] for role in response.json()]
        else:
            raise Exception("Failed to list users roles")

    def load_permissions(self):
        cmd.start_block()
        cmd.info('Loading APIs.', new_line=False, ident=True)

        for name in list(sys.modules):
            module = sys.modules[name]
            if name.startswith(tuple(self.__apps)):
                for member in inspect.getmembers(module, inspect.isclass):
                    _member_name = member[0]
                    _member_class = member[1]
                    if issubclass(_member_class, APIView) and \
                            _member_class.__module__ == name:
                        self.__apis[_member_name] = {
                            'api': _member_class,
                            'allowed': False
                        }
                        cmd.info(".", new_line=False, ident=False)

        self.__permissions = self.__prepare_permissions(
            self.__initial_permissions
        )

        cmd.new_line()
        cmd.success('Permissions Loaded Successfully.')
        cmd.end_block()

    def check_permissions(self):
        _apis = {}

        cmd.start_block()
        cmd.info('Check Permissions.', new_line=True, ident=True)

        for api_name in self.__apis:

            is_allowed = False
            if list(self.__apis[api_name]['api'].permission_classes) == []:
                is_allowed = cmd.input(
                    f"This API {api_name} has no permissions. do "
                    "you want to allow this behavior ? Press [y/n]: ",
                    new_line=False
                )
                is_allowed = True if is_allowed == 'y' else False

            _apis[api_name] = {
                'api': self.__apis[api_name]['api'],
                'allowed': is_allowed
            }

        self.__apis = _apis

        cmd.success("Permissions Checked Successfully.")
        cmd.end_block()

    def __prepare_permissions(self, permissions: dict):
        _prepared_permissions = {}

        for api_name, api in self.__apis:
            _api_permissions = {}

            for role in self.__roles:

                if api_name not in self.__permissions[api_name]:
                    if isinstance(api['api'], ModelViewSet):
                        _api_permissions[role] = {
                            'list': False,
                            'create': False,
                            'retrieve': False,
                            'update': False,
                            'partial_update': False,
                            'destroy': False,
                        }
                    else:
                        _api_permissions[role] = {
                            'GET': False,
                            'POST': False,
                            'PUT': False,
                            'PATCH': False,
                            'DELETE': False
                        }

                elif role in self.__permissions[api_name]:
                    _api_permissions[role] = api[role]

            _prepared_permissions[api_name] = _api_permissions

        return _prepared_permissions

    def generate_tests(self):
        self.__generate_files()

    def __generate_files(self):
        self.__generate_utils_file()
        self.__generate_conftest_file()
        self.__generate_permissions_tests()

        cmd.new_line()
        cmd.success("Done Generating Permissions Tests...")

    def __generate_utils_file(self):
        roles = []

        cmd.start_block()
        cmd.info("Generate Utils Files.")

        for role in self.__roles:
            if role == 'anonymous':
                continue

            roles.append({
                'role_filtered_name': role.replace('-', '_'),
                'role_name': role,
                'role_name_uppercase': role.replace('-', ' ').title()
            })

        content = self.__files_handler.import_template(
            'permissions/auth_tokens.txt', {
                'roles': roles
            }
        )

        self.__files_handler.add_permissions_utils('auth_tokens.py', content)

        cmd.success("Utils Generated Successfully.")
        cmd.end_block()

    def __generate_conftest_file(self):
        roles = []
        mock_roles = []

        cmd.start_block()
        cmd.info("Generate Conftest File..")

        for role in self.__roles:
            if role == 'anonymous':
                continue

            roles.append({
                'role_filtered_name': role.replace('-', '_'),
                'role_name': role,
                'role_name_uppercase': role.replace('-', ' ').title()
            })

            mock_roles.append(
                self.__files_handler.import_template(
                    'permissions/mock_role.txt', {
                        'role_name': role.replace('-', '_')
                    })
            )

        conftest_content = self.__files_handler.import_template(
            'permissions/conftest.txt', {
                'auth_tokens_file_import': f'tests.auto_generated_tests.utils.auth_tokens', # noqa
                'roles': roles,
                'mock_roles': mock_roles
            }
        )

        self.__files_handler.generate_permissions_conftest_file(
            conftest_content
        )

        cmd.success("Conftest File Generated Successfully..")
        cmd.end_block()

    def __generate_permissions_tests(self):
        cmd.start_block()
        cmd.info("Generate Permissions Tests...")

        for api_name, api in self.__apis.items():

            _role_tests = []
            for role in self.__roles:
                if isinstance(api['api'], ModelViewSet):
                    _role_tests.append(
                        self.__get_roles_viewset_tests(
                            role, api_name, self.__permissions[api_name],
                            api['allowed']
                        )
                    )
                else:
                    _role_tests.append(
                        self.__get_roles_api_tests(
                            role, api_name, self.__permissions[api_name],
                            api['allowed']
                        )
                    )

            cmd.start_block()
            cmd.info(f"Generate {api_name} Permissions Tests...")

            content = self.__files_handler.import_template(
                'permissions/test_permissions.txt', {
                    'api_name': api_name,
                    'api_module': api['api'].__module__,
                    'api_action': api['api'].__module__ + '.' + api['api'].__name__, # noqa
                    'is_api': False if 'create' in self.__permissions[api_name][role] else True, # noqa
                    'is_anonymous_allowed': api['allowed'],
                    'testing_roles': _role_tests
                }
            )

            self.__files_handler.generate_api_permissions_file(
                api['api'], content
            )

            cmd.end_block()

        cmd.success("Permissions Tests Generated Successfully.")
        cmd.end_block()

    def __get_roles_viewset_tests(
            self, role, api_name, api, is_anonymous_allowed=False):

        unauthorized_create_status = 'HTTP_403_FORBIDDEN'
        unauthorized_list_status = 'HTTP_403_FORBIDDEN'
        unauthorized_retrieve_status = 'HTTP_403_FORBIDDEN'
        unauthorized_update_status = 'HTTP_403_FORBIDDEN'
        unauthorized_partial_update_status = 'HTTP_403_FORBIDDEN'
        unauthorized_destroy_status = 'HTTP_403_FORBIDDEN'

        if role == 'anonymous':
            unauthorized_create_status = 'HTTP_401_UNAUTHORIZED'
            unauthorized_list_status = 'HTTP_401_UNAUTHORIZED'
            unauthorized_retrieve_status = 'HTTP_401_UNAUTHORIZED'
            unauthorized_update_status = 'HTTP_401_UNAUTHORIZED'
            unauthorized_partial_update_status = 'HTTP_401_UNAUTHORIZED'
            unauthorized_destroy_status = 'HTTP_401_UNAUTHORIZED'

        return self.__files_handler.import_template(
            'permissions/role_test_permissions.txt', {
                'role_title': role.title().replace('-', ''),
                'api_name': api_name,
                'role_filtered_name': role.replace('-', '_'),
                'create': {
                    'can_create': '' if api[role]['create'] else 'not_',
                    'url': 'url',
                    'status': 'HTTP_201_CREATED' if (
                        api[role]['create'] or is_anonymous_allowed
                    ) else unauthorized_create_status,
                },
                'list': {
                    'can_list': '' if api[role]['list'] else 'not_',
                    'url': 'url',
                    'status': 'HTTP_200_OK' if (
                        api[role]['list'] or is_anonymous_allowed
                    ) else unauthorized_list_status,
                },
                'retrieve': {
                    'can_retrieve': '' if api[role]['retrieve'] else 'not_',
                    'url': 'url',
                    'status': 'HTTP_200_OK' if (
                        api[role]['retrieve'] or is_anonymous_allowed
                    ) else unauthorized_retrieve_status,
                },
                'update': {
                    'can_update': '' if api[role]['update'] else 'not_',
                    'url': 'url',
                    'status': 'HTTP_200_OK' if (
                        api[role]['update'] or is_anonymous_allowed
                    ) else unauthorized_update_status,
                },
                'partial_update': {
                    'can_patch': '' if api[role]['partial_update'] else 'not_',
                    'url': 'url',
                    'status': 'HTTP_200_OK' if (
                        api[role]['partial_update'] or is_anonymous_allowed
                    ) else unauthorized_partial_update_status,
                },
                'destroy': {
                    'can_destroy': '' if api[role]['destroy'] else 'not_',
                    'url': 'url',
                    'status': 'HTTP_204_NO_CONTENT' if (
                        api[role]['destroy'] or is_anonymous_allowed
                    ) else unauthorized_destroy_status,
                }
            }
        )

    def __get_roles_api_tests(
            self, role, api_name, api, is_anonymous_allowed=False):

        unauthorized_post_status = 'HTTP_403_FORBIDDEN'
        unauthorized_get_status = 'HTTP_403_FORBIDDEN'
        unauthorized_put_status = 'HTTP_403_FORBIDDEN'
        unauthorized_patch_status = 'HTTP_403_FORBIDDEN'
        unauthorized_delete_status = 'HTTP_403_FORBIDDEN'

        if role == 'anonymous':
            unauthorized_post_status = 'HTTP_401_UNAUTHORIZED'
            unauthorized_get_status = 'HTTP_401_UNAUTHORIZED'
            unauthorized_put_status = 'HTTP_401_UNAUTHORIZED'
            unauthorized_patch_status = 'HTTP_401_UNAUTHORIZED'
            unauthorized_delete_status = 'HTTP_401_UNAUTHORIZED'

        return self.__files_handler.import_template(
            'permissions/role_api_test_permissions.txt', {
                'role_title': role.title().replace('-', ''),
                'api_name': api_name,
                'role_filtered_name': role.replace('-', '_'),
                'post': {
                    'can_post': '' if api[role]['POST'] else 'not_',
                    'url': 'url',
                    'status': 'HTTP_201_CREATED' if (
                        api[role]['POST'] or is_anonymous_allowed
                    ) else unauthorized_post_status,
                },
                'get': {
                    'can_get': '' if api[role]['GET'] else 'not_',
                    'url': 'url',
                    'status': 'HTTP_200_OK' if (
                        api[role]['GET'] or is_anonymous_allowed
                    ) else unauthorized_get_status,
                },
                'put': {
                    'can_put': '' if api[role]['PUT'] else 'not_',
                    'url': 'url',
                    'status': 'HTTP_200_OK' if (
                        api[role]['PUT'] or is_anonymous_allowed
                    ) else unauthorized_put_status,
                },
                'patch': {
                    'can_patch': '' if api[role]['PATCH'] else 'not_',
                    'url': 'url',
                    'status': 'HTTP_200_OK' if (
                        api[role]['PATCH'] or is_anonymous_allowed
                    ) else unauthorized_patch_status,
                },
                'delete': {
                    'can_delete': '' if api[role]['DELETE'] else 'not_',
                    'url': 'url',
                    'status': 'HTTP_204_NO_CONTENT' if (
                        api[role]['DELETE'] or is_anonymous_allowed
                    ) else unauthorized_delete_status,
                }
            }
        )
