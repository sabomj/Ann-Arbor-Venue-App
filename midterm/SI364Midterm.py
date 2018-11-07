###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError, IntegerField, RadioField # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required # Here, too
from flask_sqlalchemy import SQLAlchemy
import requests
import json
import foursquareapi

## App setup code
app = Flask(__name__)
app.debug = True

## All app.config values
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/saboMidterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################


client_id = foursquareapi.client_id
client_secret = foursquareapi.client_secret

##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

class Venues(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(40))
    tips = db.relationship('Tips', backref = 'venues')

    def __repr__(self):
        return "{}".format(self.name)

class Tips(db.Model):
    __tablename__ = 'tips'
    id = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.String(500))
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))

class Ratings(db.Model):
    __tablename__ = 'rating'
    id = db.Column(db.Integer, primary_key = True)
    venue_name = db.Column(db.String)
    rating = db.Column(db.Integer)

    def __repr__(self):
        return "You have rated {}, {}".format(self.name, self.rating)
###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name:",validators=[Required()])
    venues = StringField("Please enter the name of a venue (restaurant, bar, landmark, museum) in Ann Arbor that you would like to search:", validators = [Required()])
    def validate_name(form, field):
        if len(field.data.split()) < 2:
            raise ValidationError('You must enter your full name.')
    submit = SubmitField()


class RatingForm(FlaskForm):
    venue_name = StringField("Enter the name of a venue you have been to: ", validators =[Required()])
    rating = StringField('Enter a rating of this venue on a scale from 1-10 (1 being the worst and 10 being the best))', validators = [Required()])
    submit = SubmitField()
#######################
###### VIEW FXNS ######
#######################


@app.route('/', methods = ['GET','POST'])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data
        venue_name = form.venues.data
        newname = Name(name = name)
        db.session.add(newname)
        db.session.commit()
        # return redirect(url_for('all_names'))


        baseurl_search = 'https://api.foursquare.com/v2/venues/search'


        # params = params = dict(
        #     client_id='client_id',
        #     client_secret='client_secret',
        #     v='20180323',
        #     ll='40.7243,-74.0018',
        #     query='venue',
        #     limit=1
        # )

        params = {'client_id': client_id, 'client_secret': client_secret, 'query': venue_name, 'v': 20181020, 'near': 'Ann Arbor', 'limit':50}
        data = requests.get(baseurl_search, params = params)
        json_data = json.loads(data.text)
        #print(json_data)
        testing = json_data
        venuesid = json_data['response']['venues'][0]['id']
        print (venuesid)
        search = str(venuesid)


        baseurl_tips = 'https://api.foursquare.com/v2/venues/' + search + '/tips'
        tips = requests.get(baseurl_tips, params= {'client_id': client_id, 'client_secret': client_secret, 'v':20181020, 'mins': 3})
        tips_text = json.loads(tips.text)
        print (tips_text)
        print(testing)
        tips_list_text = []
        for x in tips_text['response']['tips']['items']:
            tips_list_text.append(x['text'])
        list_to_string = ' (2) '.join(tips_list_text)
        # print(list_to_string)
        # print ('********')


        venue = Venues.query.filter_by(name=venue_name).first()
        if not venue:
            venue = Venues(name=venue_name)
            db.session.add(venue)
            db.session.commit()
        tip_full = Tips.query.filter_by(text = list_to_string).first()
        new_tip = Tips(text = list_to_string,venue_id=venue.id)
        db.session.add(new_tip)
        db.session.commit()
        return redirect(url_for('all_tips'))


    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('index.html', form=form) #this is from HW3

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)

@app.route('/venues')
def all_venues():
    venues = Venues.query.all()
    return render_template('venues.html', venues = venues)

@app.route('/tips')
def all_tips():
    venue = Venues.query.all()
    tips= Tips.query.all()
    tip_list = []
    for x in venue:
        id_tips = x.id
        for y in tips:
            if id_tips == y.venue_id:
                tip_list.append((x.name,y.text))


    return render_template('all_tips.html', tips = tip_list)


@app.route('/user_ratings_form', methods = ['GET', 'POST'])
def user_rating_form():
    form = RatingForm()
    if form.validate_on_submit():
        venue_name = form.venue_name.data
        rating = form.rating.data
        venue = Venues.query.filter_by(name=venue_name).first()
        if not venue:
            venue = Venues(name=venue_name)
            db.session.add(venue)
            db.session.commit()

        user_review = Ratings(venue_name=venue.name, rating = rating)
        db.session.add(user_review)
        db.session.commit()
        flash('Rating has been added.')

    all_user_ratings = Ratings.query.all()
    return render_template('user_ratings.html', form=form, all_user_ratings = all_user_ratings)



@app.errorhandler(404)
def Error(x):
    return render_template('404.html'), 404


if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True, debug=True)
## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
