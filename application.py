from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///categoryitems.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/categories')
def showCategories():
	cat_list = session.query(Category).all()
	latest_item = session.query(Item).order_by(desc(Item.id)).limit(10)
	return render_template('categories.html', cat_list = cat_list, item_list = latest_item)

@app.route('/catalog/<string:cat_name>/items')
def showCatItems(cat_name):
	cat_list = session.query(Category).all()
	cat_id = [c.id for c in cat_list if c.name == cat_name][0]
	items = session.query(Item).filter_by(cat_id = cat_id)
	items_len = items.count()
	return render_template('catItems.html', cat_list = cat_list, items = items, cat_name = cat_name, items_len = items_len)

@app.route('/catalog/<string:cat_name>/<string:item_title>')
def showItemInfo(cat_name, item_title):
	item = session.query(Item).filter_by(title = item_title).first()
	description = item.description
	return render_template('itemInfo.html', item_title = item_title, description = description)

@app.route('/catalog/<string:item_title>/edit', methods=['GET', 'POST'])
def editItem(item_title):
	cat_name_list = session.query(Category.name).all()
	item = session.query(Item).filter_by(title = item_title).first()
	cat_name = cat_name_list[(item.cat_id)-1].name
	description = item.description
	
	if request.method == 'POST':
		item.title = request.form['title']
		item.description = request.form['description']
		newCat = request.form['cat_list']
		cat_id = [id for id in range(len(cat_name_list)) if newCat == cat_name_list[id].name][0]
		item.cat_id = cat_id+1
		session.add(item)
		session.commit()
		return redirect(url_for('showItemInfo', cat_name = newCat, item_title = item.title))
	else:
		return render_template('editItem.html', item = item,
		 cat_name_list = cat_name_list, cat_name=cat_name)

@app.route('/catalog/<string:item_title>/delete', methods=['GET', 'POST'])
def deleteItem(item_title):
	cat_name_list = session.query(Category.name).all()
	itemToDelete = session.query(Item).filter_by(title = item_title).first()
	cat_name = cat_name_list[(itemToDelete.cat_id)-1].name

	if request.method == 'POST':
		session.delete(itemToDelete)
		session.commit()
		return redirect(url_for('showCategories'))
	else:
		return render_template('deleteItem.html', item_title = item_title, cat_name = cat_name)

@app.route('/categories/newItem', methods=['GET', 'POST'])
def addItem():
	cat_name_list = session.query(Category.name).all()

	if request.method == 'POST':
		title = request.form['title']
		description = request.form['description']
		newCat = request.form['cat_list']
		cat_id = [id for id in range(len(cat_name_list)) if newCat == cat_name_list[id].name][0]
		newItem = Item(title = title, description = description, cat_id = cat_id+1)
		session.add(newItem)
		session.commit()
		return redirect(url_for('showCategories'))
	else:
		return render_template('addItem.html', cat_name_list = cat_name_list)

if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)
