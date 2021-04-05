# ---------------------------------------------------------------------------- #
# Imports
# ---------------------------------------------------------------------------- #
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from models import *
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


# ---------------------------------------------------------------------------- #
# Filters.
# ---------------------------------------------------------------------------- #
def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"

    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# --------------------------------------------------------------------------- #
# Controllers.
# ---------------------------------------------------------------------------- #
@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    """
    Get Venues data, num_shows should be aggregated based on number of upcoming shows per venue
    :return: List with information on venues
    """
    data = []
    venues = Venue.query.all()
    locations = Venue.query.distinct(Venue.city, Venue.state).all()

    for location in locations:
        query = {
          'city': location.city,
          'state': location.state,
          'venues': [],
        }

        for venue in venues:
            upcoming_shows = 0
            shows = Show.query.filter_by(venue_id=venue.id).all()

            for show in shows:
                if show.start_time > datetime.now():
                    upcoming_shows += 1

            if venue.city == query['city'] and venue.state == query['state']:
                query['venues'].append(
                    {
                      'id': venue.id,
                      'name': venue.name,
                      'num_upcoming_shows': upcoming_shows
                    })

        data.append(query)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    """
    Search on artists with partial string search. It is case-insensitive.
    Example: search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    :return: Page with the search
    """
    search_term = request.form.get('search_term', '')
    search_result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))

    response = {
        "count": search_result.count(),
        "data": search_result,
    }

    return render_template('pages/search_venues.html',
                           results=response,
                           search_term=request.form.get('search_term', '')
                           )


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    """
    Get venue data from the venues table, using venue_id
    shows the venue page with the given venue_id
    :param venue_id:
    :return:
    """
    venue = Venue.query.get(venue_id)

    data = {
        "id": venue.id,
        "name": venue.name,
        "city": venue.city,
        "state": venue.state,
        "address": venue.address,
        "phone": venue.phone,
        "image_link": venue.image_link,
        "facebook_link": venue.facebook_link,
        "website": venue.website,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "genres": venue.genres,
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
    """
    Insert form data as a new Venue record in the db
    :return:
    """
    form = VenueForm(request.form, meta={'csrf': False})

    if 'seeking_talent' not in request.form:
        check_seeking_talent = False
    else:
        check_seeking_talent = True

    try:
        venue_info = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website=form.website_link.data,
            seeking_talent=check_seeking_talent,
            seeking_description=form.seeking_description.data,
            genres=form.genres.data,
        )

        db.session.add(venue_info)
        db.session.commit()
    except:
        db.session.rollback()
        # On unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    """
    Delete a record and handle cases where the session commit could fail.
    :param venue_id:
    :return:
    """
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    """
    Get data returned from querying the database
    :return:
    """
    data = []
    artists = Artist.query.all()

    for artist in artists:
        data.append({
          "id": artist.id,
          "name": artist.name,
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    """
    Search on artists with partial string search. Ensure it is case-insensitive.
    Example: search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    :return:
    """
    search_term = request.form.get('search_term', '')
    result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))

    response = {
      "count": result.count(),
      "data": result,
    }

    return render_template('pages/search_artists.html',
                           results=response,
                           search_term=request.form.get('search_term', '')
                           )


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    """
    Get artist data from the artist table, using artist_id
    :param artist_id:
    :return: shows the artist page with the given artist_id
    """
    artist = Artist.query.get(artist_id)
    shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).all()
    upcoming_shows = []
    for show in shows:
        if show.start_time.strftime('%Y-%m-%d %H:%M:%S') > datetime.now():
            show_info = {
                'name_venue': show.venue.name,
                'img_venue': show.venue.image_link,
                'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            upcoming_shows.append(show_info)

    data = {
        "id": artist.id,
        "name": artist.name,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "genres": artist.genres,
        "image_link": artist.image_link,
        "facebook_link": artist.facebook_link,
        "website": artist.website,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "upcoming_shows": upcoming_shows,
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    """
    Populate form with fields from artist with ID <artist_id>
    :param artist_id:
    :return:
    """
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    artist = {
        "id": artist.id,
        "name": artist.name,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "genres": artist.genres,
        "image_link": artist.image_link,
        "facebook_link": artist.facebook_link,
        'website': artist.website,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
      }

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    """
    Take values from the form submitted, and update existing
    artist record with ID <artist_id> using the new attributes
    :param artist_id:
    :return:
    """
    form = ArtistForm()
    try:
        artist = Artist.query.get(artist_id)
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.website = form.website_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    """
    Populate form with values from venue with ID <venue_id>
    :param venue_id:
    :return:
    """
    form = VenueForm()
    venue = Venue.query.get(venue_id)

    venue = {
        "id": venue.id,
        "name": venue.name,
        "city": venue.city,
        "state": venue.state,
        "address": venue.address,
        "phone": venue.phone,
        "image_link": venue.image_link,
        "facebook_link": venue.facebook_link,
        "website": venue.website,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "genres": venue.genres,
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    """
    Take values from the form submitted, and update existing
    venue record with ID <venue_id> using the new attributes
    :param venue_id:
    :return:
    """
    form = VenueForm()
    try:
        venue = Venue.query.get(venue_id)
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.image_link = form.image_link.data
        venue.facebook_link = form.facebook_link.data
        venue.website = form.website_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        venue.genres = form.genres.data
        db.session.commit()
    except:
        db.session.rollback()
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
    """
    Insert form data as a new Venue record in the db
    :return:
    """
    form = ArtistForm()
    try:
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.city.data,
            phone=form.phone.data,
            genres=form.genres.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website=form.website_link.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data
          )
        db.session.add(artist)
        db.session.commit()
    except:
        db.session.rollback()
        # On unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
    """
    Displays list of shows at /shows,
    num_shows is aggregated based on number of upcoming shows per venue.
    :return:
    """
    shows = db.session.query(Show).join(Venue).join(Artist).all()
    data = []
    for show in shows:
        show_info = {
          "venue_id": show.venue_id,
          "venue_name": show.venue.name,
          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        }
        data.append(show_info)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    """
    Insert form data as a new Show record in the db
    :return:
    """
    form = ShowForm()
    try:

        show = Show(
            venue_id=form.venue_id.data,
            artist_id=form.artist_id.data,
            start_time=form.start_time.data
          )
        db.session.add(show)
        db.session.commit()
    except:
        db.session.rollback()
        # On unsuccessful db insert, flash an error instead.
        flash('An error occurred. Show could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    finally:
        db.session.close()

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


# ---------------------------------------------------------------------------- #
# Launch.
# ---------------------------------------------------------------------------- #
# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
