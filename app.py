import json

import pymongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Flask, jsonify, request, url_for, make_response


client = pymongo.MongoClient('localhost', 27017)
db = client["songs_db"]

app = Flask(__name__)


@app.route('/songs', methods=['GET'])
def get_songs_list():
    '''
    GET a list of songs.
    The results are paginated using the 'page' and 'limit' parameters.
    '''
    try:
        limit = int(request.args.get('limit', 5))
        page = int(request.args.get("page", 1))
    except ValueError:
        error_msg = 'limit and page parameter must be an integer'
        return make_response(jsonify({'error': error_msg}), 400)

    song_list = db.songs.find().sort("_id").skip(limit * (page - 1)).limit(limit)
    songs_count = db.songs.count_documents({})

    links = {
        "current_page": {"href": url_for(".get_songs_list", page=page, _external=True)},
        "last_page": {
            "href": url_for(
                ".get_songs_list", page=(songs_count // limit) + 1, _external=True
            )
        },
    }

    if page > 1:
        links["prev_page"] = {
            "href": url_for(".get_songs_list", page=page - 1, _external=True)
        }

    if page - 1 < songs_count // limit:
        links["next_page"] = {
            "href": url_for(".get_songs_list", page=page + 1, _external=True)
        }

    result = {
        'songs': [{item: song[item] for item in song} for song in song_list],
        'links': links,
    }

    result = json.loads(dumps(result))
    return jsonify(result)


@app.route('/songs/difficulty/avg', methods=['GET'])
def get_avg_difficulty():
    '''
    GET an average difficulty of all songs.
    The result can be filtered using the 'level' parameter.
    '''
    level = request.args.get('level')
    query = []

    if level is not None:
        try:
            query += [{"$match": {"level": int(level)}}]
        except ValueError:
            return make_response(
                jsonify({"error": 'level parameter must be an integer'}), 400
            )

    query += [{
                '$group': {
                    '_id': '_id',
                    'avg_difficulty': {'$avg': '$difficulty'}
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'average_difficulty': {'$round': ['$avg_difficulty', 2]}
                }
            }]

    result = dict(*db.songs.aggregate(query))

    if not result:
        return make_response(
            jsonify({"error": "No songs with choosen level"}), 404
        )

    return make_response(jsonify(result), 200)


@app.route('/songs/search', methods=['GET'])
def search_songs():
    '''
    GET a list of songs matching the search string.
    '''
    message = request.args.get('message')
    if message is None:
        return make_response(
            jsonify({"error": "'message' parameter is required"}), 400
        )

    db.songs.create_index(
        [("title", "text"), ("artist", "text")],
        name="songs_search"
    )
    result = db.songs.find({"$text": {"$search": message}})
    result = json.loads(dumps(result))

    if not result:
        return make_response(
            jsonify({"error": "Not found any song."}), 404
        )

    return make_response(jsonify(result), 200)


@app.route('/songs/rating', methods=['POST'])
def add_rating():
    '''
    POST a song rating.
    '''
    song_id = request.form.get('song_id')
    rating = request.form.get('rating')

    if song_id is None or rating is None:
        error_msg = "'song_id' and 'rating' parameter is required."
        return make_response(jsonify({"error": error_msg}), 400)

    rating = float(rating)

    if (float(rating) < 1 or float(rating) > 5):
        error_msg = "'rating' parameter must be between 1-5"
        return make_response(jsonify({"error": error_msg}), 400)

    if not ObjectId.is_valid(song_id):
        error_msg = 'Invalid song id.'
        return make_response(jsonify({'error': error_msg}), 400)

    if not db.songs.find_one({'_id': ObjectId(song_id)}):
        error_msg = "Song not found."
        return make_response(jsonify({"error": error_msg}), 404)

    db.songs.update_one(
        {'_id': ObjectId(song_id)},
        {'$push': {'ratings': rating}}
    )

    result = db.songs.find_one({'_id': ObjectId(song_id)})
    response = {
        "msg": "Ratings for the song updated",
        'song': json.loads(dumps(result))
    }
    return make_response(jsonify(response), 201)


@app.route('/songs/rating/<string:song_id>', methods=['GET'])
def get_song_rating(song_id: str):
    '''
    GET an average, lowest and highest rating of the given song by id.
    '''
    if not ObjectId.is_valid(song_id):
        return make_response(jsonify({'error': 'Invalid song id'}), 400)

    song = db.songs.find_one({'_id': ObjectId(song_id)})

    if not song:
        return make_response(jsonify({'error': 'Song not found'}), 404)
    if not song.get('ratings'):
        return make_response(
            jsonify({'error': "Song don't have rating yet."}), 404
        )

    query = [
        {'$unwind': "$ratings"},
        {
            '$group': {
                '_id': ObjectId(song_id),
                'avg_rating': {'$avg': '$ratings'},
                'min_rating': {'$min': '$ratings'},
                'max_rating': {'$max': '$ratings'}
            }
        },
        {
            '$project': {
                '_id': '$id',
                'average_rating': {'$round': ['$avg_rating', 2]},
                'min_rating': '$min_rating',
                'max_rating': '$max_rating'
            }
        },
    ]
    result = dict(*db.songs.aggregate(query))
    response = json.loads(dumps(result))

    return jsonify(response)
