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

verbose     = True
debug       = True
use_google  = True
UPDATE      = True

if use_google:
    import pygsheets
    gsheet_name = '912-power' # User input!
    write_timestamp_and_power = metron.write_google
else:
    write_timestamp_and_power = metron.write_website

'''
   # pseudo code

   select_image()
   if (needs_update):
       find_circles()
   else:
       download_circle_parameters()

   read_image()
   upload()
'''


def main():
   
    # 1 - Load File 
    picture_path = metron.load_file(sys.argv, verbose=verbose)
    if verbose:
        prev_time=time.time()

    # 2a - use google, get parameters
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

        if (UPDATE or wks.get_value('B7')!=''):
            wks.update_value('B7','')
            #x,y,r=metron.picture_to_circle_parameters(picture_path, debug=debug)
            x,y,r = metron.find_circle(picture_path)
            #x,y,r = (564,1022,155) # hard code (!)
            wks.update_value('B2',x)
            wks.update_value('B3',y)
            wks.update_value('B4',r)
        else:
            x=int(wks.get_value('B2'))
            y=int(wks.get_value('B3'))
            r=int(wks.get_value('B4'))

    # 2b - use website, get parameters
    else:
        command_list=[os.path.join(base_dir,'login.sh'),'check']
        out=subprocess.check_output(command_list).decode('utf-8').split()
        # a little jank: right now if the box is unchecked the update script returns one less output
        # so we prepend unchecked just to keep everything the same length, if no output appears
        # but if there is output that's not "checked" then it will still go smoothly 
        if len(out)<4:
            out.insert(0,'unchecked')
        if (UPDATE or out[0]=='checked'):
            x,y,r=metron.picture_to_circle_parameters(picture_path,
                                                      debug=debug)
            command_list=[os.path.join(base_dir,'login.sh'),'update',str(x),str(y),str(r)]
            subprocess.check_call(command_list)
        else: 
            x=int(out[1])
            y=int(out[2])
            r=int(out[3])

            
if __name__ == '__main__':
    main()
