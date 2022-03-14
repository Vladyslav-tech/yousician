import json
from typing import Optional
import unittest
from werkzeug.wrappers import Response
from bson.objectid import ObjectId
from app import db, app


class TestBase(unittest.TestCase):
    """Base test class."""

    test_song_id = "777e74484c3c579a594e04d0"

    @classmethod
    def add_test_song(cls) -> None:
        test_song = {
            "_id": ObjectId(cls.test_song_id),
            "artist": "The Yousicians",
            "difficulty": 14.6,
            "level": 13,
            "released": "2016-10-26",
            "title": "Lycanthropic Metamorphosis"
        }
        db.songs.insert_one(test_song)

    @classmethod
    def setUpClass(cls) -> None:
        cls.add_test_song()

    @classmethod
    def tearDownClass(cls) -> None:
        db.songs.delete_one({'_id': ObjectId(cls.test_song_id)})

    def setUp(self) -> None:
        app.config['TESTING'] = True
        self.client = app.test_client()


class TestSongFetch(TestBase):
    """Testing fetching songs."""

    endpoint = "/songs"
    limit = 5

    def fetch_songs_by_parameters(self,
                                  limit: Optional[int] = None,
                                  page: Optional[int] = None) -> Response:

        return self.client.get(
            self.endpoint,
            query_string={'page': page, 'limit': limit}
        )

    def test_fetching_songs(self):
        """Testing a fetching of songs."""

        response = self.client.get(self.endpoint)

        songs = json.loads(response.data)["songs"]
        links = json.loads(response.data)["links"]

        data_length = len(songs)
        song_fields = ['_id', 'artist', 'difficulty', 'level', 'released', 'title']
        links_fields = ['current_page', 'last_page', 'next_page']

        error_msg = 'Failed fetching song list.'
        self.assertEqual(response.status_code, 200, error_msg)

        error_msg = 'Default page limit incorrect.'
        self.assertEqual(data_length, 5, error_msg)

        error_msg = 'Songs fields incorrect.'
        self.assertListEqual(list(songs[3].keys()), song_fields, error_msg)

        error_msg = 'Links fields incorrect.'
        self.assertListEqual(list(links.keys()), links_fields, error_msg)
        self.assertGreaterEqual(data_length, 1)

    def test_pagination_by_limit(self):
        """Testing a fetching of songs by limit."""

        response = self.fetch_songs_by_parameters(limit=self.limit)
        data_length = len(json.loads(response.data)["songs"])

        error_msg = 'Fetching songs failed.'
        self.assertEqual(response.status_code, 200)

        error_msg = 'Incorrect number of songs in the list according to the limit'
        self.assertLessEqual(data_length, self.limit, error_msg)

    def test_pages_content(self):
        """Comparing different content on different pages."""

        page_1 = self.fetch_songs_by_parameters(page=1, limit=3)
        page_2 = self.fetch_songs_by_parameters(page=2, limit=3)

        songs_list_1 = json.loads(page_1.data)['songs']
        songs_list_2 = json.loads(page_2.data)['songs']

        error_msg = 'The same content on different pages.'
        self.assertNotEqual(songs_list_1, songs_list_2, error_msg)

    def test_test_value_error_handling(self):
        """Testing ValueError handling."""

        response = self.fetch_songs_by_parameters(
            limit='some_string',
            page='some_string',
        )
        error_msg = 'ValueError handling incorrect'
        self.assertEqual(response.status_code, 400, error_msg)


class TestSongDifficulty(TestBase):
    """Testing a fetching of songs average difficulty."""

    endpoint = "/songs/difficulty/avg"

    def get_song_difficulty(self, level: int) -> Response:
        return self.client.get(
            self.endpoint,
            query_string={'level': level}
        )

    def test_avg_difficulty_all_songs(self):
        """Testing a fetching of songs average difficulty from all songs."""

        response = self.client.get(self.endpoint)
        avg_difficulty = json.loads(response.data)

        error_msg = 'Failed fetching average songs difficulty.'
        self.assertEqual(response.status_code, 200, error_msg)
        self.assertIsInstance(avg_difficulty['average_difficulty'], float)

    def test_avg_difficulty_by_level(self):
        """Testing a fetching of songs average difficulty by level."""

        response = self.get_song_difficulty(level=9)
        error_msg = 'Failed fetching average songs difficulty.'
        self.assertEqual(response.status_code, 200, error_msg)

    def test_not_found_status(self):
        """Testing 'not found' status handling."""

        response = self.get_song_difficulty(level=0)
        error_msg = 'Handling NOT FOUND status incorrect.'
        self.assertEqual(response.status_code, 404, error_msg)

    def test_value_error_handling(self):
        """Testing ValueError handling."""

        response = self.get_song_difficulty(level='some_string')
        error_msg = 'ValueError handling incorrect.'
        self.assertEqual(response.status_code, 400, error_msg)


