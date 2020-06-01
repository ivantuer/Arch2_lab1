import time

import requests
from bs4 import BeautifulSoup
import urllib.request
import re
from email_scraper import scrape_emails
from requests_html import HTMLSession
from selectolax.parser import HTMLParser
import xml.etree.ElementTree as ET
import gevent


def findMails(soup, mails):
    for name in soup.find_all('a'):
        if (name is not None):
            emailText = name.text
            match = bool(re.match('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
                                  emailText))
            if '@' in emailText and match:
                emailText = emailText.replace(" ", '').replace('\r', '')
                emailText = emailText.replace('\n', '').replace('\t', '')
                if (len(mails) == 0) or (emailText not in mails):
                    print(emailText)
                mails.append(emailText)


def getEmails(url, depth, mails):
    if depth == 0:
        return
    time.sleep(1)
    print("Depth: ", depth)
    print("Processing url: ", url)

    allLinks = []
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = [a.attrs.get('href') for a in soup.select('a[href]')]
    for i in links:
        if (("contact" in i or "Contact") or
            ("Career" in i or "career" in i)) \
                or ('about' in i or "About" in i) \
                or ('Services' in i or 'services' in i):
            allLinks.append(i)
    allLinks = set(allLinks)

    i = 0
    for link in allLinks:
        i += 1
        print("Depth: ", depth, " Index: ", i)
        try:
            if link.startswith("http") or link.startswith("www"):
                time.sleep(1)
                # Recursive call
                depth -= 1
                getEmails(link, depth, mails)
                depth += 1
                #
                time.sleep(1)
                print(link)
                r = requests.get(link)
                data = r.text
                soup = BeautifulSoup(data, 'html.parser')
                findMails(soup, mails)

            else:
                time.sleep(1)
                # Recursive call
                depth -= 1
                getEmails(link, depth, mails)
                depth += 1
                #
                print(link)
                time.sleep(1)
                newurl = url + link
                r = requests.get(newurl)
                data = r.text
                soup = BeautifulSoup(data, 'html.parser')
                findMails(soup, mails)
        except Exception:
            print("Error: ", link)

    mails = set(mails)
    create_xml(mails)
    if len(mails) == 0:
        print("NO MAILS FOUND")


def readFromXml():
    mails = []
    tree = ET.parse('input.xml')
    root = tree.getroot()
    threads = []
    # one specific item attribute
    depth = int(root[0].text)
    # all item attributes
    print('\nAll attributes:')
    for elem in root:
        for subelem in elem:
            print(subelem.text)
            print("Loading all emails...")
            threads.append(gevent.spawn(getEmails, subelem.text, depth, mails))
            print("All emails:\n", mails)
    gevent.joinall(threads)


def create_xml(mails):
    usrconfig = ET.Element("data")
    usrconfig = ET.SubElement(usrconfig, "data")
    for mail in range(len(mails)):
        email = ET.SubElement(usrconfig, "email")
        email.text = str(mails[mail])
    tree = ET.ElementTree(usrconfig)
    tree.write("output.xml", encoding='utf-8', xml_declaration=True)


if __name__ == "__main__":
    readFromXml()
    # print(getLinks(url))
    # getEmails(url)
