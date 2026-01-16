# -*- coding: utf-8 -*-
import sys
import re
import json
import os
from datetime import date
from datetime import timedelta
from collections import defaultdict
from datetime import datetime
from text_process import TextProcess
import calendar
import pickle
from calendar_converter import *
from datetime import time
import logging
F_PATH = os.path.dirname(__file__) 

# logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('time norm')

def _format_timepoint(tunit):
    # result = [-1, -1, -1, -1, -1,-1, -1, -1]

    date = "{}:{}:{}".format(tunit[0],tunit[1],tunit[2])
    time = "{}:{}:{}".format(tunit[3],tunit[4],tunit[5])

    timePoint = [{'date':date,'time':time, 'isRepeat':False,'repeat':'0,0,0,0,0,0'}]
    result = {
        'isRealTime':False,
        'timePoint':timePoint,
        'timeSpan':[],
        'status': True,
        'isTimeSpan':False,
        }
    return result

def _format_timespan(tunit_start,tunit_end):

    if tunit_start == tunit_end:
        return _format_timepoint(tunit_start)

    date_1 = "{}:{}:{}".format(tunit_start[0],tunit_start[1],tunit_start[2])
    time_1 = "{}:{}:{}".format(tunit_start[3],tunit_start[4],tunit_start[5])

    
    date_2 = "{}:{}:{}".format(tunit_end[0],tunit_end[1],tunit_end[2])
    time_2 = "{}:{}:{}".format(tunit_end[3],tunit_end[4],tunit_end[5])
    
    datetime_1 = date_1 + ' ' + time_1
    datetime_2 = date_2 + ' ' + time_2
    if '-1' not in datetime_1 and '-1' not in datetime_2:
        datetime_1 = datetime.strptime(datetime_1,"%Y:%m:%d %H:%M:%S")
        datetime_2 = datetime.strptime(datetime_2,"%Y:%m:%d %H:%M:%S")
        if datetime_1 > datetime_2:
            raise ParseError()

    result = {
        'isRealTime':False,
        'timePoint':[],
        'timeSpan':[{
            'begin':{
            'date': date_1,
            'time': time_1,
            },
            'end':{
            'date': date_2,
            'time': time_2,
            },
            'isRepeat': False,
            'repeat':'0,0,0,0,0,0'
            }],
        'status': True,
        'isTimeSpan':True,
        }
    return result




class ParseError(Exception):
    def __init__(self):
        pass




class TimePoint:
    def __init__(self):
        # year month day hour minute second isrepeat
        self.tunit = [-1, -1, -1, -1, -1, -1, -1]
    def _set_time(self, value, index):
        if value != -1:
            if self.tunit[index] != -1:
                raise ParseError()
            self.tunit[index] = value
    def _special_set(self,value,index):
        if value != -1:
            self.tunit[index] = value



