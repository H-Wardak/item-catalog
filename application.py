from flask import Flask, render_template, request, redirect, jsonify, url_for, flash

app = Flask(__name__)

@app.route('/')
@app.route('/categories')
def showCategories():
	return render_template('categories.html')

@app.route('/catalog/<string:cat_name>/items')
def showCatItems(cat_name):
	item_len = 5
	return render_template('catItems.html', cat_name = cat_name, item_len = item_len)

@app.route('/catalog/<string:cat_name>/<string:item_name>')
def showItemInfo(cat_name, item_name):
	description = "this is item description"
	return render_template('itemInfo.html', item_name = item_name, description = description)

@app.route('/catalog/<string:item_name>/edit', methods=['GET', 'POST'])
def editItem(item_name):
	description = "this is item description"
	category = ['snob','hai', 'box']
	if request.method == 'POST':
		return "POst edit item"
	else:
		return render_template('editItem.html', item_name = item_name, description = description, category = category)

@app.route('/catalog/<string:item_name>/delete', methods=['GET', 'POST'])
def deleteItem(item_name):
	if request.method == 'POST':
		return "POst delete item"
	else:
		return render_template('deleteItem.html', item_name = item_name)


if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)
