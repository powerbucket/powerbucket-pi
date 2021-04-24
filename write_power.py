# Updated 25 Jan 2015

import numpy as np
#import matplotlib.pyplot as plt

import sys
import os
import subprocess

import time
from datetime import datetime
import metron 

base_dir=os.path.dirname(os.path.realpath(__file__))

verbose = True
debug   = False
use_google=False

if use_google:
    import pygsheets
    gsheet_name = '912-power' # User input!

def main():

    pic_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if verbose:
        if len(sys.argv)<2:
            print('take picture')
        else:
            print('pictures: '+str(sys.argv[1:]))
        prev_time=time.time()

    # if the user doesn't specify a file, assume this is the pi and
    # we want to take the picture(s) 
    if len(sys.argv)<2:
        take_pic=True
        #print ('usage: python program.py fname')
        #print ('using default "joe_easy_test.jpg" ')
        #print('answer should be 89359.9')
        #picture_path='pictures/joe_easy_test.jpg'
        #pic_file_array=[picture_path]*3
        # x=1178
        # y=1340
        # r=133
    else:
        take_pic=False
        pic_file_array=sys.argv[1:]
        picture_path=pic_file_array[0]

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
        update_params=(out[0]=='checked')
        x=int(out[1])
        y=int(out[2])
        r=int(out[3])
        s=int(out[4])
        w=int(out[5])
        h=int(out[6])
        is_analog=(out[-2]=='Analog')
        calculate_online=(out[-1]=='checked')

        if take_pic:
            subprocess.check_output(['python', os.path.join(base_dir, 'flash_on.py')])
            if is_analog:
                picture_path=os.path.join(base_dir,
                                          "pictures",
                                          str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))+'.jpg')
                subprocess.check_output(['raspistill',
                                         '-vf','-hf','-o',
                                         picture_path])
            else:
                pic_file_array=[]
                num_pics=5
                sleep_time=2.8
                for i in range(num_pics):
                    pic_file_array.append(os.path.join(base_dir,
                                                      "pictures",
                                                      '{}_{}.jpg'.format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),i)))
                    subprocess.check_output(['raspistill',
                                             '-vf','-hf','-o',
                                             pic_file_array[-1]])
                    time.sleep(sleep_time)
            subprocess.check_output(['python', os.path.join(base_dir, 'flash_off.py')])
        
        if update_params and not calculate_online:
            if is_analog:
                x,y,r=metron.picture_to_circle_parameters(picture_path,
                                                          debug=debug)
                # see the "if update" portion of login.sh, order is
                # x,y,r,
                # s,h,w,
                # update,meter_type,calculate_online
                command_list=[os.path.join(base_dir,'login.sh'),'update',
                              str(x),str(y),str(r),
                              str(s),str(h),str(w),
                              str(False),str(0),str(calculate_online)]
                subprocess.check_call(command_list)
            
    if verbose:
        next_time=time.time()
        print('getting parameters time: {}'.format(next_time-prev_time))
        prev_time=next_time

    # if user wants to calculate on website just set to a dummy value for now,
    # say all 0s
    if calculate_online:
        power = [0,0,0,0,0]
    else:
        if is_analog:
            power = metron.picture_to_power(picture_path,
                                            x,
                                            y,
                                            r,
                                            debug=debug)
        else:
            picture_path = metron.find_energy_pic(pic_file_array)
            power = metron.pic_to_dig_reading(x,y,w,h,s,picture_path,debug=debug)

    if verbose:
        next_time=time.time()
        print('getting power time: {}'.format(next_time-prev_time))
        prev_time=next_time

    # to get the exact time at which the pic was taken
    # (might be off by a minute since the pi takes
    # that long to calculate
    #pic_time=picture_path[:-4] 

    if not debug:
        if use_google:
            metron.write_google(wks,power,pic_time)
        else:
            metron.write_website(picture_path,power,pic_time)

    if verbose:
        next_time=time.time()
        print('writing power time: {}'.format(next_time-prev_time))
        prev_time=next_time
        print()
            
if __name__ == '__main__':
    main()
