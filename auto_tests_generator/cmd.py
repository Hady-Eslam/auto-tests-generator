from colorama import Fore, Style
from colorama import init as colorama_init

colorama_init()


class CMD:

    __identitation = 0

    def start_block(self):
        self.__identitation += 1

    def end_block(self):
        self.__identitation -= 1
        if self.__identitation < 0:
            self.__identitation = 0

    def info(self, message, new_line=True, ident=True):
        _ident = ''.join(['\t' for i in range(self.__identitation)])
        if not ident:
            _ident = ''

        print(
            f"{Fore.LIGHTWHITE_EX}{_ident}{message}{Style.RESET_ALL}",
            end='\n' if new_line else ''
        )

    def success(self, message, new_line=True, ident=True):
        _ident = ''.join(['\t' for i in range(self.__identitation)])
        if not ident:
            _ident = ''

        print(
            f"{Fore.LIGHTGREEN_EX}{_ident}{message}{Style.RESET_ALL}",
            end='\n' if new_line else ''
        )

    def input(self, message, new_line=True, ident=True):
        _ident = ''.join(['\t' for i in range(self.__identitation)])
        if not ident:
            _ident = ''

        print(
            f"{Fore.LIGHTCYAN_EX}{_ident}{message}{Style.RESET_ALL}",
            end='\n' if new_line else ''
        )
        return input()

    def new_line(self):
        print()


cmd = CMD()
