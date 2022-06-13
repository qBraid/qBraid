# Updating the SDK in Lab

## Install new distribution in Lab virtual environment

Login to <https://lab.qbraid.com>, install the current `qBraid-SDK` environment if it not already, and open Terminal. Make sure that qBraid Quantum Jobs are disabled in the SDK environment using the qBraid CLI:

```shell
qbraid jobs disable -n qbraid_sdk
```

Install/upgrade build dependencies in the base conda environment, clone latest version of the SDK into your working directory, and build its wheel/tarball:

```shell
pip install --upgrade pip setuptools build
git clone https://github.com/qBraid/qBraid.git
python -m build qBraid/
```

Open the installed SDK python virtual environment config file with your preffered text editor,

```shell
vim /home/jovyan/.qbraid/environments/qbraid_sdk_9j9sjy/pyenv/pyvenv.cfg
```

and set `include-system-site-packages = false`:

```bash
home = /opt/conda/bin
include-system-site-packages = false 
version = 3.9.7
```

Activate the SDK python virtual environment, upgrade pip and setupools, and perform package updgrade by pip installing the new wheel:

```shell
source /home/jovyan/.qbraid/environments/qbraid_sdk_9j9sjy/pyenv/bin/activate
pip install --upgrade pip setuptools
pip install qBraid/dist/qbraid-[version]-py3-none-any.whl
deactivate
```

Undo the modifications made to the installed SDK python virtual environment config file by repeating the same procedure as before, but this time setting `include-system-site-packages = true`:

```bash
home = /opt/conda/bin
include-system-site-packages = true 
version = 3.9.7
```

Activate the `qBraid-SDK` environment from the environment manager, open a new notebook with the `Python 3 [qBraid-SDK]` kernel, and verify that the imports work, and that the new version is as expected:

```python
import qbraid
qbraid.__version__
```

## Update environment directory in EFS

`ssh` into the EFS filesystem, and navigate to the global environment directory:

```shell
cd /filesystem/global/environments
```

Archive the existing SDK package directory by appending the old version number e.g. `x.y.z` to the end of the slug (make sure to remove the periods):

```shell
mv qbraid_sdk_9j9sjy qbraid_sdk_9j9sjy_[xyz]
```

If needed, you can check the version of the existing SDK package by inspecting its `_version.py` file:

```bash
cat qbraid_sdk_9j9sjy/pyenv/lib/python3.9/site-packages/qbraid/_version.py
```

Next, copy over the new SDK directory from your lab account environments directory to the global environments directory. You can use the `admin-threaded-copy.py` python script to speed up the process:

```shell
mkdir qbraid_sdk_9j9sjy
sudo python3 admin-threaded-copy.py /filesystem/home/[userdir]/.qbraid/environments/qbraid_sdk_9j9sjy /filesystem/global/environments/qbraid_sdk_9j9sjy
```

There are a few important things to note when carrying out the step above:

1. The copy script requires that the target directory already exists. So, as shown above, you must create the new empty slug directory *first*, before executing the copy script.

2. The script will fail if either of the source or target directory end with a forward-slash. In other words, each directory location should end with `qbraid_sdk_9j9sjy`, not `qbraid_sdk_9j9sjy/`.

3. If the email associated with your account is exampleuser@gmail.com, then the value `userdir` in the filepath above will be `exampleuser-40gmail-2ecom`. Notice how `@` is mapped to `-40`, And `.` is mapped to `-2e`. Similar mappings exist for a number of other values, so keep that in mind when specifying the directory associated with your account.

## Verify successful update in Lab

Finally, navigate back to lab, uninstall and re-install the `qBraid-SDK` environment, and verify the environment is working as expected without any errors.
