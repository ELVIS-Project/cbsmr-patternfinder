ROOTDIR="$( cd "$( dirname ${BASH_SOURCE[0]} )" >/dev/null 2>&1 && pwd)/../../"

set -x

source ${ROOTDIR}/conf/env.docker
export NGINX_HOST=localhost

make docker
docker-compose build
docker-compose up -d
docker-compose logs -f -t &
python3 ${ROOTDIR}/tests/integration/test_integration.py
docker-compose down

set +x
