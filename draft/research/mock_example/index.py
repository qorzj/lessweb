from lessweb import Application
from lessweb.plugin import database
from controller import list_reply

database.init(dburi='mysql+mysqlconnector://root:pwd@localhost/db')
app = Application()
app.add_get_mapping('/reply/list', list_reply)

if __name__ == '__main__':
    app.run()