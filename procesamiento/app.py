from pyspark.sql import SparkSession
from pyspark.sql.functions import *


# Inicializar SparkSession
spark = SparkSession.builder \
    .appName("KafkaExample") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

# Definir las opciones de Kafka
kafka_options = {
    "kafka.bootstrap.servers": "broker:9092",  # Dirección de los brokers Kafka
    "subscribe": "topic_idUser"                      # Nombre del tema Kafka al que quieres suscribirte
}

# Leer datos de Kafka como un DataFrame de Spark Streaming
df = spark.readStream \
    .format("kafka") \
    .options(**kafka_options) \
    .load()

# Procesar los datos
query = df \
    .writeStream \
    .outputMode("append") \
    .foreachBatch(process_results) \  
    .start()

# Esperar a que el proceso de streaming finalice
query.awaitTermination()
print("Proceso de streaming finalizado.")