from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
import numpy as np
import matplotlib.pyplot as plt
import itertools
import copy
from datetime import datetime
import sys

import pygsheets

# input in rad
# output number between (0,10)
def angle_to_power(t, ccw=True):

        x = 10* (t - np.pi/2)/(2*np.pi)

        if (ccw):
                return (10-x)
        else:
                return (10+x) % 10

def picture_to_power(picture_path,x,y,r,back_height_percentage,width_percentage):
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
                power=angle_to_power(theta_min, not which_circle%2)
                if i!=num_circles-1:
                        power=np.floor(power)
                final_power+=power*pow(10,num_circles-1 -i)
        return final_power

def write_timestamp_and_power(wks,power,time):
        rownum=1
        cell_val=wks.get_value('D{}'.format(rownum))
        while cell_val!='':
                rownum+=1
                cell_val=wks.get_value('D{}'.format(rownum))
        wks.update_value('D{}'.format(rownum),time)
        wks.update_value('E{}'.format(rownum),power)
        
def main():
        client=pygsheets.authorize()
        sh=client.open('173power')
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
                back_height_percentage=.2
                width_percentage=.3

        else:
                picture_path=sys.argv[1]
                x=int(wks.get_value('B2'))
                y=int(wks.get_value('B3'))
                r=int(wks.get_value('B4'))
                back_height_percentage=float(wks.get_value('B5'))
                width_percentage=float(wks.get_value('B6'))

        power = picture_to_power(picture_path,
                         x,
                         y,
                         r,
                         back_height_percentage,
                         width_percentage)

        time=datetime.now().strftime("%m/%d/%Y %H:%M:%S")

        write_timestamp_and_power(wks,power,time)
        
if __name__ == '__main__':
        main()
