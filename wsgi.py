from gevent import monkey
monkey.patch_all()

from gme_shorts.app import app

if __name__ == '__main__':
    app.run()
