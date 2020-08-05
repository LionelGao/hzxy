import requests
from selenium import webdriver
import  time
from bs4 import BeautifulSoup
import json
import pymssql
#1遍历五个品牌
# 'keyword=IHIMI&brand_sn=10028906'
# ,

brandlist = [ 'keyword=sr&brand_sn=10028615'
,'keyword=XWI&brand_sn=10013861'
  ,'keyword=沫晗依美&brand_sn=10014085'
    , 'keyword=丝柏舍&brand_sn=10012320']
search_head = 'https://category.vip.com/suggest.php?'
page = '&page='
ua = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'}
cnt = 0

#数据库信息
server = ""
user = ""
password = ""
#创建链接
conn = pymssql.connect(server,user,password,"FRXY")
#创建游标
cursor = conn.cursor()
#1.0 创建浏览器对象
browser = webdriver.Chrome()
# 1.1爬取数据
for brand in brandlist:
    # 1.1.1 拼接品牌和搜索url
    error_url = []
    brandcnt = 0
    for p in range(1,50):
        search_url = search_head+brand+page+str(p)
        detail_urls = []
        islastpage = False
        # 1.1.1.1 打开浏览器驱动
        browser.get(search_url)
        try:
            browser.find_element_by_xpath("//a[contains(@class,'cat-paging-next')]")
        except:
            islastpage = True
        #找到页面底部坐标
        for i in range(300):  # 每页模拟鼠标滚动滑到最底部
            para = "window.scrollTo(100," + str(i*300) + ")"
            browser.execute_script(para)
            # 滑动到页面底部就退出循环
            time.sleep(0.1)
            check_height = browser.execute_script("return document.body.scrollHeight;")
            print(i, " check_height = ", check_height)
            if((i*300)>check_height) :
                break

        #1.1.1.2 获取所有detail url
        details = browser.find_elements_by_xpath("//div[contains(@class,'c-goods-item  J-goods-item c-goods-item--auto-width')]")
        for detail in details:
            detail_url = detail.find_element_by_tag_name('a').get_attribute('href')
            detail_urls.append(detail_url)

        #进入detail页面获取元素
        for i in detail_urls:
            browser.get(i)
            salesprice=0
            try:
                browser.get(i)
                pdtcodeinfo = browser.find_element_by_xpath("//p[contains(@class,'other-infoCoding')]").text
                pdtcode = pdtcodeinfo.split('：')[1]
                salesprice = float(browser.find_element_by_xpath("//span[contains(@class,'sp-price')]").text)
            except:
                try:
                    salesprice = float(browser.find_element_by_xpath("//em[contains(@class,'J-price')]").text)
                except:
                    error_url.append(i)
                    continue
            pic_url = browser.find_element_by_xpath("//img[contains(@class,'slide-mid-pic')]").get_attribute('src')
            dict = {}
            try:
                re = requests.get(i, headers=ua)
                soup = BeautifulSoup(re.text, "lxml")
                moredetail = soup.find('tbody', class_='J_dc_table')
                kv = moredetail.find_all('tr')
                for x in kv:
                    name = x.find('th', class_='dc-table-tit').text.split('：')[0]
                    val = x.find('td').text
                    dict[name] = val
            except:
                print("请求",i,"时 失败！")
            xjson = json.dumps(dict,ensure_ascii=False)
            create_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            brandstring = ''
            if '丝' in brand:
                brandstring = '丝柏舍'
            elif 'sr' in brand:
                brandstring = 'SR/时然'
            elif 'IHIMI' in brand:
                brandstring = 'IHIMI/海谧'
            elif '沫' in brand:
                brandstring = '沫晗依美'
            elif 'XWI' in brand:
                brandstring = '茜舞XWI'
            #print(pdtcode,salesprice,i,pic_url,xjson,create_time)
            cursor.execute(
                "insert into dbo.ods_crawler_vip_goodsdetail (pdtcode,brand,online_price,detail_url,pic_url,detail_json,create_time) values (%s,%s,%d,%s,%s,%s,%s)",
                (pdtcode,brandstring,salesprice,i,pic_url,xjson,create_time)
            )
            conn.commit()
            cnt+=1
            brandcnt+=1
            print(brandstring, " 第 ", brandcnt," 款 ","第", p, " 页 ", detail_urls.index(i) + 1, "/", len(detail_urls),pdtcode," 总计： ",cnt,"款 ","成功!")
            if(cnt%200==0):
                time.sleep(30)
            time.sleep(1)
        time.sleep(3)
        #1.1.1.3如果有下一页就翻页，没有就退出
        if islastpage:
            break

    #错误的url处理
    for i in error_url:
        browser.get(i)
        salesprice = 0
        try:
            browser.get(i)
            pdtcodeinfo = browser.find_element_by_xpath("//p[contains(@class,'other-infoCoding')]").text
            pdtcode = pdtcodeinfo.split('：')[1]
            salesprice = float( browser.find_element_by_xpath("//span[contains(@class,'sp-price')]").text)
        except:
            try:
                salesprice = float(browser.find_element_by_xpath("//em[contains(@class,'J-price')]").text)
            except:
                print(i,"  失败")
                continue
        pic_url = browser.find_element_by_xpath("//img[contains(@class,'slide-mid-pic')]").get_attribute('src')
        dict = {}
        try:
            re = requests.get(i, headers=ua)
            soup = BeautifulSoup(re.text, "lxml")
            moredetail = soup.find('tbody', class_='J_dc_table')
            kv = moredetail.find_all('tr')
            for x in kv:
                name = x.find('th', class_='dc-table-tit').text.split('：')[0]
                val = x.find('td').text
                dict[name] = val
        except:
            print("请求", i, "时 失败！")
        xjson = json.dumps(dict, ensure_ascii=False)
        create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        brandstring = ''
        if '丝' in brand:
            brandstring = '丝柏舍'
        elif 'sr' in brand:
            brandstring = 'SR/时然'
        elif 'IHIMI' in brand:
            brandstring = 'IHIMI/海谧'
        elif '沫' in brand:
            brandstring = '沫晗依美'
        elif 'XWI' in brand:
            brandstring = '茜舞XWI'
        # print(pdtcode,salesprice,i,pic_url,xjson,create_time)
        cursor.execute(
            "insert into dbo.ods_crawler_vip_goodsdetail (pdtcode,brand,online_price,detail_url,pic_url,detail_json,create_time) values (%s,%s,%d,%s,%s,%s,%s)",
            (pdtcode, brandstring, salesprice, i, pic_url, xjson, create_time)
        )
        conn.commit()
        cnt += 1
        brandcnt += 1
        print(brandstring, " 第 ", brandcnt, " 款 ", "第", p, " 页 ", error_url.index(i) + 1, "/", len(error_url), pdtcode,
              " 总计： ", cnt, "款 ", "成功!")
        if (cnt % 200 == 0):
            time.sleep(30)
        time.sleep(1)
time.sleep(10)

conn.close()
