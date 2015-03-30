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
