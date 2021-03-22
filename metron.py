'''
  This is a library of functions for write_power.py
  Updated: 25 January 2021
'''

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# Pillow library for image handling
from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps

#import itertools # unused?
import copy
import os
import subprocess

# input : radians
# output: floating number between (0,10)
def angle_to_power(t, ccw=True):
    x = 10 * t / (2*np.pi)

    if (ccw):
        return x
    else:
        return 10-x

def write_timestamp_and_power_scalar(wks,power,pic_time):
    rownum=wks.get_value('B9')
    if rownum=='':
        rownum=1
        cell_val=wks.get_value('D{}'.format(rownum))
        while cell_val!='':
            rownum+=1
            cell_val=wks.get_value('D{}'.format(rownum))
    wks.update_value('B9',int(rownum)+1)
    wks.update_value('D{}'.format(rownum),pic_time)
    wks.update_value('E{}'.format(rownum),power)

# writes timestamp and power to googlesheet
def write_google(wks,power,pic_time):
    col_names=['D','E','F','G','H','I']
    rownum=wks.get_value('B9')
    if rownum=='':
        rownum=1
        cell_val=wks.get_value('{}{}'.format(col_names[0],rownum))
        while cell_val!='':
            rownum+=1
            cell_val=wks.get_value('{}{}'.format(col_names[0],rownum))
    wks.update_value('B9',int(rownum)+1)
    wks.update_value('{}{}'.format(col_names[0],rownum),pic_time)
    for i in range(len(power)):
        wks.update_value('{}{}'.format(col_names[i+1],rownum),power[i])

# writes timestamp and power to website
def write_website(pic_path, power, pic_time):
    base_dir=os.path.dirname(os.path.realpath(__file__))
    command_list=[os.path.join(base_dir,'login.sh'),'write']
    command_list+=[str(pic_time)]
    command_list+=[str(numeral) for numeral in power]
    command_list+=["@"+pic_path]
    subprocess.check_call(command_list)
    

# Inputs: x,y are center of circle, r is radius
# Output: 5 digit power
def picture_to_power(picture_path,x,y,r,debug=False):
    
    image = Image.open(picture_path)
    image=image.convert('L') # monochrome
    image=ImageOps.invert(image)
    # PIL does stuff upside down 
    image = np.flipud(np.array(image))

    num_circles=5
    
    cropped_image=image[y-r:y+r, x-r:x+(num_circles*2-1)*r]


#    num_circles=5
    final_power=[]
    thetas = np.linspace(0,2*np.pi,num=200,endpoint=False) 
    for i,which_circle in enumerate(np.arange(num_circles)):
        single_circle=cropped_image[:,which_circle*2*r:(which_circle+1)*2*r]

        if debug:
            polar_im=np.zeros((r,len(thetas)))
            for r_ind in range(r):
                for theta_ind,theta in enumerate(thetas):
                    polar_im[r_ind,theta_ind]=single_circle[int(np.floor(np.cos(theta)*r_ind+r)),
                                        int(np.floor(np.sin(theta)*r_ind+r))]

        theta_weights=np.zeros(len(thetas))
        for theta_ind,theta in enumerate(thetas):
            for r_ind in range(r):
                theta_weights[theta_ind]+=single_circle[int(np.floor(np.cos(theta)*r_ind+r)),
                                    int(np.floor(np.sin(theta)*r_ind+r))]
        theta_min=thetas[np.argmax(theta_weights)]

        power=angle_to_power(theta_min, not which_circle%2)
        final_power.append(power)

        if debug:
            print(theta_min*180/np.pi)
            print(power)

            fig,(ax1,ax2)=plt.subplots(2,sharex=True)
            # can make subplot in one figure instead of 5
            
            polar_grid=np.meshgrid(thetas,list(range(r)))
            ax1.contourf(polar_grid[0],polar_grid[1],polar_im)

            ax2.plot(thetas, theta_weights)
            ax1.axvline(theta_min,c='r')
            ax2.axvline(theta_min,c='r')
            plt.show()
        
    return final_power

