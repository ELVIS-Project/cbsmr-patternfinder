# cbsmr-patterfinder

Content-based symbolic music retrieval service infrastructure.

## Basic installation instructions

### With docker-compose

Clone repo

```
git clone https://github.com/ELVIS-Project/cbsmr-patterfinder.git
cd cbsmr-patterfinder/
source conf/env.docker
make docker
docker-compose up
```


### Otherwise

Compile required libraries and install dependencies. In a new terminal window:

```
```

```
brew install go

# install postgres and start a database
brew install postgresql
launchctl load ~/Library/LaunchAgents/homebrew.mxcl.postgresql.plist

git clone https://github.com/ELVIS-Project/cbsmr-patterfinder.git
cd cbsmr-patternfinder

git submodule update --init --recursive

make --directory=smr/helsinki-ttwi
virtualenv env --python=python3
source env/bin/activate

pip install -r requirements.txt
pip install -e helsinki-ttwi/
pip install -e .

cd smr
go build
```

To run the app:
```
python3 indexer/server.py &
smr/smr &
python3 flask/app.py
```

Steps to populate the database (and actual data) will be posted soon.
