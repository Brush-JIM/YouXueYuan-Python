from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time,re,json,pickle,sys,os,logging
from collections import OrderedDict
from bs4 import BeautifulSoup
from pathlib import Path
try:
    import chromedriver_binary
except:
    pass

#设置logging
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
logging.basicConfig(filename='.\debug_run.log',level=logging.INFO, format=LOG_FORMAT,datefmt=DATE_FORMAT,filemode='w')

#退出函数
def Exit():
    try:
        driver.quit()
    except:
        pass
    print ('程序终止，请将错误信息以及目录下的debug_run.log发送至EMail:Brush-JIM@protonmail.com')
    input ('回车关闭')
    sys.exit()

#加载cookies
def Load_cookies():
    logging.info('加载cookies Load_cookies()')
    if os.path.exists('cookies.pkl') == True:
        if os.path.isfile('cookies.pkl') == True:
            try:
                cookies = pickle.load(open('cookies.pkl','rb'))
                for cookie in cookies:
                    driver.add_cookie(cookie)
                return True
            except Exception:
                logging.warning("cookies.pkl加载失败",exc_info = True)
                return False
        else:
            logging.warning('cookies.pkl不是文件',exc_info = True)
            return False
    else:
        logging.warning('cookies.pkl不存在',exc_info = True)
        return False

#检查登录状态
def Check_login():
    logging.info('检测登录状态 Check_login()')
    try:
        driver.get('https://www.ulearning.cn/umooc/learner/userInfo.do?operation=studentChangeInfo')
    except Exception:
        print('driver.get失败，请确认chomedriver正常运行')
        logging.warning('driver.get失败',exc_info = True)
        Exit()
    if driver.page_source.find(username) != -1:
        return True
    else:
        logging.warning('登录状态失效',exc_info = True)
        try:
            driver.delete_all_cookies()
        except Exception:
            logging.warning('清空cookie失败',exc_info = True)
        return False

#登录
def Login():
    logging.info('登录 Login()')
    try:
        driver.get('https://www.ulearning.cn/ulearning/index.html#/index/portal')
    except Exception:
        print('driver.get失败，请确认chomedriver正常运行')
        logging.error('driver.get失败',exc_info = True)
        Exit()
    while True:
        if driver.page_source.find('<div class="login-btn-text" data-bind="click: login, text: publicI18nText.signin">') != -1:
            break
        else:
            time.sleep(3)
    while True:
        if driver.page_source.find('<div class="form-title">登录</div>') == -1:
            try:
                driver.find_element_by_xpath('//div[@class="login-btn-text"]').click()
                break
            except:
                pass
        else:
            pass
    while True:
        try:
            driver.find_element_by_id('userLoginName').send_keys(username)
            break
        except Exception:
            logging.warning('用户名填写失败',exc_info = True)
    while True:
        try:
            driver.find_element_by_id('userPassword').send_keys(password)
            break
        except Exception:
            logging.warning('密码填写失败',exc_info = True)
    while True:
        try:
            driver.find_element_by_xpath('//*[@id="loginForm"]/button').click()
            break
        except Exception:
            logging.error('点击登录失败',exc_info = True)
    if Check_login() == True:
        try:
            pickle.dump( driver.get_cookies() , open("cookies.pkl","wb"))
            with open('data.json','w') as data:
                data.write(json.dumps({'username':username,'password':password,'headless':headless,'save':save}))
            return True
        except Exception as error:
            logging.warning('保存cookie失败',exc_info = True)
            return None
    else:
        return False

#跳转至课程
def Jump2class():
    logging.info('跳转至课程 Jump2class()')
    print('开始跳转至课程页面')
    try:
        driver.get('https://dgut.ulearning.cn/umooc/learner/study.do?operation=catalog')
    except Exception:
        logging.error('driver.get失败，请确认chomedriver正常运行',exc_info = True)
        Exit()
    while True:
        if driver.page_source.find('<span onclick="changeYear(0);">全部</span>') != -1:
            try:
                #借鉴js版项目方法
                driver.execute_script("""window.changeYear(0);""")
                break
            except Exception:
                logging.error('Jump2class js执行失败',exc_info = True)
                try:
                    driver.find_element_by_xpath('//span[@onclick="changeYear(0);"]').click()
                    break
                except Exception:
                    logging.error('Jump2class 点击失败',exc_info = True)
        else:
            break
    print('跳转成功')

