"""
Module for executing a pip install of a package programmatically.

"""
# import logging
# import subprocess
# import sys

# from qbraid import QbraidError


# def install(package: str):
#     """Executes ``python -m pip install package`` for given ``package``"""
#     logging.info("Installing %s....", package)
#     try:
#         subprocess.check_call([sys.executable, "-m", "pip", "install", package])
#     except subprocess.CalledProcessError as err:
#         raise QbraidError(f"Failed to install {package}") from err
