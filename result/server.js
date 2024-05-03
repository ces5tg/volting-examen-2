var express = require('express'),
    async = require('async'),
    { Pool } = require('pg'),
    cookieParser = require('cookie-parser'),
    app = express(),
    server = require('http').Server(app),
    io = require('socket.io')(server);

var port = process.env.PORT || 4000;

io.on('connection', function (socket) {

  socket.emit('message', { text : 'Welcome!' });

  socket.on('subscribe', function (data) {
    socket.join(data.channel);
  });
});

var pool = new Pool({
  connectionString: 'postgres://postgres:postgres@db/postgres'
});

async.retry(
  {times: 1000, interval: 1000},
  function(callback) {
    pool.connect(function(err, client, done) {
      if (err) {
        console.error("Waiting for db");
      }
      callback(err, client);
    });
  },
  function(err, client) {
    if (err) {
      return console.error("Giving up");
    }
    console.log("Connected to db");
    getVotes(client);//PERROS Y GATOS
    getRecomendaciones(client);//PERROS Y GATOS

  }
);

function getVotes(client) {
  client.query('SELECT vote, COUNT(id) AS count FROM votes GROUP BY vote', [], function(err, result) {
    if (err) {
      console.error("Error performing query: " + err);
    } else {
      var votes = collectVotesFromResult(result);
      io.sockets.emit("scores", JSON.stringify(votes));
    }

    setTimeout(function() {getVotes(client) }, 1000);
  });
}

function collectVotesFromResult(result) {
  var votes = {a: 0, b: 0};

  result.rows.forEach(function (row) {
    votes[row.vote] = parseInt(row.count);
  });

  return votes;
}
// RECOMENDACION ----------------------------
function getRecomendaciones(client) { // ERA PARA SOCKET IO 
  client.query('SELECT usuarioid, nombrelibro  , rating FROM recomendaciones order by id desc limit 5', [], function(err, result) {
    if (err) {
      console.error("Error performing query: " + err);
    } else {
      var recomendaciones = collectRecomendacionesFromResult(result);
     console.log("emitiendo un evento")
      io.sockets.emit("listaRecomendaciones", JSON.stringify(recomendaciones));
    }

    setTimeout(function() {getRecomendaciones(client) }, 1000);
  });
}

function collectRecomendacionesFromResult(result) { // era para socker io , NO FUNCIONA :()
  var listaRecomendaciones = []
  result.rows.forEach(function (row) {
    var recomendacion = {
      usuarioId:row.usuarioid , 
      nombreLibro: row.nombrelibro , 
      rating:row.rating
    }
    console.log("extrayendo datossssss")
    console.log(recomendacion)
    listaRecomendaciones.push(recomendacion)
  });

  return listaRecomendaciones;
}
// fin -------------------------
const path = require('path');

app.use(cookieParser());
app.use(express.urlencoded());
app.use(express.static(__dirname + '/views'));

app.get('/', function (req, res) {
  res.sendFile(path.resolve(__dirname + '/views/index.html'));
});

app.get('/resultados', function (req, res) {
  // extrae las ultimas 5 inserciones
  pool.query('SELECT usuarioid, nombrelibro, rating FROM recomendaciones ORDER BY id DESC LIMIT 5', (err, result) => {
    if (err) {
      console.error("error");
      res.status(500).send('error ---------');
    } else {
      res.json(result.rows);
    }
  });
});
server.listen(port, function () {
  var port = server.address().port;
  console.log('App running on port ' + port);
});
