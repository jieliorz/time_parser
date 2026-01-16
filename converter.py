#-*- coding:utf-8 -*-
# from time_normalizer import TimeNormalizer
from datetime import datetime
from datetime import timedelta


def vali(date,hour):
    year = date.split(":")[0]
    month = date.split(":")[1]
    day = date.split(":")[2]
    tts=""
    piece={}
    if year == "-1":
        tts+="缺少年"
    if month == "-1":
        tts+=" 缺少月"
    if day == "-1":
        tts+=" 缺少日"
    
    if tts == "":
        date = "{}-{:0>2}-{:0>2}".format(year,month,day)
        if hour == "-1":
            hour = ""
        piece["real"]=False
        piece["date"]=date
        piece["hour"]=hour
        status = True
    else:
        status = False

    return tts,piece,status



def time_converter(res):
    ret = {"status":False,"tts":"","query":[]}

    if not res["status"]:
        ret["tts"]="请输入正确的时间"
        return ret
    else:
        if res["is_real"]:
            ret["status"]=True
            ret["tts"]="正在为您查询当前天气..."
            ret["query"]=[{"real":True,"date":"","time":""}]
            return ret
        else:
            for tp in res["timePoint"]:
                hour = tp["time"].split(":")[0]

                tts,piece,status=vali(tp["date"],hour)
                ret["tts"] = tts
                ret["status"]=status

            for tsp in res["timeSpan"]:
                begin=tsp["begin"]
                begin_date=begin["date"]
                begin_time=begin["time"]
                begin_hour=begin_time.split(":")[0]
                begin_tts,begin_piece,begin_status=vali(begin_date,begin_hour)
                if not begin_status:
                    ret["tts"]="时间段开头"+begin_tts
                    return ret
                else:
                    ret["query"].append(begin_piece)
                
                end=tsp["end"]
                end_date=end["date"]
                end_time=end["time"]
                end_hour=end_time.split(":")[0]
                end_tts,end_piece,end_status=vali(end_date,end_hour)
                if not end_status:
                    ret["tts"]="时间段结尾"+end_tts
                    return ret
                if begin_hour == "-1:-1:-1":
                    begin_datetime = datetime.strptime(begin_date,"%Y:%m:%d")
                else:
                    begin_datetime = begin_date+" "+begin_time
                    begin_datetime = datetime.strptime(begin_datetime,"%Y:%m:%d %H:%M:%S")

                if end_hour == "-1:-1:-1":
                    end_datetime = datetime.strptime(end_date,"%Y:%m:%d")
                else:
                    end_datetime = end_date+" "+end_time
                    end_datetime = datetime.strptime(end_datetime,"%Y:%m:%d %H:%M:%S")
                span = end_datetime - begin_datetime
                if span.days > 15 or span.days < 0:
                    ret["tts"] = "时间段表述不正确"
                    return ret
                else:
                    ret["status"]=True
                    ret["query"].append(piece)
                    if span.days == 0:
                        for i in range(3600,span.seconds-3600,3600):
                            interval = begin_datetime + timedelta(seconds=i)

                            date=datetime.strftime(interval,"%Y:%m:%d")
                            hour=datetime.strftime(interval,"%H")
                            tts,piece,status=vali(date,hour)
                            ret["query"].append(piece)
                    else:
                        for i in range(1,span.days-1):
                            interval = begin_datetime + timedelta(days=i)
                            date=datetime.strftime(interval,"%Y:%m:%d")
                            hour=""
                            tts,piece,status=vali(date,hour)
                            ret["query"].append(piece)
                    ret["query"].append(end_piece)
    return ret
                        
