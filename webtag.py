#! /usr/bin/env python2

from flask import (
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    Flask
)
import json
import os
import sqlite3


app = Flask(__name__)
app.config.from_pyfile('webtag.cfg')


# config

def gen_secret_key():
    with open('secret_key', 'w') as secret_key_file:
        secret_key_file.write(os.urandom(48))


def set_secret_key():
    with open('secret_key', 'r') as secret_key_file:
        app.secret_key = secret_key_file.read()


# database stuff

def get_sqlite_database():
    return sqlite3.connect(app.config['DATABASE'])


def init_database():
    if app.config['DATABASE_TYPE'] == 'sqlite':
        with open('schema_sqlite.sql', 'r') as schema:
            database = get_sqlite_database()
            database.cursor().executescript(schema.read())
            database.commit()
            database.close()


def insert_bookmark(name='', url=''):
    try:
        g.db.execute(
            'insert into bookmarks (name, url) values (?, ?)', [name, url]
        )
        g.db.commit()
    except sqlite3.IntegrityError, e:
        # in case of an existing url return the bookmark id
        # todo: replace this hack in favor of more atomic functions
        return g.db.execute('select id from bookmarks where url = ?', (url,)).fetchone()[0]
        print(e)
    return g.db.execute('select last_insert_rowid()').fetchone()[0]


def insert_tag(name=''):
    g.db.execute('insert into tags (name) values (?)', (name,))
    g.db.commit()
    return g.db.execute('select last_insert_rowid()').fetchone()[0]


def get_tag_id(tag_name=''):
    tag_id = g.db.execute(
        'select id from tags where name = ?', (tag_name,)
    ).fetchone()
    if tag_id is not None:
        return tag_id[0]
    else:
        return insert_tag(name=tag_name)


def insert_bookmark_tag(bookmark_id, tag_id):
    g.db.execute(
        'insert into bookmark_tags (bookmark_id, tag_id) values (?, ?)',
        [bookmark_id, tag_id]
    )
    g.db.commit()


def select_bookmark(name=''):
    try:
        return g.db.execute(
            'select url from bookmarks where name = ?', (name,)
        ).fetchone()[0]
    except:
        return 'not found'


def get_bookmark_record(url=''):
    try:
        bookmark_id = g.db.execute(
            'select id from bookmarks where url = ?', (url,)
        ).fetchone()[0]
        cursor = g.db.execute(
            '''select name from tags
                where id in (select tag_id from bookmark_tags where bookmark_id = ?)''',
            (bookmark_id,)
        )
        tags = [{'tag': row[0]} for row in cursor.fetchall()]
        bookmark_tuple = g.db.execute(
            'select name, url from bookmarks where url = ?',
            (url,)
        ).fetchone()
        bookmark_record = {'name': bookmark_tuple[0], 'url': bookmark_tuple[1], 'tags': tags}
        return bookmark_record
    except Exception, e:
        print(e)
        return False


def select_bookmark_tag_id(bookmark_id, tag_id):
    return g.db.execute(
        'select id from bookmark_tags where bookmark_id = ? and tag_id = ?',
        (bookmark_id, tag_id,)
    ).fetchone()


# startup/teardown

@app.before_request
def before_request():
    g.db = get_sqlite_database()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


# http routes

@app.route('/')
def index():
    if 'url' in request.args:
        bookmark_record = get_bookmark_record(url=request.args['url'])
        if bookmark_record:
            return render_template(
                'edit_bookmark.html',
                options=bookmark_record['tags'],
                items=[item['tag'] for item in bookmark_record['tags']],
                page=bookmark_record['url'],
                name=bookmark_record['name']
            )
        else:
            return render_template(
                'index.html',
                page=request.args['url'],
                name=request.args['name']
            )
    else:
        return render_template('index.html')


@app.route('/bookmark', methods=['GET', 'POST'])
def bookmark():
    if request.method == 'POST':
        bookmark_id = insert_bookmark(
            name=request.form['name'],
            url=request.form['url']
        )
        tags = request.form.getlist('tag-list')
        if not tags:
            tag_id = get_tag_id(tag_name='notag')
            insert_bookmark_tag(bookmark_id, tag_id)
        else:
            for tag in tags:
                tag_id = get_tag_id(tag)
                bookmark_tag_id = select_bookmark_tag_id(bookmark_id, tag_id)
                if bookmark_tag_id is None:
                    insert_bookmark_tag(bookmark_id, tag_id)
        return redirect(request.form['url'])
    else:
        return redirect(select_bookmark(name=request.args['name']))


@app.route('/tag', methods=['GET', 'POST'])
def tag():
    if request.method == 'POST':
        g.db.execute(
            'insert into tags (name) values (?)', (request.form['name'],)
        )
        return '{} saved'.format(request.form['name'])
    else:
        query = request.args.get('query')
        cursor = g.db.execute(
            'select name from tags where name like ?', ('%' + query + '%',)
        )
        tags = [{'tag': row[0]} for row in cursor.fetchall()]
        return json.dumps(tags)


@app.route('/search')
def search():
    query_json = request.args.get('q')
    query = json.loads(query_json)
    for item in query:
        cursor = g.db.execute(
            'select id, name from bookmarks where name like ?', (item+'%',)
        )
    bookmarks = [{'id': row[0], 'text': row[1]} for row in cursor.fetchall()]
    return json.dumps(bookmarks)


@app.route('/login')
def login():
    # todo: implement real authentication
    session['authenticated'] = True
    return render_template('index.html')


# specialities

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/x-icon'
    )


if __name__ == '__main__':
    set_secret_key()
    app.run(host='0.0.0.0', port=7777)
