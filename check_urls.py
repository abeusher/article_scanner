#!/usr/bin/env python3

import re
import requests
import sqlite3
import time
import sys
import csv
import html

conn = sqlite3.connect('news.db')
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS story (id INTEGER PRIMARY KEY, url TEXT, retrieved_utc INTEGER, html TEXT)")
conn.commit()

def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def get_page(url,story_id,refetch=False):
    c.execute("SELECT id FROM story WHERE id = ?",(story_id,))
    id = c.fetchone()
    if id and not refetch:
        print("Prefetch is false and already have url: {}".format(url))
        return
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    r = requests.get(url,headers=headers)
    retrieved_utc = int(time.time())
    if r.status_code == 200:
        try:
            c.execute("INSERT INTO story VALUES (?,?,?,?)",(story_id,url,retrieved_utc,r.content))
            conn.commit()
        except:
            sys.exit("Something went wrong with the sqlite3 insert")
        else:
            print("Successfully fetched url: {}".format(url))
    else:
        print("Issue fectching {}".format(url))
        return

def get_stories():
    lines = csv.reader([line.rstrip('\n') for line in open("data")])
    for idx,line in enumerate(lines):
        if idx == 0: continue # Skip header line
        story_id = line[0]
        url = line[3]
        get_page(url,story_id)

def scan_stories():
    SAMPLE_WIDTH = 150
    terms = [line.rstrip('\n') for line in open("terms") if len(line) > 2]
    print (terms)
    c.execute("SELECT id, url, html FROM story")
    stories = c.fetchall()
    for story in stories:
        id = story[0]
        url = story[1]
        html_text = cleanhtml(html.unescape(story[2].decode()))
        print ("Story id: {} (url: {})".format(id,url))
        for term in terms:
            test = findWholeWord(term)(html_text)
            if test is not None:
                start = test.start() - int(SAMPLE_WIDTH/2)
                end = test.end() + int(SAMPLE_WIDTH/2)
                print ("Contains \"{}\" used in this context:\n{}".format(term,html_text[start-20:end+20]))

        print("-------------------------------------")



scan_stories()
