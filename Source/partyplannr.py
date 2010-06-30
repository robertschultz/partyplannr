import cgi
import os
import re
import wsgiref.handlers
import captcha
import math
import uuid
import logging
import datetime
import urllib

from os import environ
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import mail
from google.appengine.api import memcache
from django.core.paginator import ObjectPaginator, InvalidPage
from google.appengine.api import images

#Set global vars here
recaptcha_public_key = "6LdkIgkAAAAAAJw7yxe01QPbnQ1FYZPFVMw4z5n8"
recaptcha_private_key = "6LdkIgkAAAAAACK4MmHhG_3hwNUa9b3uKkErr71z"

# Promotion DB model.  Used to hold each record created on the main index page.
class Promotion(db.Model):
	uniquename = db.StringProperty();
	venue = db.StringProperty();
	event = db.StringProperty();
	description = db.TextProperty();
	date = db.StringProperty();
	time = db.StringProperty();
	email = db.EmailProperty();
	private = db.BooleanProperty();
	category = db.StringProperty();
	password = db.StringProperty();
	image = db.BlobProperty();
	imageoriginal = db.BlobProperty();
	imagethumbnail = db.BlobProperty();
	timestamp = db.DateTimeProperty(auto_now_add=True);
	
# Reservation DB model.  Used to hold each persons registration that is linked to a single promotion record.
class Reservation(db.Model):
	uniquename = db.StringProperty();
	name = db.StringProperty();
	status = db.StringProperty();
	comment = db.StringProperty();
	guests = db.IntegerProperty();
	timestamp = db.DateTimeProperty(auto_now_add=True);
	
# Promotion DB model.  Used to hold each record created on the main index page.
class Category(db.Model):
	uniquename = db.StringProperty();
	parentcategory = db.StringProperty();
	name = db.StringProperty();
	description = db.StringProperty();
	
class CreateCategories(webapp.RequestHandler):
	def get(self):
		# Party
		category = Category()
		category.uniquename = "Birthday-Party"
		category.name = "Birthday Party"
		category.parentcategory = "Party"
		category.description = ""
		category.put()
		
		category = Category()
		category.uniquename = "Cocktail-Party"
		category.name = "Cocktail Party"
		category.parentcategory = "Party"
		category.description = ""
		category.put()
		
		category = Category()
		category.uniquename = "Club-Party"
		category.name = "Club Party"
		category.parentcategory = "Party"
		category.description = ""
		category.put()
		
		category = Category()
		category.uniquename = "Potluck"
		category.name = "Potluck"
		category.parentcategory = "Party"
		category.description = ""
		category.put()
		
		category = Category()
		category.uniquename = "Fraternity-Sorority-Party "
		category.name = "Fraternity/Sorority Party"
		category.parentcategory = "Party"
		category.description = ""
		category.put()
		
		# Causes
		category = Category()
		category.uniquename = "Fundraiser"
		category.name = "Fundraiser"
		category.parentcategory = "Causes"
		category.description = ""
		category.put()

		category = Category()
		category.uniquename = "Protest"
		category.name = "Protest"
		category.parentcategory = "Causes"
		category.description = ""
		category.put()
		# Education
		category = Category()
		category.uniquename = "Class"
		category.name = "Class"
		category.parentcategory = "Education"
		category.description = ""
		category.put()

		# Meetings
		category = Category()
		category.uniquename = "Club-Group-Meeting"
		category.name = "Club/Group Meeting"
		category.parentcategory = "Meetings"
		category.description = ""
		category.put()

		# Music/Arts 
		category = Category()
		category.uniquename = "Exhibit"
		category.name = "Exhibit"
		category.parentcategory = "Music-Arts"
		category.description = ""
		category.put()
		

