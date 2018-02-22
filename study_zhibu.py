'''
Author: sunhui 2018/02/15
description: scraping "zhibugongzuo.com"
             reading news and studying materials and committing comments
requirement: selenium, Chrome, BeautifulSoup, RE, time, random, sys
             PIL, pyocr, pickle, cv2.
'''
from selenium import webdriver
import pickle
import os
import sys

global driver


sys.setrecursionlimit(1000000)

class zhibu:

    def __init__(self, username, password, web_address="https://www.zhibugongzuo.com/login",
                 APP_ID='', API_KEY='', SECRET_KEY=''):
        self.web_address = web_address
        self.username = username
        self.password = password
        self.APP_ID = APP_ID
        self.API_KEY = API_KEY
        self.SECRET_KEY = SECRET_KEY
        self.setting_up_browser()
        self.access()
        self.log_in()



    def setting_up_browser(self):
        global driver
        try:
            # Chromium Browser headers is adopted
            print('Chrome is adopted')
            options = webdriver.ChromeOptions()
            options.add_argument('--save-page-as-mhtml')
            driver = webdriver.Chrome(chrome_options=options)
            driver.maximize_window()
            return driver
        except:
            print("cannot find browser!")
            sys.exit()

    def access(self):
        from selenium.common.exceptions import TimeoutException
        global driver
        # acquiring Javascript form
        try:
            driver.get(self.web_address)
        except TimeoutException:
            driver.execute_script('window.stop()')

    def get_verify_code(self):
        from PIL import Image
        import scipy.signal as signal
        global driver
        # acquiring varify Code
        driver.get_screenshot_as_file('01.png')
        verifyImage = driver.find_element_by_id("captcha-img")
        # multiple by 2 is for Mac with Retina Display
        left = int(verifyImage.location['x']) * 2
        top = int(verifyImage.location['y']) * 2
        right = left + int(verifyImage.size['width']) * 2
        bottom = top + int(verifyImage.size['height']) * 2
        im = Image.open('01.png')
        im = im.crop((left, top, right, bottom)).convert('L')
        im = signal.medfilt2d(im, (5, 5))
        im = Image.fromarray(im)
        output_name = 'verify.jpg'
        im.save(output_name)
        return output_name

    def verify_ocr(self, APP_ID, API_KEY, SECRECT_KEY):
        from aip import AipOcr
        import re
        client = AipOcr(APP_ID, API_KEY, SECRECT_KEY)
        i = open(r'./verify.jpg', 'rb')
        img = i.read()
        message = client.basicGeneral(img)
        for i in message.get('words_result'):
            res = i.get('words')
        return res

    def log_in(self):
        import time
        global driver

        # type in username password and varify code
        print("*" * 50)
        print("username :" + self.username)
        print("password :" + self.password)
        if self.APP_ID != '' and self.API_KEY != '' and self.SECRET_KEY != '':
            self.get_verify_code()
            verify_code = self.verify_ocr(self.APP_ID, self.API_KEY, self.SECRET_KEY)
            if (not verify_code.isdigit()) or (len(verify_code) != 4):
                verify_code = input('识别失败，输入验证码')
        else:
            verify_code = input('手动输入验证码')
        print("verify Code:" + verify_code)
        print("*" * 50)
        user = driver.find_element_by_id('uname')
        user.send_keys(self.username)
        passwd = driver.find_element_by_id('pwd')
        passwd.send_keys(self.password)
        verify = driver.find_element_by_id('captcha')
        verify.send_keys(verify_code)
        time.sleep(1)
        driver.find_element_by_tag_name("button").click()
        time.sleep(3)

    def read_home(self, keyword='要闻', num = 10):
        #TODO: 目前只支持要闻和评论
        import time
        import random
        global driver
        print('*' * 50)
        print('进入' + keyword)
        menu = driver.find_element_by_class_name("tf-common-nav")
        menu_list = menu.text.split('\n')
        menu_list = [i.replace(' ', '') for i in menu_list]
        try:
            index = menu_list.index(keyword.strip())
        except ValueError:
            print('没有找到{}, 进入{}'.format(keyword, menu_list[0]))
            index = 0
        #menu.find_element_by_xpath(".//*[@class='clearfix tf-common-nav-list pos-rel']/li[{}]".format(index)).click()
        more = driver.find_element_by_class_name('tf-news-getMore')
        print('*' * 50)
        print('进入')
        title_list = driver.find_elements_by_class_name('tf-news-item')
        while num > len(title_list):
            more.click()
            title_list = driver.find_elements_by_class_name('tf-news-item')
            time.sleep(random.random())
        print(title_list)
        #viewList = random.shuffle(title_list)
        for i in range(num):
#            print('正在阅读{}'.format(viewList[i].text))
            title_list[i].click()
            #time.sleep(random.randint(10, 20))
            #driver.close()
            time.sleep(2)

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
        # driver.get_screenshot_as_file('submit.png')
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
        comment_text = driver.find_element_by_css_selector(".taste-text.j-reply-text")
        comment_text.send_keys(comments)
        time.sleep(2)
        # js2 = 'document.getElementsByClassName("btn btn-yellow hf j-btn-comment-sub")[0].click();'
        # driver.execute_script(js2)
        submit = driver.find_element_by_css_selector(".btn.btn-yellow.pos-abs.pl.j-btn-comment-sub")
        ActionChains(driver).move_to_element(submit).click().perform()
        time.sleep(3)
        # driver.get_screenshot_as_file(title+'.png')
        print('评论成功！ %s' % comments)

    def reading_news(num_news=10, comment_yn='n', comments="学习", ):
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
        while (len(NewsList) < num_news):
            js2 = 'document.getElementById("j-news-more").click();'
            driver.execute_script(js2)
            pageSource = driver.page_source
            soup = BeautifulSoup(pageSource, 'lxml')
            NewsList = soup.findAll("div", {"class": "zbgz-infolist-item-container"})
            time.sleep(1)
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
            # f = open(title + '.txt', "w")
            # f.write(text)
            # f.close()

            if comment_yn == 'y':
                comment_news(title, comments)

    def close():
        global driver
        driver.close()
        print('学习完毕！')





