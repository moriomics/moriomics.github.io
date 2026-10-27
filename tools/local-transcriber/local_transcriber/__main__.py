import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    from .gui import launch
    raise SystemExit(launch())
