import logging
import azure.functions as func
import pandas as pd
import os
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs
from datetime import datetime

marketList = [ 
    ['nyse','https://www.reuters.com/finance/markets/mostActives?symbol=&index=4'],
    ['amex','https://www.reuters.com/finance/markets/mostActives?symbol=&index=9'],
    ['nasdaq','https://www.reuters.com/finance/markets/mostActives?symbol=&index=14'],
    ['nasdaqpost','https://www.reuters.com/finance/markets/mostActives?symbol=&index=14'],
    ['ftse','https://www.reuters.com/finance/markets/mostActives?symbol=&index=19'],
]
    
# ------------------------------------------------------------------------
#                 source: https://www.reuters.com/finance/markets
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
#                 webdrive_manager ssl error workaround.
#
# https://github.com/SergeyPirogov/webdriver_manager/blob/master/CHANGELOG.md#352
#
# ------------------------------------------------------------------------
os.environ['WDM_SSL_VERIFY']='0'

version='3.50'
serverPort = 7071
driver = None

# ------------------------------------------------------------------------
#                       getSoupStr
# ------------------------------------------------------------------------

def getSoupStr(url):
    #
    # BeautifulSoup html fetch.
    # 
    global driver
    cwd = os.getcwd()

    if driver == None:
        opt = Options()
        opt.headless = True
        # ==== Linux chromedriver version ====
        driver = webdriver.Chrome(executable_path=f'{cwd}/MostActiveStocks/chromedriver', chrome_options=opt)

    driver.get(url)
    content = driver.page_source
    soup = BeautifulSoup(content, 'html.parser')
    #
    # parser and output
    #
    sStr = soup.prettify().encode("utf-8")

    return sStr

# ------------------------------------------------------------------------
#                       getNavStr
# ------------------------------------------------------------------------

def getNavStr(homePath):

    basePath = f'{homePath}?market='

    title = ''
    s1 = homePath.find('/api/')
    if s1 != -1:
        title = homePath[(s1+5):]

    navStr = f'<!DOCTYPE html><html><head><title>{title}</title></head>'
    # 
    #   <style> CSS, note cannot include a css file due to webdriver_manager.chrome restriction.
    #
    navStr += '<style type="text/css">'
    navStr += 'body { font-family: verdana,arial,sans-serif; vertical-align: text-top;}'
    navStr += 'table, th, td { border: 1px solid black; border-collapse: collapse; padding-top:5px; padding-bottom:5px; padding-left:5px; padding-right:5px; }'
    navStr += 'table { margin-left: auto; margin-right: auto; }'
    navStr += 'h1 { color:blue; text-align:center; font-size: 30px; }'
    navStr += 'div { background-color:white; color:black; padding:50px; text-align:center; }'
    navStr += 'ul { text-align:center; font-size: 30px; }'
    navStr += 'input { font-family: verdana,arial,sans-serif; font-size:20px; }'
    navStr += 'a:hover { font-weight: bold; color: #b22222; background-color: white; }'
    #
    #   Headline: HOME Nyse Amex Nasdaq NasdaqPost Ftse ReutersMostActives Investing.com
    #
    navStr += '#main { padding: 5px; padding-left: 15px; padding-right: 15px; background-color: #ffffff; border-radius: 0 0 5px 5px; }'
    navStr += 'ul#menu { padding: 0; margin-bottom: 11px; }'
    navStr += 'ul#menu li { display: inline; margin-right: 10px; }'
    navStr += 'ul#menu li a { background-color: #ffffff; padding: 3px; text-decoration: none; color: #696969; border-radius: 4px 0; }'
    navStr += 'ul#menu li a:hover { color: white; background-color: black; }'
    navStr += '</style>'
    #
    #   Headline nav list
    #
    navStr += '<strong><nav class="center">'
    navStr += '<ul class=center id="menu">'
    #
    #   HOME page defaults to NYSE data.
    #
    navStr += f'<li><a href="{homePath}">HOME | </a></li>'
    navStr += f'<li><a href="{basePath}nyse">Nyse | </a></li>'
    navStr += f'<li><a href="{basePath}amex">Amex | </a></li>'
    navStr += f'<li><a href="{basePath}nasdaq">Nasdaq | </a></li>'
    navStr += f'<li><a href="{basePath}nasdaqpost">NasdaqPost | </a></li>'
    navStr += f'<li><a href="{basePath}ftse">Ftse</a></li>'
    navStr += '<br><li><a href="https://www.reuters.com/finance/markets/mostActives">ReutersMostActives | </a></li>'
    navStr += '<li><a href="https://www.investing.com">Investing.com</a></li></br>'
    navStr += '</ul>'
    navStr += '</nav></strong>'
    # 
    #   SYMBOL textbox and button
    #
    navStr += '<p style="text-align:center; font-family: verdana,arial,sans-serif; font-size: 20px; ">Custom stock requests may be entered here \n'
    navStr += '<input type="text" placeholder="SYMBOL" id="symbol" autocomplete="off" style="width: 150px;" maxlength="10"/>\n'
    navStr += '<input type="button" value="Submit" onclick="requestYahoo()"/>\n'
    navStr += ' see notes below. </p>\n'

    navStr += '<script>\n'
    navStr += 'function requestYahoo() {\n'
    navStr += '  var sym= document.getElementById("symbol").value;\n'
    navStr += '  url = "https://finance.yahoo.com/quote/" + sym + "?p=" + sym;\n'
    navStr += '  window.location.href = url; \n'
    navStr += '}\n'
    navStr += '</script>\n'

    return navStr