# Handler that takes care of the processing for the RSS.
class RssHandler(webapp.RequestHandler):
	def get(self, uniquename):
		# Set the proper Content-Type in the response.
		self.response.headers['content-type']  = 'application/rss+xml'
		
		# Obtain reference to the Promotion object.  First, check Memcache for the record.
		promotion = memcache.get("promotion-" + uniquename)
		if promotion is None:
			promotion = db.GqlQuery("SELECT * FROM Promotion WHERE uniquename = :1 LIMIT 1", uniquename).get()
			# Add the record to Memcache.
			memcache.add("promotion-" + uniquename, promotion, 3600)
			# Log the Memcache reload.
			logging.info("Reloading Promotion Memcache for %s", uniquename)
		
		# Check if there exists any event by this name following the root.  If not, set the response status to 404 and show not found page.
		if (promotion == None):
			self.error(404)
		else:
			# Create header data for RSS XML.
			self.response.out.write('<?xml version=\"1.0\" ?>\n')
			self.response.out.write('<rss version=\"2.0\">\n')
			self.response.out.write('\t<channel>\n')
			self.response.out.write('\t\t<title>PartyPlannr : ' + promotion.event + '</title>\n')
			self.response.out.write('\t\t<link>http://www.partyplannr.com/</link>\n')
			self.response.out.write('\t\t<description>' + promotion.description + '</description>\n')
			
			# Obtain reference to the Promotion object.  First, check Memcache for the record.
			reservations = memcache.get("reservations-" + uniquename)
			if reservations is None:
				reservations = db.GqlQuery("SELECT * FROM Reservation WHERE uniquename = :1 ORDER BY timestamp desc", uniquename)
				# Add the record to Memcache.
				memcache.add("reservations-" + uniquename, reservations, 3600)
				# Log the Memcache reload.
				logging.info("Reloading Reservations Memcache for %s", uniquename)
				
			if (reservations != None):
				# Loop over all Reservation objects, and display each as an RSS item.
				for reservation in reservations:
					self.response.out.write('\t\t\t<item>\n')
					if (reservation.guests == 0) or (reservation.guests == None):
						self.response.out.write('\t\t\t\t<title>(' + (reservation.status == "Y" and "Yes" or "No") + ') ' + reservation.name + ' Confirmed</title>\n')
					else:
						self.response.out.write('\t\t\t\t<title>(' + (reservation.status == "Y" and "Yes" or "No") + ') ' + reservation.name + ' Confirmed +' + str(reservation.guests) + ' Guests' + '</title>\n')
					self.response.out.write('\t\t\t\t<link>http://www.partyplannr.com/' + uniquename + '</link>\n')
					self.response.out.write('\t\t\t\t<description>' + reservation.comment + '</description>\n')
					self.response.out.write('\t\t\t</item>\n') 
				
			# Create the closing data for RSS XML.
			self.response.out.write('\t</channel>\n')
			self.response.out.write('</rss>\n')
		
