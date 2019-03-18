# cbsmr-patterfinder

Content-based symbolic music retrieval service infrastructure.

## Basic installation instructions

Clone repo and instantiate required submodules

```
git clone https://github.com/ELVIS-Project/cbsmr-patterfinder.git
cd cbsmr-patterfinder/
git submodule update --init
```

Launch docker container with database

```
cd cbsmr-patterfinder/db
docker-compose up db
```

Compile required libraries and install dependencies. In a new terminal window:

```
cd cbsmr-patterfinder/search/helsinki-ttwi/
make w-cffi
cd ..
virtualenv env --python=python3
source env/bin/activate

pip install -r requirements.txt
pip install -e helsinki-ttwi/
pip install -e .
```

To run the app:
```
FLASK_APP=flask/app.py flask run
```

Steps to populate the database (and actual data) will be posted soon.
