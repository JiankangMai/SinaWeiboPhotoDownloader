# 新浪图片下载器


## 简介

自用开车工具，用于下载新浪某用户在微博处的发布所有图片

## 依赖
* python 3.4
* python/requests


## 使用
###linux
1. 安装python3，pip：略
2. 安装python/requests 模块：`sudo pip install requests`
3. 配置configure.json文件：见下
4. python3 downloader.py
###window
同上，略

##配置说明
    {
      "weiboUrl":"http://weibo.com/u/3937348351?topnav=1&wvr=6&topsug=1&is_hot=1",
      "cookieStr":"SUB=_2A256o1qkDeTxaedM7FYX8yzFyz2IHXVZ2ctsrDV8PUNbmtBeLXD2kW93O-BgeXGKb8uoAhokO282tLII3w..; SUHB=0P19ta0gqYwMQP; ALF=1505109297; wvr=6; UOR=www.sina.com.cn,weibo.com,login.sina.com.cn; SINAGLOBAL=824138557934.2789.1470555046768; ULV=1470573324155:2:2:2:7969681356946.756.1470573304147:1470555046831; YF-Page-G0=f70469e0b5607cacf38t47457e34254f; SSOLoginState=1470573100; _s_tentry=login.sina.com.cn; Apache=7969681356946.756.1470573304147; YF-V5-G0=e2def7ce19d3add53399b12462da454a",
      "threadNum":20
    }
*《configure.json》*

- weiboUrl：该用户的任意微博页面
- cookieStr：cookie字符串，可以通过浏览器console中输入*copy(document.cookie)*复制到黏贴版中，但其中一重要cookie‘SUB’为httponly，需要手动添加。**基于安全问题默认cookie做了少量调整，无法直接使用**
- threadNum：下载并发数
- netTimeout：超时重试秒数
##其余


使用中有任何疑问可发邮件到maijiankang@foxmail.com
##License
The MIT License (MIT)

Copyright 2016 maijiankang@foxmail.com
