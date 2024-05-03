import codecs
from math import sqrt
class recommender:

    def __init__(self, data, k=1, metric='pearson', n=5):

        self.k = k
        self.n = n
        self.username2id = {}
# username2id = {
#"toronto, ontario, canada": "278846",
#"brooklyn, new york, usa": "278847" }
        self.userid2name = {}
#userid2name = {
#"278846": "toronto, ontario, canada  (age: 23)",
#"278847": "brooklyn, new york, usa  (age: NULL)"}
        self.productid2name = {}
#productid2name = {
#    "0195153448": "Classical Mythology by Mark P. O. Morford",
#    "0002005018": "Clara Callan by Richard Bruce Wright"}

        self.metric = metric
        if self.metric == 'pearson':
            self.fn = self.pearson
        #
        # if data is dictionary set recommender data to it
        #
        if type(data).__name__ == 'dict':
            self.data = data

    def convertProductID2name(self, id): # le pasamos el Id del libro y nos retorna su nombre
        """Given product id number return product name"""
        if id in self.productid2name:
            return self.productid2name[id]
        else:
            return id # si no esta dentro del self.productid2name , entonces retornara su id


    def userRatings(self, id, n): # extrae los id(libros) y los ratings de un usuario
        """Return n top ratings for user with id"""
        print ("Ratings for " + self.userid2name[id])
        ratings = self.data[id]
        print(len(ratings))
        ratings = list(ratings.items())
        print(ratings)
        #[('0000913154', 8), ('0002157853', 0), ('0002167425', 0),
        ratings = [(self.convertProductID2name(k), v)
                   for (k, v) in ratings]
        # ratings => el metodo self.convertproductid2name reemplaza el id de libro por el NOMBRE
        #RESULTADOS ===>>>>>>>>>>>>>>[('The Way Things Work: An Illustrated Encyclopedia of Technology by C. van Amerongen (translator)', 8),
        print("====== raings lista")
        print(ratings)

        ratings.sort(key=lambda artistTuple: artistTuple[1],
                     reverse = True)
        #ordenamiento segun el rating
        ratings = ratings[:n]
        for rating in ratings:
            print("%s\t%i" % (rating[0], rating[1]))




    def loadBookDB(self, path=''):
        """loads the BX book dataset. Path is where the BX files are
        located"""
        self.data = {}
        i = 0
        #
        # First load book ratings into self.data
        #
        f = codecs.open(path + "BX-Book-Ratings.csv", 'r', 'utf8')
        for line in f:
            i += 1
            #separate line into fields
            fields = line.split(';')
            user = fields[0].strip('"')
            book = fields[1].strip('"')
            rating = int(fields[2].strip().strip('"'))
            if user in self.data:

                currentRatings = self.data[user]
                #print(currentRatings , " current ratings ---")
            else:
                currentRatings = {}
            currentRatings[book] = rating
            self.data[user] = currentRatings
        f.close()
        #data = {
        #    "36327": {
        #        "0688150349": 9,
        #        "0689710879": 8,
        #        "0689710887": 0,
        #        "0736903054": 8,
        #        "0764223259": 0
        #    }
        #}



        #"0195153448";"Classical Mythology";"Mark P. O. Morford";"2002";"Oxford University Press";"http://images.amazon.com/images/P/0195153448.01.THUMBZZZ.jpg";"http://images.amazon.com/images/P/0195153448.01.MZZZZZZZ.jpg";"http://images.amazon.com/images/P/0195153448.01.LZZZZZZZ.jpg"
        f = codecs.open(path + "BX-Books.csv", 'r', 'utf8')
        for line in f:
            i += 1
            #separate line into fields
            fields = line.split(';')
            isbn = fields[0].strip('"')
            title = fields[1].strip('"')
            author = fields[2].strip().strip('"')
            title = title + ' by ' + author
            self.productid2name[isbn] = title
        f.close()
        #productid2name = {
