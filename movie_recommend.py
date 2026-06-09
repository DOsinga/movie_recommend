from projects.common import HttpResponse, Project
from django.db import connection
import json


class MovieRecommender(Project):
    def fill_dict(self, request, d):
        movie = request.GET.get('movie')
        if movie:
            d['movie'] = movie
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT image, x, y, vec, wikipedia_id "
                    "FROM movie_recommender WHERE lower(wikipedia_id) LIKE %s "
                    "ORDER BY viewcount DESC LIMIT 7",
                    (movie.lower() + '%',),
                )
                matches = list(cursor)
                if not matches:
                    d['error'] = 'Movie not found'
                    return
                image, x, y, vec, wikipedia_id = matches[0]
                if wikipedia_id.lower() != movie.lower():
                    d['top_movie'] = wikipedia_id
                    d['other_movies'] = [x[-1] for x in matches[1:]]

                movies = []
                cursor.execute(
                    "SELECT wikipedia_id, image, cube_distance(cube(vec), cube(%s)) as distance "
                    "FROM movie_recommender ORDER BY distance "
                    "LIMIT 10",
                    (vec,),
                )
                for wikipedia_id, image, distance in cursor:
                    movies.append((wikipedia_id, image, distance))
            w = 240
            h = 400
            d['movie_image'] = image
            d['movie_x'] = x - w * 1
            d['movie_y'] = y - h * 1
            d['movie_w'] = w * 3
            d['movie_h'] = h * 3
            d['movies'] = movies[1:]

    def handle_request(self, handler, request):
        if handler == 'autocomplete':
            term = request.GET.get('term', '')
            if len(term) < 3:
                return HttpResponse('[]')
            term = term.lower().strip()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT wikipedia_id "
                    "FROM movie_recommender WHERE lower(wikipedia_id) LIKE %s "
                    "ORDER BY viewcount DESC LIMIT 7",
                    (term + '%',),
                )
                matches = [{'value': wikipedia_id, 'label': wikipedia_id} for wikipedia_id in cursor]
            return HttpResponse(json.dumps(matches))
