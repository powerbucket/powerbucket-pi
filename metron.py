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

import time
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
def write_website(power, pic_time):
    base_dir=os.path.dirname(os.path.realpath(__file__))
    command_list=[os.path.join(base_dir,'login.sh'),'write']
    command_list+=[str(pic_time)]
    command_list+=[str(numeral) for numeral in power]
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

def read_image(picture_path, new_scale, debug=False):

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
    print('scale_factor:', scale_factor)
    imageWithEdges = imageWithEdges.resize((int(new_scale*size_ratio),new_scale),Image.ANTIALIAS)

    # PIL does stuff upside down 
    imageWithEdges=np.flipud(np.array(imageWithEdges))
    image=np.flipud(np.array(image))

    return image, imageWithEdges, scale_factor

# builds a window of N circles side by side
# the edge circles only contain half windows
# must have at least N > 3 (else degenerate)
def build_window(r,num_circles):

    ##### Build window #####
    # The window is composed of two rings, which sum to 0 in principle. 
    # A negative ring is slightly large than the positive ring.
    p_window = np.zeros( (r*2, 2*r*num_circles) )
    n_window = np.zeros( (r*2, 2*r*num_circles) )

    thetas = np.linspace(0,2*np.pi,360,endpoint=False)
    positive_r_offset = 0
    negative_r_offset = 1

    ### Fill the negative values first so the positive overwrites it

    circle_weights = [1,2,2,3,5]
    for i in range(num_circles):
        for theta in thetas:
           ###### only look at half-circles for the edge circles
            if i==0 and theta>np.pi/2 and theta<3*np.pi/2:
                continue
            if i==num_circles-1 and (theta<np.pi/2 or theta>3*np.pi/2):
                continue

            # first edit negatives
            try:
                n_window[ int(np.floor( r+(r+negative_r_offset)*np.sin(theta) )),
                    int(np.floor( (2*i+1)*r+(r+negative_r_offset)*np.cos(theta) ))]= -circle_weights[i]
            except:
                pass

            # then edit positives
            try:
                p_window[int(np.floor(r+ (r+positive_r_offset)*np.sin(theta))),
                         int(np.floor((2*i+1)*r+(r+positive_r_offset)*np.cos(theta)))]= circle_weights[i] 
            except:
                pass
            
            # weight center
            #p_window[int(np.floor(r )), int(np.floor((2*i+1)*r ))] = 2
    
    weight = np.abs( np.sum(p_window)/ np.sum(n_window) )      
    window = p_window + n_window * weight
    
    return window
 


def square_circle_window(r,num_circles=5):
    
    positive_r_offset = 0
    negative_r_offset = 1
    
    ##### Build window #####
    # The window is composed of a negative square (2D), overlayed with a positive circle (1D)
    # The overall sum is 0.
    
    p_window = np.zeros( (r*2, 2*r*num_circles) )
    n_window = np.zeros( (r*2, 2*r*num_circles) ) - 1
    thetas = np.linspace(0,2*np.pi,360,endpoint=False)

    ### Fill the negative values first so the positive overwrites it

    circle_weights = [1,2,2,3,5]
    for i in range(num_circles):
        for theta in thetas:
           ###### only look at half-circles for the edge circles
            if i==0 and theta>np.pi/2 and theta<3*np.pi/2:
                continue
            if i==num_circles-1 and (theta<np.pi/2 or theta>3*np.pi/2):
                continue

            # then edit positives
            try:
                p_window[int(np.floor(r+ (r+positive_r_offset)*np.sin(theta))),
                         int(np.floor((2*i+1)*r+(r+positive_r_offset)*np.cos(theta)))]= circle_weights[i]
            except:
                pass
            
            # weight center
            #p_window[int(np.floor(r )), int(np.floor((2*i+1)*r ))] = 1
    
    #print( np.sum(p_window), np.sum(n_window) )
    weight = np.abs( np.sum(p_window)/ np.sum(n_window) )      
    window = p_window + n_window * weight
    
    return window

