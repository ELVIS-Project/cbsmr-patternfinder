ROOTDIR="$( cd "$( dirname ${BASH_SOURCE[0]} )" >/dev/null 2>&1 && pwd)/../../"

source ${ROOTDIR}/conf/env.docker
docker-compose up -d
pytest ${ROOTDIR}/tests/integration/test_palestrina_integration.py
docker-compose down
