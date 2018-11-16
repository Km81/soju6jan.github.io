# -*- coding: utf-8 -*-
import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')

import xml.etree.ElementTree as ET
import re, pickle, urllib, urllib2, json, traceback

def insert_image(root):
	history = GetHistory()
	print 'LOADHISTORY COUNT : %s' % len(history)
	wrong = {}

	list = root.findall('programme')
	total = len(list)
	count = 0
	for item in list:
		count += 1
		title = item.find('title')
		icon = item.find('icon')
		try:
			search_text = title.text
			patten = re.compile(r'\(.*?\)')
			search_text = re.sub(patten, '', search_text).strip()

			patten = re.compile(r'\[.*?\]')
			search_text = re.sub(patten, '', search_text).strip()

			patten = re.compile(u'\s\d+회$')
			search_text = re.sub(patten, '', search_text).strip()

			patten = re.compile(u'\s\d+화$')
			search_text = re.sub(patten, '', search_text).strip()

			patten = re.compile(u'\s\d+부$')
			search_text = re.sub(patten, '', search_text).strip()

			patten = re.compile(u'^재\s')
			search_text = re.sub(patten, '', search_text).strip()
		except:
			pass
		title.text = search_text
		if icon is None:
			try:
				if search_text in history:
					img = history[search_text]
					#print('EXIST IN HISTROTY ')
				elif search_text in wrong:
					#print('ALREADY FAIL')
					img = None
				else:
					img = get_daum_poster(search_text)
					if img is not None:
						history[search_text] = img
					else:
						wrong[search_text] = None
				if img is not None:
					element = ET.Element('icon')
					element.attrib['src'] = img
					item.append(element)
			except:
				exc_info = sys.exc_info()
				traceback.print_exception(*exc_info)

		else:
			pass
	SaveHistory(history)
	print 'SAVEHISTORY COUNT : %s' % len(history)

def insert_episode_num(root):
	list = root.findall('programme')
	for item in list:
		try:
			element = ET.Element('episode-num')
			element.attrib['system'] = 'xmltv_ns'
			ep_num = item.find('episode-num')
			if ep_num is not None:
				element.text = '0.%s.' % (int(ep_num.text) - 1)
			else:
				tmp = item.attrib['start']
				element.text = '%s.%s.' % (int(tmp[2:4])-1, int(tmp[4:8])-1)
			item.append(element)
		except:
			pass


def get_daum_poster(str):
	try:
		url = 'https://search.daum.net/search?w=tv&q=%s' % (urllib.quote(str.encode('utf8')))
		request = urllib2.Request(url)
		request.add_header('user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36')
		response = urllib2.urlopen(request)
		data = response.read()
		match = re.compile('irk\=(?P<id>\d+)').search(data)  
		id = match.group('id') if match else ''
		if id is not '':
			match = re.compile('img\ssrc\=\"\/\/search(?P<src>.*?)\"').search(data)
			if match:
				return 'https://search%s' % match.group('src')
		else:
			return None
	except:
		import traceback
		exc_info = sys.exc_info()
		traceback.print_exception(*exc_info)

def GetHistory():
	try:
		HISTORY = os.path.join( os.getcwd(), 'daum_poster_urls.txt')
		file = open(HISTORY, 'rb')
		history = pickle.load(file)
		file.close()
	except:
		history = {}
	return history

def SaveHistory(history):
	HISTORY = os.path.join( os.getcwd(), 'daum_poster_urls.txt')
	file = open(HISTORY, 'wb')
	pickle.dump(history, file)
	file.close()

def LoadTvhProxy(url):
	request = urllib2.Request(url)
	response = urllib2.urlopen(request)
	tvh_data = json.load(response, encoding='utf8')
	return tvh_data


def GetGuideNumber(tvh_data, guideName):
	for d in tvh_data:
		if d['GuideName'] == guideName:
			return d['GuideNumber']
	return None

def change_display_for_plex(root, url):
	tvh_data = LoadTvhProxy(url)	
	list = root.findall('channel')
	total = len(list)
	count = 0
	for item in list:
		count += 1
		name = item.findall('display-name')
		if len(name) == 4:
			number = GetGuideNumber(tvh_data, name[0].text)
			if number == None:
				number = GetGuideNumber(tvh_data, name[1].text)
			if number is not None:
				name[2].text = number
			else:
				name[2].text = '0'
		else:
			print 'ERROR'

if __name__ == '__main__':
	input_filename = 'xmltv.xml'
	output_filename = 'xmltv_plex.xml'

	tree = ET.parse(input_filename)
	root = tree.getroot()

	# 1. 포스터 추가
	insert_image(root)

	# 2. episode_num 태크 추가
	insert_episode_num(root)

	# 3. 채널번호를 display number 태그에 넣는다.
	#url = 'http://192.168.0.41:5004/lineup.json'	
	#change_display_for_plex(root, url)

	tree.write(output_filename, encoding='utf-8', xml_declaration=True)

