import requests
import re
import codecs
import csv
from lxml import etree

area_title = ['省', '市', '县']
cost_title = ['下限', '上限']
parts = {'inst-intro':'详情_机构介绍', 'inst-charge':'详情_收费标准', 'facilities':'详情_设施', \
         'service-content':'详情_服务内容', 'inst-notes':'详情_入住须知'}
fn = ['id',
 '交通',
 '人气',
 '占地面积',
 '地址',
 '床位数',
 '成立时间',
 '所在地区',
 '所在地区_县',
 '所在地区_市',
 '所在地区_省',
 '收住对象',
 '收住对象_全护理',
 '收住对象_半自理',
 '收住对象_特护',
 '收住对象_自理',
 '收费区间',
 '收费区间_上限',
 '收费区间_下限',
 '机构性质',
 '机构类型',
 '特色服务',
 '特色服务_具备医保定点资格',
 '特色服务_可接收异地老人',
 '电话',
 '网址',
 '联系人',
 '详情_入住须知',
 '详情_收费标准',
 '详情_服务内容',
 '详情_机构介绍',
 '详情_设施',
 '负责人',
 '邮箱',
 '邮编']
def scrape_detail(url):
    pid = re.search('resthome/(\d+)\.html', url).group(1)
    info = {'id':pid}
    hxs = etree.HTML(requests.get(url).content)
    # phone
    try:
        phone = hxs.xpath('/html/body/div[6]/div[1]/div[1]/div/div[2]/ul/li[@class="phone"]/text()')[0].strip()
        info['电话'] = phone
    except IndexError:
        pass
    # hotness
    try:
        hotness = hxs.xpath('/html/body/div[6]/div[1]/div[1]/div/div[1]/span[last()]/text()')[0].split('：')
        info[hotness[0].strip()] = int(hotness[-1])
    except IndexError:
        pass
    # basic info
    items = hxs.xpath('/html/body/div[6]/div[1]/div[2]/div[2]/div[1]/div/ul/li')
    for item in items:
        try:
            key = item.xpath('em/text()')[0].replace(' ','').replace('：','')
            value = ''.join(item.xpath('.//text()')[1:]).strip()
            if key=='收住对象':
                value = value.split()
                for k in value:
                    info['{}_{}'.format(key, k)] = True
                value = ' '.join(value)
            elif key=='所在地区':
                value = value.replace(' ','').split('-')
                for i in range(len(value)):
                    info['{}_{}'.format(key, area_title[i])] = value[i]
                value = '-'.join(value)
            elif key=='特色服务':
                value = value.split()
                for k in value:
                    info['{}_{}'.format(key, k)] = True
                value = ' '.join(value)
            elif key=='收费区间':
                value = value.replace(' ','').split('-')
                for i in range(len(value)):
                    info['{}_{}'.format(key, cost_title[i])] = value[i]
                value = '-'.join(value)
            info[key] = value
        except IndexError:
            pass
    # contact info
    items = hxs.xpath('//*[@id="boxWrap"]/div/ul/li')
    for item in items:
        try:
            key = item.xpath('em/text()')[0].replace(' ','').replace('：','')
            value = ''.join(item.xpath('.//text()')[1:]).strip()
            info[key] = value
        except IndexError:
            pass
    for part in parts:
        xpath_query = '//div[@class="{}"]/div[@class="cont"]//text()'.format(part)
        try:
            info[parts[part]]=' '.join(
                (''.join(hxs.xpath(xpath_query))).split()
                                       )
        except Exception:
            pass
    return info

def export2csv(file, items, fieldnames=None):
    if not fieldnames:
        fieldnames = list(items.keys())
    writer = csv.DictWriter(file, fieldnames=fieldnames, restval='', extrasaction='ignore')
    if file.tell()==0:
        writer.writerow(dict((t,t) for t in fieldnames))
    writer.writerows(items)
    return file

def scrape_location(location):
    print('scraping '+location)
    host = 'http://www.yanglao.com.cn'
    base_url = '{}/{}'.format(host, location)
    # get number of pages
    hxs = etree.HTML(requests.get(base_url).content)
    last_page_url = hxs.xpath('//*[@id="yw1"]/li[14]/a/@href')[0]
    pages = 1
    try:
        pages = int(last_page_url.split('_')[-1])
    except Exception:
        pass
#     data = []
    count = 0
    filename = '{}.csv'.format(location)
    csv_file = codecs.open(filename, 'wb','utf-8-sig')
    fieldnames = set()
    for page_n in range(1, pages+1):
        url = ''
        if page_n==1:
            url = base_url
        else:
            url = '{}_{}'.format(base_url, page_n)
        hxs = etree.HTML(requests.get(url).content)
        homes = hxs.xpath('//*[@id="yw0"]/ul/li/div/h4/a/@href')
        for relative_url in homes:
            info = scrape_detail(host+relative_url)
#             data.append(info)
            fieldnames |= set(info.keys())
            count += 1
            export2csv(csv_file, [info], fn)
        print(page_n, count, info['id'])
    # export2csv(csv_file, data, fn)
    csv_file.close()
    print(len(fn), len(fieldnames))
for loc in ['jiangsu']:
    scrape_location(loc)