#! usr/bin/python
# coding=utf-8
import os
import threading
import requests
import re
import json
import time
import traceback
import requests.exceptions
import socket


def parse_user_info(weibo_url):
    """
    解析出用户page_id
    :param string weibo_url:
    :return:dict {page_id,username}
    """
    global COOKIES
    request_result = requests.get(
        weibo_url,
        cookies=COOKIES,
    ).text
    with open('request_result.html', 'wb') as file:
        file.write(request_result.encode('utf-8'))
    # 匹配目标/p/1005051274632901/home
    page_id_match_list = re.compile(
        r'\\/p\\/(\d+)\\/home').findall(request_result)
    #<h1 class=\"username\">共青团中央<\/h1>
    username_match_list = re.compile(
        r'<h1 class=\\"username\\">([\s\S]*)<\\/h1>').findall(request_result)
    if 0 == len(page_id_match_list) or 0 == len(username_match_list):
        raise BaseException('Cant parse uesrinfo.\n'
                            'You can :\n'
                            '1:check the url is valid sina weibo url.\n'
                            '2:check and update your cookie.\n'
                            '3:just retry')
    else:
        return {'page_id': page_id_match_list[0],
                'username': username_match_list[0]}


def get_first_photo(page_id):
    """
    解析出第一个图片的信息
    :param string page_id:
    :return:list photo_info [uid,mid,pic_objects,pic_objects]此类字段均为新浪命名，含义不明，下同
    """
    global COOKIES
    request_result = requests.get(
        'http://weibo.com/p/' + str(page_id) + '/photos',
        cookies=COOKIES,
    ).text
    with open('user_page.html', 'wb') as file:
        file.write(request_result.encode('utf-8'))
   # 匹配目标示例"uid=2466336935&mid=4005525836627195&pid=930150a7jw1f6k5edlv5qj20qo0zkta2&pic_objects=1042018:52b55c4e58e1d2fbb3835fac4d943748\"
    match_list = re.compile(
        r'"uid=(\d+)&mid=(\d+)&pid=([^&]+)&pic_objects=([^"^&]+)\\"').findall(request_result)
    # 一般为cookie异常
    if 0 == len(match_list):
        raise BaseException('Cant parse photo ancestor.\n'
                            'You can :\n'
                            '1:check and update your cookie.\n'
                            '2:just retry')
    else:
        return match_list[0]


def get_photo_list(mid, pid, back_queue):
    """
    新浪前端大量异步化优化，通过模仿图片播放器ajax接口获取更多图片信息
    :param string mid:
    :param string pid:
    :param string back_queue:[{mid,pid,object_id}]备用下载队列
    :return: dict
    {pic_next: {photo_id,mid,pid,type},
    pic_list: [
            {mid,pid,object_id}
    ]}
    """
    query_param = {
        'ajwvr': 6,
        'photo_id': mid,
        'mid': mid,
        'pid': pid,
        'type': -1,
        'uid': 2466336935
    }
    try:
        request_result = requests.get(
            'http://weibo.com/aj/photo/popview',
            cookies=COOKIES,
            params=query_param,
            timeout=net_timeout).text
    #     避免主线程卡住
    except requests.exceptions.Timeout as e:
        print('get list request timeout retry')
        return get_photo_list(mid, pid, back_queue)
    # 匹配目标示例$CONFIG['islogin'] = '0';
    if len(re.compile(r"\$CONFIG\['islogin'\] = '0").findall(
            request_result)) > 0:
        raise BaseException('Return unlogined status.\n'
                            'You can :\n'
                            '1:check and update your cookie.\n'
                            '2:just retry')
    else:
        result_data = json.loads(request_result)['data']
        if'' == result_data:
            # 遇到被删除的微博时回溯上一张图片
            print('Weibo be deleted,download point roll back')
            back_photo_info = back_queue.pop()
            return get_photo_list(
                back_photo_info['mid'],
                back_photo_info['pid'],
                back_queue)
        else:
            return result_data


def dowanload_from_queue(photo_info_queue):
    """
    从下载队列中获取下载内容并下载
    :param list photo_info_queue: [{mid,pid,object_id}]下载队列
    """
    global PARSE_END_FLAG, QUEUE_LOCK
    try:
        while True:
            QUEUE_LOCK.acquire()
            try:
                if len(photo_info_queue) == 0:
                    photo_info = None
                else:
                    photo_info = photo_info_queue.pop(0)
            except BaseException as e:
                raise e
            finally:
                QUEUE_LOCK.release()

            if None == photo_info:
                if PARSE_END_FLAG:
                    break
                else:
                    time.sleep(0.5)
            else:
                download_photo(str(photo_info['pid']))
    except BaseException as e:
        print(threading.current_thread().name +
              ' happen error(' + str(e) + ') and will exit()')
        with open('error_log' + threading.current_thread().name + '.log', 'wb') as error_log:
            error_log.write(traceback.format_exc().encode('utf-8'))
        exit()