#解析课程
def Analysis_class():
    logging.info('解析课程 Analysis_class()')
    print('开始解析课程')
    try:
        title_rule = re.compile(r'<h3>(.*?)</h3>')
        schedule_rule = re.compile(r'<span class="progress-pre left">(.*?)</span>')
        url_rule = re.compile(r'<a class="btn-primary btn-coursein title" href="(.*?)">')
        html = driver.page_source.replace('amp;','')
        soup = BeautifulSoup(html,features = "html5lib")
        trees = soup.find_all('div',class_='course-detail left english-course-detail')
    except Exception:
        logging.error('beautifulsoup解析课程失败',exc_info = True)
        Exit()
    data = OrderedDict()
    count = 0
    try:
        for tree in trees:
            title = re.search(title_rule,str(tree)).group(1)
            schedule = re.search(schedule_rule,str(tree)).group(1)
            try:
                url = re.search(url_rule,str(tree)).group(1).replace('amp;','')
            except:
                url = None
            data[str(count)] = OrderedDict()
            data[str(count)]['title'] = title
            data[str(count)]['schedule'] = schedule
            data[str(count)]['url'] = url
            count = count + 1
    except Exception:
        logging.error('课程输出失败',exc_info = True)
        Exit()
    print('解析成功')
    return data

#选择课程
def Choose_course():
    logging.info('选择课程 Choose_course()')
    all_class = Analysis_class()
    while True:
        print('\n课程名称：')
        for data in all_class:
            if all_class[data]['url'] == None:
                print(str(data) + '.' + all_class[data]['title'] + '\t 警告：此课程无法获取URL，若选择该课程，请确定是否到期')
            else:
                print(str(data) + '.' + all_class[data]['title'])
        print('-1.退出')
        choose = input('请选择编号：')
        if choose == '-1':
            driver.quit()
            sys.exit()
        elif all_class[choose]['url'] == None:
            print('url获取失败，请检查课程是否到期！')
        else:
            break
    return all_class[choose]['url']

#选择名称
def Choose_name(url):
    logging.info('选择名称 Choose_name()')
    print('开始解析目录')
    try:
        driver.get('https://www.ulearning.cn' + url)
    except Exception:
        logging.error('driver.get失败，请确认chomedriver正常运行',exc_info = True)
        Exit()
    try:
        html = driver.page_source.replace('&nbsp;','')
        soup = BeautifulSoup(html,features = "html5lib")
        trees = soup.find_all('tr',class_='thecuorse')
        title_rule = re.compile(r'<p>(.*?)</p>')
    except Exception:
        logging.error('Choose_name 解析失败',exc_info = True)
        Exit()
    data = OrderedDict()
    count = 1
    print('')
    print('从下面选名称')
    print('0.自动')
    try:
        for tree in trees:
            title = str(tree.find('p').get_text()).replace(' ','').replace('\t','').replace('\n','').replace('\r','')
            schedule = str(tree.find('span',class_='progress-pre course-over').get_text()).replace(' ','').replace('\t','').replace('\n','').replace('\r','').replace('&nbsp;','').replace(u'\xa0', u'')
            onclick = re.search(r'<div class="btn-primary title tsize14" onclick="(.*?)">',str(tree)).group(1)
            print(str(count) + '.' + title)
            data[str(count)] = OrderedDict()
            data[str(count)]['title'] = title
            data[str(count)]['schedule'] = schedule
            data[str(count)]['onclick'] = onclick
            count = count + 1
    except Exception:
        logging.error('Choose_name 目录输出失败',exc_info = True)
        Exit()
    choose = input('请选择序号：')
    global choose_type
    choose_type = choose
    print('')
    if choose == '-1':
        return data['1']['onclick']
    elif choose == '0':
        for tree in data:
            if data[tree]['schedule'] != '100%':
                return data[tree]['onclick']
            else:
                pass
        return True
    elif choose in data:
        return data[choose]['onclick']
    else:
        print('选择错误，默认自动选择')
        for tree in data:
            if data[tree]['schedule'] != '100%':
                return data[tree]['onclick']
            else:
                pass
        return True

#点击目录
def Click_name(choose):
    logging.info('点击目录 Click_name()')
    if choose == True:
        return None
    else:
        try:
            driver.execute_script(choose)
            return True
        except Exception:
            logging.error('执行点击目录脚本失败',exc_info = True)
            return False

#删除用户指导和统计元素
def Del_message():
    logging.info('删除元素 Del_message()')
    try:
        element = driver.find_element_by_xpath("//div[@class='user-guide']")
        driver.execute_script("""
var element = arguments[0];
element.parentNode.removeChild(element);
""", element)
    except:
        try:
            #借鉴js项目的方法
            driver.execute_script("""var elements = document.getElementsByClassName('operating-area')[0];
document.getElementsByClassName("user-guide")[0].parentNode.removeChild(document.getElementsByClassName("user-guide")[0]);
""")
        except:
            pass
    try:
        element = driver.find_element_by_xpath("//div[@id='statModal']")
        driver.execute_script("""
var element = arguments[0];
element.parentNode.removeChild(element);
""", element)
    except:
        try:
            #借鉴js项目的方法
            driver.execute_script("""var elements = document.getElementsByClassName('operating-area')[0];
document.getElementById('statModal').parentNode.removeChild(document.getElementById('statModal'));
""")
        except:
            pass