# Handler that takes care of the processing for the Atom.
class AtomHandler(webapp.RequestHandler):
	def get(self, uniquename):
		# Set the proper Content-Type in the response.
		self.response.headers['content-type']  = 'application/atom+xml'
		
		# Obtain reference to the Promotion object.  First, check Memcache for the record.
		promotion = memcache.get("promotion-" + uniquename)
		if promotion is None:
			promotion = db.GqlQuery("SELECT * FROM Promotion WHERE uniquename = :1 LIMIT 1", uniquename).get()
			# Add the record to Memcache.
			memcache.add("promotion-" + uniquename, promotion, 3600)
			# Log the Memcache reload.
			logging.info("Reloading Promotion Memcache for %s", uniquename)
		
		# Check if there exists any event by this name following the root.  If not, set the response status to 404 and show not found page.
		if (promotion == None):
			self.error(404)
		else:
			# Create header data for RSS XML.
			self.response.out.write('<?xml version=\"1.0\" ?>\n')
			self.response.out.write('<atom:feed xmlns:atom=\"http://www.w3.org/2005/Atom\">\n')
			
			self.response.out.write('\t<atom:id>http://partyplannr.com</atom:id>\n')
			self.response.out.write('\t<atom:title>PartyPlannr</atom:title>\n')
			self.response.out.write('\t<atom:updated>' + datetime.date.today().strftime('%Y-%m-%d') + 'T00:00:00Z</atom:updated>\n')
			self.response.out.write('\t<atom:link href=\"http://www.partyplannr.com/' + uniquename + '\" rel=\"self\"/>\n')
			
			self.response.out.write('\t<atom:author>\n')
			self.response.out.write('\t\t<atom:name>Robert Schultz</atom:name>\n')
			self.response.out.write('\t\t<atom:email>rob@partyplannr.com</atom:email>\n')
			self.response.out.write('\t</atom:author>\n')
			
			#self.response.out.write('\t<channel>\n')
			#self.response.out.write('\t\t<title>PartyPlannr: ' + promotion.event + '</title>\n')
			#self.response.out.write('\t\t<link>http://www.partyplannr.com/</link>\n')
			#self.response.out.write('\t\t<description>' + promotion.description + '</description>\n')
			
			# Obtain reference to the Promotion object.  First, check Memcache for the record.
			reservations = memcache.get("reservations-" + uniquename)
			if reservations is None:
				reservations = db.GqlQuery("SELECT * FROM Reservation WHERE uniquename = :1 ORDER BY timestamp desc", uniquename)
				# Add the record to Memcache.
				memcache.add("reservations-" + uniquename, reservations, 3600)
				# Log the Memcache reload.
				logging.info("Reloading Reservations Memcache for %s", uniquename)
				
			if (reservations != None):
				# Loop over all Reservation objects, and display each as an RSS item.
				for reservation in reservations:
					
					self.response.out.write('\t<atom:entry>\n')
					if (reservation.guests == 0) or (reservation.guests == None):
						self.response.out.write('\t\t<atom:title>(' + (reservation.status == "Y" and "Yes" or "No") + ') ' + reservation.name + ' Confirmed</atom:title>\n')
					else:
						self.response.out.write('\t\t<atom:title>(' + (reservation.status == "Y" and "Yes" or "No") + ') ' + reservation.name + ' Confirmed +' + str(reservation.guests) + ' Guests' + '</atom:title>\n')
					self.response.out.write('\t\t<atom:id>http://www.partyplannr.com/' + uniquename + '</atom:id>\n')
					self.response.out.write('\t\t<atom:updated>' + reservation.timestamp.strftime('%Y-%m-%d') + 'T00:00:00Z</atom:updated>\n')
					
					self.response.out.write('\t\t<atom:link href=\"http://www.partyplannr.com/' + uniquename + '\"/>\n')
					
					if len(reservation.comment) > 20:
						self.response.out.write('\t\t<atom:summary>' + reservation.comment[0:20] + '</atom:summary>\n')
					else:
						self.response.out.write('\t\t<atom:summary>' + reservation.comment + '</atom:summary>\n')
						
					self.response.out.write('\t\t<atom:content type=\"html\">\n')
					self.response.out.write('\t\t<![CDATA[ ' + reservation.comment + ' ]]>\n')
					self.response.out.write('\t\t</atom:content>\n')
					
					self.response.out.write('\t</atom:entry>\n')
			# Create the closing data for RSS XML.
			self.response.out.write('</atom:feed>\n')
		