# ------------------------------------------------------------------------
#                       getInfoStr
# ------------------------------------------------------------------------

def getInfoStr():
    dateStr = datetime.now().strftime("%A %d %b %Y %I:%M:%S")
    infoStr = '<ul style="text-align:left; font-family: verdana,arial,sans-serif; font-size: 15px; ">\n'
    infoStr += '<br>\n'
    infoStr += '<li><b>Links</b> : `Nyse | Amex | Nasdaq | NasdaqPost | Ftse` query Reuters for the `Most Active Companies` info.</li>\n'
    infoStr += '<li><b>ReutersMostActives</b> to view data source, note the mid page `INDEX` list.</li>\n'
    infoStr += '<li style="padding-left:2em">NYSE Most Actives -> HOME, Nyse default</li>\n'
    infoStr += '<li style="padding-left:2em">AMEX Most Actives -> Amex</li>\n'
    infoStr += '<li style="padding-left:2em">NASDAQ Most Actives -> both Nasdaq and NasdaqPost</li>\n'
    infoStr += '<li style="padding-left:2em">FTSE Most Actives -> Ftse</li>\n'
    infoStr += '<li><b>For more Reuters data</b>, use ReutersMostActives, then INDEX to `Price Gainers (%)`,`Price Losers (%)`,`Dollar Gainers`, `Dollar Losers` </li>\n'
    infoStr += '<li><b>Investing.com</b> to view other most active USA and international stocks. See <b>Markets->Stocks->Most Active</b></li>\n'
    infoStr += '<li>Each <b>Symbol element</b> links to its "Yahoo Finance" site providing complete symbol data, browser back arrow gets back to here.</li>\n'
    infoStr += '<li>Note lower lefthand browser window shows the url.</li>\n'
    infoStr += '<li><b>Nasdaq and NasdaqPost</b> both result in the same table data, NasdaqPost links to the native Nasdaq site for more direct info, again back arrow to return here. </li>\n'
    infoStr += '<li><b>SYMBOL</b> textbox provides any symbol query to "Yahoo Finance".</li>'
    infoStr += '<li>[Extensions may not be vaild on "Yahoo Finance"] Example, Nyse base symbol JCP.N enter `JCP`, include the `.L` extension for London, ie `LLOY.L` </li>\n'
    infoStr += f'<li>[Version: {version}][{dateStr}]</li>\n'
    infoStr += '</ul>\n'
    
    return infoStr

# ------------------------------------------------------------------------
#                       getDataStr
# ------------------------------------------------------------------------