#关闭提示
def Close_tips():
    logging.info('关闭提示 Close_tips()')
    time.sleep(1)
    while driver.page_source.find('<div class="modal-backdrop fade in"></div>') != -1:
        if driver.page_source.find('text: $root.i18nMsgText().confirmLeave') != -1:
            try:
                driver.find_element_by_xpath('//button[@data-bind="text: $root.i18nMsgText().confirmLeave"]').click()
                break
            except:
                #借鉴js项目的方法
                try:
                    driver.execute_script("""
if (document.querySelector("[data-bind='text: $root.i18nMsgText().confirmLeave']") != null) {
document.querySelector("[data-bind='text: $root.i18nMsgText().confirmLeave']").click();
}
""")
                    break
                except Exception:
                    logging.error('关闭二次确认失败',exc_info = True)
                    Exit()
        else:
            pass
        if driver.page_source.find('text: $root.i18nMsgText().gotIt') != -1:
            try:
                driver.find_element_by_xpath('//button[@data-bind="text: $root.i18nMsgText().gotIt"]').click()
                break
            except:
                #借鉴js项目的方法
                try:
                    driver.execute_script("""
if (document.querySelector("[data-bind='text: $root.i18nMsgText().gotIt']") != null) {
document.querySelector("[data-bind='text: $root.i18nMsgText().gotIt']").click();
}
""")
                    break
                except Exception:
                    logging.error('关闭确认失败',exc_info = True)
                    Exit()

#判断是否视频
def Check_video():
    logging.info('判断视频 Check_video()')
    code = driver.page_source
    if code.find('file-media') != -1:
        return True
    else:
        return False

#播放视频
def Adjust_player():
    logging.info('播放视频 Adjust_player()')
    try:
        while True:
            if driver.page_source.find('title="Pause" aria-label="Pause" tabindex="0"></button>') == -1 or driver.page_source.find('title="Play" aria-label="Play" tabindex="0"></button>') != -1:
                try:
                    #借鉴js项目的方法
                    driver.execute_script("""document.querySelector("[aria-label='Play']").click();""")
                    break
                except Exception:
                    logging.warning('js命令执行失败',exc_info = True)
                    try:
                        driver.find_element_by_xpath('//button[@title="Play"]').click()
                        break
                    except Exception:
                        if driver.page_source.find('title="Pause" aria-label="Pause" tabindex="0"></button>') == -1 or driver.page_source.find('title="Play" aria-label="Play" tabindex="0"></button>') != -1:
                            logging.error('播放失败',exc_info = True)
                            Exit()
                        else:
                            break
            else:
                break
    except Exception:
        print('Adjust_player()函数执行错误')
        logging.error('Adjust_player()函数执行错误',exc_info = True)
        Exit()
            

#判断视频是否完成
def Check_done():
    logging.info('判断视频完成开始 Check_done()')
    while True:
        if driver.page_source.find('<span data-bind="text: $root.i18nMessageText().finished">已看完</span>') == -1:
            progress = re.search(r'<span data-bind="text: pageElement.record\(\).viewProgress\(\)">(\d+).(\d+)</span>',driver.page_source)
            if not progress:
                pass
            else:
                print("\r当前视频进度：" + progress.group(1) + "." + progress.group(2) + "%",end='',flush=True)
                time.sleep(1)
        else:
            print("\r视频完成。              ")
            time.sleep(3)
            logging.info('判断视频完成结束 Check_done()')
            return True

#下一页
def Next_page():
    logging.info('下一页 Next_page()')
    while True:
        try:
            #借鉴js项目的方法
            driver.execute_script("""window.koLearnCourseViewModel.goNextPage();""")
            break
        except Exception:
            logging.error('JS方法 下一页失败',exc_info = True)
            try:
                driver.find_element_by_xpath('//div[@data-bind="click: goNextPage"]').click()
            except Exception:
                logging.error('selenium方法 下一页失败',exc_info = True)
                Exit()
    Close_tips()
    if BeautifulSoup(driver.page_source,features = "html5lib").find('div',class_='course-title small'):
        for title in BeautifulSoup(driver.page_source,features = "html5lib").find('div',class_='course-title small'):
            print('标题：' + title.string)
            logging.info('标题：' + title.string)
            break
    if driver.page_source.find('<span class="text" data-bind="text: $root.nextPageName()">没有了</span>') != -1:
        return None
    else:
        return True

