'''
Author: sunhui 2018/02/06
description: scraping "zhibugongzuo.com"
             reading news and studying materials and committing comments
requirement: selenium, PhantomJS, BeautifulSoup, RE, time, random, sys
             PIL, pyocr, pickle.

'''
from selenium import webdriver

global driver
import sys

sys.setrecursionlimit(1000000)


def reading(time_min, time_max):
    import time
    import random
    from operator import mod
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    readtime = random.randint(time_min, time_max)
    print('阅读 %d 秒钟：' % readtime)
    print('现在时间是 %s：' % time.asctime(time.localtime(time.time())))
    for it in range(0, readtime):
        ActionChains(driver).key_down(Keys.DOWN).key_up(Keys.DOWN).perform()  # 方向下键
        time.sleep(1)
        if mod(it, 20) == 0:
            driver.get_screenshot_as_file(str(it)+".png")
    return


def setting_up_browser():
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    global driver
    try:
        # setting up headless browser, Chromium Browser headers is adopted
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/63.0.3239.132")
        driver = webdriver.PhantomJS(executable_path='/usr/local/Cellar/phantomjs/2.1.1/bin/phantomjs',
                                     desired_capabilities=dcap)
        print('PhantomJS is adopted')
        return driver
    except:
        print("cannot find browser!")
        sys.exit()


def access(web_address="https://www.zhibugongzuo.com/site/login"):
    from selenium.common.exceptions import TimeoutException
    global driver
    # acquiring Javascript form
    try:
        driver.get(web_address)
    except TimeoutException:
        driver.execute_script('window.stop()')


def get_verify_code(captcha='login-captcha'):
    from PIL import Image
    global driver
    # acquiring varify Code
    driver.get_screenshot_as_file('01.png')
    verifyimage = driver.find_element_by_id(captcha)
    left = int(verifyimage.location['x'])
    top = int(verifyimage.location['y'])
    right = int(verifyimage.location['x'] + verifyimage.size['width'])
    bottom = int(verifyimage.location['y'] + verifyimage.size['height'])
    im = Image.open('01.png')
    im = im.crop((left, top, right, bottom)).convert('L')
    output_name = 'verify.tif'
    im.save(output_name)
    return output_name


def verify_ocr(filename):
    from pyocr import pyocr
    from PIL import Image
    # verify Code OCR
    tools = pyocr.get_available_tools()[:]
    print("Using '%s'" % (tools[0].get_name()))
    if len(tools) == 0:
        print("No OCR tool found")
        print("input manually")
    im = Image.open(filename)
    output = tools[0].image_to_string(Image.open('verify.tif'), lang='eng')
    print("trying varify code..." + output)
    im.show()
    print("if not correct, retype")
    output2 = input('input correct varify code:')
    return output2


def log_in(verify_code, username='', password=''):
    import time
    global driver
    # type in username password and varify code
    print("*" * 50)
    if username is '' and password is '':
        username = input('input username')
        password = input('input password')
    print("username :" + username)
    print("password :" + password)
    print("verify Code:" + verify_code)
    print("*" * 50)
    user = driver.find_element_by_id('username')
    user.send_keys(username)
    passwd = driver.find_element_by_id('password')
    passwd.send_keys(password)
    verify = driver.find_element_by_id('verifyCode')
    verify.send_keys(verify_code)
    time.sleep(1)
    driver.find_element_by_tag_name("button").click()
    time.sleep(3)


def writing_cookies():
    import pickle
    global driver
    # get cookies from website
    print('正在写入cookie')
    cookie_list = driver.get_cookies()
    f = open('cookies.zhibu', 'wb')
    pickle.dump(cookie_list, f)
    f.close()


# enter section 学习


def get_title_list(keyword='系列讲话'):
    import pickle
    from bs4 import BeautifulSoup
    import re
    import time
    global driver
    print('*' * 50)
    namedict = {'系列讲话': '12', '理论源地': '14', '党章党规': '11', '从严治党': '12'}
    print('进入' + keyword)
    try:
        namedict[keyword]
    except KeyError:
        print(keyword + 'not in list')
        pass
    # 获取所有标题列表
    try:
        namelist = pickle.load(open(keyword + '.lst', "rb"))
        print("找到列表，总共 %d 条记录" % len(namelist))
        return namelist
    except FileNotFoundError:
        print("列表不存在，在线爬取列表")
        driver.get('https://www.zhibugongzuo.com/Study/Material?type_id=' + namedict[keyword])
        pageSource = driver.page_source
        soup = BeautifulSoup(pageSource, 'lxml')
        tagsum = re.findall("[0-9]+", soup.find("", {"class": 'pagesum'}).get_text())[0]
        print("总共 %d 条记录" % int(tagsum))
        namelist = []
        niter = int(int(tagsum) / 15)
        for i in range(0, niter + 1):
            print("%d of %d" % (i, niter + 1))
            istart = str(i * 15)
            web_address = 'https://www.zhibugongzuo.com/study/Material?type_id=&start=' + istart + '&keyword='
            driver.get(web_address)
            pageSource = driver.page_source
            soup = BeautifulSoup(pageSource, 'lxml')
            namelist.extend(soup.findAll("a", {"href": re.compile("/Study/MaterialDetail*")}))
            time.sleep(3)

        pickle.dump(namelist, open(keyword + '.lst', 'wb'))
        print('列表已经保存完成')
        return namelist


