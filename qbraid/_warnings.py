"""Module for disabling certain warnings"""
import warnings
import urllib3

warnings.filterwarnings("ignore", category=UserWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
