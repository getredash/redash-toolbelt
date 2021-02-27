# redash-toolbelt
API client and utilities to manage a Redash instance

# testing

## included test environment

use `make redash-start` to start it

- `./redash` contains a docker-compose based test environment
- redash admin credentials:
  - user: admin
  - email: admin@example.org
  - passwd: testerpassword

## test data

- the packaged test env contains the `northwind` database https://github.com/pthom/northwind_psql