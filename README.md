# facetview-prov-es
Advanced FacetView User Interface and REST Service for PROV-ES


## Install template

```
cd scripts
./install_es_template.sh http://localhost:9200 prov_es ../config/es_template-prov_es.json
```


## Install

```
cd ..
python setup.py install
```


## Run PROV-ES FacetView on port 8888

```
PROVES_ENV=prod ./manage.py server -h 0.0.0.0 -p 8888
```


## Demo

http://prov-es.jpl.nasa.gov/beta
