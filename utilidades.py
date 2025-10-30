import logging, signal

_abort = False

def setup_logging(verbose: bool = True):
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(message)s")


def install_sigint_handler():
    def _on_sigint(sig, frame):
        global _abort
        _abort = True
        logging.warning("[Sistema] Interrupción recibida; limpiando...")
    signal.signal(signal.SIGINT, _on_sigint)


def aborted() -> bool:
    return _abort
