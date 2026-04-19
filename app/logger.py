import logging
import sys

def setup_logger():
    l = logging.getLogger("JetsonMobile")
    l.setLevel(logging.INFO)
    if not l.handlers:
        h = logging.StreamHandler(sys.stdout)
        f = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        h.setFormatter(f)
        l.addHandler(h)
    return l

logger = setup_logger()