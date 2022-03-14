import json
import app


def main():
    songs = app.db.songs

    with open('songs.json') as songs_json:
        songs_list = []
        for line in songs_json:
            songs_list.append(json.loads(line))

        songs.drop()
        songs.insert_many(songs_list)


if __name__ == "__main__":
    main()
