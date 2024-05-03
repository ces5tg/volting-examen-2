from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import logging
from vecino import recommender
option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()

app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis",  db=0, socket_timeout=5)
    return g.redis

@app.route("/", methods=['POST','GET'])
def hello():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None

    if request.method == 'POST':
        redis = get_redis()
        vote = request.form['vote']
        app.logger.info('Received vote for %s', vote)
        data = json.dumps({'voter_id': voter_id, 'vote': vote})
        redis.rpush('votes', data)

    resp = make_response(render_template(
        'index.html',
        option_a=option_a,
        option_b=option_b,
        hostname=hostname,
        vote=vote,
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp

@app.route("/formulario", methods=['POST','GET'])
def formulario():
    
    if request.method == 'POST':
        redis = get_redis()
        idUser = request.form['idUser']
        ### algoritmo
        rec = recommender(data={}, k=1, metric='pearson', n=5)  # Puedes inicializar con 
        username = idUser
        rec.loadBookDB(path='')
        recommendations = rec.recommend(username)
        print(recommendations)
        data = json.dumps({'idUser': idUser, 'recomendaciones': recommendations})
        redis.rpush('reco', data)
        print("===================================0000 xxxssssss")
        """ valores_bytes = redis.lrange('votes', 0, -1)

        # Decodificar los valores de bytes a cadenas y luego cargarlos como diccionarios JSON
        valores = [json.loads(valor.decode()) for valor in valores_bytes]

        # Imprimir los valores obtenidos
        for valor in valores:
            print(valor)

        # Cerrar la conexión con Redis
        redis.close() """
       
        #redis.rpush('votes', recommendations)

    resp = make_response(render_template(
        'formulario.html'
    ))
    return resp

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
