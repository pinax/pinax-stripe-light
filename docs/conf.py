import os
import sys

extensions = []
templates_path = []
source_suffix = '.rst'
master_doc = 'index'
project = u'django-stripe-payments'
copyright_holder = 'Eldarion'
copyright = u'2013, %s' % copyright_holder
exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_theme = 'default'
htmlhelp_basename = '%sdoc' % project
latex_documents = [
  ('index', '%s.tex' % project, u'%s Documentation' % project,
   copyright_holder, 'manual'),
]
man_pages = [
    ('index', project, u'%s Documentation' % project,
     [copyright_holder], 1)
]

sys.path.insert(0, os.pardir)
m = __import__('payments')

version = m.__version__
release = version
