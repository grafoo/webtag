#! /usr/bin/env python2

#import psycopg2
from flask import Flask, request, render_template, redirect, g, send_from_directory
import json
import os
import sqlite3
import re


app = Flask(__name__)
app.config.from_pyfile('webtag.cfg')


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
    g.db.execute('insert into bookmarks (name, url) values (?, ?)', [name, url])
    g.db.commit()
    return g.db.execute('select last_insert_rowid()').fetchone()[0]

def insert_tag(name=''):
    g.db.execute('insert into tags (name) values (?)', (name,))
    g.db.commit()
    return g.db.execute('select last_insert_rowid()').fetchone()[0]

def get_tag_id(tag_name=''):
    tag_id = g.db.execute('select id from tags where name = ?', (tag_name,)).fetchone()
    if tag_id != None:
        return tag_id[0]
    else:
        return insert_tag(name=tag_name)

def insert_bookmark_tag(bookmark_id, tag_id):
    g.db.execute('insert into bookmark_tags (bookmark_id, tag_id) values (?, ?)', [bookmark_id, tag_id])
    g.db.commit()

def select_bookmark(name=''):
    try:
        return g.db.execute('select url from bookmarks where name = ?', (name,)).fetchone()[0]
    except:
        return 'not found'

## startup/teardown

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
        return render_template('index.html', page=request.args['url'])
    else:
        return render_template('index.html')

@app.route('/bookmark', methods=['GET', 'POST'])
def bookmark():
    if request.method == 'POST':
        bookmark_id = insert_bookmark(name=request.form['name'], url=request.form['url'])
        tags = request.form.getlist('tag-list')
        for tag in tags:
            try:
                tag_id = int(tag)
                insert_bookmark_tag(bookmark_id, tag_id)
            except ValueError:
                tag_id = get_tag_id(tag_name=tag)
                insert_bookmark_tag(bookmark_id, tag_id)
        return redirect(request.form['url'])
    else:
        return redirect(select_bookmark(name=request.args['name']))

@app.route('/tag', methods=['GET', 'POST'])
def tag():
    if request.method == 'POST':
        g.db.execute('insert into tags (name) values (?)', (request.form['name'],))
        return '{} saved'.format(request.form['name'])
    else:
        tag = request.args.get('q')
        print(tag)
        cursor = g.db.execute('select id, name from tags where name like ?', ('%' + tag + '%',))
        tags = [{'id': row[0], 'text': row[1]} for row in cursor.fetchall()]
        return json.dumps(tags)

@app.route('/search')
def search():
    query_json = request.args.get('q')
    query = json.loads(query_json)
    for item in query:
        cursor = g.db.execute('select id, name from bookmarks where name like ?', (item+'%',))
    bookmarks = [{'id': row[0], 'text': row[1]} for row in cursor.fetchall()]
    return json.dumps(bookmarks)

@app.route('/import', methods=['POST'])
def import_bookmarks():
    if request.form['file-type'] == 'Firefox':
        bookmarks_file = request.files['bookmarks-file']
    
        bookmarks_obj = json.loads(bookmarks_file.readlines()[0])

        for child in bookmarks_obj['children']:
            if child['guid'] == 'menu________':
                for bookmark in child['children']:
                    try:
                        if re.match("(^http)|(^ftp)", bookmark['uri']) != None:
                            bookmark_id = insert_bookmark(name=bookmark['title'], url=bookmark['uri'])
                            tags = bookmark['tags'].split(',')
                            for tag in tags:
                                tag_id = get_tag_id(tag_name=tag)
                                insert_bookmark_tag(bookmark_id, tag_id)
                    except KeyError, e:
                        # some children won't have a uri
                        pass


# specialities

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/x-icon'
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777)