# Handler that takes care of the processing for the RSS.
class SitemapHandler(webapp.RequestHandler):
	def get(self):
		# Set the proper Content-Type in the response.
		self.response.headers['content-type']  = 'text/xml'

		# Create standard Sitemap XML header.
		self.response.out.write('<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n')
		
		# Add Home page.
		self.response.out.write('\t<url>\n')
		self.response.out.write('\t\t<loc>http://www.partyplannr.com</loc>\n')
		self.response.out.write('\t\t<lastmod>' + datetime.date.today().strftime('%Y-%m-%d') + '</lastmod>\n')
		self.response.out.write('\t\t<changefreq>monthly</changefreq>\n')
		self.response.out.write('\t\t<priority>1.0</priority>\n')
		self.response.out.write('\t</url>\n')
		
		# Add About page.
		self.response.out.write('\t<url>\n')
		self.response.out.write('\t\t<loc>http://www.partyplannr.com/about</loc>\n')
		self.response.out.write('\t\t<lastmod>' + datetime.date.today().strftime('%Y-%m-%d') + '</lastmod>\n')
		self.response.out.write('\t\t<changefreq>monthly</changefreq>\n')
		self.response.out.write('\t\t<priority>0.8</priority>\n')
		self.response.out.write('\t</url>\n')
		
		# Add FAQ page.
		self.response.out.write('\t<url>\n')
		self.response.out.write('\t\t<loc>http://www.partyplannr.com/faq</loc>\n')
		self.response.out.write('\t\t<lastmod>' + datetime.date.today().strftime('%Y-%m-%d') + '</lastmod>\n')
		self.response.out.write('\t\t<changefreq>monthly</changefreq>\n')
		self.response.out.write('\t\t<priority>0.8</priority>\n')
		self.response.out.write('\t</url>\n')
		
		# Add Privacy page.
		self.response.out.write('\t<url>\n')
		self.response.out.write('\t\t<loc>http://www.partyplannr.com/privacy</loc>\n')
		self.response.out.write('\t\t<lastmod>' + datetime.date.today().strftime('%Y-%m-%d') + '</lastmod>\n')
		self.response.out.write('\t\t<changefreq>monthly</changefreq>\n')
		self.response.out.write('\t\t<priority>0.8</priority>\n')
		self.response.out.write('\t</url>\n')
		
		# Add Terms of Use page.
		self.response.out.write('\t<url>\n')
		self.response.out.write('\t\t<loc>http://www.partyplannr.com/terms</loc>\n')
		self.response.out.write('\t\t<lastmod>' + datetime.date.today().strftime('%Y-%m-%d') + '</lastmod>\n')
		self.response.out.write('\t\t<changefreq>monthly</changefreq>\n')
		self.response.out.write('\t\t<priority>0.8</priority>\n')
		self.response.out.write('\t</url>\n')
		
		for category in categories():
			# Add Terms of Use page.
			self.response.out.write('\t<url>\n')
			self.response.out.write('\t\t<loc>http://www.partyplannr.com/categories/' + category.uniquename + '</loc>\n')
			self.response.out.write('\t\t<lastmod>' + datetime.date.today().strftime('%Y-%m-%d') + '</lastmod>\n')
			self.response.out.write('\t\t<changefreq>daily</changefreq>\n')
			self.response.out.write('\t\t<priority>0.8</priority>\n')
			self.response.out.write('\t</url>\n')
		
		# Obtain reference to the Promotion objects.
		
		# Use memcache for sitemap...
		promotions = memcache.get("promotions-sitemap")
		if promotions is None:
			promotions = db.GqlQuery("SELECT * FROM Promotion WHERE private = False ORDER BY timestamp desc")
			memcache.add("promotions-sitemap", promotions, 86400)
			logging.info("Reloaded Promotions Sitemap Memcache")
		
		
		for promotion in promotions:
			self.response.out.write('\t<url>\n')
			self.response.out.write('\t\t<loc>http://www.partyplannr.com/' + promotion.uniquename.replace('&', '&amp;').replace('\'', '&apos;').replace('\"', '&quot;').replace('>', '&gt;').replace('<', '&lt;') + '</loc>\n')
			self.response.out.write('\t\t<lastmod>' + promotion.timestamp.strftime('%Y-%m-%d') + '</lastmod>\n')
			self.response.out.write('\t\t<changefreq>daily</changefreq>\n')
			self.response.out.write('\t\t<priority>0.5</priority>\n')
			self.response.out.write('\t</url>\n')
		
		self.response.out.write('</urlset>')

# Handler that takes care of the processing for the FAQ page.
class FaqHandler(webapp.RequestHandler):
	def get(self):
		template_values = {
			'categories': categories()
		}
		
		path = os.path.join(os.path.dirname(__file__), 'faq.html')
		self.response.out.write(template.render(path, template_values))	

# Handler that takes care of serving dynamic images.
class ImageHandler(webapp.RequestHandler):
	def get(self):
		# Set the proper Content-Type in the response.
		# self.response.headers['content-type']  = 'image/png'
		
		uniquename = self.request.get('id')
		type = self.request.get('type')
		
		# Obtain reference to the Promotion object.  First, check Memcache for the record.
		promotion = memcache.get("promotion-" + uniquename)
		if promotion is None:
			promotion = db.GqlQuery("SELECT * FROM Promotion WHERE uniquename = :1 LIMIT 1", uniquename).get()
			# Add the record to Memcache.
			memcache.add("promotion-" + uniquename, promotion, 3600)
			# Log the Memcache reload.
			logging.info("Reloading Promotion Memcache for %s", uniquename)
		
		# Check if there exists any event by this name following the root.  If not, set the response status to 404 and show not found page.
		if (promotion == None):
			self.error(404)
		else:
			if promotion.image:
				self.response.headers['Content-Type'] = "image/png"
				
				if type == "":
					self.response.out.write(promotion.image)
				elif type == "thumbnail":
					self.response.out.write(promotion.imagethumbnail)
				else:
					self.response.out.write(promotion.imageoriginal)
			else:
				self.error(404)
	
