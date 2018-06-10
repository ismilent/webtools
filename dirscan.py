#! python3
# author: smilent

import time
import uvloop
import asyncio
import aiohttp
from tqdm import tqdm
from asyncio.queues import Queue

MAX_SEMAPHORE_NUM = 200 # 最大协程数量


async def wait_with_progress(coroutines):
    for f in tqdm(asyncio.as_completed(coroutines), total=len(coroutines)):
        await f

async def fetch(session, url):
    async with session.head(url) as resopnse:
        return resopnse.status

async def run_request(cor_id, url_queue, head=True):
    try:
        print('[+] Coroutine {}: Starting'.format(cor_id))
        async with aiohttp.ClientSession(conn_timeout=10) as session:
            while True:
                url = await url_queue.get()
                if url is None:
                    url_queue.task_done()
                    break
                else:
                    code = await fetch(session, url)
                    url_queue.task_done()
                    tqdm.write('\r' + url + '\t CODE [%d]' % code)

    except Exception as e:
        print(e)
    else:
        print('[-] Coroutine {}: ending'.format(cor_id))


async def generate_url_path(queue, dir_path,  coroutins_num):
    for path in dir_path:
        await queue.put('http://localhost/%s' % path)

    print('producer: adding stop signals to the queue')
    for i in range(coroutins_num):
        await queue.put(None)

    print('producer: waiting for queue to empty')
    await queue.join()
    print('producer: ending')


async def main(loop, coroutins_num):
    url_queue = Queue(maxsize=coroutins_num)
    tasks = []
    print('[+] Generating url path...')

    with open('directory-list-lowercase-2.3-small.txt') as f:
        dir_path = [line.strip() for line in f]

    tasks = [asyncio.ensure_future(run_request(i, url_queue)) for i in range(coroutins_num)]

    tasks.append(loop.create_task(generate_url_path(url_queue, dir_path, coroutins_num)))

    await asyncio.wait(tasks)


if __name__ == '__main__':
    start_time = time.time()
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop.run_until_complete(main(loop, MAX_SEMAPHORE_NUM))
    print(time.time() - start_time)