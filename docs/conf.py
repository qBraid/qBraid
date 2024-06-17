# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import qbraid

# Set an environment variable to detect whether we are building the docs
# so that we know to use raw imports instead of lazy loading.
# os.environ['SPHINX_BUILD'] = '1'

# -- Project information -----------------------------------------------------

project = "qBraid"
copyright = "2024, qBraid Development Team"
author = "qBraid Development Team"

# The full version, including alpha/beta/rc tags
release = qbraid.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.autosummary",
    "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
]

# set_type_checking_flag = True
autodoc_member_order = "bysource"
autoclass_content = "both"
autodoc_mock_imports = [
    "boto3",
    "braket",
    "cirq",
    "matplotlib",
    "pennylane",
    "pyqir",
    "pyquil",
    "pytket",
    "qcaas_client",
    "qiskit",
    "qiskit_ibm_runtime",
    "scc",
    "stim",
]
napoleon_numpy_docstring = False
todo_include_todos = True
mathjax_path = "https://cdn.jsdelivr.net/npm/mathjax@2/MathJax.js?config=TeX-AMS-MML_HTMLorMML"

# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "*.pytest_cache",
    "*.ipynb_checkpoints",
    "*tests",
]

# A boolean that decides whether module names are prepended to all object names
# (for object types where a “module” of some kind is defined), e.g. for
# py:function directives.
add_module_names = False

# A list of prefixes that are ignored for sorting the Python module index
# (e.g., if this is set to ['foo.'], then foo.bar is shown under B, not F).
# This can be handy if you document a project that consists of a single
# package. Works only for the HTML builder currently.
modindex_common_prefix = ["qbraid."]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# html_theme_options = {
#     "collapse_navigation": False
# }

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_favicon = "_static/favicon.ico"
html_show_sphinx = False

html_css_files = ["css/s4defs-roles.css"]

# -- More customizations ----------------------------------------------------


# def skip_member(app, what, name, obj, skip, options):
#     print(app, what, name, obj, skip, options)
#     return True
#
#
# def setup(app):
#     app.connect('autodoc-skip-member', skip_member)