def studying(namelist, chosen):
    global driver
    from bs4 import BeautifulSoup
    title = namelist[chosen].p.get_text().strip()
    print('今天学习的内容是：%s' % title)
    url = 'https://www.zhibugongzuo.com' + namelist[chosen]["href"]
    print(url)
    driver.get(url)
    pageSource = driver.page_source
    print("*" * 50)
    print('正文如下：')
    soup = BeautifulSoup(pageSource, 'lxml')
    text = soup.find("div", {"class": "text"}).get_text().strip()
    print(text)
    paragraphs = [par.strip() for par in text.split('\n') if par.strip() is not '']
    print("*" * 50)
    reading(300, 450)
    return paragraphs


def comment(paragraphs):
    global driver
    import random
    from selenium.webdriver.common.action_chains import ActionChains
    import time
    print("*" * 50)
    print('阅读完成，发表评论！')
    # 随机选择两个段落发表评论
    comment = driver.find_element_by_id("content-text")
    comment_list = [paragraphs[random.randint(1, len(paragraphs))].lstrip() for _ in range(2)]
    comment_text = ('\n').join(comment_list)
    print("评论如下：")
    print(comment_text)
    send = input("是否需要修改")
    if (send in ['是', 'y']):
        comment_text = input("在下方输入评论")
    else:
        pass
    comment.send_keys(comment_text)
    # js2 = "var q=document.getElementById('content-submit').click();"
    # driver.execute_script(js2)
    submit = driver.find_element_by_id("content-submit")
    ActionChains(driver).move_to_element(submit).click().perform()
    driver.get_screenshot_as_file('submit.png')
    print('提交成功！')
    time.sleep(1)


def study_comment(namelist, comment_yn='n'):
    global driver
    import re
    import random
    # 找到未学习的部分
    print("*" * 50)
    unreadlist = []
    for name in namelist:
        if re.search("暂未阅读", name.i.get_text()) is not None:
            print(name.p.get_text().strip())
            unreadlist.append(name)
    if len(unreadlist) is not 0:
        print('有 %d 条尚未学习' % len(unreadlist))
        chosen = random.randint(0, len(unreadlist))
        paragraphs = studying(unreadlist, chosen)
        comment(paragraphs)
    else:
        print('全部学习完成')
        chosen = random.randint(0, len(namelist))
        paragraphs = random.randint(namelist, chosen)
    if comment_yn == 'y':
        comment(paragraphs)


def comment_news(title, comments):
    from selenium.webdriver.common.action_chains import ActionChains
    import time
    global driver
    #js2 = 'var ele = document.getElementsByClassName("taste-text j-reply-text")[0]; ele.value = ele.value + '+comments+';'
    #driver.execute_script(js2)
    comment_text = driver.find_element_by_css_selector(".taste-text.j-reply-text")
    comment_text.send_keys(comments)
    time.sleep(2)
    # js2 = 'document.getElementsByClassName("btn btn-yellow hf j-btn-comment-sub")[0].click();'
    # driver.execute_script(js2)
    submit = driver.find_element_by_css_selector(".btn.btn-yellow.pos-abs.pl.j-btn-comment-sub")
    ActionChains(driver).move_to_element(submit).click().perform()
    time.sleep(3)
    driver.get_screenshot_as_file(title+'.png')
    print('评论成功！ %s' % comments)


def reading_news(num_news=10, comment_yn='n', comments="赞！👍", ):
    import time
    from bs4 import BeautifulSoup
    global driver
    # 进入要闻学习，阅读十条重要新闻
    print("进入要闻学习，阅读 %d 条重要新闻" % num_news)
    web_address = "https://www.zhibugongzuo.com/News/ImportantIndex"
    driver.get(web_address)
    time.sleep(3)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    js2 = 'document.getElementById("j-news-more").click();'
    driver.execute_script(js2)
    # driver.find_element_by_id("j-news-more").click()  # 加载更多
    time.sleep(3)
    pageSource = driver.page_source
    soup = BeautifulSoup(pageSource, 'lxml')
    NewsList = soup.findAll("div", {"class": "zbgz-infolist-item-container"})
    for i in range(0, num_news):
        title = NewsList[i].a.get_text()
        url = 'https://www.zhibugongzuo.com' + NewsList[i].a["href"]
        print('正在学习第 %d 条新闻，%s：%s' % (i + 1, title, url))
        driver.get(url)
        print('正在阅读' + title)
        pageSource = driver.page_source
        soup = BeautifulSoup(pageSource, 'lxml')
        text = soup.find("div", {"class": "indexinfotext"}).get_text()
        print(text)
        reading(10, 15)
        f = open(title + '.txt', "w")
        f.write(text)
        f.close()

        if comment_yn == 'y':
            comment_news(title, comments)


def close():
    global driver
    driver.close()
    print('学习完毕！')


if __name__ == '__main__':
    setting_up_browser()
    access("https://www.zhibugongzuo.com/site/login")
    verify_file = get_verify_code()
    verify_code = verify_ocr(verify_file)
    log_in(verify_code)
    writing_cookies()
    #title_list = get_title_list('系列讲话')
    #study_comment(title_list, 'y')
    reading_news(10, 'y')
    close()
