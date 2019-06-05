'''
Author: sunhui 2018/02/15
description: scraping "zhibugongzuo.com"
             reading news and studying materials and committing comments
requirement: selenium, Chrome, BeautifulSoup, RE, time, random, sys
             PIL, pyocr, pickle, cv2.
'''
from selenium import webdriver
import time
import random
import sys

sys.setrecursionlimit(1000000)


class zhibu:

    def __init__(self, username, password, web_address="https://www.zhibugongzuo.com/login",
                 APP_ID='', API_KEY='', SECRET_KEY=''):
        self.driver = None
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
        try:
            # Chromium Browser headers is adopted
            print('Chrome is adopted')
            options = webdriver.ChromeOptions()
            options.add_argument('--save-page-as-mhtml')
            self.driver = webdriver.Chrome(chrome_options=options)
            self.driver.maximize_window()
        except:
            print("cannot find browser!")
            sys.exit()

    def access(self):
        from selenium.common.exceptions import TimeoutException
        # acquiring Javascript form
        try:
            self.driver.get(self.web_address)
        except TimeoutException:
            driver.execute_script('window.stop()')

    def get_verify_code(self):
        from PIL import Image
        import scipy.signal as signal
        # acquiring varify Code
        self.driver.get_screenshot_as_file('01.png')
        verifyImage = self.driver.find_element_by_id("captcha-img")
        # multiple by 2 is for Mac with Retina Display
        left = int(verifyImage.location['x']) * 2
        top = int(verifyImage.location['y']) * 2
        right = left + int(verifyImage.size['width']) * 2
        bottom = top + int(verifyImage.size['height']) * 2
        im = Image.open('01.png')
        im = im.crop((left, top, right, bottom)).convert('L')
        # im = signal.medfilt2d(im, (5, 5))
        # im = Image.fromarray(im)
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
        user = self.driver.find_element_by_id('uname')
        user.send_keys(self.username)
        passwd = self.driver.find_element_by_id('pwd')
        passwd.send_keys(self.password)
        verify = self.driver.find_element_by_id('captcha')
        verify.send_keys(verify_code)
        time.sleep(1)
        self.driver.find_element_by_tag_name("button").click()
        time.sleep(3)

    def read_home(self, keyword='要闻', num=5, save=True, SaveFolder='./News/', sleepTime=10, comment=False):
        # TODO: 目前只支持要闻和评论
        import random
        print('*' * 50)
        print('进入' + keyword)
        menu = self.driver.find_element_by_class_name("tf-common-nav")
        menu_list = menu.text.split('\n')
        menu_list = [i.replace(' ', '') for i in menu_list]
        try:
            index = menu_list.index(keyword.strip())
        except ValueError:
            print('没有找到{}, 进入{}'.format(keyword, menu_list[0]))
            index = 0
        menu.find_elements_by_xpath(".//*[@class='clearfix tf-common-nav-list pos-rel']/li")[index].click()
        # 导入适量的新闻
        more = self.driver.find_element_by_class_name('tf-news-getMore')
        print('*' * 50)
        title_list = self.driver.find_elements_by_class_name('tf-news-item')
        while num > len(title_list):
            more.click()
            title_list = self.driver.find_elements_by_class_name('tf-news-item')
            time.sleep(random.random())
        # 随机化阅读顺序
        random.shuffle(title_list)
        # 生成新闻文件夹
        if save:
            import os
            if not os.path.exists(SaveFolder):
                print('新闻保存在{}中'.format(SaveFolder))
                os.mkdir(SaveFolder)
        # 阅读每一条新闻
        for i in range(num):
            title = title_list[i].text.split('\n')[0]
            print('正在阅读\t{}'.format(title))
            title_list[i].click()
            windows = self.driver.window_handles
            self.driver.switch_to.window(windows[1])
            time.sleep(1)
            try:
                context = self.driver.find_element_by_css_selector("[class='tf-newsDetail-content-text font-16']").text
                print('*' * 50)
                print(context)
                print('*' * 50)
            except:
                self.driver.switch_to.window(windows[0])
                continue
            # 是否保存新闻
            if save:
                f = open("{}/{}.txt".format(SaveFolder, title), "w")
                f.write(context)
                f.close()
            # 模拟阅读部分，向下移动键盘
            self.scroll(wait=sleepTime)
            # 是否评论
            if comment:
                submit_content = self.get_comment()
                self.input_comment(submit_content)
                time.sleep(random.random())
                self.submit_comment()
            # 关闭标签页，回到初始新闻列表
            self.driver.close()
            time.sleep(1)
            windows = self.driver.window_handles
            self.driver.switch_to.window(windows[0])

    def scroll(self, wait=15):
        import random
        for _ in range(random.randint(wait, wait * 2)):
            scl = random.randint(100, 300)
            # self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            self.driver.execute_script("window.scrollBy(0,{})".format(scl))
            time.sleep(random.random())

    def get_comment(self):
        import random
        comments = self.driver.find_elements_by_css_selector("[class='comment-content-text font-14']")
        submit = random.choice(comments)
        return submit

    def input_comment(self, submit):
        comment = self.driver.find_element_by_css_selector("[placeholder='别默默地看了，发表你的观点吧!']")
        comment.send_keys(submit)

    def submit_comment(self):
        from selenium.webdriver.common.action_chains import ActionChains
        submit = self.driver.find_element_by_css_selector("[class='tf-comment-btn cursor']")
        ActionChains(self.driver).move_to_element(submit).click().perform()

    def studying_material(self, num=2, save=True, SaveFolder='./Study/', sleepTime=60, comment=False):

        self.driver.get("https://www.zhibugongzuo.com/study#/study/studyIndex")
        time.sleep(5)
        self.driver.find_element_by_class_name('showAll').click()
        time.sleep(3)
        sortList = self.driver.find_element_by_class_name("sortList")
        items = sortList.find_elements_by_class_name("item")
        # 随机化阅读顺序
        random.shuffle(items)
        # 生成学习文件夹
        if save:
            import os
            if not os.path.exists(SaveFolder):
                print('新闻保存在{}中'.format(SaveFolder))
                os.mkdir(SaveFolder)

        for item in items[:num]:
            item.click()
            time.sleep(2)
            windows = self.driver.window_handles
            self.driver.switch_to.window(windows[1])
            title = self.driver.find_element_by_class_name("title").text
            print('*' * 50)
            print("正在学习{}".format(title))
            context = self.driver.find_element_by_class_name("MDcontent").text
            print(context)
            print('*' * 50)
            if save:
                f = open("{}/{}.txt".format(SaveFolder, title), "w")
                f.write(context)
                f.close()
            self.scroll(wait=sleepTime)
            # 是否评论
            if comment:
                submit_content = self.get_comment_study()
                self.input_comment_study(submit_content)
                time.sleep(random.random())
                self.submit_comment_study()
            # 关闭标签页，回到初始新闻列表
            self.driver.close()
            time.sleep(1)
            windows = self.driver.window_handles
            self.driver.switch_to.window(windows[0])

    def get_comment_study(self):
        comments = self.driver.find_element_by_class_name("holder")
        items = comments.find_elements_by_class_name("content")
        commit = random.choice(items).text
        return commit

    def input_comment_study(self, submit):
        comment = self.driver.find_element_by_id("comment")
        comment.send_keys(submit)

    def submit_comment_study(self):
        post = self.driver.find_element_by_class_name('post')
        submit = post.find_element_by_xpath("//span[@class='']")
        submit.click()

    def close(self):
        self.driver.quit()
        print('学习完毕！')


if __name__ == "__main__":
    study = zhibu(username='', password='', APP_ID='', API_KEY='', SECRET_KEY='')
    study.read_home(num=2, save=True, SaveFolder='./News', comment=False)
    study.studying_material(num=2, save=True, SaveFolder='./Study/', comment=False)
    study.close()
