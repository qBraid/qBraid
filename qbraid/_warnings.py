"""Module for disabling certain warnings"""
import warnings
import urllib3

warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=UserWarning, message="Setuptools is replacing distutils")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
