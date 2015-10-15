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

- copy and paste the content of bookmarklet.js into the ulr field of a new bookmark
- hit the newly created bookmarklet on every page you'd like to bookmark
- create another bookmark for accessing webtag on it's default index page
