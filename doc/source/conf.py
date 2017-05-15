extensions = []
source_suffix = ".rst"
master_doc = "index"

project = "DICE TOSCA Library"
copyright = "2017, XLAB d.o.o."
author = "XLAB d.o.o."

# Dummy versions, these are set by pbr when generating docs
version = "1.0"
release = "1.0.0"

language = None
pygments_style = "sphinx"

# Theme
html_theme = "alabaster"
html_theme_options = {
    "page_width": "90em",
    "sidebar_width": "20em",
}
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
    ]
}
