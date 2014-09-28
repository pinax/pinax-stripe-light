import pkg_resources


extensions = []
templates_path = []
source_suffix = '.rst'
master_doc = 'index'
project = u'django-stripe-payments'
copyright_holder = 'James Tauber and Contributors'
copyright = u'2014, %s' % copyright_holder
exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_theme = 'default'
htmlhelp_basename = '%sdoc' % project
latex_documents = [
    ('index', '%s.tex' % project, u'%s Documentation' % project, copyright_holder, 'manual'),
]
man_pages = [
    ('index', project, u'%s Documentation' % project,
     [copyright_holder], 1)
]

version = pkg_resources.get_distribution("payments").version
release = version
