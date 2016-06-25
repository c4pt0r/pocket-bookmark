import config
import model
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
                print e
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

def sync_all_for_user(username, access_token):
    logger.info("start fetching items for user: %s", username)
    pocket = Pocket(config.POCKET_CONSUMER_KEY)
    pocket.set_access_token(access_token)
    resp = pocket.get(sort = 'newest', detailType = 'simple')
    # TODO use transaction
    for (pocket_id, item) in resp['list'].iteritems():
        i = {}
        i['pocket_id'] = pocket_id
        i['username'] = username
        i['time_added'] = datetime.fromtimestamp(int(item['time_added']))
        i['url'] = item['given_url']
        i['title'] = item.get('resolved_title', item.get('given_title', ''))
        model.Item.insert(**i).upsert().execute()
    logger.info("finish fetching items for user %s", username)
    return resp['list']
