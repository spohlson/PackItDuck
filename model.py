import config
import bcrypt
from datetime import datetime, date, timedelta

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, Text, Index

from sqlalchemy.orm import sessionmaker, scoped_session, relationship, backref

from flask.ext.login import UserMixin

engine = create_engine(config.DB_URI, echo=False)
session = scoped_session(sessionmaker(bind=engine, autocommit = False, autoflush = False))

Base = declarative_base()
Base.query = session.query_property()

### Class Declarations ####

class User(Base, UserMixin):
	__tablename__ = "users" 
	id = Column(Integer, primary_key=True)
	email = Column(String(64), nullable=False)
	username = Column(String(64), nullable=False)
	password = Column(String(64), nullable=False)
	salt = Column(String(64), nullable=False)

	def set_password(self, password):
		self.salt = bcrypt.gensalt()
		password = password.encode("utf-8")
		self.password = bcrypt.hashpw(password, self.salt)

	def authenticate(self, password):
		password = password.encode("utf-8")
		return bcrypt.hashpw(password, self.salt.encode("utf-8")) == self.password


class Trip(Base):
	__tablename__="trips"
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('users.id'))
	name = Column(String(64), nullable=False)
	destination= Column(String(100), nullable=True) # <-- Null for now
	start_date = Column(DateTime, nullable=True) #Null for now
	end_date = Column(DateTime, nullable=True) # Null for now

	user = relationship("User", backref=backref("trips", order_by=id))

	def date_range(self):
		length_of_trip = []
		current = self.start_date
		while current <= self.end_date:
			length_of_trip.append(current)
			current = current + timedelta(days=1)
		return length_of_trip[0]

class PackingList(Base):
	__tablename__="packing_lists"
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('users.id'))
	trip_id = Column(Integer, ForeignKey('trips.id'))

### Write code to auto-update user_id in Trip and PackingList ####

	user = relationship("User", backref=backref("packing_lists", order_by=id))
	trip = relationship("Trip", backref=backref("packing_lists", order_by=id))

# google sqlalchemy: auto-update for foreignkeys
# figure out why db let you add packing list to a trip that didn't exist


class PackListItems(Base):
	__tablename__="packlist_items"
	id = Column(Integer, primary_key=True)
	packing_list_id=Column(Integer, ForeignKey('packing_lists.id'))
	item_id=Column(Integer, ForeignKey('items.id'))

	packing_list = relationship("PackingList", backref=backref("packlist_items", order_by=id))
	item = relationship("Item", backref=backref("packlist_items", order_by=id))

class Item(Base):
	__tablename__="items"
	id = Column(Integer, primary_key=True)
	name = Column(String(64), nullable=False)

class ActivityItem(Base):
	__tablename__="activity_items"
	id = Column(Integer, primary_key=True)
	item_id = Column(Integer, ForeignKey('items.id'))
	activity_id = Column(Integer, ForeignKey('activities.id'))

	item = relationship("Item", backref=backref("activity_items", order_by=id))
	activity = relationship("Activity", backref=backref("activity_items", order_by=id))

class Activity(Base):
	__tablename__="activities"
	id = Column(Integer, primary_key=True)
	name = Column(String(100), nullable=False)

class TripActivity(Base):
	__tablename__="trip_activities"
	id = Column(Integer, primary_key=True)
	trip_id = Column(Integer, ForeignKey('trips.id'))
	activity_id = Column(Integer, ForeignKey('activities.id'))

	trip = relationship("Trip", backref=backref("trip_activities", order_by=id))
	activity = relationship("Activity", backref=backref("trip_activities", order_by=id))


### End of class declarations  ###


#### Creating Tables in Database ####

def create_user(email, username, password):
	new_user = User(email=email, username=username)
	new_user.set_password(password)
	session.add(new_user)
	session.commit()

def create_trip(name):
	# add destination, start_date, end_date  (DATETIME NOT WORKING!!!!)
    new_trip = Trip(name=name)
    session.add(new_trip)
    session.commit()

