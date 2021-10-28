#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import json
from operator import countOf
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler, error
from flask_wtf import Form
from sqlalchemy.orm import backref
from wtforms import meta
from forms import *
from flask_migrate import Migrate
from datetime import date
import sys
from models import db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
#db = SQLAlchemy(app)
#db = SQLAlchemy
db.init_app(app)

# Done: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:test@localhost:5432/fyyur'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models moved to models.py
#----------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # Done: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  areas = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)
  data = []
  for area in areas:
    areas = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
    venue_data = []
    for venue in areas:
      venue_data.append({'id':venue.id, 'name':venue.name})  
    data.append({'city':area.city, 'state':area.state, 'venues':venue_data})
  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # Done: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  response = {}
  data = []
  try:
    search_term = request.form.get('search_term', '')
    results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    num_shows = len(results)

    for result in results:
      data.append({"id": result.id,"name": result.name, })
    response = {
      "count": num_shows,
      "data": data,
    }
    
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))
  
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # Done: replace with real venue data from the venues table, using venue_id

  venueshows = Show.query.filter_by(venue_id=venue_id)
  venuequery = Venue.query.get(venue_id)
  ucount = 0
  pcount = 0 
  upcoming_shows = []
  past_shows = []
  today = date.today()

  for show in venueshows:
    artist = Artist.query.get(show.artist_id)
    if show.start_time.date() <= today:
      pcount += 1
      past_shows.append({
          "venue_id": show.venue_id,
          "artist_id": show.artist_id,
          "artist_name": artist.name,
          "start_time": str(show.start_time),
          "artist_image_link": artist.image_link
        })
    else: 
      ucount += 1 
      upcoming_shows.append({
          "venue_id": show.venue_id,
          "artist_name": artist.name,
          "artist_id": show.artist_id,
          "start_time": str(show.start_time),
          "artist_image_link": artist.image_link
        })

  if venuequery:
    
    venue_details = venuequery
    data ={
      "name": venue_details.name,
      "id": venue_details.id,
      "genres": venue_details.genres,
      "city": venue_details.city,
      "state": venue_details.state,
      "address": venue_details.address,
      "phone": venue_details.phone,
      "website": venue_details.website_link,
      "facebook_link": venue_details.facebook_link,
      "seeking_talent": venue_details.seeking_talent,
      "seeking_description": venue_details.seeking_description,
      "image_link": venue_details.image_link,
      "upcoming_shows":upcoming_shows,
      "upcoming_shows_count": ucount,
      "past_shows": past_shows,
      "past_shows_count": pcount 
      }

  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  form = VenueForm(request.form)
  try:
    venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, address=form.address.data, phone=form.phone.data,
                  genres=form.genres.data, image_link=form.image_link.data, facebook_link=form.facebook_link.data,
                  website_link=form.website_link.data, seeking_talent=form.seeking_talent.data, 
                  seeking_description=form.seeking_description.data 
                  )
    # Done: Checks if venue already exists in db and flash error if it does. Do not commit to db. Allows same name with diff address.
    venueexists = Venue.query.filter_by(name=venue.name, address=venue.address).first()
    if venueexists is None:
      db.session.add(venue)
      db.session.commit()
    # Done: on successful db insert, flash success
      flash('Venue ' + form.name.data + ' was successfully listed!')
    else:
      db.session.rollback()
      #Done: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + form.name.data + ' ' + form.city.data + ' already exists.')  
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
    # Done: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
  finally:
    db.session.close()
  # on successful db insert, flash success
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.filter_by(id=venue_id).first_or_404()
        db.session.delete(venue)
        db.session.commit()
        flash('Venue was successfully deleted!')
        return render_template('pages/home.html')
    except:
        db.session.rollback()
        flash('It was not possible to delete this Venue')
    finally:
        db.session.close()
    return None
  # BONUS CHALLENGE COMPLETE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage


#  Artists
#  ----------------------------------------------------------------

# Done: replace with real data returned from querying the database

