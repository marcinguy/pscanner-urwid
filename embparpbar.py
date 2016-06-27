#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Marcin Kozlowski <marcinguy@gmail.com>"


import time
from multiprocessing.pool import Pool
from progressbar import ProgressBar, Percentage, Bar, ETA

class ProgressPool(Pool):

    def __init__(self, bar, loop):
	super(ProgressPool, self).__init__()
	self.bar = bar
	self.loop = loop

    def map(self, func, iterable, callback, chunksize=1, pbar='ProgressPool'):
        
        # need to get the length, for the progress bar
        if not hasattr(iterable, '__len__'):
            iterable = list(iterable)
        total_items = len(iterable)

        # initialize the progress bar
        self.bar.done = total_items

        # get the pool working asynchronously
        a_map = self.map_async(func, iterable, chunksize, callback=callback)

        def update_completion(loop, user_data):
            time.sleep(0.1)
            left = a_map._number_left
            self.bar.set_completion(total_items-left)

            if left == 0:
                return
	    loop.set_alarm_in(0.1,update_completion)
            loop.draw_screen()
            
        self.alarm = self.loop.set_alarm_in(0.1,update_completion) 
        return a_map

