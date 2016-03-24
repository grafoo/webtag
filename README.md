# webtag
browser independent bookmark store

## init
fire up python and execute following commands to initialize the db

```
>>> from webtag import init_database
>>> init_database()
```

## config

```
DEBUG = True

# database (sqlite, postgres)
DATABASE_TYPE = 'sqlite'

# postgres db config
#DATABASE_HOST = 'somehost'
#DATABASE_NAME = 'somedb'
#DATABASE_USERNAME = 'someuser'
#DATABASE_PASSWORD = '$up3r$3cr3t'

# sqlite db config
DATABASE = 'somefile'
```

# usage

- copy and paste the content of bookmarklet.js into the url field of a new bookmark
- hit the newly created bookmarklet on every page you'd like to bookmark
- create another bookmark for accessing webtag on it's default index page


# dependencies

- twitter-bootstrap 3.3.5
  - bootstrap.min.css
  - bootstrap.min.js

- jquery 2.1.4
  - jquery.min.js

- selectize.js 0.12.1 (standalone)
  - selectize.min.js
  - selectize.css


# ideas

- argon2_cffi ( https://github.com/hynek/argon2_cffi ) seems promising for userpasswords
