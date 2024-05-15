using System;
using System.Data.Common;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using Newtonsoft.Json;
using Npgsql;
using StackExchange.Redis;
using Confluent.Kafka;
namespace Worker
{
    public class Program
    {
        public static int Main(string[] args)
        {
            try
            {
                var pgsql = OpenDbConnection("Server=db;Username=postgres;Password=postgres;");
                var redisConn = OpenRedisConnection("redis");
                var redis = redisConn.GetDatabase();

                // Keep alive is not implemented in Npgsql yet. This workaround was recommended:
                // https://github.com/npgsql/npgsql/issues/1214#issuecomment-235828359
                var keepAliveCommand = pgsql.CreateCommand();
                keepAliveCommand.CommandText = "SELECT 1";

                var definition = new { vote = "", voter_id = "" };
                var idUserDefinition = new { idUser = ""};


                var config = new ProducerConfig
                {
                    BootstrapServers = "broker:9092", // Dirección del servidor Kafka
                    // Otras configuraciones como seguridad, serializadores, etc., si es necesario
                };
                var kafkaProducer = new ProducerBuilder<string, string>(config).Build();

                while (true)
                {
                    // Slow down to prevent CPU spike, only query each 100ms
                    Thread.Sleep(100);

                    // Reconnect redis if down
                    if (redisConn == null || !redisConn.IsConnected) {
                        Console.WriteLine("Reconnecting Redis");
                        redisConn = OpenRedisConnection("redis");
                        redis = redisConn.GetDatabase();
                    }
                    string json = redis.ListLeftPopAsync("votes").Result;
                    
                    //string jsonReco = redis.ListLeftPopAsync("reco").Result;
                    string jsonUser= redis.ListLeftPopAsync("idUser").Result;
                    if (json != null)
                    {
                        // deserealizacion convierte un JSON  un OBJETO
                        var vote = JsonConvert.DeserializeAnonymousType(json, definition);
                        Console.WriteLine($"Processing vote for '{vote.vote}' by '{vote.voter_id}'");
                        // Reconnect DB if down
                        if (!pgsql.State.Equals(System.Data.ConnectionState.Open))
                        {
                            Console.WriteLine("Reconnecting DB");
                            pgsql = OpenDbConnection("Server=db;Username=postgres;Password=postgres;");
                        }
                        else
                        { // Normal +1 vote requested
                            UpdateVote(pgsql, vote.voter_id, vote.vote);
                        }
                    }
                    if(jsonUser !=null)
                    {
           
                        var idU = JsonConvert.DeserializeAnonymousType(jsonUser, idUserDefinition);
                        Console.WriteLine($"EL VALOR DE ID-USER ->> '{idU.idUser}'");
                        // Reconnect DB if down
                        if (!pgsql.State.Equals(System.Data.ConnectionState.Open))
                        {
                            Console.WriteLine("Reconnecting DB");
                            pgsql = OpenDbConnection("Server=db;Username=postgres;Password=postgres;");
                        }
                        else
                        { // Normal +1 vote requested
                            InsertRegistro(pgsql, idU.idUser , kafkaProducer);
                        }

                    }
                    else
                    {
                        keepAliveCommand.ExecuteNonQuery();
                    }
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine(ex.ToString());
                return 1;
            }
        }

        private static NpgsqlConnection OpenDbConnection(string connectionString)
        {
            NpgsqlConnection connection;

            while (true)
            {
                try
                {
                    connection = new NpgsqlConnection(connectionString);
                    connection.Open();
                    break;
                }
                catch (SocketException)
                {
                    Console.Error.WriteLine("Waiting for db");
                    Thread.Sleep(1000);
                }
                catch (DbException)
                {
                    Console.Error.WriteLine("Waiting for db");
                    Thread.Sleep(1000);
                }
            }

            Console.Error.WriteLine("Connected to db");

            var command = connection.CreateCommand();
            command.CommandText = @"CREATE TABLE IF NOT EXISTS votes (
                                        id VARCHAR(255) NOT NULL UNIQUE,
                                        vote VARCHAR(255) NOT NULL
                                    ) ;";
            command.CommandText = @"CREATE TABLE IF NOT EXISTS recomendaciones (
                                id SERIAL PRIMARY KEY,
                                usuarioId varchar(255) NOT NULL,
                                nombreLibro varchar(255) NOT NULL,
                                rating varchar(255) NOT NULL 
                            )";