def getDataStr(htmlTitle, homePath, tableData):

    dataHtmlStr = getNavStr(homePath)
    dataHtmlStr += '<h1 class=center>'+htmlTitle+'</h1>\n'
    dataHtmlStr += '<table id="data", class=center>\n'
    dataHtmlStr += tableData
    dataHtmlStr += '</table>\n'
    dataHtmlStr += getInfoStr()
    dataHtmlStr += '</body></html>\n'

    return dataHtmlStr

# ------------------------------------------------------------------------
#                       getHomeStr
# ------------------------------------------------------------------------

def getHomeStr(homePath):

    homeStr = getNavStr(homePath)
    homeStr += getInfoStr()
    homeStr += '</body></html>\n'
    return homeStr

# ------------------------------------------------------------------------
#                       getJson
# ------------------------------------------------------------------------

def getJson(url, market):

    soupStr = getSoupStr(url)
    #
    # Find the htmlTitle 
    #
    htmlTitle = ''
    startPos = soupStr.find(b'<title>')
    endPos = soupStr.find(b'</title>')
    if startPos >= 0 and endPos >= 0:
        htmlTitle = market.upper()+' : '
        htmlTitle += soupStr[startPos+len(b'<title>'):endPos].decode("utf-8").strip()
    try:
        df_list = pd.read_html(soupStr, flavor='html5lib')
        df = df_list[0]
        df.head()
    except Exception as e:
        print(e)
        exit()

    jsonResult = df.to_json(orient="values")
    jsonParsed = json.loads(jsonResult)

    #
    # table data 
    #
    tableData = ''
    symbol = ''

    tableData = '<tr><th>_Symbol_</th><th>Company</th><th>Time</th><th>Last</th><th>Chg</th><th>Chg %</th><th>Volume</th></tr>\n'
    for item in jsonParsed:
        tableData += '<tr>'
        yahooPath = ''
        for val in item:
            if item.index(val) == 0:
                symbol = str(val)
                if "." in symbol and market != 'ftse':
                    symbol = symbol[:symbol.find(".")]
                #
                # Add yahoo finance link to row for redirection.
                # NasdaqPost directly to nasdaq website.
                #
                if market == 'nasdaqpost':
                    nasdaqPath = f'https://www.nasdaq.com/market-activity/stocks/{symbol}'
                    tableData += f'<td><a href="{nasdaqPath}">{str(val)}</a></td>\n'
                else:
                    yahooPath = f'https://finance.yahoo.com/quote/{symbol}?p={symbol}'
                    tableData += f'<td><a href="{yahooPath}">{str(val)}</a></td>\n' 
            else:
                tableData += '<td>'+str(val)+'</td>\n'
        tableData += '</tr>\n'
    return htmlTitle, tableData

# ------------------------------------------------------------------------
#                       python server
# ------------------------------------------------------------------------

# AZURE - https://mostactivestocksfunapp.azurewebsites.net/api/mostactivestockslinux
# LOCAL - http://localhost:7071/api/MostActiveStocks

marketUrl = ''

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    marketName = ''
    parsed_url = urlsplit(req.url)
    packageName = '/api/mostactivestocks'

    homePath = ''
    if parsed_url.hostname == 'localhost':
        homePath = f'http://{parsed_url.hostname}:{serverPort}{packageName}'
    else:
        homePath = f'https://mostactivestocksfunapp.azurewebsites.net{packageName}'
    homePath = homePath.lower()

    if parsed_url.path.lower() == packageName:
        params = parse_qs(parsed_url.query)
        marketUrl = ''
        if 'market' in params:
            for item in marketList:
                if item[0] == params['market'][0].lower():
                    marketName = item[0]
                    marketUrl = item[1]
                    break
        if marketUrl == '':
            return func.HttpResponse(getHomeStr(homePath).encode("utf-8"), status_code=200, headers={'content-type':'text/html'})
        else :
            htmlTitle, tableData = getJson(marketUrl, marketName)
            return func.HttpResponse(getDataStr(htmlTitle, homePath, tableData).encode("utf-8"), status_code=200, headers={'content-type':'text/html'})
