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

4. Create db:
  ```
  ./manage.py createdb
  ```

5. Run server:
  ```
  ./manage.py server -h 0.0.0.0
  ```

6. Access interface in browser: http://<host IP address>:5000
