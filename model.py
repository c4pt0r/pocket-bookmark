import json
import config
from peewee import Model, CharField, DateTimeField
from peewee import SqliteDatabase, MySQLDatabase

db = None
if config.DB_TYPE == 'mysql':
    db = MySQLDatabase(config.DB_NAME,
            user = config.DB_USER,
            password = config.DB_PASSWORD,
            host = config.DB_HOST, 
            port = config.DB_PORT,
            charset='utf8mb4')

if config.DB_TYPE == 'sqlite':
    db = SqliteDatabase(config.DB_NAME)

class JsonModel(Model):
    def jsonify(self):
        r = {}
        for k in self._data.keys():
            try:
                r[k] = str(getattr(self, k))
            except:
                r[k] = json.dumps(getattr(self, k))
        return str(r)

class User(JsonModel):
    class Meta:
        database = db
    name = CharField(unique = True)
    token = CharField()

class Item(JsonModel):
    class Meta:
        database = db
    pocket_id = CharField(unique = True)
    username = CharField(index = True)
    url = CharField()
    title = CharField()
    time_added = DateTimeField()

db.create_tables([User, Item], safe = True)
