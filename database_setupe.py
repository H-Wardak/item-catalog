from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class Category(Base):
	__tablename__ = 'category'

	id = Column(Integer, primary_key = True)
	name = Column(String(80), nullable = False)

	@property
	def serialize(self):
		return {
		    'id'     : self.id,
		    'name'   : self.name,
		}
	
class Item(Base):
	__tablename__ = 'item'

	id = Column(Integer, primary_key = True)
	title = Column(String(80), nullable = False)
	description = Column(String(250))
	cat_id = Column(Integer, ForeignKey('category.id'))
	category = relationship(Category)

	@property
	def serialize(self):
		return {
		    'id'            : self.id,
		    'title'         : self.title,
		    'description'   : self.description,
		}
	
engine = create_engine('sqlite:///categoryitems.db')
Base.metadata.create_all(engine)