#返回章节
def Exit_chapter():
    logging.info('返回章节 Exit_chapter()')
    while True:
        try:
            #借鉴js项目的方法
            driver.execute_script("""window.koLearnCourseViewModel.goBack();""")
            break
        except Exception:
            logging.warning('js命令 返回章节失败',exc_info = True)
            try:
                driver.find_element_by_xpath('//span[@class="back btn-text"]').click()
                break
            except:
                try:
                    driver.find_element_by_xpath('//div[@class="back-btn control-btn cursor"]').click()
                    break
                except:
                    try:
                        driver.find_element_by_xpath('//div[@data-bind="css: { \'return-url\': returnUrl }, click: $root.goBack"]').click()
                        break
                    except:
                        try:
                            driver.find_element_by_xpath('//span[@data-bind="text: i18nMessageText().backToCourse"]').click()
                            break
                        except Exception:
                            logging.warning('返回章节失败',exc_info = True)

#更新数据
def Updata():
    logging.info('更新数据 Updata()')
    global headless,save
    #是否隐藏窗口
    #not in ['y','Y'] 借鉴https://github.com/Alivon/Panda-Learning/blob/master/Source%20Packages/pandalearning.py 项目，反正学到了更简单的方法
    if (input('是否隐藏窗口（Y/n）：')) not in ['y','Y']:
        headless = False
    else:
        headless = True
    if (input('是否保存该设置（Y/n）：')) not in ['y','Y']:
        save = False
    else:
        save = True
    with open('data.json','w') as data:
        data.write(json.dumps({'username':username,'password':password,'headless':headless,'save':save}))

if __name__ == '__main__':
    #准备登录信息
    logging.info('准备登录信息')
    if os.path.exists('data.json') == True:
        if os.path.isfile('data.json') == True:
            try:
                with open('data.json','r') as data:
                    data = json.loads(data.read())
                    username = data['username']
                    password = data['password']
                    save = data['save']
                    headless = data['headless']
                    if save == True:
                        pass
                    else:
                        Updata()
            except Exception:
                logging.warning('加载data.json失败，重新写入',exc_info = True)
                username = input('账号：')
                password = input('密码：')
                Updata()
        else:
            username = input('账号：')
            password = input('密码：')
            Updata()
    else:
        username = input('账号：')
        password = input('密码：')
        Updata()
    #准备chrome
    logging.info('准备chromedriver')
    print('开始准备chromedriver')
    chrome_options = webdriver.ChromeOptions()
    if headless == True:
        chrome_options.add_argument('--headless')
        pass
    else:
        pass
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument('log-level=3')
    chrome_options.add_argument('--window-size=5000,5000')
    chrome_options.add_argument('--window-position=800,0')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36")
    try:
        driver = webdriver.Chrome(chrome_options=chrome_options)
        print('chromedriver准备成功')
    except Exception:
        logging.warning('默认chromedriver.exe加载失败',exc_info = True)
        try:
            driver = webdriver.Chrome(chrome_options=chrome_options,executable_path = '.\chromedriver.exe')
            print('chromedriver准备成功')
        except Exception:
            logging.warning('同目录chromedriver.exe加载失败',exc_info = True)
            try:
                path = input('请输入完整路径，包括文件名：')
                driver = webdriver.Chrome(chrome_options=chrome_options,executable_path = path)
                print('chromedriver准备成功')
            except Exception:
                print('自定义chromedriver.exe加载失败')
                logging.error('自定义chromedriver.exe加载失败',exc_info = True)
                Exit()
    try:
        logging.info('跳转至主页')
        driver.get('https://www.ulearning.cn/ulearning/index.html#/index/portal')
    except Exception:
        logging.error('driver.get失败，请确认chomedriver正常运行',exc_info = True)
        Exit()

    if Load_cookies() == True:
        if Check_login() == True:
            print('登录成功。')
        else:
            if Login() == True:
                print('登录成功。')
            else:
                input ('登录失败，回车退出。')
                Exit()
    else:
        if Login() == True:
            print('登录成功。')
        else:
            input('登录失败，回车退出。')
            Exit()
    print('准备就绪')
    while True:
        Jump2class()
        click_name = Click_name(Choose_name(Choose_course()))
        if click_name == True:
            Del_message()
            while True:
                Close_tips()
                check_video = Check_video()
                if check_video == True:
                    Adjust_player()
                    Check_done()
                next_page = Next_page()
                if next_page == True:
                    continue
                else:
                    break
            Exit_chapter()
        elif click_name == False:
            print('无法执行点击目录脚本')
        else:
            print('课程完成')
        if (input('是否继续（Y/n）：')) in ['y','Y']:
            pass
        else:
            logging.info('正常退出')
            driver.quit()
            sys.exit()
            break