# Handler that takes care of the processing for the About page.
class AboutHandler(webapp.RequestHandler):
	def get(self):
		template_values = {
			'categories': categories()
		}
		
		path = os.path.join(os.path.dirname(__file__), 'about.html')
		self.response.out.write(template.render(path, template_values))	
	
# Handler that takes care of the processing for the Privacy page.
class PrivacyHandler(webapp.RequestHandler):
	def get(self):
		template_values = {
			'categories': categories()
		}
		
		path = os.path.join(os.path.dirname(__file__), 'privacy.html')
		self.response.out.write(template.render(path, template_values))

# Handler that takes care of the processing for the Terms of Use page.
class TermsHandler(webapp.RequestHandler):
	def get(self):
		template_values = {
			'categories': categories()
		}
		
		path = os.path.join(os.path.dirname(__file__), 'terms.html')
		self.response.out.write(template.render(path, template_values))
		
# Handler that takes care of the processing for the Terms of Use page.
class CategoriesHandler(webapp.RequestHandler):
	def get(self):
		# Set the template parameters to pass back to the template.
		template_values = {
			'categories': categories()
		}
	
		path = os.path.join(os.path.dirname(__file__), 'categories.html')
		self.response.out.write(template.render(path, template_values))
		
# Handler that takes care of the processing to check if an event name exists already or not.
class EventCheckHandler(webapp.RequestHandler):
	def get(self):
		# Obtain reference to the Promotion object.
		promotion = db.GqlQuery("SELECT * FROM Promotion WHERE event = :1 LIMIT 1", self.request.get('event'))
		
		if (promotion.count() == 0):
			self.response.out.write("true")
		else:
			self.response.out.write("false")
			
# Handler that takes care of the processing for the Events listing page.
class EventsHandler(webapp.RequestHandler):
	def get(self, parameter):
		# First, get the categeory parameter.
		# Then, we will want to obtain all events by this category, where Private = False and order them by the date.  Also need to do result set paging.
		
		page_maxrecs = 5
		
		page = 'events.html'
		template_values = {}
		page_number = 1
		arr = parameter.split('/') 

		if (len(arr) == 1):
			page_number = 1
			category = arr[0]
		elif (len(arr) == 2):
			category = arr[0]
			try:
				page_number = int(arr[1])
			except:
				page_number = 1
		else:
			self.error(404)
			page = 'notfound.html'
		
		category_value = category
		
		# Obtain reference to the Promotion object.
		promotions = db.GqlQuery("SELECT * FROM Promotion WHERE category = :1 AND private = False ORDER BY timestamp DESC", category)

		reccount = str(promotions.count())
		paginator = ObjectPaginator(promotions, page_maxrecs)
		promotions = promotions.fetch(page_maxrecs, offset=((page_number*page_maxrecs)-page_maxrecs))
		
		for category1 in categories():
			if category1.uniquename == category:
				category_value = category1.name
		
		# Obtain amount of Reservations + Guests for the event.
		# Obtain total pages (promotions.count()/10)
		
		if ((page_number-1) < 1):
			page_prev = 1
		else:
			page_prev = page_number-1
			
		if ((page_number+1) > paginator.pages):
			page_next = paginator.pages
		else:
			page_next = page_number+1
		
		for promotion in range(len(promotions)):
			promotions[promotion].description = promotions[promotion].description.replace('\n', '<br>')
		
		# Set the template parameters to pass back to the template.
		template_values = {
			'reccount': reccount,
			'promotions': promotions,
			'category': category,
			'category_value': category_value,
			'page_number': page_number,
			'page_count': range(1,paginator.pages+1),
			'page_prev': page_prev,
			'page_next': page_next,
			'categories': categories(),
		}
	
		path = os.path.join(os.path.dirname(__file__), page)
		self.response.out.write(template.render(path, template_values))
	def post(self):
		path = os.path.join(os.path.dirname(__file__), 'events.html')
		self.response.out.write(template.render(path, {}))
	
