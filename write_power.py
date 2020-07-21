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

# this is the slow, inaccurate way with the full triangle scan
def picture_to_power_old(picture_path,x,y,r,back_height_percentage,width_percentage):
        image = Image.open(picture_path)
        image=image.convert('L') # monochrome
        # PIL does stuff upside down 
        image = np.flipud(np.array(image))
        num_circles=5
        image_copy=copy.deepcopy(image)
        final_power=0
        # we focus on one circle at a time for now
        thetas = np.linspace(0,360,endpoint=False) * (np.pi / 180)
        for i,which_circle in enumerate(np.arange(num_circles)):
                this_x = x+r*2*i  
                my_grid=np.array([elem for elem in
                                  itertools.product(np.arange(this_x-r,this_x+r),
                                                    np.arange(y-r,y+r))])
                #is_inside_circle=circle.contains_points(my_grid)
                is_inside_circle=(np.square(my_grid[:,0]-this_x)+np.square(my_grid[:,1]-y))<np.square(r)
                circle_points=my_grid[is_inside_circle]

                circle_mean=0
                for point in circle_points:
                        circle_mean+=image_copy[point[1],point[0]]
                circle_mean/=len(circle_points)

                ####################

                costs=np.full(len(thetas),0.0)
                for j,theta in enumerate(thetas):

                        edge_ind_pair=[int(this_x+r*np.cos(theta)),int(y+r*np.sin(theta))]
                        delta_x=edge_ind_pair[0]-this_x
                        delta_y=edge_ind_pair[1]-y

                        bottom_ind_pair=[this_x-delta_x*back_height_percentage,y-delta_y*back_height_percentage]
                        bottom_left_ind_pair=[bottom_ind_pair[0]-delta_y*width_percentage,
                                                                  bottom_ind_pair[1]+delta_x*width_percentage]
                        bottom_right_ind_pair=[bottom_ind_pair[0]+delta_y*width_percentage,
                                                                  bottom_ind_pair[1]-delta_x*width_percentage]
                        triangle=plt.Polygon([bottom_left_ind_pair,bottom_right_ind_pair,edge_ind_pair])

                        my_grid=np.array([elem for elem in itertools.product(np.arange(this_x-r,this_x+r),np.arange(y-r,y+r))])
                        is_inside_triangle=triangle.get_path().contains_points(my_grid)
                        triangle_points=my_grid[is_inside_triangle]

                        costs[j]=0
                        for point in triangle_points:
                                # this makes it binary 
                                if image_copy[point[1],point[0]]>circle_mean:
                                        # this is setting the cost
                                        costs[j]+=1

                                        # this part is just so we can see what the computer sees
                                        image_copy[point[1],point[0]]=200
                                else:
                                        image_copy[point[1],point[0]]=0
                        # need to take average since triangles are all different sizes
                        costs[j]=costs[j]/len(triangle_points) 

                        # keep track of which points we tested by plotting the edges
                        #ax1.scatter(edge_ind_pair[0],edge_ind_pair[1])

                min_arg=np.argmin(costs)
                theta_min=thetas[min_arg]
                power=angle_to_power_old(theta_min, not which_circle%2)
                if i!=num_circles-1:
                        power=np.floor(power)
                final_power+=power*pow(10,num_circles-1 -i)
        return final_power

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
        
def main():
        get_time = True
        
        if get_time:
	        prev_time=time.time()
                
        client=pygsheets.authorize()
        if get_time:
	        next_time=time.time()
	        print('authorization time: {}'.format(next_time-prev_time))
	        prev_time=next_time

        sh=client.open('173power')
        if get_time:
	        next_time=time.time()
	        print('opening sheet time: {}'.format(next_time-prev_time))
	        prev_time=next_time
        
        wks=sh.sheet1

        # # if the user doesn't specify a file do the test case...
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
                x=int(wks.get_value('B2'))
                y=int(wks.get_value('B3'))
                r=int(wks.get_value('B4'))
                back_height_percentage=float(wks.get_value('B5'))
                width_percentage=float(wks.get_value('B6'))
                if get_time:
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
        if get_time:
	        next_time=time.time()
	        print('getting power time: {}'.format(next_time-prev_time))
	        prev_time=next_time

        pic_time=picture_path[:-4] #datetime.now().strftime("%m/%d/%Y %H:%M:%S")

        write_timestamp_and_power(wks,power,pic_time)
        if get_time:
	        next_time=time.time()
	        print('writing power time: {}'.format(next_time-prev_time))
	        prev_time=next_time

        
if __name__ == '__main__':
        main()
