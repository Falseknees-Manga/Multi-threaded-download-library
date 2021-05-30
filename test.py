from Multi_threaded_download_library import *
from time import sleep
from threading import enumerate as thread_enumerate


#Logger
logger = Logger('test', get_level('debug'))
logger.debug('test')
logger.info('logger已加载')


header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}
proxies={
	"http": 'http://127.0.0.1:7890',
	"https": 'http://127.0.0.1:7890'
}
try:
	my_requests = requests(header, 5, False, None, 'get_error', disable_insecure_request_warning=True)
	logger.info('让我们获取一个页面看看')
	response = my_requests.get('https://falseknees.com/archive.html')
	logger.info('状态码：' + str(response.status_code))
	logger.info('让我们使用代理获取一个页面看看')
	response = my_requests.get('https://falseknees.com/archive.html', proxies=proxies)
	logger.info('状态码：' + str(response.status_code))
except:
	logger.warning('Oops，网络IO似乎出了点问题，但requests类绝对没有出bug')

def display_thread_list():
	thread_list = thread_enumerate()
	logger.info(f'当前线程列表, 共 {len(thread_list)} 个活跃线程:')
	for i in thread_list:
		logger.info(f'	- {i.getName()}')

sleep_time = 0.5

def on_thread_running(thread):
	a = 5
	b = 0
	while a > b:
		thread.check_exit()
		logger.debug(str(b))
		sleep(sleep_time)
		b+=1

def on_thread_exit(thread):
	logger.warning(f'{thread.name}已退出')

threads = start_download_thread(2, on_thread_running, on_thread_exit)
display_thread_list()
for i in threads:
	i.join()
logger.info('他们已经自己执行完成任务，关闭了！')
display_thread_list()

logger.info('让我们启动1个线程，然后强行关闭它')
threads = start_download_thread(1, on_thread_running, on_thread_exit)
display_thread_list()

sleep(1)

threads[0].raise_system_exit()
sleep(2) # 不知道为啥，sleep的线程还能免疫抛错。实际测试时，正在进行网络IO的线程可以被立即强制关闭
logger.warning('让我们来强制退出吧')
display_thread_list()

logger.warning('好耶，线程强制退出了！')
logger.info('这里有一个获取到的文件名，明显有问题，保存会出现WinError！')
file_name = 'this:is/a|file<name'
logger.info(file_name)
logger.info('来进行清理吧')
file_name = file_name_format(file_name, '_')
logger.info('好耶，输出为：' + file_name)
