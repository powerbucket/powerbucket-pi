from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
import numpy as np
import matplotlib.pyplot as plt
import itertools
import copy
from datetime import datetime
import sys
import time
from scipy import signal

import pygsheets

# input in rad
# output number between (0,10)
def angle_to_power_old(t, ccw=True):

        x = 10* (t - np.pi/2)/(2*np.pi)

        if (ccw):
                return (10-x)
        else:
                return (10+x) % 10

def angle_to_power(t, ccw=True):
        x = 10 * t / (2*np.pi)

        if (ccw):
                return x
        else:
                return 10-x

def write_timestamp_and_power_scalar(wks,power,pic_time):
        rownum=1
        cell_val=wks.get_value('D{}'.format(rownum))
        while cell_val!='':
                rownum+=1
                cell_val=wks.get_value('D{}'.format(rownum))
        wks.update_value('D{}'.format(rownum),pic_time)
        wks.update_value('E{}'.format(rownum),power)

def write_timestamp_and_power(wks,power,pic_time):
        col_names=['D','E','F','G','H','I']
        rownum=1
        cell_val=wks.get_value('{}{}'.format(col_names[0],rownum))
        while cell_val!='':
                rownum+=1
                cell_val=wks.get_value('{}{}'.format(col_names[0],rownum))
        wks.update_value('{}{}'.format(col_names[0],rownum),pic_time)
        for i in range(len(power)):
                wks.update_value('{}{}'.format(col_names[i+1],rownum),power[i])

def picture_to_power(picture_path,x,y,r,back_height_percentage,width_percentage,debug=False):
        
        image = Image.open(picture_path)
        image=image.convert('L') # monochrome
        image=ImageOps.invert(image)
        # PIL does stuff upside down 
        image = np.flipud(np.array(image))

        num_circles=5
        
        cropped_image=image[y-r:y+r,x-r:x+(num_circles*2-1)*r]
        
        num_circles=5
        final_power=[]
        thetas = np.linspace(0,2*np.pi,num=200,endpoint=False) 
        for i,which_circle in enumerate(np.arange(num_circles)):
                single_circle=cropped_image[:,which_circle*2*r:(which_circle+1)*2*r]

                length_correlation=int(len(thetas) * width_percentage)
                filter_correlation=np.zeros(len(thetas))
                filter_correlation[:int(length_correlation/2)]=1
                filter_correlation[-int(length_correlation/2):]=1
                
                r_correlation=int(r/2)

                if debug:
                        polar_im=np.zeros((r,len(thetas)))
                        for r_ind in range(r):
                                for theta_ind,theta in enumerate(thetas):
                                        polar_im[r_ind,theta_ind]=single_circle[int(np.floor(np.cos(theta)*r_ind+r)),
                                                                                int(np.floor(np.sin(theta)*r_ind+r))]

                        circular_signal=np.concatenate((polar_im,polar_im),axis=1)
                                
                        correlation=np.array(list(reversed(np.correlate(filter_correlation,
                                                                        circular_signal[r_correlation,:],
                                                                        mode='valid'))))
                else:
                        circle_im=np.zeros(len(thetas))
                        for theta_ind,theta in enumerate(thetas):
                                circle_im[theta_ind]=single_circle[int(np.floor(np.cos(theta)*r_correlation+r)),
                                                                   int(np.floor(np.sin(theta)*r_correlation+r))]
                        circular_signal=np.concatenate((circle_im,circle_im))
                        correlation=np.array(list(reversed(np.correlate(filter_correlation,
                                                                        circular_signal,
                                                                        mode='valid'))))

                best_location=( np.argmax(correlation)-1 ) 

                theta_min=thetas[best_location]

                power=angle_to_power(theta_min, not which_circle%2)
                # if i!=num_circles-1:
                #         power=np.floor(power)
                # final_power+=power
                final_power.append(power)

                if debug:
                        print(theta_min*180/np.pi)
                        print(power)

                        fig,(ax1,ax2)=plt.subplots(2,sharex=True)
                        
                        polar_grid=np.meshgrid(thetas,list(range(r)))
                        ax1.contourf(polar_grid[0],polar_grid[1],polar_im)

                        ax2.plot(thetas,correlation[1:])
                        
                        circular_thetas=np.concatenate((thetas,thetas))
                        ax1.scatter(circular_thetas[best_location-int(length_correlation/2):best_location+int(length_correlation/2)],
                                    [r_correlation]*length_correlation,c='r')
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
        positive_r_offsets=[0]
        negative_r_offsets=[1]

        max_vals=[]
        max_inds=[]
        convolutions=[]
        filters=[]
        for r in r_arr: #np.arange(int(new_scale*.05),int(new_scale*.1))

                ##### Build filter #####
                thetas=np.linspace(0,2*np.pi,360,endpoint=False)
                filter=np.zeros((r*2,r*2*num_circles))
                ### Fill the negative values first so the positive overwrites it
                for i in range(num_circles):
                        for theta in thetas:
                                ###### only look at half-circles for the edge circles
                                if i==0 and theta>np.pi/2 and theta<3*np.pi/2:
                                        continue
                                if i==num_circles-1 and (theta<np.pi/2 or theta>3*np.pi/2):
                                        continue
                                
                                for r_offset in negative_r_offsets:
                                        try:
                                                filter[int(np.floor(r+(r+r_offset)*np.sin(theta))),
                                                       int(np.floor((2*i+1)*r+(r+r_offset)*np.cos(theta)))]=-1
                                        except:
                                                pass
                for i in range(num_circles):
                        for theta in thetas:
                                ###### only look at half-circles for the edge circles
                                if i==0 and theta>np.pi/2 and theta<3*np.pi/2:
                                        continue
                                if i==num_circles-1 and (theta<np.pi/2 or theta>3*np.pi/2):
                                        continue
                                
                                for r_offset in positive_r_offsets:
                                        try:
                                                filter[int(np.floor(r+(r+r_offset)*np.sin(theta))),
                                                       int(np.floor((2*i+1)*r+(r+r_offset)*np.cos(theta)))]=1  
                                        except:
                                                pass

                filters.append(filter)
                convolution=signal.convolve2d(filter,imageWithEdges,mode='valid')
                max_vals.append(np.max(convolution))
                max_inds.append(np.unravel_index(convolution.ravel().argmax(),convolution.shape))
                convolutions.append(convolution)

        max_vals=np.array(max_vals)
        max_inds=np.array(max_inds)
        
        ind=np.argmax(max_vals)
        r=int(r_arr[ind]*scale_factor)
        x=int(max_inds[ind][1]*scale_factor+r)
        y=int(max_inds[ind][0]*scale_factor+r)

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
                ax3.contourf(filters[ind])

                plt.show()
                
                plt.contourf(image)
                
                thetas=np.linspace(0,2*np.pi,endpoint=False)
                for i in range(num_circles):
                        plt.scatter(x+i*2*r,y,c='r')
                        for theta in thetas:
                                plt.scatter(x+i*2*r+r*np.cos(theta),y+r*np.sin(theta),c='orange',alpha=.1)
                plt.show()

        return((x,y,r))
                
