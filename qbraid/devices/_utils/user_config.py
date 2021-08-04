import configparser
import os
import sys

raw_input = input

aws_cred_path = os.path.join(os.path.expanduser("~"), ".aws-test", "credentials")
aws_config_path = os.path.join(os.path.expanduser("~"), ".aws-test", "config")
qiskit_config_path = os.path.join(os.path.expanduser("~"), ".qiskit-test", "settings.conf")

aws_values_to_prompt = [
    # (config_name, prompt_text, filepath, section)
    ('aws_access_key_id', "AWS Access Key ID", "default", aws_cred_path),
    ('aws_secret_access_key', "AWS Secret Access Key", "default", aws_cred_path),
    ('region', "Default region name", "default", aws_config_path),
    ('output', "Default output format", "default", aws_config_path),
]


def mask_value(current_value):
    if current_value is None:
        return 'None'
    else:
        return ('*' * 16) + current_value[-4:]


def get_value(current_value, config_name, prompt_text=''):
    if config_name in ('aws_access_key_id', 'aws_secret_access_key'):
        current_value = mask_value(current_value)
    response = compat_input("%s [%s]: " % (prompt_text, current_value))
    if not response:
        response = None
    return response


def compat_input(prompt):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    return raw_input()


def _run_main(values_to_prompt):
    config_dict = {}
    config = configparser.ConfigParser()
    for config_name, prompt_text, section, filename in values_to_prompt:
        if not os.path.exists(filename):

        config.read(filename)
        if section not in config.sections():
            config.add_section(section)
        current_value = config_dict.get(config_name)
        new_value = get_value(current_value, config_name, prompt_text)
        if new_value is not None and new_value != current_value:
            config.set(section, config_name, str(new_value))
            try:
                with open(filename, "w") as cfgfile:
                    config.write(cfgfile)
            except OSError as ex:
                raise Exception(f"Unable to load the config file {filename}. Error: '{str(ex)}'")
    return 0


if __name__ == "__main__":
    _run_main(aws_values_to_prompt)

