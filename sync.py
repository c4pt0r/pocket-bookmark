import config
import model
import time
from datetime import datetime
from pocket import Pocket 
from log import logger

from Queue import Queue
from threading import Thread

class Worker(Thread):
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception, e:
                logger.error(e)
            finally:
                self.tasks.task_done()

class ThreadPool:
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        logger.debug("add async task")
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        self.tasks.join()

pool = ThreadPool(20)

def sync_all_for_user(username, resync_all = False):
    try:
        u = model.User.get(model.User.name == username)
    except model.UserDoesNotExist:
        logger.error("no such user %s", username)
        return None

    logger.info("start fetching items for user: %s", username)
    pocket = Pocket(config.POCKET_CONSUMER_KEY)
    pocket.set_access_token(u.token)

    try:
        if resync_all == True:
            resp = pocket.get(sort = 'newest', detailType = 'simple')
        else:
            resp = pocket.get(sort = 'newest', detailType = 'simple', since =
                    time.mktime(u.last_sync.timetuple()))
    except Exception, e:
        logger.error(e)
        return None

    if len(resp['list']) == 0:
        return []

    with model.db.atomic() as txn:
        for (pocket_id, item) in resp['list'].iteritems():
            i = {}
            i['pocket_id'] = pocket_id
            i['username'] = username
            i['time_added'] = datetime.fromtimestamp(int(item['time_added']))
            i['url'] = item['given_url']
            i['title'] = item.get('resolved_title', item.get('given_title', ''))
            model.Item.insert(**i).upsert().execute()
        u.last_sync = datetime.now()
        u.save()

    logger.info("finish fetching items for user %s, updated %d items",
            username, len(resp['list']))
    return resp['list']

def check_loop():
    while True:
        for u in model.User.select(model.User.name):
            sync_all_for_user(u.name)
            time.sleep(10)

pool.add_task(check_loop)
