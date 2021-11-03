import subprocess
import sys
import logging


def install(package):
    logging.info(f"Installing {package}....")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
