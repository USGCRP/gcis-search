#GCIS FacetView

Facet Search interface for GCIS.

## Requirements

Install ElasticSearch
* http://www.elasticsearch.org

Demo:
https://gcis-search-stage.jpl.net/search


## Installation

1. Clone repo:
  ```
  git clone https://github.com/USGCRP/gcis-search.git
  cd gcis-search
  ```

2. Create virtualenv:
  ```
  virtualenv env
  source env/bin/activate
  ```

3. Install required modules:
  ```
  pip install -r requirements.txt
  ```

4. Build gcis:
  ```
  python setup.py develop
  ```

5. Create db:
  ```
  ./manage.py createdb
  ```

6. Install GCIS ES template:
  ```
  cd scripts
  ./install_gcis_template.sh http://localhost:9200 gcis ../config/es_template-gcis.json
  ```

7. Download GCIS data:
  ```
  ./download_gcis_data.py
  ```

8. Import GCIS data:
  ```
  ./import_gcis_data.py
  ```

9. Run server:
  ```
  ./manage.py server -h 0.0.0.0
  ```

10. Access interface in browser: http://<host IP address>:5000
