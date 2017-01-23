#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'Leon Hwa'

' url handlers '

import re, time, json, logging, hashlib, base64, asyncio
from aiohttp import web
from coroweb import get, post

from Models import User, Comment, Blog, next_id
from  apis import APIValueError,APIError,APIPermissionError,PageManager

COOKIE_NAME = 'awesession'
_COOKIE_KEY = 'nkjnihyugyftff'

def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p
@get('/')
async def index(*,page = '1'):
    page_index = get_page_index(page)
    blogCount = await Blog.findNumber('count(id)')
    # jinja2
    return {
        '__template__': 'blogs.html',
        'blogCount':blogCount,
        'page_index' : page_index,
    }

@get('/register')
def user_registers(request):
    return {
        '__template__':'register.html'

    }


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    else:
        logging.info('找到用户')
    user = users[0]
    # check passwd:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    logging.info('设置cookie成功')
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


# 注册
@post('/api/users')
async def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = await User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    await user.save()
    # make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/signin')
def user_sigin(request):
    return {
        '__template__' :'login.html'
    }


def user2cookie(user,max_age):
    expiress = str(int(time.time()) + max_age)
    s = '%s-%s-%s-%s' % (user.id,user.passwd,expiress,_COOKIE_KEY)
    L = [user.id,expiress,hashlib.sha1(s.encode('utf-8')).hexdigest()]
    logging.info('-'.join(L))
    logging.info('cookie设置好了')
    return '-'.join(L)


async def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r



#请求创建博客页面
@get('/manager/blog/create')
def editBlog(request):
    return {
            '__template__': 'manage_blog_edit.html',
            'id': '',
            'action': '/api/blogs'
    }




@get('/blog/{id}')
async def get_detailBlog(id):
    blog = await Blog.find(id)
    c1 = Comment(id='ssd',blog_id = 'hhhhhhh',created_at = '2222')
    c2 = Comment(id='ssd', blog_id='hhhhhhh',created_at = '2222')
    comments = [c1,c2]
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }

@get('/test')
def user_register(request):
    return {
        '__template__':'test.html'

    }

# ######################################################------API--------#####################################################
'''
API
'''
#翻页
@get('/api/blogs')
async  def get_api_blogs(*,page= '1'):
    page_index = get_page_index(page)
    blogCount = await Blog.findNumber('count(id)')
    page = PageManager(blogCount, page_index)
    blogs = await Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))
    return  dict(blogs = blogs,page = page,page_index = page_index)
#保存博客
@post('/api/blogs')
async def api_create_blog(request, *, blogtitle, blogsummary, blogcontent):
    # check_admin(request)
    if not blogtitle or not blogtitle.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not blogsummary or not blogsummary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not blogcontent or not blogcontent.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=blogtitle.strip(), summary=blogsummary.strip(), content=blogcontent)
    await  blog.save()
    logging.info(blogcontent);
    return blog

def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

# @get('/api/blogs')
# async def api_blogs(*, page='1'):
#     page_index = get_page_index(page)
#     blogCount = await Blog.findNumber('count(id)')
#     page = PageManager(blogCount,page_index)
#     blogs = await Blog.findAll(orderBy='created_at desc',limit=(page.offset,page.limit))
#     return dict(blogs = blogs,page = page)

@get('/api/blogs/{id}')
async def get_blog(request,*,id):
    blog = await Blog.find(id)
    logging.info('调用  blog')
    logging.info(blog)
    return dict(blog = blog)