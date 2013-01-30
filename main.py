import webapp2
import jinja2
import os
import json
import urllib2
from google.appengine.ext import db
from google.appengine.api import users

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))


	def render_json(self, d):
		json_text = json.dumps(d)
		self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
		self.write(json_text)

	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		if self.request.url.endswith('.json'):
			self.format = 'json'
		else:
			self.format = 'html'





class BusUpdates(db.Model):
	user = db.StringProperty()
	bus = db.StringProperty(required=True)
	entry = db.TextProperty()
	latitude = db.StringProperty()
	longitude = db.StringProperty()
	created = db.DateTimeProperty(auto_now_add=True)

	def as_dict(self):
		time_format = '%c'
		d = {'user' : self.user, 'bus': self.bus, 'entry': self.entry, 'lat': self.latitude, 'long': self.longitude, 'time': self.created.strftime(time_format) }
		return json.dumps(d)




federated = {
    'Google'   : 'https://www.google.com/accounts/o8/id',
    'Yahoo'    : 'http://www.yahoo.com',
    'Myspace'  : 'http://www.myspace.com',
    'AOL'      : 'http://www.aol.com',
    'MyOpenID' : 'http://www.myopenid.com'

}


new_providers = {}
for i in federated.keys():
	new_providers[i] = users.create_login_url(federated_identity=federated[i])


class ChoicePage(Handler):
	def get(self):
		user = users.get_current_user()
		logout_url = users.create_logout_url(self.request.uri)
		self.render("choicepage.html", user=user, new_providers=new_providers, logout_url=logout_url)

update_type = None

current_bus = None

class UpdatesPage(Handler):
	def render_all(self, update_type="", bus="", entry="", url="",error="", user=""):
		bus_info = BusUpdates.all().order('-created')
		
		self.render("update.html", update_type=update_type, bus=bus, entry=entry, error=error, bus_info=bus_info, url=url, user=user)
		
	update_type = None
	def get_update(self):
		riders = self.request.get("riding")
		waiters = self.request.get("waiting")
		if riders:
			self.update_type = "riding"
		if waiters:
			self.update_type = "waiting"
	

	def get(self):
		
		buses = BusUpdates.all().order('-created')
		self.get_update()
		update_type = self.update_type
		name = users.get_current_user()
		user = None
		if name:
			user = name.nickname()
		tmp = self.request.url
		posit = tmp.find('updates')
		url = tmp[0: posit+ 7] + '/'
		if self.format == 'json':
			self.render_json([b.as_dict() for b in buses])
		else:
			self.render_all(update_type=update_type, url=url, user=user)
	

	def post(self):
		# use the current_user to get status from User model
		#u = User.all()
		#person = u.filter('userid =', users.get_current_user()).order('-created')
		#for i in person.run(limit=1):
		#	status = i.update_state
		
		self.get_update()
		update_type = self.update_type
		user = 'guest'
		if users.get_current_user():
			user = users.get_current_user().nickname()

		bus = self.request.get("bus")
		entry = self.request.get("entry")
		latitude = self.request.get("latitude")
		longitude = self.request.get("longitude")

		if bus:
			b = BusUpdates(bus=bus)
			b.user = user
			b.entry = entry
			if latitude and longitude:
				b.latitude = latitude
				b.longitude = longitude
			b.put()
			current_bus = b.bus
			
		  		
			self.redirect('/updates/%s' % str(b.bus))
		
			#self.render_all(update_type=update_type)
	
		else:
			error = "We need a bus number to proceed."
			self.render_all(update_type=update_type, error=error, bus=bus, entry=entry, user=user)


class IndividualBus(Handler):
	def get(self, bus_id):
		url_u = str(self.request.url)
		length = len(url_u)
		posit = url_u.find('updates')
		bus = url_u[posit+8:]
		
		b = BusUpdates.all()
		this_bus = b.filter('bus =', bus).order('-created')
		
		if self.format == 'html':	
			if this_bus:
				self.render("individual_bus.html", bus=bus, this_bus=this_bus)
			else:
				self.write("There is a freaking error dog!")		
		else:
			self.render_json([j.as_dict() for j in this_bus])

		#bus = BusUpdates.all()
		#this_bus = bus.filter('bus')




app = webapp2.WSGIApplication([('/', ChoicePage),
			       ('/updates(?:.json)?', UpdatesPage), 
			       ('/updates/([a-zA-Z]{1}[0-9]+)(?:.json)?', IndividualBus)],
			       debug=True)












