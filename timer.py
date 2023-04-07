#!/usr/bin/env python
import time
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from threading import Lock
import random

class Timer(object):

    current_date: date
    researcher_id: str
    lock: Lock = Lock()
    run: bool

    def __init__(self, researcher_id: str) -> None:
        # initialize date
        self.current_date = date.today()
        self.researcher_id = researcher_id
        self.run = True

    def start(self) -> None:
        while self.run:
            #print(f" [T-{self.researcher_id}] Current date: {self.current_date.strftime('%d-%m-%Y')}")
            with self.lock:
                self.current_date = self.current_date + relativedelta(days=1)
            #increase date between 1 and 5 seconds
            time_to_sleep = random.randint(4, 6)
            time.sleep(time_to_sleep)
    
    def stop(self) -> None:
        self.run = False

    def get_time(self) -> date:
        with self.lock:
            return self.current_date
        
    def get_time_str(self) -> str:
        with self.lock:
            return self.current_date.strftime("%d-%m-%Y")
        
    #adjust timer after receiving request
    def adjust_timer(self, timestamp: str) -> None:
        timestamp_to_date = datetime.strptime(timestamp, '%d-%m-%Y').date()
        with self.lock:
            if self.current_date < timestamp_to_date:
                self.current_date = timestamp_to_date + relativedelta(days=1)