import os
import subprocess

def _call_script(script):
    dir_path = os.path.dirname(os.path.realpath(__file__)) + '/scripts'
    scripts = list(filter(lambda x: x[-3:] == ".sh", os.listdir(dir_path)))
    if script not in scripts:
        raise ValueError(f"\ndir_path: {dir_path}\n scripts: {scripts} \n Script '{script}' not found.\n")
    script_path = os.path.join(dir_path, script)
    subprocess.call([script_path])

def update_headers():
    _call_script("update-headers.sh")


if __name__ == "__main__":

    update_headers()

