# MicroService Collector

## Development environment

1. Redis

clone spex_backend into the parent directory.  
```
$ cd ./backend/micro-services/redis  
$ docker build --pull --rm -t spex_redisjson .
$ docker run -p 6379:6379 --name spex_redisjson -d spex_redisjson
```

2. ArangoDB

`$ docker run -p 8529:8529 -e ARANGO_ROOT_PASSWORD=pass --name spex_arangodb -d arangodb:3.7.7`

will be set default user/password
```
user: root
pass: pass
```

3. Copy .env.development to .env.development.local

4. Set the following variables:
```
ARANGODB_DATABASE_URL=http://localhost:8529

REDIS_HOST=localhost
REDIS_PORT=6379

DATA_STORAGE=${TEMP}\\DATA_STORAGE
```

6. Run

```
$ pipenv install
$ pipenv shell
$ export MODE=development
$ python ./app.py
```