#    "0195153448": "Classical Mythology by Mark P. O. Morford",
#    "0002005018": "Clara Callan by Richard Bruce Wright"}

        f = codecs.open(path + "BX-Users.csv", 'r', 'utf8')
        #"278846"; "toronto, ontario, canada";"23"
        for line in f:
            i += 1
            fields = line.split(';') # SEPARA LA FILA EN UN ARRAY DE 3 VALORES
            userid = fields[0].strip('"')#"278846" , quieta comillas dobles
            location = fields[1].strip('"')#"toronto, ontario, canada"
            if len(fields) > 3:
                age = fields[2].strip().strip('"')
            else:
                age = 'NULL'
            if age != 'NULL':
                value = location + '  (age: ' + age + ')'
            else:
                value = location
            self.userid2name[userid] = value
            #userid2name = {
            #"278846": "toronto, ontario, canada  (age: 23)",
            #"278847": "brooklyn, new york, usa  (age: NULL)"}
            self.username2id[location] = userid
            # username2id = {
            #"toronto, ontario, canada": "278846",
            #"brooklyn, new york, usa": "278847",
        f.close()
        print(i)


    def pearson(self, rating1, rating2):# covarianza xy / media
        sum_xy = 0
        sum_x = 0
        sum_y = 0
        sum_x2 = 0
        sum_y2 = 0
        n = 0
        for key in rating1:
            if key in rating2:
                n += 1
                x = rating1[key]
                y = rating2[key]
                sum_xy += x * y
                sum_x += x
                sum_y += y
                sum_x2 += pow(x, 2)
                sum_y2 += pow(y, 2)
        if n == 0:
            return 0
        # now compute denominator
        denominator = (sqrt(sum_x2 - pow(sum_x, 2) / n)
                       * sqrt(sum_y2 - pow(sum_y, 2) / n))
        if denominator == 0:
            return 0
        else:
            return (sum_xy - (sum_x * sum_y) / n) / denominator


    def computeNearestNeighbor(self, username):
            #data = {
        #    "36327": {
        #        "0688150349": 9,
        #        "0689710879": 8,
        #        "0689710887": 0,
        #        "0736903054": 8,
        #        "0764223259": 0
        #    }
        #}

        distances = []
        for instance in self.data:
            if instance != username:# tiene que ser diferente al username a buscar
                distance = self.fn(self.data[username],
                                   self.data[instance])
                distances.append((instance, distance))
        distances.sort(key=lambda artistTuple: artistTuple[1],
                       reverse=True)
        return distances

    def recommend(self, user):
       recommendations = {}
       # first get list of users  ordered by nearness
       nearest = self.computeNearestNeighbor(user)
       print("nearessttttttttttttttttttt")
       print(nearest) #[('62716', 1.0000000000000058), ('8019', 1.0000000000000022), ('254417', 1.000000000000002), -> (USERNAME , VALOR PEARSON)
       userRatings = self.data[user]

       totalDistance = 0.0
       for i in range(self.k):# hemos definido el self.k como uno , por lo que tomaremos al primer vecino mas cercano
          #print(nearest[i][0])
          totalDistance += nearest[i][1] # suma las distancias con los vecinos mas cercanos , en nuestro caso el self.k es 1
       if totalDistance == 0.0:
         # si la distancia es 0 , quiere decir que no se encontraron coincidencias
          print("Warning: Total distance is zero, cannot calculate weights.")
          return []
       for i in range(self.k):
          weight = nearest[i][1] / totalDistance
          name = nearest[i][0]
          neighborRatings = self.data[name]# name -> es el id , '62716'
          print("esto es del neighborRatings")
          print(neighborRatings) #{'0380423901': 0, '0440227704': 0, '0440901588': 10, '044098761X': 10, '0440998050': 10, '0441002692': 8, '0441003583': 10, '0441006000': 10, '0671042858': 9, '0866839461': 10}
          for artist in neighborRatings:
             if not artist in userRatings:
                if artist not in recommendations:
                   recommendations[artist] = (neighborRatings[artist] * weight) # multiplica valor de RATING x PESO ()
                else: # si ya existe entonces sumara el peso al recomendations[artist]
                   recommendations[artist] = (recommendations[artist] + neighborRatings[artist] * weight)
       print("aqui vienen las recomendaciones")
       print(recommendations)
       #{'0380423901': 0.0, '0440901588': 10.0, '0441002692': 8.0, '0441003583': 10.0, '0441006000': 10.0, '0671042858': 9.0, '0866839461': 10.0}  , devuelve las recomendaciones
       recommendations = list(recommendations.items())
       recommendations = [(self.convertProductID2name(k), v)
                          for (k, v) in recommendations]
       # finally sort and return
       recommendations.sort(key=lambda artistTuple: artistTuple[1],
                            reverse = True)
       # Return the first n items
       return recommendations[:self.n]