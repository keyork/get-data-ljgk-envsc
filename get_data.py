'''
get data from the website: https://ljgk.envsc.cn/index.html
data format: 序号, 企业名称, 企业地址, 行政区划, 企业投产日期, 焚烧炉数量,
            焚烧炉名称, 焚烧炉炉型, 焚烧炉投产日期, 焚烧炉处理能力(t/d), 是否停止报送数据, 停止时间
data path: ./data.csv

Instruction:
    open Terminal
    cd dir_name, such as: cd Desktop/code/
    conda info --envs
    source activate xxx
    python file.py
    

'''


import os
import time

import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm


opt = Options()
opt.add_argument('--headless')
opt.add_argument('--window-size=1920,1080')
opt.add_argument("--no-sandbox")

url = 'https://ljgk.envsc.cn/index.html'

target_file = 'data_' + time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  + '.csv'

def save_data(name, addr, region, date, boilnum, boillist, discard, stop_time, target_path, id):
    '''
    Arguments:
        name: company name
        addr: company address
        region: company region
        date: company start date
        boilnum: the number of incinerator in the company
        discard: the discard incinerator's name
        stop_time: the stop time of the discard incinerator
        target_path: save data's path
        id: company id
    '''
    # # debug
    # print(name)
    # print(addr)
    # print(region)
    # print(date)
    # print(boilnum)
    # print(boillist)
    # print(discard)

    # the target file is existing or not
    # if don't exist, create and write the head
    try:
        with open(target_path, 'r') as f:
            csv_read = csv.reader(f)
    except:
        # create and write head
        # print('Target file not exists, create it!')
        with open(target_path, 'w') as f_create:
            csv_write = csv.writer(f_create)
            csv_head = ['序号', '企业名称', '企业地址', '行政区划', '企业投产日期', '焚烧炉数量',\
                        '焚烧炉名称', '焚烧炉炉型', '焚烧炉投产日期', '焚烧炉处理能力(t/d)', '是否停止报送数据', '停止时间']
            csv_write.writerow(csv_head)
    
    boil_num = len(boillist) // 4 # = boilnum
    
    for boil_id in range(boil_num):
        # write, each incinerator occupies one line
        with open(target_path, 'a+') as f_write:
            csv_write = csv.writer(f_write)
            boil_id_final = str(id).zfill(5) + '-' + str(boil_id + 1) # incinerator id, xxxxx-x

            if discard == boillist[boil_id*4]: # same name
                is_stop = '停产'
            else:
                # clear this two msg
                is_stop = ''
                stop_time = ''
            # merge single data to a row and write in csv file
            data_row = [boil_id_final, name, addr, region, date, boil_num, boillist[boil_id*4],\
                        boillist[boil_id*4+1], boillist[boil_id*4+2], boillist[boil_id*4+3], is_stop, stop_time]
            csv_write.writerow(data_row)

def close_yellow(browser):
    '''
    Arguments:
        browser: webdriver
    When open the web, there is a yellow frame in the screen, close it.
    '''
    try:
        close_button = browser.find_element_by_xpath('//*[@id="gkClose"]')
        close_button.click()
    except:
        print('no close button, ingore')
    time.sleep(1)

def get_list_num(browser):
    '''
    Arguments:
        browser: webdriver
    Return:
        page_num: number of the pages which contain all the company
    Get the number of pages, the value should be 39, but it may change in the future
    '''

    # click to unfold the box
    get_data_list = browser.find_element_by_xpath('//*[@id="psListShowBtn"]')
    get_data_list.click()
    time.sleep(1)

    # get "Page number" from texts
    next_page = browser.find_element_by_xpath('//*[@id="pageCNo"]')
    page_num_fullstr = next_page.get_attribute('innerText')
    page_num_str = ''
    is_page_num = False

    for char in page_num_fullstr:
        if char == '/':
            is_page_num = True
            continue
        if char == '页':
            is_page_num = False
            break
        if is_page_num:
            page_num_str += char
    page_num = int(page_num_str)

    return page_num