def picture_to_circle_parameters(picture_path, new_scale=200, debug=False):
    image = Image.open(picture_path)
    image=image.convert('L') # monochrome
    image=ImageOps.invert(image)

    if debug:
        plt.imshow(image)
        plt.show()

    imageWithEdges = image.filter(ImageFilter.FIND_EDGES)

    # NOTES: resizing the image first is needed to make the current 
    # circle-finding algorithm (at the bottom of the notebook) work 
    size_ratio = imageWithEdges.size[0] / imageWithEdges.size[1]
    scale_factor=imageWithEdges.size[1] / new_scale
    imageWithEdges = imageWithEdges.resize((int(new_scale*size_ratio),new_scale),Image.ANTIALIAS)

    # PIL does stuff upside down 
    imageWithEdges=np.flipud(np.array(imageWithEdges))
    image=np.flipud(np.array(image))

    num_circles=5

    if debug:
        plt.contourf(imageWithEdges)
        plt.show()

    r_arr=np.arange(1,
                    int(np.floor(min(imageWithEdges.shape[0],
                    imageWithEdges.shape[1]/num_circles)/2)))

    positive_r_offset = 0
    negative_r_offset = 1

    max_vals=[]
    max_inds=[]
    convolutions=[]
    windows=[]
    for r in r_arr: 
    # for each radius, build a window, and scan

        ##### Build window #####
        # The window is composed of two rings, which sum to 0 in principle. 
        # A negative ring is slightly large than the positive ring.
        thetas=np.linspace(0,2*np.pi,360,endpoint=False)
        window=np.zeros((r*2,r*2*num_circles))

        ### Fill the negative values first so the positive overwrites it
        for i in range(num_circles):
            for theta in thetas:
                ###### only look at half-circles for the edge circles
                if i==0 and theta>np.pi/2 and theta<3*np.pi/2:
                    continue
                if i==num_circles-1 and (theta<np.pi/2 or theta>3*np.pi/2):
                    continue
                
                # first negatives
                try:
                    window[int(np.floor(r+(r+negative_r_offset)*np.sin(theta))),
                           int(np.floor((2*i+1)*r+(r+negative_r_offset)*np.cos(theta)))]=-1
                except:
                    pass
#
#        for i in range(num_circles):
#            for theta in thetas:
#                ###### only look at half-circles for the edge circles
#                if i==0 and theta>np.pi/2 and theta<3*np.pi/2:
#                    continue
#                if i==num_circles-1 and (theta<np.pi/2 or theta>3*np.pi/2):
#                    continue
#
                # then positives
                try:
                    window[int(np.floor(r+(r+positive_r_offset)*np.sin(theta))),
                           int(np.floor((2*i+1)*r+(r+positive_r_offset)*np.cos(theta)))]=1  
                except:
                    pass

        windows.append(window)
        # main computation is here: signal.convolve2d
        convolution=signal.convolve2d(window,imageWithEdges,mode='valid')
        max_vals.append(np.max(convolution))
        max_inds.append(np.unravel_index(convolution.ravel().argmax(),convolution.shape))
        convolutions.append(convolution)

    max_vals=np.array(max_vals)
    max_inds=np.array(max_inds)
    
    ind=np.argmax(max_vals)
    r = int( r_arr[ind]*scale_factor )
    x = int( max_inds[ind][1]*scale_factor + r)
    y = int( max_inds[ind][0]*scale_factor + r)

    if debug:
        fig,(ax1,ax2,ax3)=plt.subplots(3,sharex=True,sharey=True)
        ax1.contourf(imageWithEdges)
        ax1.axvline(max_inds[ind][1],c='r')
        ax1.axvline(max_inds[ind][1]+r_arr[ind]*2*num_circles,c='r')
        ax1.axhline(max_inds[ind][0],c='r')
        ax1.axhline(max_inds[ind][0]+r_arr[ind]*2,c='r')
        ax1.scatter(max_inds[ind][1],max_inds[ind][0],c='r')
        ax2.contourf(convolutions[ind])
        ax2.scatter(max_inds[ind][1],max_inds[ind][0],c='r')
        ax3.contourf(windows[ind])

        plt.show()
        
        plt.contourf(image)
        
        thetas=np.linspace(0,2*np.pi,endpoint=False)
        for i in range(num_circles):
            plt.scatter(x+i*2*r,y,c='r')
            for theta in thetas:
                plt.scatter(x+i*2*r+r*np.cos(theta),y+r*np.sin(theta),c='orange',alpha=.1)
        plt.show()

    # ((,)) for html
    return ((x,y,r))
        
