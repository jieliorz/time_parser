# -*- coding: utf-8 -*-
import re

S_NUM_CH = {
'零':'0',
'一':'1',
'二':'2',
'三':'3',
'四':'4',
'五':'5',
'六':'6',
'七':'7',
'八':'8',
'九':'9',
'壹':'1',
'贰':'2',
'叁':'3',
'肆':'4',
'伍':'5',
'陆':'6',
'柒':'7',
'捌':'8',
'玖':'9',
'幺':'1',
'两':'2',
}



B_NUM_CH = {
'万':'0000',
'千':'000',
'百':'00',
}



class TextProcess:
	@classmethod
	def transNum(cls,sentence,transType=''):
		sentence = sentence.lower()
		for word in S_NUM_CH:
			sentence = re.sub(word,S_NUM_CH[word],sentence)


		if '十' in sentence:
			pattern = re.compile('\\d{1}十\\d{1}')
			for m in pattern.finditer(sentence):
				sentence = sentence.replace(m.group(),m.group().replace('十',''))
			pattern = re.compile('\\d{1}十')
			for m in pattern.finditer(sentence):
				sentence = sentence.replace(m.group(),m.group().replace('十','0'))
			pattern = re.compile('十\\d{1}')
			for m in pattern.finditer(sentence):
				sentence = sentence.replace(m.group(),m.group().replace('十','1'))
			sentence = sentence.replace('十','10')

		if '万' in sentence:
			pattern = re.compile('\\d{1}万')
			for m in pattern.finditer(sentence):
				sentence = sentence.replace(m.group(), m.group().replace('万', '0000'))
		if '千' in sentence:
			pattern = re.compile('\\d{1}千0')
			for m in pattern.finditer(sentence):
				sentence = sentence.replace(m.group(), m.group().replace('千', '0'))			
			pattern = re.compile('\\d{1}千')
			for m in pattern.finditer(sentence):
				sentence = sentence.replace(m.group(), m.group().replace('千', '000'))
		if '百' in sentence:
			pattern = re.compile('\\d{1}百0')
			for m in pattern.finditer(sentence):
				sentence = sentence.replace(m.group(), m.group().replace('百', ''))		
			pattern = re.compile('\\d{1}百')
			for m in pattern.finditer(sentence):
				sentence = sentence.replace(m.group(), m.group().replace('百', '00'))

		return sentence






