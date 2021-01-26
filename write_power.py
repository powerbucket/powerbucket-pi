# Updated 25 Jan 2015

import numpy as np
import matplotlib.pyplot as plt

import sys
import os
import subprocess

import time
from datetime import datetime
import metron 

base_dir=os.path.dirname(os.path.realpath(__file__))

verbose = True
debug   = True
use_google=False

if use_google:
    import pygsheets
    gsheet_name = '912-power' # User input!
    write_timestamp_and_power = metron.write_google
else:
    write_timestamp_and_power = metron.write_website


def main():
    
    if verbose:
        if len(sys.argv)<2:
            print('test case:')
        else:
            print(sys.argv[1])
        prev_time=time.time()

    # if the user doesn't specify a file do the test case...
    if len(sys.argv)<2:
        print ('usage: python program.py fname')
        print ('using default "joe_easy_test.jpg" ')
        print('answer should be 89359.9')
        picture_path='pictures/joe_easy_test.jpg'
        # x=1178
        # y=1340
        # r=133
    else:
        picture_path=sys.argv[1]

    if use_google:
        client=pygsheets.authorize()
        if verbose:
            next_time=time.time()
            print('authorization time: {}'.format(next_time-prev_time))
            prev_time=next_time

        sh=client.open(gsheet_name)
        if verbose:
            next_time=time.time()
            print('opening sheet time: {}'.format(next_time-prev_time))
            prev_time=next_time

        wks=sh.sheet1

        if (wks.get_value('B7')!=''):
            wks.update_value('B7','')
            x,y,r=picture_to_circle_parameters(picture_path,
                               debug=debug)
            wks.update_value('B2',x)
            wks.update_value('B3',y)
            wks.update_value('B4',r)
        else:
            x=int(wks.get_value('B2'))
            y=int(wks.get_value('B3'))
            r=int(wks.get_value('B4'))
    else:
        command_list=[os.path.join(base_dir,'login.sh'),'check']
        out=subprocess.check_output(command_list).decode('utf-8').split()
        # a little jank: right now if the box is unchecked the update script returns one less output
        # so we prepend unchecked just to keep everything the same length, if no output appears
        # but if there is output that's not "checked" then it will still go smoothly 
        if len(out)<4:
            out.insert(0,'unchecked')
        if out[0]=='checked':
            x,y,r=metron.picture_to_circle_parameters(picture_path,
                               debug=debug)
            command_list=[os.path.join(base_dir,'login.sh'),'update',str(x),str(y),str(r)]
            subprocess.check_call(command_list)
        else: 
            x=int(out[1])
            y=int(out[2])
            r=int(out[3])
    if verbose:
        next_time=time.time()
        print('getting parameters time: {}'.format(next_time-prev_time))
        prev_time=next_time
            

    power = metron.picture_to_power(picture_path,
                 x,
                 y,
                 r,
                 debug=debug)
    if verbose:
        next_time=time.time()
        print('getting power time: {}'.format(next_time-prev_time))
        prev_time=next_time

    pic_time=datetime.now().strftime("%m/%d/%Y %H:%M:%S")

    # to get the exact time at which the pic was taken
    # (might be off by a minute since the pi takes
    # that long to calculate
    #pic_time=picture_path[:-4] 

    if use_google:
        write_timestamp_and_power(wks,power,pic_time)
    else:
        write_timestamp_and_power(power,pic_time)

    if verbose:
        next_time=time.time()
        print('writing power time: {}'.format(next_time-prev_time))
        prev_time=next_time
        print()
            
if __name__ == '__main__':
    main()