def find_circle(picture_path, new_scale=200, debug=True, crop=True):

    image, imageWithEdges, scale_factor = read_image(picture_path, new_scale)
    
    # crop image
    yc,xc = np.shape(imageWithEdges)
    x_filter = 0.1
    y_filter = 0.2
    
    xmin = int(xc*x_filter)
    xmax = int(xc*(1-x_filter))   
    ymin = int(yc*y_filter)
    ymax = int(yc*(1-y_filter))
    crop_reduced_image = imageWithEdges[ymin:ymax,xmin:xmax]

    if debug:
        plt.figure(figsize=(8,4))
        
        plt.subplot(1,2,1)
        plt.title('Image')
        plt.contourf(image) # first image
        plt.colorbar()
    
        plt.subplot(1,2,2)
        plt.title('Image with edges')
        plt.contourf(imageWithEdges) # first image
        plt.colorbar()
        plt.axhline(ymin, color='C1', label='proposed crop')
        plt.axhline(ymax, color='C1')
        plt.axvline(xmin, color='C1')
        plt.axvline(xmax, color='C1')
        plt.legend()
        
        plt.show()
        
        
    max_vals=[]
    max_inds=[]
    convolutions=[]
    windows=[]
    
    num_circles=5
    
    r_arr = np.arange(3,15)
    for r in r_arr: 
    # for each radius, build a window, and scan
    
        window = build_window(r,num_circles=num_circles)
        #window = square_circle_window(r,num_circles=num_circles)
        windows.append(window)
        
        # main computation is here: signal.convolve2d
        
        
        if (crop):
            convolution = signal.convolve2d(window,crop_reduced_image,mode='valid')
        else:
            convolution = signal.convolve2d(window,imageWithEdges,mode='valid')
            
        convolutions.append(convolution)
        max_vals.append(np.max(convolution))
        max_inds.append(np.unravel_index(convolution.ravel().argmax(), convolution.shape)) # get 2D index
        
    
    max_vals=np.array(max_vals)
    max_inds=np.array(max_inds)
    
    ind = np.argmax(max_vals) # choose max out of r_arr
    
    
    # x,y,r - scaled, reduced coordinaes
    # X,Y,R - original, larger coordinates
    r = r_arr[ind]
    x = max_inds[ind][1] + r
    y = max_inds[ind][0] + r
    
    if crop:
        x += xmin
        y += ymin
        
    X = int( x*scale_factor )
    Y = int( y*scale_factor )
    R = int( r*scale_factor )

    if debug:
    
        plt.figure()
        plt.contourf(image)
    
        thetas=np.linspace(0,2*np.pi,endpoint=False)
        for i in range(num_circles):
            plt.scatter(X + i*2*R, Y, c='r')
            for theta in thetas:
                plt.scatter(X + i*2*R + R*np.cos(theta),
                            Y + R*np.sin(theta),c='orange',alpha=.1)
                
        plt.axhline(ymin*scale_factor, color='C1')
        plt.axhline(ymax*scale_factor, color='C1')
        plt.axvline(xmin*scale_factor, color='C1')
        plt.axvline(xmax*scale_factor, color='C1')
    
    
        plt.show()
        value = input('  Are you satisfied? [y]/n\n')
        if value == 'n':
            print('user says no')
            X,Y,R = user_select(image)
        else:
            print('user says yes')
    
    print('x,y,r:', X,Y,R)

    # ((,)) for html
    return ((X,Y,R))
    
coords = []
def user_select(img):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    #global picture_path
    
    #ax.set_title( picture_path.split('/')[-1] )
    
    ax.contourf(img)
    
    
    def plot_circle(x,y,r, N=100):
    
        t = np.linspace(0,np.pi*2,N,endpoint=False)
        X = x + r*np.cos(t)
        Y = y + r*np.sin(t)
    
        plt.plot(X,Y,'C1')
    
    def onclick(event):
        global ix, iy
        ix, iy = event.xdata, event.ydata
        print ('x = %d, y = %d'%( ix, iy) )
        plt.plot(ix,iy,'C1*')
        plt.draw()
    
        global coords
        coords.append((ix, iy))
    
        if len(coords) == 5:
            fig.canvas.mpl_disconnect(cid)
    
            x,y = np.transpose(coords)
            dx = ( x[1:] - x[:-1] )/2
            dy = ( y[1:] - y[:-1] )/2
            r  = np.mean( np.sqrt(dx*dx + dy*dy) )
            print('average radius:',r)
    
            for i in range(5):
                plot_circle(x[i],y[i],r)
    
        #return coords
    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()    
    
    x,y = np.transpose(coords)
    dx = ( x[1:] - x[:-1] )/2
    dy = ( y[1:] - y[:-1] )/2
    r  = np.mean( np.sqrt(dx*dx + dy*dy) )
    #return x[-1], y[-1], r
    return x[0], y[0], r
        
### main functions
def load_file(argv, verbose=False):

    if verbose:
        if len(argv)<2:
            print('test case:')
        else:
            print(argv[1])
        prev_time=time.time()

    # if the user doesn't specify a file do the test case...
    if len(argv)<2:
        print ('usage: python program.py fname')
        print ('using default "joe_easy_test.jpg" ')
        print('answer should be 89359.9')
        picture_path='pictures/joe_easy_test.jpg'
        # x=1178
        # y=1340
        # r=133
    else:
        picture_path=argv[1]

    return picture_path

