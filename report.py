#!/usr/bin/python3
# coding=utf-8
import math
import os
import re
import subprocess
import sys
from io import BytesIO
from shutil import which
import calmap
import datetime,time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from distlib.compat import raw_input
from matplotlib import pylab as pl
from PIL import Image
from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph
from wordcloud import WordCloud
from urllib.request import build_opener
from urllib.error import HTTPError
from urllib.parse import urlencode,quote_plus
import json
import datetime, pytz


__version__ = "0.5.5"
__author__ = "np1"
__license__ = "LGPLv3"

t1 = datetime.datetime.now()
print("start >> {}".format(t1))
year = str(time.strftime('%Y', time.localtime()))
month = str(time.strftime('%m', time.localtime()))
day = str(time.strftime('%d', time.localtime()))

missing = []
dir = os.path.join(os.getcwd(), "Takeout/YouTube and YouTube Music/")
if not os.path.exists(dir):
    missing.append(dir)
found = False
for path in ("Verlauf/Wiedergabeverlauf.html", "history/watch-history.html"):
    watch_history = os.path.join(dir, path)
    if os.path.exists(watch_history):
        found = True
        break
if not found:
    missing.append(watch_history)
found = False
for path in ("Verlauf/Suchverlauf.html", "history/search-history.html"):
    search_history = os.path.join(dir, path)
    if os.path.exists(search_history):
        found = True
        break
if not found:
    missing.append(search_history)
found = False
for path in ("Meine Kommentare/Meine Kommentare.html", "my-comments/my-comments.html"):
    comments_history = os.path.join(dir, path)
    if os.path.exists(comments_history):
        found = True
        break
if not found:
    missing.append(comments_history)
found = False
playlists_path = os.path.join(dir, 'playlists')

for path in ("Playlists/Positive Bewertungen.json", "playlists/Liked videos.csv"):
    like_history = os.path.join(dir, path)
    if os.path.exists(like_history):
        found = True
        break
if not found:
    missing.append(like_history)
del found

if len(missing) > 0:
    raise OSError("Required directories do not exist: %s" % (missing))
del missing


