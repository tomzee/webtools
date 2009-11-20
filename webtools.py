import web
import types

"""
Helpers for applications that use web.py
"""

_all__ = [
  "Unauthorized", "unauthorized", 
  "Singleton", "filterDict", "filterStorage",
  "DBHelper", "hashString",
  "application", "get", "post", "delete", "put",
  "locked", "released"
]


class Unauthorized(web.HTTPError):
    """`401 Unauthorized` error."""
    message = "unauthorized"
    def __init__(self, message=None):
        status = '401 Unauthorized'
        headers = {'Content-Type': 'text/html'}
        web.HTTPError.__init__(self, status, headers, message or self.message)
unauthorized = Unauthorized


class DBHelper(object):
    """
    Databsase helpers
    """
    @staticmethod
    def getAll(db, table, **options):
        dbObjects = list(db.select(table, **options))
        vals = []
        for o in dbObjects:
            vals.append(web.Storage(o))
        return vals
    
    @staticmethod
    def getBy(db, table, vars, **kwargs):
        where = ' AND '.join(map(lambda k: '%s=$%s' % (k, k), vars.keys()))
        return db.select(table, where=where, vars=vars,limit=1, **kwargs)[0]
    
import hashlib

def hashString(algorithm, salt, raw):
    if algorithm == 'md5':
        return hashlib.md5(salt + raw).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(salt + raw).hexdigest()
    raise Exception, 'Invalid hashing algorithm'


class Singleton(type):
    """
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/102187
    """
    def __init__(cls,name,bases,dic):
        super(Singleton,cls).__init__(name,bases,dic)
        cls.instance=None

    def __call__(cls,*args,**kw):
       if cls.instance is None:
           cls.instance=super(Singleton,cls).__call__(*args,**kw)
       return cls.instance


def filterDict(d, *vals, **kwargs):
    """
    Filters a dictionary-like object of values to either the fields you want,
    or the fields that you don't blacklist.
    If you pass in reverse (=True) the list of fields will be filtered out.
    """
    if kwargs.get('reverse', False):
        return dict((x, d[x]) for x in filter(lambda x: x not in vals, d.keys()))
    return dict((x, d[x]) for x in filter(lambda x: x in d, vals))
filterStorage = filterDict


urls = {}
class application(web.application):
    """
    Extends the web.py application in a way that allows you to specify
    your views as decorated functions.
    Kudos to my bro Duke for putting most of this together.
    """
    def __init__(self, fvars={}, autoreload=None):
        web.application.__init__(self, urls, fvars, autoreload)
    
    def handle(self):
        method = web.ctx.method
        urls[method]
        fn, args = self._match(urls[method], web.ctx.path)
        return self._delegate(fn, self.fvars, args)

    def _delegate(self, fn, fvars, args=[]):
        if fn and isinstance(fn, (types.FunctionType, type)):
            return fn(*args)
        else:
            return web.application._delegate(self, fn, fvars, args)
        
def registerView(meth, path, fun):
    path_to_funs = urls.get(meth, [])
    # only allow path in array once
    # this also allows fun to be reloaded
    if path in path_to_funs:
        path_index = path_to_funs.index(path)
        path_to_funs[path_index + 1] = fun
    else:
        path_to_funs += [path, fun]
    urls[meth] = path_to_funs

class verb:
    def __init__(self, path):
        self.path = path
    def __call__(self, *args):
        registerView(self.__class__.__name__.upper(), self.path, args[0])
                
class get(verb): pass
class post(verb): pass
class delete(verb): pass
class put(verb): pass


class locked:
    """
    #http://www.python.org/dev/peps/pep-0343/
    A template for ensuring that a lock, acquired at the start of a
    block, is released when the block is left:

   Used as follows:

    with locked(myLock):
        # Code here executes with myLock held.  The lock is
        # guaranteed to be released when the block is left (even
        # if via return or by an uncaught exception).

    """
    def __init__(self, lock):
        self.lock = lock
    def __enter__(self):
        self.lock.acquire()
    def __exit__(self, type, value, tb):
        self.lock.release()


class released:
    """
    #http://www.python.org/dev/peps/pep-0343/
    temporarily release a previously acquired lock;
    this can be written very similarly to the locked context
    manager above by swapping the acquire() and release() calls
    """
    def __init__(self, lock):
        self.lock = lock
    def __enter__(self):
        self.lock.release()
    def __exit__(self, type, value, tb):
        self.lock.acquire()