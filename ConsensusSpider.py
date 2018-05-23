import time
import re
import requests
from urllib import parse
from bs4 import BeautifulSoup

# 时间戳转字符串
def tp2str(time_stamp, format='%Y-%m-%d %H:%M:%S'):
	time_stamp = int(time_stamp)
	time_tuple = time.localtime(time_stamp)
	time_str = time.strftime(format, time_tuple)
	return time_str

# 字符串转时间戳
def str2tp(str, format='%Y-%m-%d %H:%M:%S'):
	time_tuple = time.strptime(str, format)
	time_stamp = time.mktime(time_tuple)
	return int(time_stamp)

# 获取时间范围并返回元组
def get_time(period):
	# 时间范围
	# period = input('请输入时间范围(天数)，如：1/7/30\n')
	# 当前时间的时间戳、字符串
	current_tp = int(time.time())
	current_str = tp2str(current_tp)
	# 起始时间，转化为当天0点开始
	start_tp = current_tp - int(period) * 86400
	start_str = tp2str(start_tp, '%Y-%m-%d') + ' 00:00:00'
	start_tp = str2tp(start_str)
	# 新建元组并返回
	time_tuple = (start_tp, current_tp) 
	print('起始时间：%s\n结束时间：%s\n起始Unix：%s\n结束Unix：%s\n' % (start_str, current_str, start_tp, current_tp))
	return time_tuple

# 构造gpc数据
def make_gpc(time_tuple):
	# 'gpc=stf=开始时间,结束时间|stftype=2'
	string = 'stf=%s,%s|stftype=2' % (time_tuple[0], time_tuple[1])
	# 替换符号为URL所需的格式
	string = re.sub(r'=', '%3D', string)
	string = re.sub(r',', '%2C', string)
	string = re.sub(r'\|', '%7C', string)
	print(string)
	return string

# 构造搜索页面的URL
def make_url(period):
	gpc = make_gpc(get_time(period))
	website = {
		'tieba': 'tieba.baidu.com',
		'zhihu': 'www.zhihu.com',
		'weibo': 'weibo.com',
		'mcbbs': 'www.mcbbs.net',
		'bilibili': 'www.bilibili.com',
	}
	keyword = '我的世界'
	rn = 10
	base = 'http://www.baidu.com'
	url_dict = {}
	for key in website:
		si = '(%s)' % website[key]
		# 通过title限制一下贴吧的爬取
		if key == 'tieba':
			wd = 'site:(%s) title:("【minecraft吧】") %s' % (website[key], keyword)
		else:
			wd = 'site:(%s) %s' % (website[key], keyword)
		url_dict[key] = base + '/s?ie=utf-8&si=%s&rn=%s&wd=%s&gpc=%s' % (si, rn, wd, gpc)
		
			
	print(url_dict)
	return url_dict

# 获取URL对应网页的内容
def get_html(url):
	r = requests.get(url, timeout=30)
	r.raise_for_status()
	r.encoding = 'utf-8'
	try:
		r = requests.get(url, timeout=30)
		r.raise_for_status()
		r.encoding = 'utf-8'
		return r.text
	except:
		print('[ERROR][get_html]获取网页内容时发生错误！')

# 解析页面返回储存数据的字典
def post_parse(url):
	html = get_html(url)
	soup = BeautifulSoup(html, 'lxml')
	divTags = soup.find_all('div', class_='result c-container ')
	data_list = []
	for i in divTags:
		title = i.find('h3', class_='t')
		href = title.find('a')['href']
		content = str(i.find('div', class_='c-abstract'))
		content = re.sub(r'<br>','\n' , content)
		content = re.sub(r'<.+?>','' , content).strip()
		title = title.text.strip()
		link = parse.urljoin(url, href)
		data = {
			'title': title,
			'link': link,
			'content': content,
		}
		data_list.append(data)
	print(data_list)
	return data_list

# 检测是否有下一页，返回URL
def get_next(url):
	html = get_html(url)
	soup = BeautifulSoup(html, 'lxml')
	if soup.find('a', text=re.compile('下一页>')) is not None:
		href = soup.find('a', text=re.compile('下一页>'))['href']
		next_page = parse.urljoin(url, href)
		print(next_page)
		return next_page
	else:
		print('未找到下一页, 爬取结束')
		return None

# 持续调用解析函数爬取页面
def spider(website, period):
	target_url = make_url(period)[website]
	item_list = []
	while target_url is not None:
		item = post_parse(target_url)
		item_list.extend(item)
		target_url = get_next(target_url)
	return item_list

# 将爬取信息组成文本内容
def text_write(head, website, period):
	print('\n\n[INFO]开始爬取%s天内%s舆论信息\n' % (period, head))
	head = '## %s\n' % head
	body = ''
	item_list = spider(website, period)
	for i in item_list:
		title = i['title']
		link = i['link']		
		content = i['content']
		body = body + '### %s\n%s\n%s\n\n\n' % (title, link, content)
	text = head + body + '\n\n\n\n'
	return text

# 主函数
def main():
	period = input('请输入时间范围(天数)，如：1/7/30\n')
	current_time = time.strftime("%Y-%m-%d %H_%M_%S", time.localtime())
	file_name = '舆论监控速报-最近%s天(%s).md' % (period, current_time)
	with open(file_name, 'a+', encoding='utf-8') as f:
		news_head = '# 舆论监控速报-最近%s天(%s)\n' % (period, current_time)
		f.write(news_head)
		f.write(text_write('贴吧', 'tieba', period))
		f.write(text_write('知乎', 'zhihu', period))
		f.write(text_write('微博', 'weibo', period))
		f.write(text_write('MCBBS', 'mcbbs', period))
		f.write(text_write('哔哩哔哩', 'bilibili', period))


if __name__ == '__main__':
	main()