def main():
        verbose = True
        
        if verbose:
                if len(sys.argv)<2:
                        print('test case:')
                else:
                        print(sys.argv[1])
                prev_time=time.time()
                
        client=pygsheets.authorize()
        if verbose:
                next_time=time.time()
                print('authorization time: {}'.format(next_time-prev_time))
                prev_time=next_time

        sh=client.open('173power')
        if verbose:
                next_time=time.time()
                print('opening sheet time: {}'.format(next_time-prev_time))
                prev_time=next_time
        
        wks=sh.sheet1

        # if the user doesn't specify a file do the test case...
        if len(sys.argv)<2:
                print ('usage: python program.py fname')
                print ('using default "joe_easy_test.jpg" ')
                print('answer should be 89359.9')
                picture_path='pictures/joe_easy_test.jpg'
                x=1178
                y=1340
                r=133
                back_height_percentage=.2 # .2 is for non-radial version
                width_percentage=.11 #.3 is for non-radial version

        else:
                picture_path=sys.argv[1]
                if (wks.get_value('B7')!=''):
                        wks.update_value('B7','')
                        x,y,r=picture_to_circle_parameters(picture_path,
                                                           debug=False)
                        wks.update_value('B2',x)
                        wks.update_value('B3',y)
                        wks.update_value('B4',r)
                else:
                        x=int(wks.get_value('B2'))
                        y=int(wks.get_value('B3'))
                        r=int(wks.get_value('B4'))
                back_height_percentage=float(wks.get_value('B5'))
                width_percentage=float(wks.get_value('B6'))
                if verbose:
                        next_time=time.time()
                        print('getting parameters time: {}'.format(next_time-prev_time))
                        prev_time=next_time

        power = picture_to_power(picture_path,
                                 x,
                                 y,
                                 r,
                                 back_height_percentage,
                                 width_percentage,
                                 debug=False)
        if verbose:
                next_time=time.time()
                print('getting power time: {}'.format(next_time-prev_time))
                prev_time=next_time

        pic_time=picture_path[:-4] #datetime.now().strftime("%m/%d/%Y %H:%M:%S")

        write_timestamp_and_power(wks,power,pic_time)
        if verbose:
                next_time=time.time()
                print('writing power time: {}'.format(next_time-prev_time))
                prev_time=next_time

        if verbose:
                print()
                        
if __name__ == '__main__':
        main()
