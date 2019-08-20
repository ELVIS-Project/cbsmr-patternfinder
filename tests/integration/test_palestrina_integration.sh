ROOTDIR="$( cd "$( dirname ${BASH_SOURCE[0]} )" >/dev/null 2>&1 && pwd)/../../"

source ${ROOTDIR}/conf/env.docker
export NGINX_HOST=localhost

make docker
docker-compose build
docker-compose up -d
docker-compose logs -f -t &
python3 ${ROOTDIR}/tests/integration/test_integration.py && echo "------------ TESTS SUCCEED --------" || echo "\n\n----------------------- TESTS FAILED -------------------\n\n"
docker-compose down
