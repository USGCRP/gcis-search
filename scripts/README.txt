Import instruments from merged CEOS-GCMD excel sheet
====================================================
ops:
        PYTHONPATH=..:$PYTHONPATH ./import_instruments.py 
dev:
        PYTHONPATH=..:$PYTHONPATH PROVES_ENV=dev ./import_instruments.py 
