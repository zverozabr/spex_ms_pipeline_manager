# MicroService Collector

## Development environment

1. Memcached

`$ docker run --name spex_memcached -p 11211:11211 -d memcached memcached -m 64`

2. Redis

clone https://code.roche.com/spex/backend into the parent directory.  
```
$ cd ./backend/micro-services/redis  
$ docker build --pull --rm -t spex_redisjson .
$ docker run -p 6379:6379 --name spex_redisjson -d spex_redisjson
```

3. ArangoDB

`$ docker run -p 8529:8529 -e ARANGO_ROOT_PASSWORD=pass --name spex_arangodb -d arangodb:3.7.7`

will be set default user/password
```
user: root
pass: pass
```

4. Copy .env.development to .env.development.local

5. Set the following variables:
```
ARANGODB_DATABASE_URL=http://localhost:8529

REDIS_HOST=localhost
REDIS_PORT=6379

MEMCACHED_HOST=127.0.0.1:11211

DATA_STORAGE=${TEMP}\\DATA_STORAGE
```

6. Run

```
$ pipenv install
$ pipenv shell
$ export MODE=development
$ python ./app.py
```
