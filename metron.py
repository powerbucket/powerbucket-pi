'''
  This is a library of functions for write_power.py
  Updated: 4 April 2021
'''

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
#import imutils
import cv2

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
        
def find_energy_pic(pic_file_array,debug=False):
    return pic_file_array[2]

def find_energy_pic_real(pic_file_array,debug=False):
        n = len(pic_file_array)
        pic_series = []
        for i in range(n):
                pic_series.append(cv2.imread(pic_file_array[i]))
        
        cropped = []
        for i in range(n):
                dimensions = pic_series[i].shape
                # height and width of image
                h = pic_series[i].shape[0]
                w = pic_series[i].shape[1]
                xi = int(0.2*w) 
                yi = int(0.15*h) 
                xf = int(0.8*w) 
                yf = int(0.5*h)
                cropped.append(pic_series[i][yi:yf, xi:xf])
        if debug:
            plt.imshow(cropped[0])
            plt.title('Chosen picture')
            plt.show()
        
        most_cnts = []
        energy = cropped[0]
        pic_number = 0
        for i in range(n):
                gray = cv2.cvtColor(cropped[i], cv2.COLOR_BGR2GRAY)
                edged = cv2.Canny(gray, 50, 200, 255)
                cnts = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                most_cnts.append(imutils.grab_contours(cnts))
                if i == 0:
                        most_contours = len(most_cnts[0])
                if i>0:
                        if len(most_cnts[i]) > most_contours:
                                most_contours = len(most_cnts[i])
                                energy = cropped[i]
                                pic_number = i
        if debug:
            plt.imshow(energy)
            plt.show()
        return pic_file_array[pic_number]

def pic_to_dig_reading(x, y, w, h, s, energy_pic, debug=False):
    return [1,1,1,1,1]

def pic_to_dig_reading_real(x, y, w, h, s, energy_pic, debug=False):
        # define the dictionary of digit segments
        DIGITS_LOOKUP = {
                (1, 1, 1, 0, 1, 1, 1): 0,
                (0, 0, 1, 0, 0, 1, 0): 1,
                (1, 0, 1, 1, 1, 1, 0): 2,
                (1, 0, 1, 1, 0, 1, 1): 3,
                (0, 1, 1, 1, 0, 1, 0): 4,
                (1, 1, 0, 1, 0, 1, 1): 5,
                (1, 1, 0, 1, 1, 1, 1): 6,
                (1, 0, 1, 0, 0, 1, 0): 7,
                (1, 1, 1, 1, 1, 1, 1): 8,
                (1, 1, 1, 1, 0, 1, 1): 9
        }

        # prep the picture to read pixels
        im = cv2.imread(energy_pic)
        plt.imshow(im)
        plt.show()
        dimensions = im.shape
        y = im.shape[0] - y

        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5,5), 0)
        thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)[1]
        plt.imshow(thresh)
        plt.show()
        # loop over each of the digits
        digits = []
        for i in range(5):      
                # extract the digit ROI
                roi = thresh[y:y+h, x:x+w]
                plt.imshow(roi)
                plt.show()
                (roiH, roiW) = roi.shape
                (dW, dH) = (int(roiW * 0.25), int(roiH * 0.10))
                dHC = int(roiH * 0.05)
                
                # define the set of 7 segments
                segments = [
                        ((dW, 0), (w - dW, dH)), # top
                        ((0, 0), (dW, h//2)), # top left
                        ((w - dW, 0), (w, h//2)), # top right
                        ((dW, h//2 - dHC), (w - dW, h//2 + dHC)), # center
                        ((0, h//2), (dW, h)), # bottom left
                        ((w - dW, h//2), (w, h)), # bottom right
                        ((dW, h - dH), (w - dW, h)) # bottom                    
                ]
                on = [0] * len(segments)

                for (i, ((xA, yA), (xB, yB))) in enumerate(segments):
                        # extract the segment ROI
                        # count the total number of thresholded pixels in the segment
                        # and then compute the area of the segment
                        segROI = roi[yA:yB, xA:xB]
                        total = cv2.countNonZero(segROI)
                        area = (xB - xA) * (yB - yA)
                        
                        # if the total number of non-zero pixels is greater than 40% of the area
                        # mark the segment as "on"
                        if total / float(area) > 0.4:
                                on[i] = 1

                digit = DIGITS_LOOKUP[tuple(on)]
                digits.append(digit)
        
                x = x+s
        
        return digits
