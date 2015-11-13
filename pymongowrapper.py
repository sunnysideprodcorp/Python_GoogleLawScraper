from pymongo import MongoClient

class MongoDB(object):
    """Provides a RAII wrapper for PyMongo db connections.
    Available db functions limited to those in
    ATTRIBUTES_TO_PASS. Number of simultaneous connection 
    users tracked, and db connection is closed whenever
    there are 0 users. """

    ATTRIBUTES_TO_PASS = ("update", "insert", "count")
    client = None 
    num_users = 0

    def __init__(self, db, collection):
        MongoDB.client = MongoDB.client or MongoClient()
        self.collection = MongoDB.client[db][collection]
        MongoDB.num_users += 1

    def __enter__(self, *args):
        return self

    def __exit__(self, type, value, traceback):
        MongoDB.num_users -= 1
        if MongoDB.num_users is 0:
            self.client.close()       

    def __getattr__(self, attr):
        """Any attribute specified in ATTRIBUTES_TO_PASS
        is passed on to the class variable holding the 
        db connection."""
        if attr in self.ATTRIBUTES_TO_PASS:
            return getattr(self.collection, attr)
        else:
            return getattr(self, attr)


def main():
    with MongoDB(db = "db1", collection = "c1") as m: 
        print(m.count())
        m.update({"jello":5} , {"hello":"you"}, upsert = True)
        print(m.count())
        m.insert({"joe":6})
        with MongoDB(db ='db1', collection = 'c2') as j:
            j.insert({"joe":6})
            print(j.count())


if __name__ == "__main__":
    main()
