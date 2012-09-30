import datetime
from gaesessions import SessionMiddleware
def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = SessionMiddleware(app, cookie_key=";lkjascvpoiuzxclvkjswd:LKJHLKJHPoiu;lkj32453456lkjhkjwdhfgsdfggfdse",lifetime=datetime.timedelta(365))

    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)

    # Add the following
    from gae_bingo.middleware import GAEBingoWSGIMiddleware
    app = GAEBingoWSGIMiddleware(app)

    return app
