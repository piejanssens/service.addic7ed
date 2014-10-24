#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        addic7ed
# Purpose:     Parsing and downloading subs from addic7ed.com
# Version:
# Author:      Roman Miroshnychenko
# Created on:  05.03.2013
# Copyright:   (c) Roman Miroshnychenko, 2013
# Licence:     GPL v.3 http://www.gnu.org/licenses/gpl.html
#-------------------------------------------------------------------------------

import re
import urllib2
from urllib import quote_plus
from bs4 import BeautifulSoup
from xbmcvfs import File

SITE = "http://www.addic7ed.com"
HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:23.0) Gecko/20100101 Firefox/23.0",
            "Host": SITE[7:],
            "Referer": SITE,
            "Accept-Charset": "UTF-8"}


def search_episode(show_name, season, episode, languages=[("English", "English")]):
    """
    Search episode function. Accepts a TV show name, a season #, an episode # and language.
    Note that season and episode #s must be strings, not integers!
    For better search results relevance, season and episode #s should be 2-digit, e.g. 04.
    languages param must be a list of tuples
    ("Kodi language name", "addic7ed language name")
    If search returns only 1 match, addic7ed.com redirects to the found episode page.
    In this case the function returns the list of available subs and an episode page URL.
    If connection error occurs, the function returns -1 and an empty string.
    """
    listing = []
    episode_url = ""
    url = "{site}/search.php?search={show}+{season}x{episode}&Submit=Search".format(
        site=SITE, show=quote_plus(show_name.encode("utf-8")), season=season, episode=episode)
    request = urllib2.Request(url, None, HEADER)
    try:
        session = urllib2.urlopen(request, None)
    except urllib2.URLError:
        listing = -1
    else:
        results_page = session.read()
        session.close()
        if re.search(r"<table width=\"100%\" border=\"0\" align=\"center\" class=\"tabel95\">", results_page) is not None:
            listing = parse_episode(results_page, languages)
            episode_url = session.geturl()
    return listing, episode_url


def parse_episode(episode_page, languages):
    """
    Parse episode page. Accepts an episode page and a language.
    languages param must be a list of tuples
    ("Kodi language name", "addic7ed language name")
    Returns the list of available subs where each item is a dictionary
    with the following keys:
    "language": subtitles language (Kodi)
    "version": subtitles version (description on addic7ed.com)
    "link": subtitles link
    "hi" (bool): True for subs for hearing impaired.
    """
    listing = []
    soup = BeautifulSoup(episode_page)
    sub_cells = soup.find_all("table", {"width": "100%", "border": "0", "align": "center", "class": "tabel95"})
    for cell in sub_cells:
        for language in languages:
            if language[1] in cell.find("td", {"class": "language"}).get_text():
                item = {"language": language[0]}
                item["version"] = re.search(r"Version (.*?),",
                            cell.find("td", {"colspan": "3", "align": "center", "class": "NewsTitle"}).text).group(1)
                works_with = cell.find("td", {"class": "newsDate", "colspan": "3"}).get_text(strip=True)
                if works_with:
                    item["version"] += ", " + works_with
                download_tag = cell.find("a", {"class": "buttonDownload"}, text="most updated")
                if download_tag is None:
                    download_tag = cell.find("a", {"class": "buttonDownload"}, text="Download")
                item["link"] = SITE + download_tag["href"]
                item["hi"] = download_tag.find_next("tr").contents[1].find("img", title="Hearing Impaired") is not None
                listing.append(item)
                break
    return listing


def download_subs(url, referer, filename="subtitles.srt"):
    """
    Sub downloader function. Accepts a URL to a sub, an episode page URL as a referrer and the name of a file
    where to save subs. Returns 1 if the subs have been downloaded, 0 if there has been a connection error
    or -1 if addic7ed.com returns "Daily limit exceeded" page.
    """
    header = HEADER
    header["Referer"] = referer
    request = urllib2.Request(url, None, header)
    try:
        page = urllib2.urlopen(request, None)
    except urllib2.URLError:
        success = 0
    else:
        subtitles = page.read()
        if subtitles[:9] != "<!DOCTYPE":
            file_ = File(filename, "w")
            file_.write(subtitles)
            file_.close()
            success = 1
        else:
            success = -1
        page.close()
    return success

if __name__ == "__main__":
    pass
