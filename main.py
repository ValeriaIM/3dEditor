import sys

ERROR_EXCEPTION = 1
ERROR_PYTHON_VERSION = 2
ERROR_MODULES_MISSING = 3
ERROR_QT_VERSION = 4
ERROR_OPEN_WINDOW = 5

try:
    from editor import redactor
    from editor import drawer
except Exception as e:
    print('Game modules not found: "{}"'.format(e), file=sys.stderr)
    sys.exit(ERROR_MODULES_MISSING)

if sys.version_info < (3, 6):
    print('Use python >= 3.6', file=sys.stderr)
    sys.exit(ERROR_PYTHON_VERSION)

try:
    from PyQt5 import QtGui, QtCore, QtWidgets
except Exception as e:
    print('PyQt5 not found: "{}". Use console version (cmines)'.format(e),
          file=sys.stderr)
    sys.exit(ERROR_QT_VERSION)

import argparse
from contextlib import contextmanager
import itertools
import logging

__version__ = '1.1'
__author__ = 'ValeriaIM'
__email__ = 'vkvaleria2000@gmail.com'

LOGGER_NAME = '3d-editor'
LOGGER = logging.getLogger(LOGGER_NAME)


def parse_args():
    """Разбор аргуметов запуска"""
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS]',
        description='3d editor. GUI version {}'.format(__version__),
        epilog='Author: {} <{}>'.format(__author__, __email__))

    parser.add_argument(
        '-c', '--config', type=str,
        metavar='FILENAME', default='settings.ini', help='configuration file')
    arg_group = parser.add_mutually_exclusive_group()
    arg_group.add_argument(
        '-l', '--log', type=str,
        metavar='FILENAME', default='3d-editor.log', help='log filename')
    arg_group.add_argument(
        '--no-log',
        action='store_true', help='no log')

    return parser.parse_args()


class NullStream:
    """Ничегонеделающий context manager"""

    def __getattr__(self, name):
        self.name = lambda *args: None
        return self.name

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def main():
    """Точка входа в приложение"""
    args = parse_args()

    if not args.no_log:
        try:
            stream = open(args.log, 'a')
        except Exception:
            stream = sys.stderr
    else:
        stream = NullStream()

    with stream:
        log = logging.StreamHandler(stream)
        log.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s <%(name)s>] %(message)s'))

        for module in (sys.modules[__name__], redactor, drawer):
            logger = logging.getLogger(module.LOGGER_NAME)
            logger.setLevel(logging.DEBUG if args.log else logging.ERROR)
            logger.addHandler(log)

        LOGGER.info('GUI Application started')

        try:
            application = QtWidgets.QApplication(sys.argv)
            redactor_window = redactor.RedactorWindow()
            redactor_window.setMaximumSize(redactor.RESOLUTION[0],
                                           redactor.RESOLUTION[1])
            redactor_window.show()
        except Exception as e:
            print('PyQt5 not found: "{}". Use console version (cmines)'.format(e),
                  file=sys.stderr)
            sys.exit(ERROR_OPEN_WINDOW)

        LOGGER.info('Window OK. Start application...')
        application.exec_()


if __name__ == "__main__":
    main()