def get_list(browser, page):
    '''
    Arguments:
        browser: webdriver
        page: which page to get
    Return:
        company_list: all the company in this page
    '''

    # if not the first page, click the "Next Page" button
    # because the element is not reachable, so use this method: mouse = ActionChains(browser)
    if not page == 1:
        next_page = browser.find_element_by_xpath('//*[@id="pageNext"]')
        mouse = ActionChains(browser)
        # time.sleep(0.5)
        mouse.move_to_element(next_page).perform()
        # time.sleep(0.5)
        mouse.click().perform()
        # time.sleep(0.5)

    # get company list and return
    company_list_box = browser.find_element_by_xpath('//*[@id="pListul"]')
    company_list_str = company_list_box.text
    company_list = company_list_str.split()
    return company_list

def get_single_company(browser, list_idx, company_idx):
    '''
    Arguments:
        browser: webdriver
        list_idx: the index of the list
        company_id: the index of the company
    Return:
        data: the company's data, contains 序号；企业名称；企业地址；x坐标；y坐标；行政区划；投产日期；焚烧炉数量；炉型；处理能力（t/d）
    '''
    # handmake Xpath and get the element
    xpath = '//*[@id="pListul"]/li[' + str(list_idx) + ']'
    company_sel = browser.find_element_by_xpath(xpath)
    company_sel.click()
    time.sleep(0.5)
    company_discard_text = ''
    stop_time_text = ''

    # confirm it have been stop or not
    try:
        stop_tip = browser.find_element_by_xpath('//*[@id="gzTitle2"]')
        if stop_tip.text == '信息公开提示':
            company_discard = browser.find_element_by_xpath('//*[@id="stopMpName"]')
            # print(company_discard.text)
            company_discard_text = company_discard.text
            stop_time = browser.find_element_by_xpath('//*[@id="stopTime"]')
            stop_time_text = stop_time.text
    except:
        pass

    # jump to the frame of company information and get data
    browser.switch_to.frame('psInfoFrame')
    company_name = browser.find_element_by_xpath('//*[@id="ps_name"]')
    company_addr = browser.find_element_by_xpath('//*[@id="address"]')
    company_region = browser.find_element_by_xpath('//*[@id="region_name"]')
    company_date = browser.find_element_by_xpath('//*[@id="manufacture_date"]')
    company_boilnum = browser.find_element_by_xpath('//*[@id="boiler_num"]')
    company_boillist = browser.find_element_by_xpath('//*[@id="dataRow"]')

    # transform elememt.text to str
    company_name_text = company_name.text
    company_addr_text = company_addr.text
    company_region_text = company_region.text
    company_date_text = company_date.text
    company_boilnum_text = company_boilnum.text
    company_boillist_list = company_boillist.text.split()

    # # debug
    # print('-'*20)
    # print(company_name.text)
    # print(company_addr.text)
    # print(company_region.text)
    # print(company_date.text)
    # print(company_boilnum.text)
    # for i in range(len(company_boillist.text.split())//4):
    #     print(company_boillist.text.split()[(4*i):(4+4*i)])
    
    # jump back to the default content
    browser.switch_to.default_content()
    
    # save
    company_id = save_data(company_name_text, company_addr_text, company_region_text, company_date_text,\
            company_boilnum_text, company_boillist_list, company_discard_text, stop_time_text, target_file, company_idx)

if __name__ == '__main__':

    print('Program Start.')

    browser = webdriver.Chrome(executable_path='chromedriver', options=opt)
    browser.get(url)

    time.sleep(1)

    close_yellow(browser)
    all_page = get_list_num(browser)
    company_idx = 1
    print('Start getting data from: ' + url)
    for page_idx in range(all_page):
        print('Data Page: ' + str(page_idx + 1) + '/' + str(all_page))
        company_list = get_list(browser, page_idx + 1)
        for company in tqdm(company_list):
            get_single_company(browser, str(company_list.index(company) + 1), company_idx)
            company_idx += 1
    browser.quit()
    print('Done')