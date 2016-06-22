#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" A multiprocess `Pool` variant with a `ProgressBar`.  """

__author__ = "Valentin Haenel <valentin.haenel@epfl.ch>"

import time
from multiprocessing.pool import Pool
from progressbar import ProgressBar, Percentage, Bar, ETA

class ProgressPool(Pool):
    """ Extension of `multiprocessing.Pool` with `ProgressBar`.

    The `map` function now displays a progress bar. The usual caveats about
    multiprocessing not working in an interactive interpreter apply.

    """

    def __init__(self, bar, loop):
	super(ProgressPool, self).__init__()
	self.bar = bar
	self.loop = loop
	
    def map(self, func, iterable, callback, chunksize=1, pbar='ProgressPool'):
        """ Apply function on iterables in available subprocess workers.

        Parameters
        ----------
        func : callable
            the function to execute
        iterable : iterable
            the arguments to the func
        chunksize : int, default: 1
            the approximate number of tasks to distribute to a process at once
        pbar : str or ProgressBar
            if str, use the string in a standard ProgressBar, else use the
            given ProgressBar

        Returns
        -------
        results : list
            the result of applying func to each value in iterables

        Raises
        ------
        TypeError if the pbar argument has the wrong type

        """
        # need to get the length, for the progress bar
        if not hasattr(iterable, '__len__'):
            iterable = list(iterable)
        total_items = len(iterable)

        # initialize the progress bar
        self.bar.done = total_items

        # get the pool working asynchronously
        a_map = self.map_async(func, iterable, chunksize, callback=callback)

        # Crux: monitor the _number_left of the a_map, and update the progress
        # bar accordingly
        # TODO should probably check for termination on each run here
        def update_completion(loop, user_data):
            time.sleep(0.1)
            left = a_map._number_left
            self.bar.set_completion(total_items-left)

            if left == 0:
                return
	    loop.set_alarm_in(0.2,update_completion)
            loop.draw_screen()
        self.alarm = self.loop.set_alarm_in(0.2,update_completion) 
        return a_map