class HTML:
    with open(watch_history, "r", encoding="utf-8") as f:
        html_watch = f.read()
    with open(search_history, "r", encoding="utf-8") as f:
        html_search = f.read()
    try:
        with open(comments_history, "r", encoding="utf-8") as f:
            html_comment = f.read()
    except Exception:
        print("Could not parse comments.")

    # 下面的watch history的title/time可与video_id一并写入一个函数，从而直接输出三列的df而无需在report中分别再处理它们
    def find_video_id(self):
        video_id = []
        pattern = re.compile(
            r"""Watched\xa0<a href=\".[^v]*v=(.[^\"]*)\">.[^<]*<\/a><br><a href=\".[^\"]*\">.[^<]*<\/a>""")
        matchList = pattern.findall(str(self.html_watch))
        for match in matchList:
            if type(match) == str:
                video_id.append(match)
        return video_id
        links2 = []
        for i in video_id:
            if '</a>' in i:
                p = re.compile(r"""(.*)<\/a>""")  # (.[^ <] *)
                j = p.findall(str(i))
                # return i
                # links2.append(j)
                # return j
            else:
                links2.append(i)
        return links2

    def find_video_title(self):
        video_title = []
        pattern = re.compile(r"""Watched\xa0<a href=\".[^\"]*\">(.[^<]*)<\/a><br><a href=\".[^\"]*\">.[^<]*<\/a>""")
        matchList = pattern.findall(str(self.html_watch))
        for match in matchList:
            if type(match) == str:
                video_title.append(match)
        return video_title

    def find_date_time(self):
        # search all links based on your personal html file
        date_time = []
        pattern = re.compile(
            r"""Watched\xa0<a href=\".[^\"]*\">.[^<]*<\/a><br><a href=\".[^\"]*\">.[^<]*<\/a><br>(\w{1,3}\s.*?)<\/div>""")
        matchList = pattern.findall(str(self.html_watch))
        for match in matchList:
            if type(match) == str:
                date_time.append(match)
        return date_time

    def find_channel_link(self):
        channel_link = []
        pattern = re.compile(r"""Watched\xa0<a href=\".*?\">.*?<\/a><br><a href=\"(.*?)\">.*?<\/a>""")
        matchList = pattern.findall(str(self.html_watch))
        for match in matchList:
            if type(match) == str:
                channel_link.append(match)
        return channel_link

    def find_channel_title(self):
        channel_title = []
        pattern = re.compile(r"""Watched\xa0<a href=\".*?\">.*?<\/a><br><a href=\".*?\">(.*?)<\/a>""")
        matchList = pattern.findall(str(self.html_watch))
        for match in matchList:
            if type(match) == str:
                channel_title.append(match)
        return channel_title

    # def raw_find_links(self,translation):
    def raw_find_times(self):
        regex0 = r"<\/a><br><a href=.*?<.*?<.*?>.*?<\/div>"
        regex1 = [r"<\/a><br><a href=.*?<.*?<.*?>([A-Z][a-z]{2,3}\s\d\d?.*?)<\/div>", '%b %d %Y %I:%M:%S %p']
        regex2 = [r"<\/a><br><a href=.*?<.*?<.*?>(\d\d?\s[A-Z][a-z]{2,3}.*?)<\/div>", '%d %b %Y %H:%M:%S']
        pattern0 = re.compile(regex0)
        pattern1 = re.compile(regex1[0])
        pattern2 = re.compile(regex2[0])
        raw_matchlist = pattern0.findall(str(self.html_watch))
        raw_matchlist_element = raw_matchlist[0]
        # return raw_matchlist_element
        is_regex1 = True
        testlist = pattern1.findall(str(raw_matchlist_element))
        # return matchList
        if len(testlist) != 0:
            matchList = pattern1.findall(str(raw_matchlist))
            times1 = []
            for time in matchList:
                if type(time) != str:
                    time = ' '.join(time)
                time = time.replace(',', '')
                time = time.replace('Sept', 'Sep')
                times1.append(time)
                # return times1
            times2 = []
            for i in times1:
                i = re.sub(r'.{3}$', 'UTC', i)
                i = i.split()
                tz = ''.join(i[-1])
                timez = ' '.join(i[:-1])
                # return tz
                if is_regex1:
                    date_time_time = datetime.datetime.strptime(timez, regex1[1])
                else:
                    date_time_time = datetime.datetime.strptime(timez, regex2[1])
                times2.append(pytz.timezone(tz).localize(date_time_time))
            # return is_regex1
            return times2
        else:
            is_regex1 = False
            matchList = pattern2.findall(str(raw_matchlist))
            times1 = []
            for time in matchList:
                if type(time) != str:
                    time = ' '.join(time)
                time = time.replace(',', '')
                time = time.replace('Sept', 'Sep')
                times1.append(time)
                # return times1
            times2 = []
            for i in times1:
                i = re.sub(r'.{3}$', 'UTC', i)
                i = i.split()
                tz = ''.join(i[-1])
                timez = ' '.join(i[:-1])
                # return tz
                if is_regex1:
                    date_time_time = datetime.datetime.strptime(timez, regex1[1])
                else:
                    date_time_time = datetime.datetime.strptime(timez, regex2[1])
                times2.append(pytz.timezone(tz).localize(date_time_time))
            # return is_regex1
            return times2

    # def _find_times(self):
    #     """
    #     Find and format times within the HTML file.
    #
    #     Returns
    #     -------
    #     times : List[str]
    #         e.g. "19 Feb 2013, 11:56:19 UTC Tue"
    #     """
    #     # Format all matched dates
    #     times = [
    #         datetime_obj.strftime("%d %b %Y, %H:%M:%S UTC %a")
    #         for datetime_obj in self._find_times_datetime()
    #     ]
    #     return times

    def search_history(self):
        pattern1 = re.compile(r"""Searched for\xa0<a href=\"(.*?\?search_query=.*?)\"\>(.*?)<\/a><br>(.*?)<""")
        raw_data = pattern1.findall(HTML.html_search)
        search_list = []
        search_link_list = []
        time_list = []
        for i in raw_data:
            search_link_list.append(i[0])
            search_list.append(i[1])
            time_list.append(i[2])
        # return search_link_list
        df0 = pd.DataFrame(search_link_list)
        df1 = pd.DataFrame(search_list)
        df2 = pd.DataFrame(time_list)
        df_searches = pd.concat([df1, df0, df2], axis=1)
        df_searches.columns = ['SEARCHES', 'SEARCHES_LINK', 'DATE_TIME']
        return df_searches

    def comment_history(self):
        try:
            # regex = r'(?<="\s+at\s+{yyyy}-{mm}-{dd}\s+{hh}:{mm}:{ss}\s+UTC\.\s+")\S+(?=")'
            # r"<a href=\".*\">[^<]*<\/a>\"([^\"]*)\"<br>"
            # r"<a href=\".*\">[^<]*<\/a>\"([^\"]*)\"<br>"
            pattern1 = re.compile(r"""<a href=['"].*?['"]>""")
            match_list1 = pattern1.findall(str(HTML.html_comment))
            pattern2 = re.compile(r"""at\s(.*?\s.[^\s]*).*?<br\/>(.*?)<\/li>""")
            match_list2 = pattern2.findall(str(HTML.html_comment))
            comments_list = []
            time_list = []
            for i in match_list2:
                time_list.append(i[0])
                comments_list.append(i[1])
            df1 = pd.DataFrame(comments_list)
            df2 = pd.DataFrame(time_list)
            df_comments = pd.concat([df1, df2], axis=1)
            df_comments.columns = ['COMMENTS', 'DATE_TIME']
            link = match_list1[-1][9:-2]
            return df_comments  # match_list1, match_list2
        except Exception:
            pass

    def like_history(self):
        df_likes = pd.read_csv(playlists_path + '/' + 'Liked videos.csv', encoding="utf_8_sig")
        # df = pd.DataFrame(f)
        df_likes.drop([0, 1], axis=0, inplace=True)
        df_likes.drop(df_likes.iloc[:, 2:], axis=1, inplace=True)
        df_likes.columns = ['liked_video_id', 'liked_time']
        df_likes.reset_index(inplace=True, drop=True)
        liked_video_url = []
        for i in df_likes['liked_video_id']:
            i = "https://www.youtube.com/watch?v=" + str(i)
            liked_video_url.append(i)
        df_likes['liked_video_url'] = liked_video_url
        liked_time = []
        for i in df_likes['liked_time']:
            i = i[:-4]
            liked_time.append(i)
        df_likes['liked_time'] = liked_time
        df_likes = df_likes.reindex(columns=["liked_video_id", 'liked_video_url', "liked_time"])
        return df_likes

    def dataframe_heatmap(self, day):
        times = self.raw_find_times()
        watchtimes = [0 for t in range(12)]

        for time in times:
            if time.weekday() == day:
                watchtimes[(time.hour // 2) - time.hour % 2] += 1

        return watchtimes

# print((HTML().html_watch))
# print(len((HTML().find_video_id())))
# print(HTML().raw_find_times())
# print(HTML().search_history())


# youtube api
with open('key.txt', "r", encoding="utf-8") as f:
    api_key = f.read()
pfx =  "https://www.googleapis.com/youtube/v3/"
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
opener = build_opener()
opener.addheaders = [('User-Agent', user_agent)]
def call_gdata(api, qs):
    """Make a request to the youtube api."""
    qs = dict(qs)
    qs['key'] = api_key
    url = pfx + api + '?' + urlencode(qs, safe = ',')
    url = url.replace('%2C',',')
    try:
        data = opener.open(url).read().decode('utf-8')
    except HTTPError as e:
        try:
            errdata = e.text.read().decode()
            error = json.loads(errdata)['error']['message']
            errmsg = 'Youtube Error %d: %s' % (e.getcode(), error)
        except:
            errmsg = str(e)
    # return (data)
    dataz = json.loads(data)
    return url,dataz


image_dir = os.path.join(os.getcwd(),"Images/")
logo = os.path.join(image_dir,"LOGO.png")
csv_dir = os.getcwd()+'/csv_file/'
if not os.path.exists(csv_dir):
    os.mkdir(csv_dir)


def time_format(str):
    num_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    str = str.replace('Sept', 'Sep')
    # print(i[0])
    # print(i[0] in num_list)
    if str[-5] == 'M' and str[0] not in num_list:
        str = str[:-4]
        date = datetime.datetime.strptime(str, "%b %d, %Y, %I:%M:%S %p")
        date_string = date.strftime("%Y-%m-%d %H:%M:%S")
        str = date_string

    elif str[-5] != 'M' and str[0] not in num_list:
        str = str[:-4]
        date = datetime.datetime.strptime(str, "%b %d %Y, %H:%M:%S")
        date_string = date.strftime("%Y-%m-%d %H:%M:%S")
        str = date_string

    elif str[-5] == 'M' and str[0] in num_list:
        str = str[:-4]
        date = datetime.datetime.strptime(str, "%d %b, %Y, %I:%M:%S %p")
        date_string = date.strftime("%Y-%m-%d %H:%M:%S")
        str = date_string

    elif str[-5] != 'M' and str[0] in num_list:
        str = str[:-4]
        date = datetime.datetime.strptime(str, "%d %b %Y, %H:%M:%S")
        date_string = date.strftime("%Y-%m-%d %H:%M:%S")
        str = date_string

    return str


### watch_rel
urls_id = HTML().find_video_id()
channel_link = HTML().find_channel_link()
channel_title = HTML().find_channel_title()
video_title = HTML().find_video_title()
date_time = HTML().find_date_time()

### heatmap_github
df_urls_id = pd.DataFrame(urls_id)
df_video_title = pd.DataFrame(video_title)
df_channel_link = pd.DataFrame(channel_link)
df_channel_title = pd.DataFrame(channel_title)
dftime = pd.DataFrame(date_time)
url_list = df_urls_id.iloc[:,0].tolist()
links_list = []
for i in url_list:
    i = 'https://www.youtube.com/watch?v='+i
    links_list.append(i)
df_urls_id['video_link'] = links_list
df_urls_id = df_urls_id.rename(columns={0: "video_id"})
# print(dfid)
dftime.columns =['watch_time']
time_list = []
for i in dftime['watch_time']:
    # print(i)
    i = time_format(i)
    time_list.append(i)
dftime['watch_time'] = time_list
# print(dftime)
# print(type(dftime['time']))
time_day_list = []
for i in dftime['watch_time']:
    match = re.match(r"\d{4}\-\d{2}\-\d{2}", i)
    i = match.group()
    time_day_list.append(i)
    # print(list)
    # print(i)
dftime['watch_time_day'] = time_day_list
df_new = pd.DataFrame(dftime.groupby("watch_time_day").size()).reset_index()
df_new.columns=['watch_time','values']
active_day = df_new['watch_time'].count()
# print(df_new['watch_time'].count())
watch_time = []
for i in df_new['watch_time']:
    watch_time.append(i)
# print(watch_time)
values = []
for i in df_new['values']:
    values.append(i)
# print(values)
ts = pd.Series(values, index=pd.DatetimeIndex(watch_time))
# print(ts)
plt.figure(figsize=(20,10))
calmap.yearplot(ts, cmap='YlGn', fillcolor='lightgrey',daylabels='MTWTFSS',dayticks=[0, 2, 4, 6],
                linewidth=2)
plt.savefig(os.path.join(image_dir,"heatmap.png"))


### BASIC
if(len(channel_link)==0):
    raise ValueError("Could not find any links. Please send the developer your takeout data, so the issue can be addressed")
df_searches = HTML().search_history()
for i,j in df_searches['DATE_TIME'].items():
    k = time_format(j)
    df_searches.loc[i,'DATE_TIME'] = k
df_searches_yr = df_searches[df_searches['DATE_TIME'].str.contains('2022')]
# print(df_searches)
# print(type(df_searches['SEARCHES']))
try:
    df_comments = HTML().comment_history()
except TypeError:
    all_links = ""
df_comments_yr = df_comments[df_comments['DATE_TIME'].str.contains('2022')]
# print(df_comments_yr)
try:
    df_likes = HTML().like_history()
except FileNotFoundError:
    df_likes = ""
# print(df_likes['liked_time'])
df_likes_yr = df_likes[df_likes['liked_time'].str.contains('2022')]

#
watched_video = len(urls_id)
searches = df_searches['SEARCHES'].count()
likes = df_likes['liked_video_id'].count()
comments = df_comments['COMMENTS'].count()

searches_yr = df_searches_yr['SEARCHES'].count()
likes_yr = df_likes_yr['liked_video_id'].count()
comments_yr = df_comments_yr['COMMENTS'].count()
active_total_day = str(active_day) + '/' + '365'
UpTime = '{:.2%}'.format(active_day/365)
vpd ='{:.2f}'.format(watched_video/365)

stat_list = [watched_video,searches,likes,comments,active_total_day,UpTime,vpd]
dfstat = pd.DataFrame(stat_list).T
dfstat.columns=['watched','searches','likes','comments','active_total_day','UpTime','video_watched_per_day']
stat_list_yr = [watched_video,searches_yr,likes_yr,comments_yr,active_total_day,UpTime,vpd]
dfstat_yr = pd.DataFrame(stat_list_yr).T
dfstat_yr.columns=['watched','searches','likes','comments','active_total_day','UpTime','video_watched_per_day']
# print(dfstat)

### TOP5_WATCH
url_sizes = df_urls_id.groupby("video_id").size()
sorted_watch = dict(url_sizes.sort_values(ascending=False))
df_sorted_watch = pd.DataFrame(sorted_watch,index =[0]).T
df_sorted_watch.reset_index(inplace=True)
df_sorted_watch.columns = ['video_id','watch_time']
# print(df_sorted_watch)
df_top5 = pd.DataFrame({'watch_time_rank':[0],'video_id':[0],'video_link':[0],'watch_times':[0]})
# print(df_top5)
for i in range(5):
    list_top5 = ['TOP'+str(i+1),df_sorted_watch.iloc[i,0],
                 'https://www.youtube.com/watch?v='+str(df_sorted_watch.iloc[i,0]),df_sorted_watch.iloc[i,1]]
    df_top5.loc[i,:] = list_top5
    # df.to_csv('watch_top5.csv', mode='a',encoding='utf_8_sig', header=True, index=True)
# print(df_top5)
df_top5.to_csv(csv_dir + 'TOP5_watch.csv', encoding='utf_8_sig', index = False)
# print(dftime)
dftime.columns=['watch_time','watch_time_day']

df = pd.concat([df_video_title,df_urls_id,df_channel_link,df_channel_title,dftime,df_searches,df_likes,df_comments],axis=1)
df.columns=['video_title','video_id','video_link','channel_link','df_channel_title','watch_time','time_day',
            'searches','searches_link','search_time','liked_video_id','liked_video_link','liked_time','comments',
            'comment_time']
df.drop(['time_day'],axis=1,inplace=True)
df_yr = pd.concat([df_video_title,df_urls_id,df_channel_link,df_channel_title,dftime,df_searches_yr,df_likes_yr,
                   df_comments_yr],axis=1)
df_yr.columns=['video_title','video_id','video_link','channel_link','channel_title','watch_time','time_day',
               'searches','searches_link','search_time','liked_video_id','liked_video_link','liked_time','comments',
               'comment_time']
df_yr.drop(['time_day'],axis=1,inplace=True)

## api requests
df_yr_dlc = pd.DataFrame({'publishedAt':0,'title':0,'categoryId':0,'defaultAudioLanguage':0,'duration':0,'licensedContent':0,
                          'viewCount':0, 'likeCount':0, 'commentCount':0,},index=[0])

ids = dict(df_yr['video_id'])
for i,j in ids.items():
    print(i)
    print(j)
    if i > 13:
        break
    else:
        query = {'id': j,
                'part': 'snippet,contentDetails,statistics'}
        catchinfo = call_gdata('videos', query)[1]
        for item in catchinfo.get('items', []):
                        s1 = item.get('snippet', {})
                        s1_names = ['publishedAt', 'title', 'categoryId', 'defaultAudioLanguage']  # 'tags','description'
                        s1_ = {key: value for key, value in s1.items() if key in s1_names}
                        for k in s1_names:
                            if s1.get(k) != None:
                                continue
                            else:
                                s1_[k] = 'N/A'
                        p1 = re.compile(r'zh.*')
                        p2 = re.compile(r'en.*')
                        if p1.search(s1_['defaultAudioLanguage']):
                            s1_['defaultAudioLanguage'] = 'cn'
                        elif p2.search(s1_['defaultAudioLanguage']):
                            s1_['defaultAudioLanguage'] = 'en'

                        s2 = item.get('contentDetails', {})
                        s2_names = ['duration', 'licensedContent']
                        s2_ = {key: value for key, value in s2.items() if key in s2_names}
                        s3 = item.get('statistics', {})
                        s3_names = ['viewCount', 'likeCount', 'commentCount']
                        s3_ = {key: value for key, value in s3.items() if key in s3_names}
                        for k in s3_names:
                            if s3.get(k) != None:
                                continue
                            else:
                                s3_[k] = 'N/A'
                        sz = {}
                        sz.update(s1_)
                        sz.update(s2_)
                        sz.update(s3_)
                        # dfz = pd.DataFrame(sz, index=[0])
                        # print(dfz)
                        dataz = list(sz.values())
                        # print(dataz)
                        df_yr_dlc.loc[i, :] = dataz


for i,j in df_yr_dlc['publishedAt'].items():
    j = re.sub(r'[a-z]|[A-Z]',' ',j)
    j = j.rstrip(' ')
    df_yr_dlc.loc[i,'publishedAt'] =j
for i,j in df_yr_dlc['duration'].items():
    hours_pattern = re.compile(r'(\d+)H')
    minutes_pattern = re.compile(r'(\d+)M')
    seconds_pattern = re.compile(r'(\d+)S')

    hours = hours_pattern.search(j)
    minutes = minutes_pattern.search(j)
    seconds = seconds_pattern.search(j)

    hours = int(hours.group(1)) if hours else 0
    minutes = int(minutes.group(1)) if minutes else 0
    seconds = int(seconds.group(1)) if seconds else 0

    s = f'{hours}:{minutes}:{seconds}'
    df_yr_dlc.loc[i,'duration'] = s

df_yr_dlc = df_yr_dlc.reindex(columns=['title','publishedAt','categoryId','duration','licensedContent',
                          'viewCount', 'likeCount', 'commentCount','defaultAudioLanguage'])
# print(df_yr_dlc)

df.to_csv(csv_dir+'info_total.csv',encoding='utf_8_sig',header = True,index=True)
df_yr.to_csv(csv_dir+'info_yr.csv',encoding='utf_8_sig',header = True,index=True)
df_yr_dlc.to_csv(csv_dir+'info_yr_dlc.csv',encoding='utf_8_sig',header = True,index=True)
dfstat.to_csv(csv_dir+'info_misc.csv',encoding='utf_8_sig',header = True,index=True)
dfstat_yr.to_csv(csv_dir+'info_misc_yr.csv',encoding='utf_8_sig',header = True,index=True)

### df_api_dlc
indict = {
    1:'Film & Animation',
    2:'Autos & Vehicles',
    10:'Music',
    15:'Pets & Animals',
    17:'Sports',
    18:'Short Movies',
    19:'Travel & Events',
    20:'Gaming',
    21:'Videoblogging',
    22:'People & Blogs',
    23:'Comedy',
    24:'Entertainment',
    25:'News & Politics',
    26:'Howto & Style',
    27:'Education',
    28:'Science & Technology',
    29:'Nonprofits & Activism',
    30:'Movies',
    31:'Anime / Animation',
    32:'Action / Adventure',
    33:'Classics',
    34:'Comedy',
    35:'Documentary',
    36:'Drama',
    37:'Family',
    38:'Foreign',
    39:'Horror',
    40:'Sci - Fi / Fantasy',
    41:'Thriller',
    42:'Shorts',
    43:'Shows',
    44:'Trailers'
    }
def id_name(id):
    switcher = indict
    return switcher.get(id)

## language
df_lang = pd.DataFrame(dict(df_yr_dlc['defaultAudioLanguage'].value_counts(ascending=False)),index =[0]).T
df_lang.reset_index(inplace=True)
df_lang.columns = ['language','lanCounts']
df_lang.drop(df_lang[df_lang['language']=='N/A'].index,inplace=True)
other = 0
if len(df_lang) < 3:
    df_lang = df_lang.sort_index().reset_index(drop=True)
    df_lang['lanCounts'] = df_lang['lanCounts'].apply(int)
else:
    for i,j in df_lang['lanCounts'].items():
        if i < 3:
            continue
        else:
          other += j
    df_lang.loc[3.5, :] = ['other', other]
    df_lang = df_lang.sort_index().reset_index(drop=True)
    df_lang['lanCounts'] = df_lang['lanCounts'].apply(int)
# print(df_lang)

### categoryName & ~watchTime/~watchTime_min
df_api_dlc = df_yr_dlc.copy(deep=False)
# if len(df_api_dlc['Unnamed: 0']):
#     df_api_dlc.drop(columns='Unnamed: 0',inplace=True)
df_api_dlc.insert(3,'categoryName',value ='NaN')
for i,j in df_api_dlc['categoryId'].items():
    k = id_name(int(j))
    df_api_dlc.loc[i,'categoryName'] = k


## categoryWatchTimes
# insert a new columns 'duration in seconds'
df_api_dlc.insert(5,'durations',value ='NaN')
for i,j in df_api_dlc['duration'].items():
    j = str(j)
    p = re.compile(r'(\d+):(\d+):(\d+)')
    s = p.search(j)
    h = int(s.group(1))
    m = int(s.group(2))
    s = int(s.group(3))
    total = h*60 + m*60 + s
    df_api_dlc.loc[i,'durations'] = total
df_catSize= pd.DataFrame(df_api_dlc["categoryName"].value_counts())
df_catSize.reset_index(inplace=True)
df_catSize.columns=['categoryName','watchTimes1']
# print(df_api_dlc['durations'])

## categoryWatchTime_min
dict_catDu = {}
for i in indict.keys():
    if i==0:
        continue
    dfid = df_api_dlc[df_api_dlc['categoryId'] == str(i)]
    # print(dfid['durations'])
    dict_catDu[id_name(i)] = dfid['durations'].sum() * 0.34
df_catDu = pd.DataFrame(dict_catDu,index=[0]).T
df_catDu.reset_index(inplace=True)
print(df_catDu)
df_catDu.columns=['categoryName','watchTime_min']
for i,j in df_catDu['watchTime_min'].items():
    df_catDu.iloc[i,1] = '{:.2f}'.format(j/60)
    df_catDu.iloc[i, 1] = float(df_catDu.iloc[i, 1])
df_catDu.sort_values(['watchTime_min'],ascending=False,inplace=True)
df_catDu.reset_index(inplace=True,drop=True)
cnt = 0
for i in df_catDu['watchTime_min']:
    if i:
        cnt += 1
if cnt > 3:
    list1 = []
    total = 0
    other = 0
    for j, k in df_catDu['watchTime_min'].items():
        if j < 3:
            list1.append(k)
            total += k
        else:
            list1.append(k)
            other += k
    total += other
    list1.insert(3, other)
    list2 = []
    for i, j in enumerate(list1):
        if type(j) != str:
            list2.append('{:.2f}'.format(list1[i] / total))
        else:
            list2.append(j)
    list2.pop(-1)
    df_catDu.insert(2, 'categoryRatio', value=list2)
elif cnt == 3:
    list1 = []
    total = 0
    for j, k in df['watchTime_min'].items():
            list1.append(k)
            total += k
            continue
    list2 = ['{:.2f}'.format(list1[0] / total), '{:.2f}'.format(list1[1] / total), '{:.2f}'.format(list1[2] / total)]
    df_catDu.insert(2, 'categoryRatio', value=list2)
elif cnt == 2:
    list1 = []
    total = 0
    for j, k in df['watchTime_min'].items():
            list1.append(k)
            total += k
            continue
    list2 = ['{:.2f}'.format(list1[0] / total), '{:.2f}'.format(list1[1] / total)]
    df_catDu.insert(2, 'categoryRatio', value=list2)
elif cnt == 1:
    list1 = []
    total = 0
    for j, k in df['watchTime_min'].items():
            list1.append(k)
            total += k
            continue
    list2 = ['{:.2f}'.format(list1[0] / total)]
    df_catDu.insert(2, 'categoryRatio', value=list2)
print('-----------------------xxxxxxxxx-----------------------')
print(df_catDu)
df_cat = pd.concat([df_catSize,df_catDu],axis=1)

# ### channelWatchTimes
df_chnlSize = pd.DataFrame(df_yr["channel_title"].value_counts())
df_chnlSize.reset_index(inplace=True)
df_chnlSize.columns=['channelTitle','watchTimes2']
# print(df_chnlSize)
df_chnlSize.insert(2,'channelLink',value ='NaN')
for i,j in df_chnlSize['channelTitle'].items():
      dictz=dict(df_yr.loc[df_yr['channel_title']==j,'channel_link'])
      chnlLink = dictz.get(int(next(iter(dictz))))
      df_chnlSize.loc[i, 'channelLink'] = chnlLink
# print(df_chnlSize)
dfz = pd.concat([df_cat,df_chnlSize,df_lang],axis=1)
dfz = dfz.fillna('')
dfz.to_csv(csv_dir+'api_rep.csv',encoding='utf_8_sig')


english_stopwords = [
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "ours",
            "ourselves",
            "you",
            "you're",
            "you've",
            "you'll",
            "you'd",
            "your",
            "yours",
            "yourself",
            "yourselves",
            "he",
            "him",
            "his",
            "himself",
            "she",
            "she's",
            "her",
            "hers",
            "herself",
            "it",
            "it's",
            "its",
            "itself",
            "they",
            "them",
            "their",
            "theirs",
            "themselves",
            "what",
            "which",
            "who",
            "whom",
            "this",
            "that",
            "that'll",
            "these",
            "those",
            "am",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "having",
            "do",
            "does",
            "did",
            "doing",
            "a",
            "an",
            "the",
            "and",
            "but",
            "if",
            "or",
            "because",
            "as",
            "until",
            "while",
            "of",
            "at",
            "by",
            "for",
            "with",
            "about",
            "against",
            "between",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "to",
            "from",
            "up",
            "down",
            "in",
            "out",
            "on",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "any",
            "both",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "s",
            "t",
            "can",
            "will",
            "just",
            "don",
            "don't",
            "should",
            "should've",
            "now",
            "d",
            "ll",
            "m",
            "o",
            "re",
            "ve",
            "y",
            "ain",
            "aren",
            "aren't",
            "couldn",
            "couldn't",
            "didn",
            "didn't",
            "doesn",
            "doesn't",
            "hadn",
            "hadn't",
            "hasn",
            "hasn't",
            "haven",
            "haven't",
            "isn",
            "isn't",
            "ma",
            "mightn",
            "mightn't",
            "mustn",
            "mustn't",
            "needn",
            "needn't",
            "shan",
            "shan't",
            "shouldn",
            "shouldn't",
            "wasn",
            "wasn't",
            "weren",
            "weren't",
            "won",
            "won't",
            "wouldn",
            "wouldn't",
            'youtube',
            'www'
        ]

class Visualization:
    def heat_map_week(self):
        print("Generating Heat Map.....")
        html = HTML()
        Mon = html.dataframe_heatmap(0)
        Tue = html.dataframe_heatmap(1)
        Wed = html.dataframe_heatmap(2)
        Thu = html.dataframe_heatmap(3)
        Fri = html.dataframe_heatmap(4)
        Sat = html.dataframe_heatmap(5)
        Sun = html.dataframe_heatmap(6)
        df = np.vstack((Mon, Tue, Wed, Thu, Fri, Sat, Sun))

        Index = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        Cols = [
            "0AM to 2AM",
            "2AM to 4AM",
            "4AM to 6AM",
            "6AM to 8AM",
            "8AM to 10AM",
            "10AM to 12PM",
            "12PM to 2PM",
            "2PM to 4PM",
            "4PM to 6PM",
            "6PM to 8PM",
            "8PM to 10PM",
            "10PM to 12AM",
        ]
        plt.figure(figsize=(20, 5))
        sns.set_theme()
        f, ax = plt.subplots(figsize=(20, 5))
        sns.heatmap(df,
                    cmap = 'rocket_r',
                    annot=True,
                    linewidths=1.5,
                    fmt="d", ax=ax,
                    xticklabels=Cols,
                    yticklabels=Index)

        plt.title("What Time Do You Usually Watch Youtube Videos? (Your YTB Setting Time)",
                  fontsize=27,
                  color="steelblue",
                  fontweight="bold",
                  fontname="Arial")

        plt.annotate("                 The plot above is based on a total of %s videos you have watched"%(len(urls_id)),
                     (0, 0), (0, -23),
                     fontsize=20,
                     color="steelblue",
                     fontweight="bold",
                     fontname="Arial",
                     xycoords="axes fraction",
                     textcoords="offset points",
                     va="top")

        plt.savefig(os.path.join(image_dir,"week_heatmap.png"), dpi=400)
        plt.clf()


    def table(self):
        plt.figure(figsize=(21, 14))
        # plt.title(
        #     "Do You Still Remember?",
        #     fontsize=27,
        #     color="steelblue",
        #     fontweight="bold",
        #     fontname="Arial",
        # )
        plt.annotate(
            "First Watched Video: \n\n\nMost Watched Video:\n\n\nFirst Like"
            "d Video:\n\n\nFirst Commented Video:\n\n\nFirst Searched Words:",
            (0, 0),
            (-100, 777),
            fontsize=60,
            color="k",
            fontweight="bold",
            fontname="Arial",
            xycoords="axes fraction",
            textcoords="offset points",
            va="top",
        )
        plt.axis("off")
        plt.savefig(os.path.join(image_dir, "memory.png"), dpi=400)
        plt.clf()
    def word_cloud_watch(self):
            cm = HTML().find_video_title()
            list = []
            for i in cm:
                # print(i)
                list.append(i)
            # print(list)
            print("Generating Word Cloud.....")
            if len(list) == 0:
                unique_string = 'None'
                bg = np.array(Image.open(logo))
                found = False
                stop_words = ["porn", "nigga", "pussy"] + english_stopwords
                FONTS = ("LinBiolinum_R", "Arial", "arial", "DejaVuSansMono")
                for font in FONTS:  # this should fix an error where the font couldn't be found
                    try:
                        word_cloud_watch = WordCloud(
                            stopwords=stop_words,
                            mask=bg,
                            background_color="white",
                            colormap="Set2",
                            font_path=font,
                            max_words=380,
                            contour_width=2,
                            prefer_horizontal=1,
                        ).generate(unique_string)
                        found = True
                        break
                    except OSError:
                        continue
                if not found:
                    raise OSError("Could not find any of these fonts: %s" % (FONTS))
                del FONTS
                del found

                plt.figure()
                plt.imshow(word_cloud_watch)
                plt.axis("off")
                # plt.savefig("your_file_name"+".png", bbox_inches="tight")
                plt.title("You didn't watch any video this year",
                          fontsize=18,
                          color="steelblue",
                          fontweight="bold",
                          fontname="Comic Sans MS")

                plt.savefig(os.path.join(image_dir, "word_cloud_watch.png"), dpi=400)
                plt.clf()
            else:
                unique_string = (" ").join(list)
                bg = np.array(Image.open(logo))
                # import nltk.stopwords
                # stopwords.words("english")
                found = False
                stop_words = ["porn", "nigga", "pussy"] + english_stopwords
                FONTS = ("LinBiolinum_R", "Arial", "arial", "DejaVuSansMono")
                for font in FONTS:  # this should fix an error where the font couldn't be found
                    try:
                        word_cloud_watch = WordCloud(
                            stopwords=stop_words,
                            mask=bg,
                            background_color="white",
                            colormap="Set2",
                            font_path=font,
                            max_words=380,
                            contour_width=2,
                            prefer_horizontal=1,
                        ).generate(unique_string)
                    except OSError:
                        continue
                    else:
                        found = True
                        break
                if not found:
                    raise OSError("Could not find any of these fonts: %s" % (FONTS))
                del FONTS
                del found

                plt.figure()
                plt.imshow(word_cloud_watch)
                plt.axis("off")
                # plt.savefig("your_file_name"+".png", bbox_inches="tight")
                plt.title("What Do You Usually Watch on YouTube?",
                          fontsize=18,
                          color="steelblue",
                          fontweight="bold",
                          fontname="Comic Sans MS")

                plt.annotate("   WordCloud is based on a total of %s watched vedios" % (str(len(list))),
                             (0, 0), (-10, 10),
                             fontsize=13,
                             color="steelblue",
                             fontweight="bold",
                             fontname="Comic Sans MS",
                             xycoords="axes fraction",
                             textcoords="offset points",
                             va="top")

                plt.savefig(os.path.join(image_dir, "word_cloud_watch.png"), dpi=400)
                plt.clf()
    def word_cloud_search(self):
        print("Generating Word Cloud.....")
        list = df_searches_yr['SEARCHES']    #.tolist()
        # print(list)
        if len(list) == 0:
            unique_string = 'None'
            bg = np.array(Image.open(logo))
            # import nltk.stopwords
            # stopwords.words("english")
            stop_words = ["porn", "nigga", "pussy"] + english_stopwords
            found = False
            FONTS = ("LinBiolinum_R", "Arial", "arial", "DejaVuSansMono")
            for font in FONTS:  # this should fix an error where the font couldn't be found
                try:
                    word_cloud_search = WordCloud(
                        stopwords=stop_words,
                        mask=bg,
                        background_color="white",
                        colormap="Set2",
                        font_path=font,
                        max_words=380,
                        contour_width=2,
                        prefer_horizontal=1,
                    ).generate(unique_string)
                except OSError:
                    continue
                else:
                    found = True
                    break
            if not found:
                raise OSError("Could not find any of these fonts: %s" % (FONTS))
            del FONTS
            del found

            plt.figure()
            plt.imshow(word_cloud_search)
            plt.axis("off")
            # plt.savefig("your_file_name"+".png", bbox_inches="tight")
            plt.title("You didn't search any thing this yaer",
                      fontsize=18,
                      color="steelblue",
                      fontweight="bold",
                      fontname="Comic Sans MS")

            plt.savefig(os.path.join(image_dir, "word_cloud_search.png"), dpi=400)
            plt.clf()
        else:
            unique_string = (" ").join(list)
            bg = np.array(Image.open(logo))
            # import nltk.stopwords
            # stopwords.words("english")
            found=False
            stop_words = ["porn", "nigga", "pussy"] + english_stopwords
            FONTS=("LinBiolinum_R","Arial","arial","DejaVuSansMono")
            for font in FONTS:	#this should fix an error where the font couldn't be found
                try:
                    word_cloud_search = WordCloud(
                        stopwords= stop_words,
                        mask=bg,
                        background_color="white",
                        colormap="Set2",
                        font_path=font,
                        max_words=380,
                        contour_width=2,
                        prefer_horizontal=1,
                    ).generate(unique_string)
                except OSError:
                    continue
                else:
                    found=True
                    break
            if not found:
                raise OSError("Could not find any of these fonts: %s"%(FONTS))
            del FONTS
            del found

            plt.figure()
            plt.imshow(word_cloud_search)
            plt.axis("off")
            # plt.savefig("your_file_name"+".png", bbox_inches="tight")
            plt.title("What Do You Usually Search on YouTube?",
                      fontsize=18,
                      color="steelblue",
                      fontweight="bold",
                      fontname="Comic Sans MS")

            plt.annotate("   WordCloud is based on a total of %s search queries"%(len(list)),
                         (0, 0), (-10, 10),
                         fontsize=13,
                         color="steelblue",
                         fontweight="bold",
                         fontname="Comic Sans MS",
                         xycoords="axes fraction",
                         textcoords="offset points",
                         va="top")

            plt.savefig(os.path.join(image_dir,"word_cloud_search.png"), dpi=400)
            plt.clf()
    def word_cloud_comments(self):
        list = df_comments_yr['COMMENTS']
        print("Generating Word Cloud.....")
        if len(list) == 0:
            unique_string = 'None'
            bg = np.array(Image.open(logo))
            stop_words = ["porn", "nigga", "pussy"] + english_stopwords
            found = False
            FONTS = ("LinBiolinum_R", "Arial", "arial", "DejaVuSansMono")
            for font in FONTS:  # this should fix an error where the font couldn't be found
                try:
                    word_cloud_comments = WordCloud(
                        stopwords=stop_words,
                        mask=bg,
                        background_color="white",
                        colormap="Set2",
                        font_path=font,
                        max_words=380,
                        contour_width=2,
                        prefer_horizontal=1,
                    ).generate(unique_string)
                except OSError:
                    continue
                else:
                    found = True
                    break
            if not found:
                raise OSError("Could not find any of these fonts: %s" % (FONTS))
            del FONTS
            del found

            plt.figure()
            plt.imshow(word_cloud_comments)
            plt.axis("off")
            # plt.savefig("your_file_name"+".png", bbox_inches="tight")
            plt.title("You didn't make any comment last year",
                      fontsize=18,
                      color="steelblue",
                      fontweight="bold",
                      fontname="Comic Sans MS")
            plt.savefig(os.path.join(image_dir, "word_cloud_comments.png"), dpi=400)
            plt.clf()
        else:
            unique_string = (" ").join(list)
            bg = np.array(Image.open(logo))
            found=False
            stop_words = ["porn", "nigga", "pussy"] + english_stopwords
            FONTS=("LinBiolinum_R","Arial","arial","DejaVuSansMono")
            for font in FONTS:	#this should fix an error where the font couldn't be found
                try:
                    word_cloud_comments = WordCloud(
                        stopwords=stop_words,
                        mask=bg,
                        background_color="white",
                        colormap="Set2",
                        font_path=font,
                        max_words=380,
                        contour_width=2,
                        prefer_horizontal=1,
                    ).generate(unique_string)
                except OSError:
                    continue
                else:
                    found=True
                    break
            if not found:
                raise OSError("Could not find any of these fonts: %s"%(FONTS))
            del FONTS
            del found

            plt.figure()
            plt.imshow(word_cloud_comments)
            plt.axis("off")
            # plt.savefig("your_file_name"+".png", bbox_inches="tight")
            plt.title("What Do You Usually Comments on YouTube?",
                      fontsize=18,
                      color="steelblue",
                      fontweight="bold",
                      fontname="Comic Sans MS")

            plt.annotate("   WordCloud is based on a total of %s comments"%(str(len(list))),
                         (0, 0), (-10, 10),
                         fontsize=13,
                         color="steelblue",
                         fontweight="bold",
                         fontname="Comic Sans MS",
                         xycoords="axes fraction",
                         textcoords="offset points",
                         va="top")

            plt.savefig(os.path.join(image_dir,"word_cloud_comments.png"), dpi=400)
            plt.clf()

    ### WSLC
    def bar1(self):
        print("Generating Bar Plot.....")
        plt.figure(figsize=(14, 7))
        sns.set(style="white", font_scale=1.5)
        splot = sns.barplot(
            x=[
                len(urls_id),
                searches_yr,
                likes_yr,
                comments_yr,
            ],
            y=["Watch", "Search",'Like', "Comment"],
            palette='vlag',
        )
        for p in splot.patches:
            width = p.get_width()
            splot.text(
                width,
                p.get_y() + p.get_height() / 2 + 0.1,
                "{:1.0f}".format(width),
                ha="left",
            )
        splot.grid(False)
        plt.title("Breakdown of Your Activity on Youtube",
                  fontsize=24,
                  color="steelblue",
                  fontweight="bold",
                  fontname="Comic Sans MS")
        plt.savefig(os.path.join(image_dir,"bar1.png"), dpi=400)
        plt.clf()
    ### TOP5
    def bar2(self):
        print("Generating Bar Plot.....")
        sns.set(style="white", font_scale=1.5,color_codes=True)
        data = [df_top5.iloc[0,3],df_top5.iloc[1,3],df_top5.iloc[2,3],df_top5.iloc[3,3],df_top5.iloc[4,3]]
        pal = sns.color_palette('YlOrBr', len(data))
        rank = np.array(data).argsort().argsort()
        plt.figure(figsize=(14, 7))
        splot = sns.barplot(
            x=[
                df_top5.iloc[0,3],
                df_top5.iloc[1,3],
                df_top5.iloc[2,3],
                df_top5.iloc[3,3],
                df_top5.iloc[4,3]
            ],
            y=["#1","#2",'#3',"#4",'#5'],
            palette=np.array(pal)[rank],
        )
        for p in splot.patches:
            width = p.get_width()
            splot.text(
                width,
                p.get_y() + p.get_height() / 2 + 0.1,
                "{:1.0f}".format(width),
                ha="left",
            )
        splot.grid(False)
        plt.title("Most Watched Videos This Year",
                  fontsize=24,
                  color="steelblue",
                  fontweight="bold",
                  fontname="Comic Sans MS")
        # plt.annotate('test',
        #              (0, 0), (120, 50),
        #              fontsize=54,
        #              color="teal",
        #              fontweight="bold",
        #              fontname="Arial",
        #              xycoords="axes fraction",
        #              textcoords="offset points",
        #              va="top")
        plt.savefig(os.path.join(image_dir,"bar2.png"), dpi=400)
        plt.clf()
    ## Category
    def bar3(self):
        print("Generating Bar Plot.....")
        sns.set(style="white", color_codes=True,font_scale=1.5)
        data = [dfz.iloc[0,1], dfz.iloc[1,1], dfz.iloc[2,1], dfz.iloc[3,1], dfz.iloc[4,1]]
        pal = sns.color_palette("RdPu", len(data))
        rank = np.array(data).argsort().argsort()
        plt.figure(figsize=(14, 7))
        splot = sns.barplot(
            x=[
                dfz.iloc[0,0],
                dfz.iloc[1,0],
                dfz.iloc[2,0],
                dfz.iloc[3,0],
                dfz.iloc[4,0]
            ],
            y=[dfz.iloc[0,1],dfz.iloc[1,1],dfz.iloc[2,1],dfz.iloc[3,1],dfz.iloc[4,1]],
            palette=np.array(pal)[rank],
        )
        for p in splot.patches:
            heighth = p.get_height()+dfz.iloc[0,1]/20
            splot.text(
                p.get_x() + p.get_width() / 2-0.07,
                heighth,
                "{:1.0f}".format(heighth),
                va="top",
            )
        splot.grid(False)
        plt.title("TOP5 Categories You Watched This Year",
                  fontsize=24,
                  color="steelblue",
                  fontweight="bold",
                  fontname="Comic Sans MS")
        plt.savefig(os.path.join(image_dir,"bar3.png"), dpi=400)
        plt.clf()
    ## Channel
    def bar4(self):
        sns.set(style="white", font="SimSun", color_codes=True,font_scale=1.5)
        data = [dfz.iloc[0,-4], dfz.iloc[1,-4], dfz.iloc[2,-4], dfz.iloc[3,-4], dfz.iloc[4,-4]]
        pal = sns.color_palette("GnBu", len(data))
        rank = np.array(data).argsort().argsort()
        print("Generating Bar Plot.....")
        plt.figure(figsize=(14, 7))
        splot = sns.barplot(
            x=[
                dfz.iloc[0,-5],
                dfz.iloc[1,-5],
                dfz.iloc[2,-5],
                dfz.iloc[3,-5],
                dfz.iloc[4,-5]
            ],
            y=[dfz.iloc[0,-4],dfz.iloc[1,-4],dfz.iloc[2,-4],dfz.iloc[3,-4],dfz.iloc[4,-4]],
            palette=np.array(pal)[rank]
        )
        for p in splot.patches:
            heighth = p.get_height()+dfz.iloc[0,-4]/20
            splot.text(
                p.get_x() + p.get_width() / 2-0.07 ,
                heighth,
                "{:1.0f}".format(heighth),
                va="top",
            )
        splot.grid(False)
        plt.title("Most Watched Videos This Year",
                  fontsize=24,
                  color="steelblue",
                  fontweight="bold",
                  fontname="Comic Sans MS")
        # plt.annotate('test',
        #              (0, 0), (120, 50),
        #              fontsize=54,
        #              color="teal",
        #              fontweight="bold",
        #              fontname="Arial",
        #              xycoords="axes fraction",
        #              textcoords="offset points",
        #              va="top")
        plt.savefig(os.path.join(image_dir,"bar4.png"), dpi=400)
        plt.clf()

    def score(self):
        print("Calculating Your Activity Score.....")
        colors = ["#e63946", "#06d6a0"]
        score_value = round(
            math.log(
                (
                    len(channel_link[0])
                    + searches_yr * 2
                    + likes_yr * 3
                    + comments_yr * 4
                )
                / 9,
                1.12,
            ),
            1,
        )
        x_0 = [1, 0, 0, 0]
        pl.pie([100 - score_value, score_value], autopct="%1.1f%%", startangle=90, colors=colors, pctdistance=10)
        plt.pie(x_0, radius=0.7, colors="w")
        plt.axis("equal")

        plt.title("Your YouTube Activity Score",
                  fontsize=21,
                  color="steelblue",
                  fontweight="bold",
                  fontname="Arial")

        plt.annotate(score_value,
                     (0, 0), (123, 154),
                     fontsize=54,
                     color="teal",
                     fontweight="bold",
                     fontname="Arial",
                     xycoords="axes fraction",
                     textcoords="offset points",
                     va="top")
        plt.annotate('watch:search:like:comments=1:2:3:4',
                     (0, 0), (0, 0),
                     fontsize=12,
                     color="orange",
                     fontweight="regular",
                     fontname="Arial",
                     xycoords="axes fraction",
                     textcoords="offset points",
                     va="top")

        plt.savefig(os.path.join(image_dir,"score.png"), dpi=400)
        plt.clf()
    def language(self):
        print("Calculating Your Favorite Video's Language.....")
        colors = ["#ffc300", "#2ec4b6",'#d90368','#a5a58d']
        cnt = 0
        for i in dfz['lanCounts']:
            if i:
                cnt += 1
        value1 = int(dfz.iloc[0,-1])
        value2 = int(dfz.iloc[1,-1])
        if cnt > 3:
            value3 = int(dfz.iloc[2, -1])
            value4 = int(dfz.iloc[3, -1])
            v_t = value1 + value2 + value3 + value4
            v1 = value1 / v_t
            v2 = value2 / v_t
            v3 = value3 / v_t
            v4 = value4 / v_t
            x_0 = [1, 0, 0, 0]
            pl.pie([v1, v2, v3, v4], autopct="%.1f", startangle=90, colors=colors, pctdistance=5)
            plt.pie(x_0, radius=0.7, colors="w")
            plt.axis("equal")

            plt.title("Your Favorite Videos Language",
                    fontsize=21,
                    color="steelblue",
                    fontweight="bold",
                    fontname="Arial")
            def pcntg(data):
                data_format = '{:.2%}'.format(data)
                return data_format

            v11 = dfz.iloc[0, -2] + ':'
            v12 = pcntg(v1)
            v21 = dfz.iloc[1, -2] + ':'
            v22 = pcntg(v2)
            v31 = dfz.iloc[2, -2] + ':'
            v32 = pcntg(v3)
            v41 = dfz.iloc[3, -2] + ':'
            v42 = pcntg(v4)
            plt.annotate(v11,
                        (0, 0), (330, 260),
                        fontsize=24,
                        color="#ffc300",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v12,
                        (0, 0), (370, 260),
                        fontsize=24,
                        color="#ffc300",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v21,
                        (0, 0), (330, 230),
                        fontsize=24,
                        color="#2ec4b6",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v22,
                        (0, 0), (370, 230),
                        fontsize=24,
                        color="#2ec4b6",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v31,
                        (0, 0), (330, 200),
                        fontsize=24,
                        color='#d90368',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v32,
                        (0, 0), (370, 200),
                        fontsize=24,
                        color='#d90368',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v41,
                        (0, 0), (330, 170),
                        fontsize=24,
                        color='#a5a58d',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v42,
                        (0, 0), (400, 170),
                        fontsize=24,
                        color='#a5a58d',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.savefig(os.path.join(image_dir, "language.png"), dpi=400)
            plt.clf()
        elif cnt == 3 :
            value3 = int(dfz.iloc[2, -1])
            v_t = value1 + value2 + value3
            v1 = value1 / v_t
            v2 = value2 / v_t
            v3 = value3 / v_t
            x_0 = [1, 0, 0, 0]
            pl.pie([v1, v2, v3], autopct="%.1f", startangle=90, colors=["#ffc300", "#2ec4b6",'#d90368'], pctdistance=5)
            plt.pie(x_0, radius=0.7, colors="w")
            plt.axis("equal")

            plt.title("Your Favorite Videos Language",
                        fontsize=21,
                        color="steelblue",
                        fontweight="bold",
                          fontname="Arial")


            def pcntg(data):
                    data_format = '{:.2%}'.format(data)
                    return data_format

            v11 = dfz.iloc[0, -2] + ':'
            v12 = pcntg(v1)
            v21 = dfz.iloc[1, -2] + ':'
            v22 = pcntg(v2)
            v31 = dfz.iloc[2, -2] + ':'
            v32 = pcntg(v3)
            plt.annotate(v11,
                        (0, 0), (330, 260),
                        fontsize=24,
                        color="#ffc300",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v12,
                        (0, 0), (370, 260),
                        fontsize=24,
                        color="#ffc300",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v21,
                        (0, 0), (330, 230),
                        fontsize=24,
                        color="#2ec4b6",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v22,
                        (0, 0), (370, 230),
                        fontsize=24,
                        color="#2ec4b6",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v31,
                        (0, 0), (330, 210),
                        fontsize=24,
                        color='#d90368',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v32,
                        (0, 0), (370, 210),
                        fontsize=24,
                        color='#d90368',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.savefig(os.path.join(image_dir, "language.png"), dpi=400)
            plt.clf()
        else:
            v_t = value1 + value2
            v1 = value1 / v_t
            v2 = value2 / v_t
            x_0 = [1, 0, 0, 0]
            pl.pie([v1, v2], autopct="%.1f", startangle=90, colors=["#ffc300", "#2ec4b6"], pctdistance=5)
            plt.pie(x_0, radius=0.7, colors="w")
            plt.axis("equal")

            plt.title("Your Favorite Videos Language",
                      fontsize=21,
                      color="steelblue",
                      fontweight="bold",
                      fontname="Arial")


            def pcntg(data):
                data_format = '{:.2%}'.format(data)
                return data_format


            v11 = dfz.iloc[0, -2] + ':'
            v12 = pcntg(v1)
            v21 = dfz.iloc[1, -2] + ':'
            v22 = pcntg(v2)

            plt.annotate(v11,
                         (0, 0), (330, 260),
                         fontsize=24,
                         color="#ffc300",
                         fontweight="regular",
                         fontname="Arial",
                         xycoords="axes fraction",
                         textcoords="offset points",
                         va="top")
            plt.annotate(v12,
                         (0, 0), (370, 260),
                         fontsize=24,
                         color="#ffc300",
                         fontweight="regular",
                         fontname="Arial",
                         xycoords="axes fraction",
                         textcoords="offset points",
                         va="top")
            plt.annotate(v21,
                         (0, 0), (330, 230),
                         fontsize=24,
                         color="#2ec4b6",
                         fontweight="regular",
                         fontname="Arial",
                         xycoords="axes fraction",
                         textcoords="offset points",
                         va="top")
            plt.annotate(v22,
                         (0, 0), (370, 230),
                         fontsize=24,
                         color="#2ec4b6",
                         fontweight="regular",
                         fontname="Arial",
                         xycoords="axes fraction",
                         textcoords="offset points",
                         va="top")
            plt.savefig(os.path.join(image_dir, "language.png"), dpi=400)
            plt.clf()
    def categoryRatio(self):
        print("Calculating Your Category Rank: .....")
        colors = ["#f07167", "#0081a7",'#00afb9','#fed9b7']
        cnt = 0
        for i in dfz['categoryRatio']:
            if i:
                cnt += 1
        value1 = float(dfz.iloc[0,4])
        value2 = float(dfz.iloc[1,4])
        if cnt > 3:
            value3 = float(dfz.iloc[2, 4])
            value4 = float(dfz.iloc[3, 4])
            x_0 = [1, 0, 0, 0]
            pl.pie([value1, value2, value3, value4], autopct="%.1f", startangle=90, colors=colors, pctdistance=5)
            plt.pie(x_0, radius=0.7, colors="w")
            plt.axis("equal")

            plt.title("Your Favorite Videos Language",
                    fontsize=21,
                    color="steelblue",
                    fontweight="bold",
                    fontname="Arial")
            def pcntg(data):
                data_format = '{:.2%}'.format(data)
                return data_format

            v11 = dfz.iloc[0, 2] + ':'
            v12 = pcntg(value1)
            v21 = dfz.iloc[1, 2] + ':'
            v22 = pcntg(value2)
            v31 = dfz.iloc[2, 2] + ':'
            v32 = pcntg(value3)
            v41 = 'other:'
            v42 = pcntg(value4)
            plt.annotate(v11,
                        (0, 0), (-30, 360),
                        fontsize=24,
                        color="#f07167",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v12,
                        (0, 0), (220, 360),
                        fontsize=24,
                        color="#f07167",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v21,
                        (0, 0), (-30, 330),
                        fontsize=24,
                        color="#0081a7",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v22,
                        (0, 0), (220, 330),
                        fontsize=24,
                        color="#0081a7",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v31,
                        (0, 0), (-30, 300),
                        fontsize=24,
                        color='#00afb9',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v32,
                        (0, 0), (220, 300),
                        fontsize=24,
                        color='#00afb9',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v41,
                        (0, 0), (-30, 270),
                        fontsize=24,
                        color='#fed9b7',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v42,
                        (0, 0), (220, 270),
                        fontsize=24,
                        color='#fed9b7',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.savefig(os.path.join(image_dir, "categoryRatio.png"), dpi=400)
            plt.clf()
        elif cnt == 3 :
            value3 = float(dfz.iloc[2, 4])
            x_0 = [1, 0, 0, 0]
            pl.pie([value1, value2, value3], autopct="%.1f", startangle=90, colors=["#f07167", "#0081a7",'#00afb9'], pctdistance=5)
            plt.pie(x_0, radius=0.7, colors="w")
            plt.axis("equal")

            plt.title("Your Favorite Videos Language",
                        fontsize=21,
                        color="steelblue",
                        fontweight="bold",
                          fontname="Arial")

            def pcntg(data):
                    data_format = '{:.2%}'.format(data)
                    return data_format

            v11 = dfz.iloc[0, 2] + ':'
            v12 = pcntg(value1)
            v21 = dfz.iloc[1, 2] + ':'
            v22 = pcntg(value2)
            v31 = dfz.iloc[2, 2] + ':'
            v32 = pcntg(value3)
            plt.annotate(v11,
                        (0, 0), (-30, 360),
                        fontsize=24,
                        color="#f07167",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v12,
                        (0, 0), (220, 360),
                        fontsize=24,
                        color="#f07167",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v21,
                        (0, 0), (-30, 330),
                        fontsize=24,
                        color="#0081a7",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v22,
                        (0, 0), (220, 330),
                        fontsize=24,
                        color="#0081a7",
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v31,
                        (0, 0), (-30, 270),
                        fontsize=24,
                        color='#00afb9',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.annotate(v32,
                        (0, 0), (220, 270),
                        fontsize=24,
                        color='#00afb9',
                        fontweight="regular",
                        fontname="Arial",
                        xycoords="axes fraction",
                        textcoords="offset points",
                        va="top")
            plt.savefig(os.path.join(image_dir, "categoryRatio.png"), dpi=400)
            plt.clf()
        else:
            x_0 = [1, 0, 0, 0]
            pl.pie([value1, value2], autopct="%.1f", startangle=90, colors=["#f07167", "#0081a7"], pctdistance=5)
            plt.pie(x_0, radius=0.7, colors="w")
            plt.axis("equal")

            plt.title("Your Favorite Videos Language",
                      fontsize=21,
                      color="steelblue",
                      fontweight="bold",
                      fontname="Arial")

            def pcntg(data):
                data_format = '{:.2%}'.format(data)
                return data_format

            v11 = dfz.iloc[0, 2] + ':'
            v12 = pcntg(value1)
            v21 = dfz.iloc[1, 2] + ':'
            v22 = pcntg(value2)

            plt.annotate(v11,
                         (0, 0), (-30, 360),
                         fontsize=24,
                         color="#f07167",
                         fontweight="regular",
                         fontname="Arial",
                         xycoords="axes fraction",
                         textcoords="offset points",
                         va="top")
            plt.annotate(v12,
                         (0, 0), (220, 360),
                         fontsize=24,
                         color="#f07167",
                         fontweight="regular",
                         fontname="Arial",
                         xycoords="axes fraction",
                         textcoords="offset points",
                         va="top")
            plt.annotate(v21,
                         (0, 0), (-30, 330),
                         fontsize=24,
                         color="#0081a7",
                         fontweight="regular",
                         fontname="Arial",
                         xycoords="axes fraction",
                         textcoords="offset points",
                         va="top")
            plt.annotate(v22,
                         (0, 0), (220, 330),
                         fontsize=24,
                         color="#0081a7",
                         fontweight="regular",
                         fontname="Arial",
                         xycoords="axes fraction",
                         textcoords="offset points",
                         va="top")
            plt.savefig(os.path.join(image_dir, "categoryRatio.png"), dpi=400)
            plt.clf()




    def gen_pdf(self):
        print("Combining Images into PDF.....")
        path0 = os.path.join(image_dir, "heatmap.png")
        path1 = os.path.join(image_dir, "week_heatmap.png")
        path2 = os.path.join(image_dir, "memory.png")
        path3 = os.path.join(image_dir, "word_cloud_watch.png")
        path4 = os.path.join(image_dir, "word_cloud_search.png")
        path5 = os.path.join(image_dir, "word_cloud_comments.png")
        path6 = os.path.join(image_dir, "bar1.png")
        path7 = os.path.join(image_dir, "bar2.png")
        path8 = os.path.join(image_dir, "bar3.png")
        path9 = os.path.join(image_dir, "bar4.png")
        path10 = os.path.join(image_dir, "score.png")
        path11 = os.path.join(image_dir, "red.png")
        path12 = os.path.join(image_dir, "language.png")
        path13 = os.path.join(image_dir, "categoryRatio.png")
        pdf = PdfFileWriter()

        # Using ReportLab Canvas to insert image into PDF
        img_temp = BytesIO()
        img_doc = canvas.Canvas(img_temp, pagesize=(2400, 4900))

        # heat map x, y - start position
        img_doc.drawImage(path0, -100, 3980, width=2400, height=1000)
        img_doc.drawImage(path1, 100, 3510, width=2400, height=650)
        # word_cloud
        img_doc.drawImage(path3, -25, 2690, width=780, height=778)
        img_doc.drawImage(path4, 755, 2690, width=780, height=778)
        img_doc.drawImage(path5, 1535, 2690, width=780, height=778)
        # memory
        img_doc.drawImage(path2, 1450, 2080, width=600, height=585)
        # score
        img_doc.drawImage(path10, 1500, -10, width=894, height=672)
        # bar
        img_doc.drawImage(path6, 0, 0, width=1400, height=680)
        img_doc.drawImage(path7, 0, 2030, width=1400, height=680)
        img_doc.drawImage(path8, -30, 1350, width=1200, height=680)
        img_doc.drawImage(path9, 1200, 1350, width=1200, height=680)
        # logo
        img_doc.drawImage(logo, 99, 4780, width=110, height=80)
        # red square
        img_doc.drawImage(path11, inch * 29.3, inch * 35.35, width=100, height=45)
        img_doc.drawImage(path11, inch * 29.3, inch * 33.79, width=100, height=45)
        img_doc.drawImage(path11, inch * 29.3, inch * 32.24, width=100, height=45)
        img_doc.drawImage(path11, inch * 29.3, inch * 30.70, width=100, height=45)
        img_doc.drawImage(path11, inch * 29.3, inch * 29.15, width=100, height=45)
        # language
        img_doc.drawImage(path12, 1250, 670, width=1300, height=680)
        # categoryRatio
        img_doc.drawImage(path13, 0, 670, width=1300, height=680)
        # draw four lines, x,y,width,height
        img_doc.rect(0.83 * inch, 64.6 * inch, 31.0 * inch, 0.04 * inch, fill=1)
        img_doc.rect(0.83 * inch, 48.1 * inch, 31.0 * inch, 0.04 * inch, fill=1)
        img_doc.rect(0.83 * inch, 37.8 * inch, 31.0 * inch, 0.04 * inch, fill=1)
        img_doc.rect(0.83 * inch, 28 * inch, 31.0 * inch, 0.04 * inch, fill=1)
        img_doc.rect(0.83 * inch, 18.5 * inch, 31.0 * inch, 0.04 * inch, fill=1)
        img_doc.rect(0.83 * inch, 9.5 * inch, 31.0 * inch, 0.04 * inch, fill=1)
        # title
        img_doc.setFont("Helvetica-Bold", 82)
        img_doc.drawString(
            212, 4780, "Personal YouTube Usage Report",
        )


        # first watch
        # print("First watched video: " + str(dfid.iloc[-1,1]))
        body_style = ParagraphStyle("Body", fontSize=31)

        items1 = []
        link1 = "<link href=''>%s</link>"%(str(df_top5.iloc[0,2]))
        items1.append(Paragraph(link1, body_style))
        f1 = Frame(inch*3, inch * 34.09, inch*20, inch*2)
        f1.addFromList(items1, img_doc)
        items11 = []
        link11 = "<link href='%s'>PLAY</link>" % (str(df_urls_id.iloc[-1,1]))
        items11.append(Paragraph(link11, body_style))
        f11 = Frame(inch * 29.35, inch * 34.09, inch * 12, inch * 2)
        f11.addFromList(items11, img_doc)

        # most watch
        items2 = []
        link2 = "<link href=''>%s</link>"%(df_top5.iloc[1,2])
        items2.append(Paragraph(link2, body_style))
        f2 = Frame(inch * 3, inch * 32.54, inch * 20, inch * 2)
        f2.addFromList(items2, img_doc)
        items22 = []
        link22 = "<link href='%s'>PLAY</link>" % (df_top5.loc[0, 'video_link'])
        items22.append(Paragraph(link22, body_style))
        f22 = Frame(inch * 29.35, inch * 32.54, inch * 12, inch * 2)
        f22.addFromList(items22, img_doc)

        # first like
        # print("First like: " + like)
        if likes_yr == 0:
            items3 = []
            link3 = "<link href=''>%s</link>"%(str(df_top5.iloc[2,2]))
            items3.append(Paragraph(link3, body_style))
            f3 = Frame(inch * 3, inch * 31.07, inch * 20, inch * 2)
            f3.addFromList(items3, img_doc)
            items33 = []
            link33 = "404"
            items33.append(Paragraph(link33, body_style))
            f33 = Frame(inch * 29.6, inch * 31.07, inch * 12, inch * 2)
            f33.addFromList(items33, img_doc)
        else:
            items3 = []
            link3 = "<link href=''>%s</link>"%(str(df_top5.iloc[2,2]))
            items3.append(Paragraph(link3, body_style))
            f3 = Frame(inch * 3, inch * 31.07, inch * 20, inch * 2)
            f3.addFromList(items3, img_doc)
            items33 = []
            link33 = "<link href='%s'>PLAY</link>" % (str(df_likes_yr.iloc[-1,1]))
            items33.append(Paragraph(link33, body_style))
            f33 = Frame(inch * 29.35, inch * 31.07, inch * 12, inch * 2)
            f33.addFromList(items33, img_doc)

        # first comment
        # print("First Commented Video: " + link)
        if comments_yr == 0:
            items3 = []
            link3 = "<link href=''>%s</link>"%(str(df_top5.iloc[3,2]))
            items3.append(Paragraph(link3, body_style))
            f3 = Frame(inch * 3, inch * 29.43, inch * 20, inch * 2)
            f3.addFromList(items3, img_doc)
            items33 = []
            link33 = ' 404'
            items33.append(Paragraph(link33, body_style))
            f33 = Frame(inch * 29.6, inch * 29.43, inch * 12, inch * 2)
            f33.addFromList(items33, img_doc)
        else:
            items4 = []
            link4 = "<link href=''>%s</link>"%(str(df_top5.iloc[3,2]))
            items4.append(Paragraph(link4, body_style))
            f4 = Frame(inch * 3, inch * 29.43, inch * 20, inch * 2)
            f4.addFromList(items4, img_doc)
            items44 = []
            link44 = "<link href='%s'>PLAY</link>" % (str(df_comments_yr.iloc[-1,1]))
            items44.append(Paragraph(link44, body_style))
            f44 = Frame(inch * 29.35, inch * 29.43, inch * 12, inch * 2)
            f44.addFromList(items44, img_doc)

        # first search
        if comments_yr == 0:
            items3 = []
            link3 = "<link href=''>%s</link>"%(str(df_top5.iloc[4,2]))
            items3.append(Paragraph(link3, body_style))
            f3 = Frame(inch * 3, inch * 27.95, inch * 20, inch * 2)
            f3.addFromList(items3, img_doc)
            items33 = []
            link33 = '404'
            items33.append(Paragraph(link33, body_style))
            f33 = Frame(inch * 29.6, inch * 27.95, inch * 12, inch * 2)
            f33.addFromList(items33, img_doc)
        else:
            items5 = []
            link5 = "<link href=''>%s</link>"%(str(df_top5.iloc[4,2]))
            items5.append(Paragraph(link5, body_style))
            f5 = Frame(inch * 3, inch * 27.95, inch * 20, inch * 2)
            f5.addFromList(items5, img_doc)
            items55 = []
            link55 = "<link href='%s'>PLAY</link>" % (str(df_searches_yr.iloc[-1,1]))
            items55.append(Paragraph(link55, body_style))
            f55 = Frame(inch * 29.35, inch * 27.95, inch * 12, inch * 2)
            f55.addFromList(items55, img_doc)
        #
        # items01 = []
        # link11 = "<link href='%s'>PLAY</link>" % (str(df_urls_id.iloc[-1,1]))
        # items11.append(Paragraph(link11, body_style))
        # f11 = Frame(inch * 29.35, inch * 15.39, inch * 12, inch * 2)
        # f11.addFromList(items11, img_doc)

        img_doc.save()
        pdf.addPage(PdfFileReader(BytesIO(img_temp.getvalue())).getPage(0))
        with open("YouTube_Report.pdf","wb") as f:
            pdf.write(f)
        print("Congratulations! You have successfully created your personal YouTube report!")
        if sys.platform == "win32":
            os.startfile("YouTube_Report.pdf")
        elif sys.platform == "win64":
            os.startfile("YouTube_Report.pdf")
        elif sys.platform == "darwin":
            subprocess.call(["open", "YouTube_Report.pdf"])
        elif which("xdg-open") is not None:
            subprocess.call(["xdg-open", "YouTube_Report.pdf"])
        else:
            print("No opener found for your platform. Just open YouTube_Report.pdf.")

if __name__ == "__main__":
    visual = Visualization()
    visual.heat_map_week()
    visual.table()
    visual.word_cloud_watch()
    visual.word_cloud_search()
    visual.word_cloud_comments()
    visual.score()
    visual.bar1()
    visual.bar2()
    visual.bar3()
    visual.bar4()
    visual.language()
    visual.categoryRatio()
    visual.gen_pdf()


t2= datetime.datetime.now()
print("end >> {}".format(t2))
print("end >> {}".format(t2))
print("RUNTIME >> {}".format(t2-t1))
