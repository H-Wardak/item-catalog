from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask import flash, abort, g
from flask import session as login_session
from flask import make_response
# above method convert return value into response obj that can be sent to user
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category, User
import random
import string
import httplib2  # http client lib in python
import json  # covnert in-memory py obj to serialized representation, JSON
import requests  # Apache 2 licensed HTTP lib in python, similar to urllib2
from oauth2client.client import flow_from_clientsecrets
# this methode creates flow obj from the clientssecrets JSON file
from oauth2client.client import FlowExchangeError
#  run into an error when trying to return access token

app = Flask(__name__)
# app.config['JSON_SORT_KEYS'] = False

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///categoryitems.db?check_same_thread=False')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    # Creating Anti-Forgery State Token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
        for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/')
@app.route('/categories')
def showCategories():
    cat_list = session.query(Category).all()
    latest_item = session.query(Item).order_by(desc(Item.id)).limit(10)
    return render_template('categories.html', cat_list=cat_list,
        item_list=latest_item)


@app.route('/catalog/<string:cat_name>/items')
def showCatItems(cat_name):
    cat_list = session.query(Category).all()
    cat_id = [c.id for c in cat_list if c.name == cat_name][0]
    items = session.query(Item).filter_by(cat_id=cat_id)
    items_len = items.count()
    return render_template('catItems.html', cat_list=cat_list,
        items=items, cat_name=cat_name, items_len=items_len)


@app.route('/catalog/<string:cat_name>/<string:item_title>')
def showItemInfo(cat_name, item_title):
    item = session.query(Item).filter_by(title=item_title).first()
    description = item.description
    return render_template('itemInfo.html', item_title=item_title,
        description=description, owner_id=item.user_id)


@app.route('/catalog/<string:item_title>/edit', methods=['GET', 'POST'])
def editItem(item_title):
    if 'username' not in login_session:
        return redirect('/login')

    cat_name_list = session.query(Category.name).all()
    item = session.query(Item).filter_by(title=item_title).first()

    if item.user_id != login_session['user_id']:
        flash('You are not allowed to edit somoeone else Item')
        return redirect(url_for('showCategories'))

    cat_name = cat_name_list[(item.cat_id)-1].name
    description = item.description

    if request.method == 'POST':
        item.title = request.form['title']
        item.description = request.form['description']
        newCat = request.form['cat_list']
        cat_id = [id for id in range(
            len(cat_name_list)) if newCat == cat_name_list[id].name][0]
        item.cat_id = cat_id+1
        session.add(item)
        session.commit()
        flash('Item %s Successfully modified')
        return redirect(
            url_for('showItemInfo', cat_name=newCat, item_title=item.title))
    else:
        return render_template('editItem.html', item=item,
            cat_name_list=cat_name_list, cat_name=cat_name)


@app.route('/catalog/<string:item_title>/delete', methods=['GET', 'POST'])
def deleteItem(item_title):
    if 'username' not in login_session:
        return redirect('/login')

    cat_name_list = session.query(Category.name).all()
    itemToDelete = session.query(Item).filter_by(title=item_title).first()

    if itemToDelete.user_id != login_session['user_id']:
        flash('You are not allowed to delete somoeone else Item')
        return redirect(url_for('showCategories'))

    cat_name = cat_name_list[(itemToDelete.cat_id)-1].name

    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item deleted %s Successfully')
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteItem.html',
            item_title=item_title, cat_name=cat_name)


@app.route('/categories/newItem', methods=['GET', 'POST'])
def addItem():
    if 'username' not in login_session:
        return redirect('/login')

    cat_name_list = session.query(Category.name).all()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        newCat = request.form['cat_list']
        cat_id = [id for id in range(
            len(cat_name_list)) if newCat == cat_name_list[id].name][0]
        newItem = Item(title=title, description=description,
            cat_id=cat_id+1, user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New item %s Successfully Created' % newItem.title)
        return redirect(url_for('showCategories'))
    else:
        return render_template('addItem.html', cat_name_list=cat_name_list)


@app.route('/category/newCategory', methods=['GET', 'POST'])
def addCat():
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['catNameTxtBox']
        newCat = Category(name=name)
        session.add(newCat)
        session.commit()
        flash('New Category "%s" Successfully Created' % newCat.name)
        return redirect(url_for('showCategories'))
    else:
        return render_template('addCat.html')


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token

    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']

    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    # login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
        print("New User added to DB ", login_session['username'])
        login_session['user_id'] = user_id
        flash("New User added to DB ", login_session['username'])

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    # output += '<img src="'
    # output += login_session['picture']
    # output += ' " style = "width: 300px; height: 300px;border-radius:
    # 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def createUser(login_session):
    newUser = User(username=login_session['username'],
        email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).first()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).first()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is ', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'
    % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        # del login_session['picture']
        # response = make_response(
        # json.dumps('Successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        flash("Successfully disconnected")
        return redirect('/categories')
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog.json')
def showCatItemsJSON():
    cat_list = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in cat_list])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