@app.route('/artists')
def artists():
  # Done: replace with real data returned from querying the database
  data=Artist.query.all()
  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  # Done: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  response = {}
  data = []
  try:
    search_term = request.form.get('search_term', '')
    results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    num_artists = len(results)

    for result in results:
      data.append({"id": result.id,"name": result.name, })
    response = {
      "count": num_artists,
      "data": data,
    }
    
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))
  
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # Done: replace with real artist data from the artist table, using artist_id

  artistshows = Show.query.filter_by(artist_id=artist_id)
  artistquery = Artist.query.get(artist_id)
  #upcoming_cnt = Show.query.filter_by(artist_id=artist_id).count()
  ucount = 0
  pcount = 0 
  upcoming_shows = []
  past_shows = []
  today = date.today()

  for show in artistshows:
    venue = Venue.query.get(show.venue_id)
    if show.start_time.date() <= today:
      pcount += 1
      past_shows.append({
          "venue_id": show.venue_id,
          "venue_name": venue.name,
          "start_time": str(show.start_time),
          "venue_image_link": venue.image_link
        })
    else: 
      ucount += 1 
      upcoming_shows.append({
          "venue_id": show.venue_id,
          "venue_name": venue.name,
          "start_time": str(show.start_time),
          "venue_image_link": venue.image_link
        })

  if artistquery:
    
    artist_details = artistquery
    data ={
      "name": artist_details.name,
      "id": artist_details.id,
      "genres": artist_details.genres,
      "city": artist_details.city,
      "state": artist_details.state,
      "phone": artist_details.phone,
      "website": artist_details.website_link,
      "facebook_link": artist_details.facebook_link,
      "seeking_venue": artist_details.seeking_venue,
      "seeking_description": artist_details.seeking_description,
      "image_link": artist_details.image_link,
      "upcoming_shows":upcoming_shows,
      "upcoming_shows_count": ucount,
      "past_shows": past_shows,
      "past_shows_count": pcount 
      }

  return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  # Done: populate form with fields from artist with ID <artist_id>
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # Done: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  form = ArtistForm(request.form)
  try:
    artist.name = form.name.data
    artist.genres = form.genres.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.website = form.website_link.data
    artist.facebook_link = form.facebook_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    artist.image_link = form.image_link.data
    db.session.commit()
    flash(f'Artist {form.name.data} was successfully edited!')
  except Exception as e:
    db.session.rollback()
    print(str(e))
    # Done: on unsuccessful db update, flash an error instead.
    flash(f'An error occurred. Artist {form.name.data} could not be updated.')
  finally:
    db.session.close() 
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # Done: populate form with values from venue with ID <venue_id>
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # Done: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  form = VenueForm(request.form)
  try:
    venue.name = form.name.data
    venue.genres = form.genres.data
    venue.address = form.address.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.website = form.website_link.data
    venue.facebook_link = form.facebook_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data
    venue.image_link = form.image_link.data
    db.session.commit()
    flash(f'Venue {form.name.data} was successfully updated!')
  except Exception as e:
    db.session.rollback()
    print(str(e))
    # Done: on unsuccessful db update, flash an error instead.
    flash(f'An error occurred. Venue {form.name.data} could not be updated.')
  finally:
    db.session.close() 
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # Done: insert form data as a new Venue record in the db, instead
  # Done: modify data to be the data object returned from db insertion
  error = False
  form = ArtistForm(request.form, meta={'csrf': False})
  #form = ArtistForm(request.form)
  if form.validate():
    try:
      artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, phone=form.phone.data,
                    genres=form.genres.data, image_link=form.image_link.data, facebook_link=form.facebook_link.data,
                    website_link=form.website_link.data, seeking_venue=form.seeking_venue.data, 
                    seeking_description=form.seeking_description.data 
                    )             
      # Done: Checks if artist already exists in db and flash error if it does. Do not commit to db.
      artistexists = Artist.query.filter_by(name=artist.name).first()
      if artistexists is None:
        db.session.add(artist)
        db.session.commit()
      # Done: on successful db insert, flash success
        flash('Artist ' + form.name.data + ' was successfully listed!')
      else:
        db.session.rollback()
        # Done: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' + form.name.data + ' already exists.')  
    except:
      db.session.rollback()
      error = True
      print(sys.exc_info())
      # Done: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    finally:
      db.session.close()
    # on successful db insert, flash success
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  else:
     message = []
     for field, err in form.errors.items():
       message.append(field + ' ' + '|'.join(err))
     flash('Errors ' + str(message))  


  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # Done: replace with real venues data.
  
  data = []

  allshows = Show.query.all()
  
  for show in allshows:
    artist = Artist.query.get(show.artist_id)
    venue = Venue.query.get(show.venue_id)

    data.append({
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": str(show.start_time)
    })
  return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # Done: insert form data as a new Show record in the db, instead
  error = False
  form = ShowForm(request.form)
  try:
    show = Show(venue_id=form.venue_id.data, artist_id=form.artist_id.data, start_time=form.start_time.data)
    db.session.add(show)
    db.session.commit()
    # Done: on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
    # Done: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
