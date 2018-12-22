from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from passlib.apps import custom_app_context as pwd_context # lib for password hashing provide several alogrithm, custom_base_context use option based on SHA256
import random, string
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32)) # to sign the token

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key = True)
	username = Column(String(32), index = True, nullable=False)
	email = Column(String(250), nullable=False)
	#gplus_id = Column(Integer, nullable = False)
	#password_hash = Column(String(64))

	#def hash_password(self, password):
	#	self.password_hash = pwd_context.hash(password)

class Item(Base):
	__tablename__ = 'item'

	id = Column(Integer, primary_key = True)
	title = Column(String(80), nullable = False)
	description = Column(String(250))
	cat_id = Column(Integer, ForeignKey('category.id'))
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		return {
			'cat_id'		: self.cat_id,
			'description'   : self.description,
		    'id'            : self.id,
		    'title'         : self.title,
		}

class Category(Base):
	__tablename__ = 'category'

	id = Column(Integer, primary_key = True)
	name = Column(String(80), nullable = False)
	item = relationship(Item)

	@property
	def serialize(self):
		return {
		    'id'     : self.id,
		    'name'   : self.name,
		    'item'	 : self.serializeItems,
		}
	
	@property
	def serializeItems(self):
		return [i.serialize for i in self.item]



engine = create_engine('sqlite:///categoryitems.db')
Base.metadata.create_all(engine)
