Install template
================

./install_es_template.sh http://localhost:5001 prov_es ../config/es_template-prov_es.json


Import prov_es from GRQ
=======================
ops:
        PYTHONPATH=..:$PYTHONPATH ./import_prov_es.py 
dev:
        PYTHONPATH=..:$PYTHONPATH PROVES_ENV=dev ./import_prov_es.py 


Import instruments from merged CEOS-GCMD excel sheet
====================================================
ops:
        PYTHONPATH=..:$PYTHONPATH ./import_instruments.py 
dev:
        PYTHONPATH=..:$PYTHONPATH PROVES_ENV=dev ./import_instruments.py 
