import errno
import logging
import os


def mkdir_p(path):  # type: ignore[no-untyped-def]
    """http://stackoverflow.com/a/600612/190597 (tzot)"""
    try:
        os.makedirs(path, exist_ok=True)  # Python>3.2
    except TypeError:
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


class MakeFileHandler(logging.FileHandler):
    def __init__(self, filename, mode="a", encoding=None, delay=0):  # type: ignore[no-untyped-def]
        mkdir_p(os.path.dirname(filename))  # type: ignore[no-untyped-call]
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)