class TestSearchSong(TestBase):
    """Testing a searching songs by message."""

    endpoint = "/songs/search"

    def search_song(self, message: str) -> Response:
        return self.client.get(
            self.endpoint,
            query_string={'message': message}
        )

    def test_successufull_search_songs(self):
        """Testing a searching songs by message."""

        response = self.search_song(message='The Yousicians')
        error_msg = 'Failed searching song by message parameter.'
        self.assertEqual(response.status_code, 200, error_msg)

    def test_message_insensitivity(self):
        """Testing message insensitivity."""

        response = self.search_song(message='ThE YouSicIAns')
        error_msg = 'Register error.'
        self.assertEqual(response.status_code, 200, error_msg)

    def test_not_found_status(self):
        """Testing 'not found' status handling."""

        response = self.search_song(message='1')
        error_msg = 'Not found status handling failed.'
        self.assertEqual(response.status_code, 404, error_msg)

    def test_value_error_handling(self):
        """Testing ValueError handling."""

        response = self.client.get(self.endpoint)
        error_msg = 'ValueError handling failed.'
        self.assertEqual(response.status_code, 400, error_msg)


class TestPostSongRating(TestBase):
    """Testing POST song rating by song id."""

    endpoint = "/songs/rating"

    def add_rating(self, rating: int, song_id: str) -> Response:
        return self.client.post(
            self.endpoint,
            data={
                'rating': rating,
                'song_id': song_id
            }
        )

    def test_successfull_add_rating(self):
        """Testing POST song rating by song id."""

        response = self.add_rating(rating=3, song_id=self.test_song_id)
        error_msg = 'Add rating to song failed.'
        self.assertEqual(response.status_code, 201, error_msg)

        error_msg = 'Incorrect raiting added.'
        self.assertIn(3, response.json['song']['ratings'], error_msg)

    def test_required_parameters(self):
        """Testing required parameters."""

        response = self.client.post(self.endpoint)
        error_msg = 'Handling required parameters failed.'
        self.assertEqual(response.status_code, 400, error_msg)

    def test_handling_incorrect_rating(self):
        """Handling incorrect rating value."""

        response = self.add_rating(rating=10, song_id=self.test_song_id)
        error_msg = 'Handling incorrect "rating" failed.'
        self.assertEqual(response.status_code, 400, error_msg)

    def test_handling_incorrect_song_id(self):
        """Handling incorrect song id value."""

        response = self.add_rating(rating=2, song_id='1')
        error_msg = 'Handling incorrect "song_id" failed.'
        self.assertEqual(response.status_code, 400, error_msg)

    def test_not_found_status(self):
        """Testing 'not found' status handling."""

        response = self.add_rating(rating=2, song_id='722cd50d60d56d7a16698d1d')
        error_msg = 'Handling "not found" status failed.'
        self.assertEqual(response.status_code, 404, error_msg)


class TestGetSongRating(TestBase):
    """Testing GET song rating by song id."""

    endpoint = "/songs/rating"

    def add_rating(self, rating: int, song_id: str) -> Response:
        return self.client.post(
            self.endpoint,
            data={
                'rating': rating,
                'song_id': song_id
            }
        )

    def get_rating_by_song_id(self, song_id: str):
        return self.client.get(f'{self.endpoint}/{song_id}')

    def test_fetching_song_rating_by_id(self):
        """Testing GET song rating by song id."""

        self.add_rating(song_id=self.test_song_id, rating=1)
        self.add_rating(song_id=self.test_song_id, rating=3)
        self.add_rating(song_id=self.test_song_id, rating=5)

        response = self.get_rating_by_song_id(song_id=self.test_song_id)
        error_msg = 'Fetching song ratings failed.'

        self.assertEqual(response.status_code, 200, error_msg)
        self.assertEqual(response.json['average_rating'], float(3.0), error_msg)
        self.assertEqual(response.json['max_rating'], float(5.0), error_msg)
        self.assertEqual(response.json['min_rating'], float(1.0), error_msg)

    def test_handling_incorrect_song_id(self):
        """Handling incorrect song id value."""

        response = self.get_rating_by_song_id(song_id='123')
        error_msg = 'Handling incorrect "song_id" failed.'
        self.assertEqual(response.status_code, 400, error_msg)

    def test_not_found_status(self):
        """Testing 'not found' status handling."""

        response = self.get_rating_by_song_id('722cd50d60d56d7a16698d1d')
        error_msg = 'Handling "not found" status failed.'
        self.assertEqual(response.status_code, 404, error_msg)


if __name__ == "__main__":
    unittest.main()
