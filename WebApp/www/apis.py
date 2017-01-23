#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

'''
JSON API definition.
'''

import json, logging, inspect, functools

class PageManager(object):
    def __init__(self,blog_count,page_index = 1,page_base = 3):
        self.blog_count = blog_count
        self.current_page = page_index
        if blog_count%page_base != 0 and blog_count > page_base:
            self.page_count = int(blog_count/page_base) + 1
        elif blog_count <= page_base:
            self.page_count = 1
        elif blog_count%page_base == 0:
            self.page_count = int(blog_count/page_base)
        self.offset = (page_index - 1) * page_base
        if page_index < self.page_count:
            self.limit = page_base
        elif page_index == self.page_count:
            self.limit = blog_count%page_base

        self.has_pre =  int(page_index > 1)
        self.has_next = int(page_index < self.page_count)


class APIError(Exception):
    '''
    the base APIError which contains error(required), data(optional) and message(optional).
    '''
    def __init__(self, error, data='', message=''):
        super(APIError, self).__init__(message)
        self.error = error
        self.data = data
        self.message = message

class APIValueError(APIError):
    '''
    Indicate the input value has error or invalid. The data specifies the error field of input form.
    '''
    def __init__(self, field, message=''):
        super(APIValueError, self).__init__('value:invalid', field, message)

class APIResourceNotFoundError(APIError):
    '''
    Indicate the resource was not found. The data specifies the resource name.
    '''
    def __init__(self, field, message=''):
        super(APIResourceNotFoundError, self).__init__('value:notfound', field, message)

class APIPermissionError(APIError):
    '''
    Indicate the api has no permission.
    '''
    def __init__(self, message=''):
        super(APIPermissionError, self).__init__('permission:forbidden', 'permission', message)