class TimeNormalizer:
    def __init__(self):
        self._preLoad()
        self.version = "v1.3.2"
        
    def _load(self,fname):
        fpath = os.path.join(F_PATH,'resource',fname)
        with open(fpath,'r',encoding='utf-8') as f:
            return json.load(f)

    def _replace(self,matched):
        return self.replace[matched.group()]

    def _pre_process(self,target):
        target = re.sub("|".join(self.replace),self._replace,target)
        target = re.sub("个|的|钟|份|整","",target)

        return TextProcess.transNum(target)
    
    def _preLoad(self):
        self.replace = self._load("replace.json")
        self.holi_lunar_match = self._load("holi_lunar_match.json")
        self.holi_solar_match = self._load("holi_solar_match.json")
        self.solar_terms_match = self._load("solar_terms_match.json")
        self.time_span_match = self._load("time_span_match.json")
        self.match = self._load("match.json")

    def _year(self,target,tp):
        rule = re.compile("大+前年|大+后年|今年|本年|去年|明年|来年|次年|前年|后年|\d+年")
        res = re.findall(rule,target)
        
        if len(res) == 1:
            year_match = re.findall("\d+|大+前|大+后|今|本|去|明|来|次|前|后",res[0])[0]
            
            if re.search("大",year_match):
                if re.search("前",year_match):
                    year_delta = - 2 - len(year_match[:-1])
                else:
                    year_delta = 2 + len(year_match[:-1])
                year = self.base_year + year_delta
            elif re.search("\d+",year_match):

                year = year_match
                if len(year) == 2:
                    year = int('20'+year)
                    if year > 2099:
                        raise ParseError()
                elif len(year) == 4:
                    if int(year) < 1988 or int(year) > 2099:
                        raise ParseError()
                    else:
                        year = int(year)
                else:
                    raise ParseError()
            else:
                delta = {"今":0,
                        "本":0,
                        "去":-1,
                        "明":1,
                        "来":1,
                        "次":1,
                        "前":-2,
                        "后":2}
                year = self.base_year + delta[year_match]

            tp._set_time(year,0)
            target = re.sub(res[0],"",target)
            logger.info('match year: {}, target last:{}'.format(year,target))
        if len(res) > 1:
            logger.error('multiple year found!')
            raise ParseError()

        return target

    def _month(self,target,tp):

        rule = re.compile("这月|本月|次月|下+月|上+月|\d+月")
        res = re.findall(rule,target)
        year = self.base_year
        if len(res) == 1:
            month_match = re.findall("这|\d+|下+|上+|本|次",res[0])[0]
            if re.search("上",month_match):
                month = self.base_month - len(month_match)
            elif re.search("下",month_match):
                month = self.base_month + len(month_match)
            elif re.search("\d+",month_match):
                month = int(month_match)
                logger.info('month match: {}'.format(month))
                if month > 12 or month < 1:
                    logger.error('month: {} can not > 12 or < 1!'.format(month))
                    raise ParseError()
            else:
                delta = {
                "这":0,
                "本":0,
                "次":1
                }
                month = self.base_month + delta[month_match]
                # tp._set_time(year,0)
            
            if month < 1:
                delta = int(month/(-12)) + 1
                month = 12 + month
                year -= delta
                tp._set_time(year,0)
            elif month > 12:
                delta = int(month/12)
                month = (month + delta*12)%12
                year += delta
                tp._set_time(year,0)
            # else:
            #     if self.fill:
            #         tp._set_time(year,0)


            tp._set_time(month,1)
            target = re.sub(res[0],"",target)
            logger.info('match month: {}, target last:{}'.format(month,target))
        if len(res) > 1:
            logger.error('multiple month found!')
            raise ParseError()
        return target


    def _weekday(self,target,tp):
        rule = re.compile("星期天|周天|礼拜天|星期日|周日|礼拜日|星期\d|周\d|礼拜\d|上+星期\d|上+周\d|上+礼拜\d|上+星期日|上+周日|上+礼拜日|上+星期天|上+周天|上+礼拜天|下+星期\d|下+周\d|下+礼拜\d|下+星期日|下+周日|下+礼拜日|下+星期天|下+周天|下+礼拜天|本星期\d|本周\d|本礼拜\d|本星期天|本周天|本礼拜天|本星期日|本周日|本礼拜日|这星期\d|这周\d|这礼拜\d|这星期日|这周日|这礼拜日|\这星期天|这周天|这礼拜天")
        res = re.findall(rule,target)

        if len(res) == 1:
            delta = 0
            if re.search("日|天",res[0]):
                weekday = 7
            if re.search("\d",res[0]):
                weekday = int(re.findall("\d+",res[0])[0])
                if weekday < 1 or weekday > 7:
                    raise ParseError()
            if re.search("上",res[0]):
                delta = - len(re.findall("上+",res[0])[0]) * 7
            elif re.search("下",res[0]):
                delta = len(re.findall("下+",res[0])[0]) * 7

            daydelta = weekday - self.base_weekday + delta

            refer_date = self.base_date + timedelta(days=daydelta)

            tp._set_time(refer_date.year,0)
            tp._set_time(refer_date.month,1)
            tp._set_time(refer_date.day,2)

            target = re.sub(res[0],"",target)
            
        if len(res) > 1:
            raise ParseError()
        return target



    def _day(self,target,tp):
        rule = re.compile("今天|今日|昨天|前天|大+前天|明天|明日|后天|大+后天|后日|\d+号|\d+日")
        res = re.findall(rule,target)

        if len(res) == 1:
            if re.search("大",res[0]):
                if re.search("前",res[0]):
                    delta = -2 - len(res[0][:-1]) + 1
                else:
                    delta = 2 + len(res[0][:-1]) - 1
                date_match = self.base_date + timedelta(days=delta)
                tp._set_time(date_match.year,0)
                tp._set_time(date_match.month,1)
                tp._set_time(date_match.day,2)
            elif re.search("\d+",res[0]):
                day = int(re.findall("\d+",res[0])[0])
                if day > 31 or day < 1:
                    raise ParseError()
                if tp.tunit[1] != -1:
                    if tp.tunit[0] == -1:
                        year = self.base_year
                    else:
                        year = tp.tunit[0]
                    if day > calendar.monthrange(year,tp.tunit[1])[1]:
                        raise ParseError()
                tp._set_time(day,2)
            else:
                delta_match = re.findall("今|昨|前|明|后",res[0])[0]
                delta = {
                    "今":0,
                    "昨":-1,
                    "前":-2,
                    "明":1,
                    "后":2,
                }
                date_match = self.base_date + timedelta(days=delta[delta_match])
                tp._set_time(date_match.year,0)
                tp._set_time(date_match.month,1)
                tp._set_time(date_match.day,2)
            target = re.sub(res[0],"",target)
        if len(res) > 1:
            raise ParseError()
        return target


    def _hour(self,target,tp):
        rule = "\d+点半|\d+时半|\d+点|\d+时"
        res = re.findall(rule,target)
        if len(res) == 1:
            if re.search("\d+",res[0]):
                hour = int(re.findall("\d+",res[0])[0])
                if hour > 24:
                    raise ParseError()
                tp._set_time(hour,3)
            
            if re.search("半",res[0]):
                tp._set_time(30,4)
            

            if re.search("\d+时\d+$|\d+点\d+$",target):
                minute = re.findall("(?<=时)\d+|(?<=点)\d+",target)[0]
                if int(minute) > 60:
                    raise ParseError()
                tp._set_time(int(minute) ,4)
                target = re.sub(res[0]+minute,"",target)
            else:
                target = re.sub(res[0],"",target)
            return target
        else:
            raise ParseError()

    def _minute(self,target,tp):
        rule = "1刻|3刻|\d+分"
        res = re.findall(rule,target)
        if len(res) == 1:
            num = int(re.findall("\d+",res[0])[0])
            if re.search("刻",res[0]):
                minute = num * 15
            else:
                minute = num
                if minute > 60:
                    raise ParseError()
            tp._set_time(minute, 4)
            target = re.sub(res[0],"",target)
            return target
        else:
            raise ParseError()
    def _period(self,target,tp):
        rule = "中午|凌晨|早上|早晨|清晨|清早|上午|下午|傍晚|黄昏|晚上|夜晚|夜间|夜里|半夜|午夜|深夜"
        res = re.findall(rule,target)
        if len(res) == 1:
            tp._set_time(res[0], 6)
            target = re.sub(res[0],"",target)
        if len(res) > 1:
            raise ParseError()
        return target

    def _sencond(self,target,tp):
        rule = "\d+秒"
        res = re.findall(rule,target)
        if len(res) == 1:
            second = int(re.findall("\d+",res[0])[0])
            if second > 60:
                raise ParseError()
            tp._set_time(second, 5)
            target = re.sub(res[0],"",target)
            return target
        else:
            raise ParseError()

    def _solar_term(self,target,tp):

        rule = "立春|雨水|惊蛰|春分|清明|谷雨|立夏|小满|芒种|夏至|小暑|大暑|立秋|处暑|白露|秋分|寒露|霜降|立冬|小雪|大雪|冬至|小寒|大寒"
        res = re.findall(rule,target)
        if len(res) == 1:
            if tp.tunit[0] == -1:
                year = self.base_year
            else:
                year = tp.tunit[0]
            
            refer_date = self.solar_terms_match[res[0]][str(year)]
            month = int(refer_date.split("-")[0])
            day = int(refer_date.split("-")[1])
            if tp.tunit[0] == -1 and (date(year, month, day) < self.base_date):
                year += 1
            
            if tp.tunit[0] == -1:
                tp._set_time(year, 0)
            tp._set_time(month, 1)
            tp._set_time(day, 2)
            target = re.sub(res[0],"",target)
        if len(res) > 1:
            raise ParseError()
        return target    

    def _festival(self,rule,target,tp,islunar):
        res = re.findall(rule,target)
        if len(res) == 1:
            if tp.tunit[0] == -1:
                year = self.base_year
                if islunar:
                    converter = LunarSolarConverter()
                    solar = Solar(year, self.base_month, self.base_day)
                    lunar = converter.SolarToLunar(solar)
                    year = lunar.lunarYear
                    
            else:
                year = tp.tunit[0]

            if islunar:
                converter = LunarSolarConverter()

                lunar_month = int(self.holi_lunar_match[res[0]].split("-")[0])
                lunar_day = int(self.holi_lunar_match[res[0]].split("-")[1])
                

                lunar = Lunar(year, lunar_month, lunar_day, isleap=False)
                solar = converter.LunarToSolar(lunar)

                conv_year = solar.solarYear
                conv_month = solar.solarMonth
                conv_day = solar.solarDay
                
                if tp.tunit[0] == -1 and (date(conv_year, conv_month, conv_day) < self.base_date):
                    year += 1
                    lunar = Lunar(year, lunar_month, lunar_day, isleap=False)
                    solar = converter.LunarToSolar(lunar)
                    conv_year = solar.solarYear
                    conv_month = solar.solarMonth
                    conv_day = solar.solarDay

                year = conv_year
                month = conv_month
                day = conv_day
            else:
                month = int(self.holi_solar_match[res[0]].split("-")[0])
                day = int(self.holi_solar_match[res[0]].split("-")[1])
                if tp.tunit[0] == -1 and (date(year, month, day) < self.base_date):
                    year += 1
            if tp.tunit[0] == -1:
                tp._set_time(year, 0)
            tp._set_time(month, 1)
            tp._set_time(day, 2)
            target = re.sub(res[0],"",target)
            return target
        else:
            raise ParseError()    

    
    
    def _tsp_year(self,target,tp_start,tp_end):
        if re.search("这|近",target):
            rule = re.compile("这\d+年|最近\d+年|近\d+年")
            sig = 0
        elif re.search("前|上|过去",target):
            rule = re.compile("前\d+年|前面?\d+年|上面?\d+年|过去\d+年")
            sig = -1
        elif re.search("后|下|未来|接下来",target):
            rule = re.compile("未来\d+年|下面?\d+年|后面?\d+年|接下来\d+年")
            sig = 1
        else:
            raise ParseError()
        res = re.findall(rule,target)

        if len(res) == 1:

            year = self.base_year
            if sig == 1:
                delta = sig*int(re.findall("\d+",res[0])[0])
                tp_start._set_time(year+1,0)
                tp_end._set_time(year+delta,0)
            elif sig == 0:
                delta = int(re.findall("\d+",res[0])[0])
                tp_start._set_time(year,0)
                tp_end._set_time(year+delta-1,0)
            else:
                delta = sig*int(re.findall("\d+",res[0])[0])
                tp_start._set_time(year+delta,0)
                tp_end._set_time(year-1,0)

            target = re.sub(res[0],"",target)
        if len(res) > 1:
            raise ParseError()
        return target

    def _tsp_month(self,target,tp_start,tp_end):
        if re.search("这|近",target):
            rule = re.compile("这\d+月|最近\d+月|近\d+月")
            sig = 0
        elif re.search("前|上|过去",target):
            rule = re.compile("前\d+月|前面?\d+月|上面?\d+月|过去\d+月")
            sig = -1
        elif re.search("后|下|未来|接下来",target):
            rule = re.compile("未来\d+月|下面?\d+月|后面?\d+月|接下来\d+月")
            sig = 1
        else:
            raise ParseError()
        res = re.findall(rule,target)

        if len(res) == 1:

            month = self.base_month
            refer_year = self.base_year
            if sig == 1:
                delta = sig*int(re.findall("\d+",res[0])[0])
                if (month+1) > 12:
                    year = refer_year + 1
                else:
                    year = refer_year
                tp_start._set_time(year,0)
                
                if (month+delta) > 12:
                    year = refer_year + 1
                else:
                    year = refer_year
                tp_end._set_time(year,0)

                tp_start._set_time((month+1)%12,1)
                tp_end._set_time((month+delta)%12,1)
            
            elif sig == 0:

                delta = int(re.findall("\d+",res[0])[0])
                
                tp_start._set_time(refer_year,0)

                if (month+delta-1) > 12:
                    year = refer_year + 1
                else:
                    year = refer_year
                tp_end._set_time(year,0)

                tp_start._set_time(month,1)
                tp_end._set_time((month+delta-1)%12,1)

            else:
                delta = sig*int(re.findall("\d+",res[0])[0])
                
                if (month+delta) > 12:
                    year = refer_year + 1
                else:
                    year = refer_year                
                tp_start._set_time(year,0)

                if (month+delta-1) > 12:
                    year = refer_year + 1
                else:
                    year = refer_year
                tp_end._set_time(year,0)

                tp_start._set_time((month+delta)%12,1)
                tp_end._set_time((month-1)%12,1)

            target = re.sub(res[0],"",target)
        if len(res) > 1:
            raise ParseError()
        return target


    def _tsp_day(self,target,tp_start,tp_end):
        if re.search("这|近",target):
            rule = re.compile("这\d+天|最近\d+天|近\d+天|这\d+日|最近\d+日|近\d+日")
            sig = 0
        elif re.search("前|上|过去",target):
            rule = re.compile("前\d+天|前面?\d+天|上面?\d+天|过去\d+天|前\d+日|前面?\d+日|上面?\d+日|过去\d+日")
            sig = -1
        elif re.search("后|下|未来|接下来",target):
            rule = re.compile("未来\d+天|下面?\d+天|后面?\d+天|接下来\d+天|未来\d+日|下面?\d+日|后面?\d+日|接下来\d+日")
            sig = 1
        else:
            raise ParseError()
        
        res = re.findall(rule,target)

        if len(res) == 1:

            refer_date = self.base_date
            if sig == 1:
                delta = sig*int(re.findall("\d+",res[0])[0])
                tp_start._set_time((refer_date+timedelta(days=1)).year,0)
                tp_end._set_time((refer_date+timedelta(days=delta)).year,0)

                tp_start._set_time((refer_date+timedelta(days=1)).month,1)
                tp_end._set_time((refer_date+timedelta(days=delta)).month,1)

                tp_start._set_time((refer_date+timedelta(days=1)).day,2)
                tp_end._set_time((refer_date+timedelta(days=delta)).day,2)

            elif sig == 0:

                delta = int(re.findall("\d+",res[0])[0])
                tp_start._set_time(refer_date.year,0)
                tp_end._set_time((refer_date+timedelta(days=delta-1)).year,0)

                tp_start._set_time(refer_date.month,1)
                tp_end._set_time((refer_date+timedelta(days=delta-1)).month,1)

                tp_start._set_time(refer_date.day,2)
                tp_end._set_time((refer_date+timedelta(days=delta-1)).day,2)

            else:
                
                delta = sig*int(re.findall("\d+",res[0])[0])
                tp_start._set_time((refer_date+timedelta(days=delta)).year,0)
                tp_end._set_time((refer_date+timedelta(days=-1)).year,0)

                tp_start._set_time((refer_date+timedelta(days=delta)).month,1)
                tp_end._set_time((refer_date+timedelta(days=-1)).month,1)

                tp_start._set_time((refer_date+timedelta(days=delta)).day,2)
                tp_end._set_time((refer_date+timedelta(days=-1)).day,2)

            target = re.sub(res[0],"",target)
        if len(res) > 1:
            raise ParseError()
        return target



    def _tsp_week(self,target,tp_start,tp_end):
        if re.search("这|近",target):
            rule = re.compile("这礼拜|这星期|这周|这\d+星期|最近\d+星期|近\d+星期|这\d+周|最近\d+周|近\d+周|这\d+礼拜|最近\d+礼拜|近\d+礼拜")
            sig = 0
        elif re.search("前|上|过去",target):
            rule = re.compile("上礼拜|上星期|上周|前\d+星期|前面?\d+星期|上面?\d+星期|过去\d+星期|前\d+周|前面?\d+周|上面?\d+周|过去\d+周|前\d+礼拜|前面?\d+礼拜|上面?\d+礼拜|过去\d+礼拜")
            sig = -1
        elif re.search("后|下|未来|接下来",target):
            rule = re.compile("下礼拜|下星期|下周|未来\d+星期|下面?\d+星期|后面?\d+星期|接下来\d+星期|未来\d+周|下面?\d+周|后面?\d+周|接下来\d+周|未来\d+礼拜|下面?\d+礼拜|后面?\d+礼拜|接下来\d+礼拜")
            sig = 1
        else:
            raise ParseError()

        res = re.findall(rule,target)

        if len(res) == 1:
            res_num = re.findall("\d+",res[0])

            if res_num:
                dl = int(res_num[0])
            else:
                dl = 1
            refer_date = self.base_date
            
            if sig == 1:
                day_delta = 7 - self.base_weekday + 1
                delta = sig*dl* 7 + day_delta - 1

                tp_start._set_time((refer_date+timedelta(days=day_delta)).year,0)
                tp_start._set_time((refer_date+timedelta(days=day_delta)).month,1)
                tp_start._set_time((refer_date+timedelta(days=day_delta)).day,2)

                tp_end._set_time((refer_date+timedelta(days=delta)).year,0)
                tp_end._set_time((refer_date+timedelta(days=delta)).month,1)
                tp_end._set_time((refer_date+timedelta(days=delta)).day,2)

            elif sig == 0:

                day_delta = 1 - self.base_weekday
                delta = dl*7 + day_delta - 1

                tp_start._set_time((refer_date+timedelta(days=day_delta)).year,0)
                tp_start._set_time((refer_date+timedelta(days=day_delta)).month,1)
                tp_start._set_time((refer_date+timedelta(days=day_delta)).day,2)

                tp_end._set_time((refer_date+timedelta(days=delta)).year,0)
                tp_end._set_time((refer_date+timedelta(days=delta)).month,1)
                tp_end._set_time((refer_date+timedelta(days=delta)).day,2)
            else:
                day_delta = - self.base_weekday
                delta = day_delta + sig* dl * 7 + 1

                tp_start._set_time((refer_date+timedelta(days=delta)).year,0)
                tp_start._set_time((refer_date+timedelta(days=delta)).month,1)
                tp_start._set_time((refer_date+timedelta(days=delta)).day,2)

                tp_end._set_time((refer_date+timedelta(days=day_delta)).year,0)
                tp_end._set_time((refer_date+timedelta(days=day_delta)).month,1)
                tp_end._set_time((refer_date+timedelta(days=day_delta)).day,2)
            target = re.sub(res[0],"",target)
        
        if len(res) > 1:
            raise ParseError()
        return target

    def _tsp_weekend(self,target,tp_start,tp_end):
        rule = re.compile("周末|这周末|上+周末|下+周末")
        res = re.findall(rule,target)

        if len(res) == 1:

            refer_date = self.base_date
            if re.search("上", res[0]):

                delta = - refer_date.weekday() + (len(re.findall("上+", res[0])[0]) - 1 )* (- 7)

                tp_start._set_time((refer_date+timedelta(days=delta-2)).year,0)
                tp_start._set_time((refer_date+timedelta(days=delta-2)).month,1)
                tp_start._set_time((refer_date+timedelta(days=delta-2)).day,2)

                tp_end._set_time((refer_date+timedelta(days=delta-1)).year,0)
                tp_end._set_time((refer_date+timedelta(days=delta-1)).month,1)
                tp_end._set_time((refer_date+timedelta(days=delta-1)).day,2)

            elif re.search("下+", res[0]):
                delta = 6 - refer_date.weekday() + len(re.findall("下+", res[0])[0])* 7

                tp_start._set_time((refer_date+timedelta(days=delta-1)).year,0)
                tp_start._set_time((refer_date+timedelta(days=delta-1)).month,1)
                tp_start._set_time((refer_date+timedelta(days=delta-1)).day,2)

                tp_end._set_time((refer_date+timedelta(days=delta)).year,0)
                tp_end._set_time((refer_date+timedelta(days=delta)).month,1)
                tp_end._set_time((refer_date+timedelta(days=delta)).day,2)
            else:
                delta = 7 - refer_date.weekday()
                tp_start._set_time((refer_date+timedelta(days=delta-2)).year,0)
                tp_start._set_time((refer_date+timedelta(days=delta-2)).month,1)
                tp_start._set_time((refer_date+timedelta(days=delta-2)).day,2)
                tp_end._set_time((refer_date+timedelta(days=delta-1)).year,0)
                tp_end._set_time((refer_date+timedelta(days=delta-1)).month,1)
                tp_end._set_time((refer_date+timedelta(days=delta-1)).day,2)

            target = re.sub(res[0],"",target)
        if len(res) > 1:
            raise ParseError()
        return target

    def _tsp_frmto(self,target,tp_start,tp_end):

        target_set = re.split("到|至",target)
        if '' in target_set:
            raise ParseError()
        res_1 = self.parse_tp(target_set[0])
        res_2 = self.parse_tp(target_set[1])

        if not res_1["status"] or not res_2["status"]:
            raise ParseError()

        if res_1["timePoint"] and res_2["timePoint"]:
            
            if res_1["timePoint"][0]["isRepeat"] or res_2["timePoint"][0]["isRepeat"]:

                raise ParseError()

            date_1 = [int(t) for t in res_1["timePoint"][0]["date"].split(":")]
            time_1 = [int(t) for t in res_1["timePoint"][0]["time"].split(":")]

            tp_start._set_time(date_1[0],0)
            tp_start._set_time(date_1[1],1)
            tp_start._set_time(date_1[2],2)
            tp_start._set_time(time_1[0],3)
            tp_start._set_time(time_1[1],4)
            tp_start._set_time(time_1[2],5)

            date_2 = [int(t) for t in res_2["timePoint"][0]["date"].split(":")]
            time_2 = [int(t) for t in res_2["timePoint"][0]["time"].split(":")]

            tp_end._set_time(date_2[0],0)
            tp_end._set_time(date_2[1],1)
            tp_end._set_time(date_2[2],2)
            tp_end._set_time(time_2[0],3)
            tp_end._set_time(time_2[1],4)
            tp_end._set_time(time_2[2],5)

            return ""

    def match_rule(self,match_dict):
        match_keywords = list(match_dict.keys())
        length=[len(w) for w in match_keywords]
        match_keywords_sorted = [word[0] for word in sorted(dict(zip(match_keywords,length)).items(),key=lambda x:x[1],reverse=True)]
        rule = "|".join(match_keywords_sorted)
        return rule

    def parse_tsp(self,target):
        try:

            tp_start = TimePoint()
            tp_end = TimePoint()

            if re.search("到|至",target):
                target = self._tsp_frmto(target,tp_start,tp_end)

            if re.search("年",target):
                target = self._tsp_year(target,tp_start,tp_end)
            if re.search("月",target) and target:
                target = self._tsp_month(target,tp_start,tp_end)
            if re.search("天|日",target) and target:
                target = self._tsp_day(target,tp_start,tp_end)
            if re.search("周末",target) and target:
                target = self._tsp_weekend(target,tp_start,tp_end)
            if re.search("周|星期|礼拜",target) and target:
                target = self._tsp_week(target,tp_start,tp_end)

            if not target:
                if self.fill:
                    self._filling(tp_start)
                    self._filling(tp_end)
                return _format_timespan(tp_start.tunit,tp_end.tunit)
            else:
                raise ParseError()
        except:
            return None


    def _now(self,rule,target,tp):
        res = re.findall(rule,target)
        if len(res) == 1:
            print(target)
            
            target = re.sub(res[0],"",target)
        if len(res) > 1:
            raise ParseError()
        return target

    def _special(self,rule,target,tp):

        res = re.findall(rule,target)
        if len(res) == 1:
            sub_res = re.findall("\d+",res[0])

            if len(sub_res) != 3:
                raise ParseError()

            month,count,weekday = int(sub_res[0]),int(sub_res[1]),int(sub_res[2])

            if tp.tunit[0] == -1:
                year = self.base_year
                if month < self.base_month:
                    year += 1
            else:
                year = tp.tunit[0]
            
            day = calendar.monthcalendar(year,month)[count][weekday-1]
            if day == 0:
                day = calendar.monthcalendar(year,month)[count+1][weekday-1]
            
            if tp.tunit[0] == -1:
                tp._set_time(year,0)

            tp._set_time(month,1)
            tp._set_time(day,2)
            
            target = re.sub(res[0],"",target)
            return target
        else:
            raise ParseError()
        

    def parse_tp(self,target):
        try:

            tp = TimePoint()
            rule = self.match_rule(self.match)
            if re.fullmatch(rule,target):
                res = re.findall(rule,target)[0]
                month = int(self.match[res].split('-')[0])
                day = int(self.match[res].split('-')[1])
                tp._set_time(month,1)
                tp._set_time(day,2)
                target = re.sub(res,"",target)
                logger.info('full match {}'.format(res))

            rule = re.compile("当天|那天|那1天")
            if re.search(rule,target) and target:
                target = re.sub(rule,"",target)
                if not target:
                    raise ParseError()

            rule = re.compile("现在|此时|此刻|当下|当前|目前")
            if re.fullmatch(rule,target):
                result    = {'isRealTime':True,
                            'timePoint':[],
                            'timeSpan':[],
                            'status': True,
                            'isTimeSpan':False,
                            }
                return result

            if re.search("年",target) and target:
                target = self._year(target,tp)
                

            rule = re.compile("\d+月第\d+星期\d+")    
            if re.search(rule,target):
                target = self._special(rule,target,tp)

            if re.search("月",target) and target:
                target = self._month(target,tp)

            if re.search("星期|礼拜|周",target) and target:
                target = self._weekday(target,tp)

            if re.search("号|天|日",target) and target:
                target = self._day(target,tp)


            if re.search("立春|雨水|惊蛰|春分|清明|谷雨|立夏|小满|芒种|夏至|小暑|大暑|立秋|处暑|白露|秋分|寒露|霜降|立冬|小雪|大雪|冬至|小寒|大寒",target) and target:
                target = self._solar_term(target,tp)
            
            
            rule = self.match_rule(self.holi_lunar_match)
            if re.search(rule,target) and target:
                target = self._festival(rule,target,tp,islunar=True)
            

            rule=self.match_rule(self.holi_solar_match)
            if re.search(rule,target) and target:
                target = self._festival(rule,target,tp,islunar=False)
            
            if re.search("时|点",target) and target:
                target = self._hour(target,tp)

            if re.search("刻|分",target) and target:
                target = self._minute(target,tp)
            
            if re.search("秒",target) and target:
                target = self._sencond(target,tp)
            
            if re.search("中午|凌晨|早上|早晨|清晨|清早|上午|下午|傍晚|黄昏|晚上|夜晚|夜间|夜里|半夜|午夜|深夜",target) and target:
                target = self._period(target,tp)

                if tp.tunit[6] != -1:
                    
                    year = tp.tunit[0]
                    month = tp.tunit[1]
                    day = tp.tunit[2]

                    if day == -1 and year != -1:
                        raise ParseError()
                    if day == -1 and month != -1:
                        raise ParseError()



                    if tp.tunit[3] == -1 and tp.tunit[4] == -1:
                        if target:
                            raise ParseError()


                        time_span = self.time_span_match[tp.tunit[6]]

                        tp_start = TimePoint()
                        tp_end = TimePoint()
                        start_year,start_month,start_day = tp_start.tunit[0],tp_start.tunit[1],tp_start.tunit[2]
                        end_year,end_month,end_day = tp_end.tunit[0],tp_end.tunit[1],tp_end.tunit[2]

                        start = time_span.split("-")[0]
                        start_hour = int(start.split(":")[0])
                        start_minute = int(start.split(":")[1])
                        


                        if year != -1:
                            start_year = year
                        else:
                            if self.fill:
                                start_year = self.base_year
                            
                        if month != -1:
                            start_month = month
                        else:
                            if self.fill:
                                start_month = self.base_month
                        
                        if day != -1:
                            start_day = day
                        else:
                            if self.fill:
                                start_day = self.base_day

                    
                        tp_start._set_time(start_year,0)
                        tp_start._set_time(start_month,1)
                        tp_start._set_time(start_day,2)

                        tp_start._set_time(start_hour,3)
                        tp_start._set_time(start_minute,4)
                        tp_start._set_time(0,5)

                        end = time_span.split("-")[1]
                        end_hour = int(end.split(":")[0])
                        end_minute = int(end.split(":")[1])


                        if year != -1:
                            end_year = year
                        else:
                            if self.fill:
                                end_year = self.base_year
                        
                        if month != -1:
                            end_month = month
                        else:
                            if self.fill:
                                end_month = self.base_month
                        
                        if day != -1:
                            end_day = day
                        else:
                            if self.fill:
                                end_day = self.base_day

                        if tp.tunit[6] in set({"夜里","半夜","午夜"}):
                            try:
                                start_time = "{}:{}:{} {}:{}:{}".format(start_year,start_month,start_day,start_hour,start_minute,0)
                                start_time = datetime.strptime(start_time,"%Y:%m:%d %H:%M:%S")
                                
                                end_time = "{}:{}:{} {}:{}:{}".format(end_year,end_month,end_day,end_hour,end_minute,0)
                                end_time = datetime.strptime(end_time,"%Y:%m:%d %H:%M:%S")
                                if start_time > end_time:
                                    end_time = end_time + timedelta(days=1)
                                    end_year = end_time.year
                                    end_month = end_time.month
                                    end_day    = end_time.day

                            except:
                                pass

                        
                        tp_end._set_time(end_year,0)
                        tp_end._set_time(end_month,1)
                        tp_end._set_time(end_day,2)
                        tp_end._set_time(end_hour,3)
                        tp_end._set_time(end_minute,4)
                        tp_end._set_time(0,5)
                        
                        return _format_timespan(tp_start.tunit,tp_end.tunit)

                    else:

                        if tp.tunit[3] > 24:
                            raise ParseError()
                        if tp.tunit[6] in set({"下午","傍晚","黄昏"}):
                            if tp.tunit[3] < 12 and tp.tunit[3] < 13:
                                hour = (tp.tunit[3] + 12)%24
                                tp._special_set(hour,3)
                        elif tp.tunit[6] in set({"晚上","夜晚","午夜","深夜"}):
                            if tp.tunit[3] > 5 and tp.tunit[3] < 13:
                                hour = (tp.tunit[3] + 12)%24
                                tp._special_set(hour,3)                            
                        elif tp.tunit[6] in set({"夜间","夜里","半夜"}):
                            if tp.tunit[3] > 5 and tp.tunit[3] < 13:
                                hour = (tp.tunit[3] + 12)%24
                                tp._special_set(hour,3)


            if not target:
                if self.fill:
                    self._filling(tp)
                return _format_timepoint(tp.tunit)
            else:
                raise ParseError()
        except:
            return None


    def _filling(self,tp):
        if tp.tunit[2] != -1 and tp.tunit[0] != -1 and tp.tunit[1] == -1:
            raise ParseError()

        if tp.tunit[5] != -1 and  tp.tunit[4] == -1:
            if tp.tunit[2] == -1 and tp.tunit[0] == -1 and tp.tunit[1] == -1:
                raise ParseError

        if tp.tunit[2] != -1:
            if tp.tunit[0] == -1:
                tp._set_time(self.base_year,0)
            if tp.tunit[1] == -1:
                tp._set_time(self.base_month,1)
        
        if tp.tunit[1] != -1 and tp.tunit[0] == -1:
            tp._set_time(self.base_year,0)

        if tp.tunit[0] == -1 and tp.tunit[1] == -1 and tp.tunit[2] == -1:
            tp._set_time(self.base_year,0)
            tp._set_time(self.base_month,1)
            tp._set_time(self.base_day,2)


        

        if tp.tunit[0] != -1 and tp.tunit[1] != -1 and tp.tunit[2] != -1:
            try:
                date(tp.tunit[0],tp.tunit[1],tp.tunit[2])
            except:
                raise ParseError()


        if tp.tunit[5] != -1 or tp.tunit[4] != -1 or tp.tunit[3] != -1:

            if tp.tunit[5] == -1:
                tp._set_time(0,5)

            if tp.tunit[4]== -1:
                tp._set_time(0,4)

            if tp.tunit[3] == -1:
                tp._set_time(datetime.now().hour,3)


    def parse(self,raw_target,fill=True):

        try:
            self.fill = fill
            self.base_date = date.today()
            self.base_year = self.base_date.year
            self.base_month = self.base_date.month
            self.base_day = self.base_date.day
            self.base_weekday = self.base_date.weekday() + 1

            target = self._pre_process(raw_target)

            if not target:
                logger.error('no target after preprocess')
                raise ParseError()
            res = self.parse_tp(target)
            logger.error('parse_tp res: {}'.format(res))
            if res:
                return res
            res = self.parse_tsp(target)
            if res:
                return res
            
            raise ParseError()

        except Exception as e:
            return {
                'timePoint':[],
                'timeSpan':[],
                'status': False,
                'isTimeSpan':False,
                'isRealTime':False,
            }

if __name__ == '__main__':
    t = TimeNormalizer()


    s = ['未来三天', '大后天', '今年的清明节', '早上5点23分10秒', '前年中秋节']
    for i in s:
        # print(i)parse_tp
        print(t.parse(i,fill=False))




