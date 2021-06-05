from logging import getLogger, StreamHandler
from colorlog import ColoredFormatter
from os.path import isfile as os_path_isfile, join as os_path_join, exists as os_path_exists
from os import makedirs
from json import load as json_load, dump as json_dump
from threading import Thread
from re import split as re_split, sub as re_sub
from requests import get as requests_get
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from typing import Callable
from functools import wraps as functools_wraps
from inspect import signature, isclass
from ctypes import pythonapi, c_long, py_object


logger_level = {
	'critical': 50,
	'error': 40,
	'warning': 30,
	'info': 20,
	'debug': 10
}


def get_level(level_str: str) -> int:
	return logger_level[level_str]


class Logger:
	'logging模块的logger方法，和colorlog模块的ColoredFormatter类的整合类，用于日志输出'
	console_fmt = ColoredFormatter(
		'[%(asctime)s] [%(threadName)s] [%(log_color)s%(levelname)s%(reset)s]: '
		'%(message_log_color)s%(message)s%(reset)s',
		log_colors = {
			'DEBUG': 'blue',
			'INFO': 'green',
			'WARNING': 'yellow',
			'ERROR': 'red',
			'CRITICAL': 'bold_red',
		},
		secondary_log_colors = {
			'message': {
				'WARNING': 'yellow',
				'ERROR': 'red',
				'CRITICAL': 'bold_red'
			}
		},
		datefmt = '%H:%M:%S'
	)

	def __init__(self, logger_registered_name: str = 'logger', initial_level: int = 20, console_format: dict = console_fmt):
		self.logger = getLogger(logger_registered_name)
		self.logger.setLevel(initial_level)

		self.ch = StreamHandler()
		self.ch.setLevel(initial_level)
		self.ch.setFormatter(console_format)
		self.logger.addHandler(self.ch)

		self.debug = self.logger.debug
		self.info = self.logger.info
		self.warning = self.logger.warning
		self.error = self.logger.error
		self.critical = self.logger.critical
		self.exception = self.logger.exception

	def set_level(self, level: int):
		self.logger.setLevel(level)
		self.ch.setLevel(level)

	def get_logger_object(self):
		return self.logger


class Json(dict):
	'整合的json加载/保存类，继承dict类，可直接作为字典使用'
	def __init__(self, file, default_json: dict = None, folder = None):
		if folder is None:
			self.path = file
		else:
			if not os_path_exists(folder):
				makedirs(folder)
			self.path = os_path_join(folder, file)
		if os_path_isfile(self.path):
			with open(self.path, encoding='utf-8') as f:
				super().__init__(json_load(f))
		else:
			super().__init__()
			if default_json is not None:
				self.update(default_json)
			self.save()

	def save(self, use_indent: bool = True):
		with open(self.path, 'w', encoding='utf-8') as f:
			if use_indent:
				json_dump(self.copy(), f, indent=2, ensure_ascii=False)
			else:
				json_dump(self.copy(), f, separators=(',', ':'), ensure_ascii=False)


class requests:
	def __init__(self, initial_header: dict = {}, times_limit: int = 1, verify: bool = True, proxies: dict = None, disable_insecure_request_warning: bool = False, return_all_error: bool = False):
		self.header = initial_header
		self.times_limit = times_limit
		self.verify = verify
		self.proxies = proxies
		self.return_all_error = return_all_error
		if disable_insecure_request_warning:
			disable_warnings(InsecureRequestWarning)

	def get(self, link, additional_header: dict = None, times_limit: int = None, verify: bool = None, proxies: dict = None, return_all_error: bool = None):
		times_limit = self.times_limit if times_limit is None else times_limit
		verify = self.verify if verify is None else verify
		proxies = self.proxies if proxies is None else proxies
		return_all_error = self.return_all_error if return_all_error is None else return_all_error
		try_times = 0
		error_list = []
		while try_times < times_limit:
			try:
				if additional_header is not None:
					requests_header = self.header
					requests_header.update(additional_header)
				else:
					requests_header = self.header
				if proxies is not None:
					response = requests_get(link, headers=requests_header, verify=verify, proxies=proxies)
				else:
					response = requests_get(link, headers=requests_header, verify=verify)
				response.raise_for_status()
			except Exception as e:
				if return_all_error:
					error_list.append(e)
				else:
					error = e
				try_times+=1
			else:
				return response
		return error_list if return_all_error else error


class download_thread(Thread):
	def __init__(self, function_used: Callable, threadID, on_thread_exit: Callable):
		Thread.__init__(self)
		self.setDaemon(True)
		self.threadID = threadID
		self.setName('download-thread-' + str(self.threadID))
		self.function = function_used
		self.on_thread_exit = on_thread_exit
		self.thread_exit = False

	def run(self):
		try:
			self.function(self)
		except Exception:
			pass
		self._exit()

	def check_exit(self):
		if self.thread_exit:
			self._exit()

	def _exit(self):
		self.on_thread_exit(self)
		exit()

	def stop(self):
		self.thread_exit = True

	def raise_system_exit(self):
		_async_raise(self.ident, SystemExit)


class Console(Thread):
	'独立线程的控制台'
	def __init__(self, cmd_parser: Callable):
		super().__init__(name='Console')
		self.cmd = []
		self.setName('Console')
		self.cmd_parser = cmd_parser

	def run(self):
		while True:
			try:
				raw_input = input()
				if raw_input == '':
					continue
				cmd_list = re_split(r'\s+', raw_input)
				self.cmd = [i for i in cmd_list if i != '']
				self.cmd_parser(self.cmd)
			except EOFError or KeyboardInterrupt:
				exit()


def new_thread(thread_name: str or Callable = None):
	def wrapper(func):
		@functools_wraps(func)
		def wrap(*args, **kwargs):
			thread = Thread(target=func, args=args, kwargs=kwargs, name=thread_name)
			thread.setDaemon(True)
			thread.start()
			return thread
		wrap.__signature__ = signature(func)
		return wrap
	if isinstance(thread_name, Callable):
		this_is_a_function = thread_name
		thread_name = None
		return wrapper(this_is_a_function)
	return wrapper


def file_name_format(name: str, change_to: str):
	name = str.replace(name, '\\', '/')
	return re_sub('[*:"?<>/|]', change_to, name)


def start_download_thread(number_of_thread, function_used: Callable, on_thread_exit: Callable) -> list:
	download_thread_list = []
	for i in range(1, number_of_thread + 1):
		download_thread_list.append(download_thread(function_used, i, on_thread_exit))
		download_thread_list[i - 1].start()
	return download_thread_list


def _async_raise(tid, exctype):
	'在线程中抛出异常使线程强制关闭'
	if not isclass(exctype):
		raise TypeError("Only types can be raised (not instances)")
	res = pythonapi.PyThreadState_SetAsyncExc(c_long(tid), py_object(exctype))
	if res == 0:
		raise ValueError("invalid thread id")
	elif res != 1:
		pythonapi.PyThreadState_SetAsyncExc(tid, None)
		raise SystemError("PyThreadState_SetAsyncExc failed")