def create_packinglist(user_id, trip_id):
    new_packinglist = PackingList()
    session.add(new_packinglist)
    session.commit()

def create_packlist_item(packing_list_id, item_id):
    new_packlist_items = PackListItems()
    session.add(new_packlist_items)
    session.commit()

def create_trip_activity(trip_id, activity_id):
    new_trip_activity = TripActivity()
    session.add(new_trip_activity)
    session.commit()


#### End Database Configuration ####

###############################################################################


# Check if there is a user with a certain username and password:
def validate_user(username, password):
	user = session.query(User).filter_by(username=username, password=password).first()
	if user == None:
		return None
	return user.id

# Check if an email already exists:
def email_exists(email):
    user = session.query(User).filter_by(email=email).first()
    if user == None:
        return False
    return True


# Check if a username is already taken:
def username_exists(username):
    user = session.query(User).filter_by(username=username).first()
    if user == None:
        return False
    return True


####### "GET" Functions #########


## USER ##

def get_user_by_id(id):
	user = session.query(User).get(id)
	return user

def get_user_by_username(username):
	user = session.query(User).get(username)
	return user

def get_user_by_trip_id(id):
	trip = get_trip_by_id(id)
	user_id = trip.user_id
	user = get_user_by_id(user_id)
	return user


###########################

## TRIP ##

# Get a trip's attributes by trip_id 
def get_trip_by_id(id):
	trip = session.query(Trip).get(id)
	return trip

# Get a list of trip names by the user's id
def get_user_trip_names(id):
	trip = session.query(Trip).filter_by(user_id=id)
	trip_list = []
	for t in trip:
		trip_list.append(t.name)
	return trip_list

# Get's a trip's attributes by trip name
def get_trip_by_name(name):
	trip = session.query(Trip).filter_by(name=name).first()
	return trip


#####################

## PACKING_LIST ##

# Get a list of packing_list_id's by user_id:
def get_user_packlist(id):
	packlist = session.query(PackingList).filter_by(user_id=id)
	user_trips = []
	for p in packlist:
		user_trips.append(p.id)
	return user_trips

# Get a dictionary of item names for a packing list (by packing_list_id)
def get_packing_dict(id):
	item_id_list = session.query(PackListItems).filter_by(packing_list_id=id)
	packlist_items = {}
	for item in item_id_list:
		packlist_items[item.name] = 1
	return packlist_items

# Get a list of item names for a packing list by packing_list_id
# def get_packing_list(id):
# 	item_id_list = session.query(PackListItems).filter_by(packing_list_id=id)
# 	list_item_names = []
# 	item_id = item_id_list[item_id]
# 	for item in item_id_list:

# 		item_name = get_item_name_by_id(item_id)
# 		list_item_names.append(item.name)

######## ABOVE IS NOT WORKING YET!!!! #############

# Get a packing list of items by trip name
def get_pl_items_by_trip_name(name):
	trip = get_trip_by_name(name)
	packing_list = session.query(PackingList).filter_by(trip_id=trip.id)
	packlist_items = get_packing_list(packing_list_id=packing_list.id)
	return packlist_items

#####################

## ITEM ##

# Get a list of all items in DATABASE
def get_list_of_items():
	items = session.query(Item).filter_by(name=name)
	item_list = []
	for i in items:
		item_list.append(i.name)
	return item_list

# Get a dictionary of all items in DATABASE
def get_dict_of_items():
	item_dict = {}
	item_list = get_list_of_items()
	for item in item_list:
		item_dict[item] = 1
	return item_dict

# Get item name by item id
def get_item_name_by_id(id):
	item = session.query(Item).filter_by(id)
	if item.id == id:
		return item.name


#####################




######## "Pull Items" Functions #########

# Get activity by trip_id
# def get_activity_by_trip(id):
# 	a

# Get a list of item's by activity_id
# def get_items_by_activity(id):
# 	activity_ = session.query(Activity).filter_by()



def create_tables():
	Base.metadata.create_all(engine)

def main():
	pass

if __name__ == "__main__":
	main()