# Handler that takes care of the processing for the promotion view page.  This also handles inserts for reservations for an event.
class PromotionHandler(webapp.RequestHandler):
	def get(self, uniquename):
		# Obtain reference to the Promotion object.  First, check Memcache for the record.
		promotion = memcache.get("promotion-" + uniquename)
		if promotion is None:
			promotion = db.GqlQuery("SELECT * FROM Promotion WHERE uniquename = :1 LIMIT 1", uniquename).get()
			# Add the record to Memcache.
			memcache.add("promotion-" + uniquename, promotion, 3600)
			# Log the Memcache reload.
			logging.info("Reloading Promotion Memcache for %s", uniquename)
			
		# Check if there exists any event by this name following the root.  If not, set the response status to 404 and show not found page.
		if (promotion == None):
			self.error(404)
			
			path = os.path.join(os.path.dirname(__file__), 'notfound.html')
			self.response.out.write(template.render(path, {}))
		else:
			# Obtain reference to the Promotion object.  First, check Memcache for the record.
			reservations = memcache.get("reservations-" + uniquename)
			if reservations is None:
				reservations = db.GqlQuery("SELECT * FROM Reservation WHERE uniquename = :1 ORDER BY timestamp desc", uniquename)
				# Add the record to Memcache.
				memcache.add("reservations-" + uniquename, reservations, 3600)
				# Log the Memcache reload.
				logging.info("Reloading Reservations Memcache for %s", uniquename)
			
			# Check if there exists any reservations yet for the promotion.  Pass this to the template to show custom message.
			if (reservations != None):
				if (reservations.count() == 0):
					showreservations = False
				else:
					showreservations = True
			else:
				showreservations = False
			
			promotion.description = promotion.description.replace('\n', '<br>')
			
			# Set the template parameters to pass back to the template.
			template_values = {
				'promotion': promotion,
				'eventencoded': urllib.quote(promotion.event.encode("utf-8")),
				'descriptionencoded': urllib.quote(str(promotion.description.encode("utf-8"))),
				'showreservations': showreservations,
				'reservations': reservations,
				'uniquename': uniquename,
				'categories': categories(),
			}
			
			path = os.path.join(os.path.dirname(__file__), 'promotion.html')
			self.response.out.write(template.render(path, template_values))
	def post(self, uniquename):
		# Create a new Reservation object and save back to the data store.
		reservation = Reservation()
		reservation.uniquename = uniquename
		reservation.name = self.request.get('name')
		reservation.comment = self.request.get('comment')
		reservation.status = self.request.get('status')
		reservation.guests = int(self.request.get('guests'))
		reservation.put()
		
		# Obtain reference to the Promotion object.  First, check Memcache for the record.
		promotion = memcache.get("promotion-" + uniquename)
		if promotion is None:
			promotion = db.GqlQuery("SELECT * FROM Promotion WHERE uniquename = :1 LIMIT 1", uniquename).get()
			# Add the record to Memcache.
			memcache.add("promotion-" + uniquename, promotion, 3600)
			# Log the Memcache reload.
			logging.info("Reloading Promotion Memcache for %s", uniquename)
		
		# Remove Memcache record.
		memcache.delete("reservations-" + uniquename)
		# Re-query the reservation data.
		reservations = db.GqlQuery("SELECT * FROM Reservation WHERE uniquename = :1 ORDER BY timestamp desc", uniquename)
		# Add the record to Memcache.
		memcache.add("reservations-" + uniquename, reservations, 3600)
		# Log the Memcache reload.
		logging.info("Reloading Reservations Memcache for %s", uniquename)
			
		# Check if there exists any reservations yet for the promotion.  Pass this to the template to show custom message.
		if (reservations != None):
			showreservations = True
		else:
			showreservations = False
	
		# Set the template parameters to pass back to the template.
		template_values = {
			'promotion': promotion,
			'showreservations': showreservations,
			'reservations': reservations,
			'uniquename': uniquename,
			'categories': categories(),
		}
		
		path = os.path.join(os.path.dirname(__file__), 'promotion.html')
		self.response.out.write(template.render(path, template_values))

