import os


def shrinkuser(path):
    """ Reverts expanduser() """
    return path.replace(os.path.expanduser('~'), '~')
