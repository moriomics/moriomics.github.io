"""PyInstaller entry point. freeze_support must precede GUI imports."""
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    from local_transcriber.gui import launch
    raise SystemExit(launch())