# Handler that takes care of the processing for the home page.  Also saves new Promotion record.
class HomeHandler(webapp.RequestHandler):
	def get(self):
		chtml = captcha.displayhtml(
		public_key = recaptcha_public_key,
		use_ssl = False,
		error = None)
			
		# Set the template parameters to pass back to the template.
		template_values = {
			'categories': categories(),
			'captchahtml': chtml
		}
	
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, template_values))
	def post(self):
		challenge = self.request.get('recaptcha_challenge_field')
		response  = self.request.get('recaptcha_response_field')
		remoteip  = environ['REMOTE_ADDR']
		
		cResponse = captcha.submit(
			challenge,
			response,
			recaptcha_private_key,
			remoteip)

		if cResponse.is_valid:
			success = True
		else:
			error = cResponse.error_code
			success = False

		chtml = captcha.displayhtml(
		public_key = recaptcha_public_key,
		use_ssl = False,
		error = cResponse.error_code)

		template_values = {
			'error': cResponse.error_code,
			'event': self.request.get('event'),
			'venue': self.request.get('venue'),
			'description': self.request.get('description'),
			'categories': categories(),
			'selectedcategory': self.request.get('category'),
			'eventdate': self.request.get('eventdate'),
			'eventtime': self.request.get('eventtime'),
			'email': self.request.get('email'),
			'private': self.request.get('private'),
			'captchahtml': chtml
		}

		if (success == True):
			# Create a uniqie, guid name for the event.  This fixes the problem of everyone having to have a unique event name.
			# uniquename = str(uuid.uuid4()).split("-")[0]
			uniquename = str(uuid.uuid4()).split("-")[0] + '/' + self.request.get('event').replace(' ', '-').replace('&', 'and').replace('\'', '').replace('\"', '').replace('.', '').replace("!", "").replace("@", "at").replace("*", "")
			password = str(uuid.uuid4()).split("-")[0]
		
			# Create a new Promotion record.
			promotion = Promotion()
			promotion.uniquename = uniquename
			promotion.venue = self.request.get('venue')
			promotion.event = self.request.get('event')
			promotion.description = db.Text(self.request.get('description'))
			promotion.date = self.request.get('eventdate')
			promotion.time = self.request.get('eventtime')
			promotion.email = self.request.get('email')
			promotion.category = self.request.get('category')
			promotion.password = password
	
			# Set if event is private or not.
			if not (self.request.get('private') == ''):
				promotion.private = True
			else:
				promotion.private = False
		
			image = str(self.request.get("image"))
		
			if not image is "":
				imageresized = images.resize(image, 453)
				promotion.image = db.Blob(imageresized)
				
				imagethumb = images.resize(image, 30)
				promotion.imagethumbnail = db.Blob(imagethumb)
				
				promotion.imageoriginal = db.Blob(image)

			promotion.put()

			# Create email and send to user.
			message = mail.EmailMessage(sender="PartyPlannr Support <support@partyplannr.com>",
						subject="New PartyPlannr Event Created")

			message.to = self.request.get('email')
			message.body = """
Your event has been created:
	
"%s"  
	
To view your event click the link below:
http://www.partyplannr.com/%s

Please let us know if you have any questions.

PartyPlannr
			""" % (self.request.get('event'), uniquename)

			#self.response.out.write(message.body)
		
			message.send()

			# Redirect to the new URL for the event.
			self.redirect("/%s" % uniquename, True)
		else:
			path = os.path.join(os.path.dirname(__file__), 'index.html')
			self.response.out.write(template.render(path, template_values))

# Set application, with all proper URL mappings set.
application = webapp.WSGIApplication(
	[
		('/', HomeHandler),
		('/terms', TermsHandler),
		('/privacy', PrivacyHandler),
		('/about', AboutHandler),
		('/faq', FaqHandler),
		('/sitemap', SitemapHandler),
		('/eventcheck', EventCheckHandler),
		('/categories/(.*)', EventsHandler),
		('/categories/(.*)/(.*)', EventsHandler),
		('/categories', CategoriesHandler),
		('/image', ImageHandler),
		('/createcategories', CreateCategories),
		('/(.*)/rss', RssHandler),
		('/(.*)/atom', AtomHandler),
		('/(.*)', PromotionHandler)
	],
	debug=True
)

def categories():
	# Obtain reference to the Promotion object.  First, check Memcache for the record.
	categories = memcache.get("categories")
	if categories is None:
		categories = db.GqlQuery("SELECT * FROM Category ORDER BY name")
		# Add the record to Memcache.
		memcache.add("categories", categories, 3600)
		# Log the Memcache reload.
		logging.info("Reloading Categories Memcache")
	
	return categories

def main():
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()