def download_photo(pid):
    """
    下载图片到本地
    :param string pid:
    """
    global IMAGE_DIR_PATH

    if os.path.exists(IMAGE_DIR_PATH + pid + '.jpg') or \
            os.path.exists(IMAGE_DIR_PATH + pid + '.png') or \
            os.path.exists(IMAGE_DIR_PATH + pid + '.gif'):
        return

    try:
        request_result = requests.get(
            'http://ww3.sinaimg.cn/large/' + pid,
            timeout=net_timeout)

        imag_content = request_result.content
        content_type = request_result.headers['Content-Type']
        if'image/jpeg' == content_type:
            suffix = '.jpg'
        elif'image/png' == content_type:
            suffix = '.png'
        elif'image/gif' == content_type:
            suffix = '.gif'
        elif'image/pjpeg' == content_type:
            suffix = '.jpg'
        else:
            suffix = ''
        filename = pid + suffix
        if not os.path.exists(IMAGE_DIR_PATH + filename):
            with open(IMAGE_DIR_PATH + filename, 'wb') as imag_file:
                imag_file.write(imag_content)
            print(filename + ' have been downloaded')
        # else:
        #     print(filename + ' exist ,don\'t repeat download')
    except requests.exceptions.Timeout as e:
        print('download request timeout retry')
        return download_photo(pid)
    except socket.timeout as e:
        print('download socket timeout retry')
        return download_photo(pid)

if __name__ == '__main__':
    try:
        # 读取配置
        try:
            with open('./configure.json', 'rb') as configure_file:
                configure_json = configure_file.read().decode('utf-8')
                configure = json.loads(configure_json)
                weibo_url = str(configure['weiboUrl'])
                cookies_str = str(configure['cookieStr'])
                thread_num = int(configure['threadNum'])
                net_timeout = int(configure['netTimeout'])
        except BaseException as e:
            raise BaseException('please check your <configure.json> file.')

        # 本地初始化
        # list
        photo_list_queue = []
        photo_list_queue_back = []
        thread_pool = []

        # 全局变量
        COOKIES = dict((chip.split('=') for chip in cookies_str.split('; ')))
        PARSE_END_FLAG = False
        QUEUE_LOCK = threading.Lock()

        # 线程池
        for thread_no in range(20):
            thread = threading.Thread(
                target=dowanload_from_queue, args=(
                    photo_list_queue,))
            thread_pool.append(thread)
            thread.start()

        # RUN
        user_info = parse_user_info(weibo_url)
        page_id = user_info['page_id']
        username = user_info['username']

        IMAGE_DIR_PATH = 'download_' + username + "/"
        if not os.path.exists(IMAGE_DIR_PATH):
            os.makedirs(IMAGE_DIR_PATH)
        first_photo = get_first_photo(page_id)
        photo_info_list = get_photo_list(
            str(first_photo[1]), str(first_photo[2]), photo_list_queue_back)

        if os.path.exists('queue.log'):
            os.remove('queue.log')
        while True:
            with open('queue.log', 'ab') as log_file:
                log_file.write(json.dumps(photo_info_list).encode('utf-8'))

            photo_list_queue.extend(photo_info_list['pic_list'])
            photo_list_queue_back.extend(photo_info_list['pic_list'])
            # 没有下一张时，接口pic_next值为0
            if None is photo_info_list or 0 == photo_info_list['pic_next']:
                # print ('all photo parse end,start download!All:'+str(len(photo_list_queue))+'=============')
                PARSE_END_FLAG = True
                break
            else:
                photo_info_list = get_photo_list(
                    str(photo_info_list['pic_next']['mid']),
                    str(photo_info_list['pic_next']['pid']), photo_list_queue_back)
    except BaseException as e:
        # 全局异常区
        print('Happen Error:' + str(e))
        PARSE_END_FLAG = True
        with open('error_log' + threading.current_thread().name + '.log', 'wb') as error_log:
            error_log.write(traceback.format_exc().encode('utf-8'))
    finally:
        if(0 != len(thread_pool)):
            print('Wait other thread die')
            for thread in thread_pool:
                thread.join()
                print(thread.name + 'join success ')