            command.CommandText = @"CREATE TABLE IF NOT EXISTS Registro (
                            id SERIAL PRIMARY KEY,
                            usuarioId VARCHAR(255) NOT NULL,
                            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )";

            command.ExecuteNonQuery();

            return connection;
        }

        private static ConnectionMultiplexer OpenRedisConnection(string hostname)
        {
            // Use IP address to workaround https://github.com/StackExchange/StackExchange.Redis/issues/410
            var ipAddress = GetIp(hostname);
            Console.WriteLine($"Found redis at {ipAddress}");

            while (true)
            {
                try
                {
                    Console.Error.WriteLine("Connecting to redis");
                    return ConnectionMultiplexer.Connect(ipAddress);
                }
                catch (RedisConnectionException)
                {
                    Console.Error.WriteLine("Waiting for redis");
                    Thread.Sleep(1000);
                }
            }
        }

        private static string GetIp(string hostname)
            => Dns.GetHostEntryAsync(hostname)
                .Result
                .AddressList
                .First(a => a.AddressFamily == AddressFamily.InterNetwork)
                .ToString();

        private static void UpdateVote(NpgsqlConnection connection, string voterId, string vote)
        {
            var command = connection.CreateCommand();
            try
            {
                command.CommandText = "INSERT INTO votes (id, vote) VALUES (@id, @vote)";
                command.Parameters.AddWithValue("@id", voterId);
                command.Parameters.AddWithValue("@vote", vote);
                command.ExecuteNonQuery();
            }
            catch (DbException)
            {
                command.CommandText = "UPDATE votes SET vote = @vote WHERE id = @id";
                command.ExecuteNonQuery();
            }
            finally
            {
                command.Dispose();
            }
        }
        private static void UpdateRecomendacion(NpgsqlConnection connection, string usuarioId, string nombreLibro , string rating)
        {
            var command = connection.CreateCommand();
            try
            {
                command.CommandText = "SELECT COUNT(*) FROM recomendaciones WHERE usuarioId= @usuarioId  and nombreLibro =@nombreLibro";
                command.Parameters.AddWithValue("@nombreLibro", nombreLibro);// sino  ponemos esto solo se insertara un registro
                command.Parameters.AddWithValue("@usuarioId", usuarioId);
               long rowCount = (long)command.ExecuteScalar();// usamos long ya permite manipular datos   ...
                if (rowCount > 0)
                {
                    return;
                }
                else
                {
                command.CommandText = "INSERT INTO recomendaciones (usuarioId , nombreLibro , rating) VALUES ( @usuarioId , @nombreLibro , @rating)";
                command.Parameters.AddWithValue("@rating", rating);
                }
                command.ExecuteNonQuery();
            }
            catch (DbException)
            {
                Console.WriteLine("llego al catch , no se actualizara");
            }
            finally
            {
                command.Dispose();
            }
        } 

        // ID------------------USER-------------------------------------------------
        private static void InsertRegistro(NpgsqlConnection connection, string usuarioId, IProducer<string, string> kafkaProducer)
        {
            var command = connection.CreateCommand();
            try
            {
                
                command.CommandText = "INSERT INTO Registro (usuarioId) VALUES ( @usuarioId)";
                command.Parameters.AddWithValue("@usuarioId", usuarioId);
                
                command.ExecuteNonQuery();
                 // Después de insertar en la base de datos, publicar un mensaje en Kafka
                var mensaje = new Message<string, string> { Key = null, Value = usuarioId };
                var topic = "topic_idUser"; // Reemplaza esto con el nombre del tema de Kafka al que deseas enviar el mensaje
                kafkaProducer.ProduceAsync(topic, mensaje).GetAwaiter().GetResult();
                Console.WriteLine("Mensaje enviado a Kafka: " + usuarioId);
            }
            catch (DbException)
            {
                Console.WriteLine("llego al catch , no se actualizara");
            }
            finally
            {
                command.Dispose();
            }
        }
    }
}