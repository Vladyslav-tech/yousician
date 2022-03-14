# Yousician 
#### Small API to working with songs resource
_________

## Extension
- Flask
- Pymongo

_________

## Installation

Make sure you have docker installed. Installation instructions from the official documentation:
https://docs.docker.com/get-docker/

Run container with databse in background:

```sh
docker run --detach --name songs_db --publish 127.0.0.1:27017:27017 mongo:4.4
```
Install virtual environment:

```sh
cd yousician
pip3 install venv
```
Create virtual environment:

```sh
cd yousician
python3 -m venv env
```
Activate virtual environment (for MacOS and Linux):

```sh
cd yousician
source ./env/bin/activate
```
Install dependencies:

```sh
cd yousician
pip3 install -r requirements.txt
```
Fill the database with test data:

```sh
cd yousician
python3 fill_db.py
```
Run app:

```sh
cd yousician
flask run
```

To run tests use:
```sh
cd yousician
python3 tests.py
```
_________
### API description

- http://127.0.0.1:5000/songs [GET]  
Fetching all songs  
Accepts 'page' and 'limit' as a query string parameters.  
Returns songs and links  
- http://127.0.0.1:5000/songs/search [GET]  
GET a list of songs matching the search string.  
Accepts 'message' as a required query string parameter.  
Returns the data as array of objects
- http://127.0.0.1:5000/songs/rating [POST]  
Add a song rating.  
Accepts data with required fields 'rating' and 'song_id'.  
Return song object with added rating.  
- http://127.0.0.1:5000/songs/rating/{song_id} [GET]  
Return an average, lowest and highest rating of the given song by id.  
- http://127.0.0.1:5000/songs/difficulty/avg [GET]  
The result can be filtered using the 'level' parameter.  
Return an average difficulty of all songs.  