from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
import numpy as np
import matplotlib.pyplot as plt
import itertools
import copy
import sys

testing=False

try:
	fname = sys.argv[2]
	
except:
	print ('usage: python program.py fname')
	print ('using default "joe_easy_test.jpg" ')
	testing=True
	fname='pictures/joe_easy_test.jpg'

image = Image.open(fname)

image=image.convert('L') # monochrome

# PIL does stuff upside down 
image = np.flipud(np.array(image))

num_circles=5

image_copy=copy.deepcopy(image)




######### FIGURE OUT HOW TO GET THESE #########
x=1178
y=1340
r=133
back_height_percentage=.2
width_percentage=.3
######### FIGURE OUT HOW TO GET THESE #########


# input in rad
# output number between (0,10)
def angle_to_power(t, ccw=True):

	x = 10* (t - np.pi/2)/(2*np.pi)

	if (ccw):
		return (10-x)
	else:
		return (10+x) % 10

final_power=0
# we focus on one circle at a time for now
for i,which_circle in enumerate(np.arange(num_circles)):
	thetas = np.linspace(0,360,endpoint=False) * (np.pi / 180)
	this_x = x+r*2*i  
	circleIn=plt.Circle((this_x,y),r-1,fill=False,color='k',alpha=.5)
	circle=plt.Circle((this_x,y),r,fill=False,color='r',linewidth=5,alpha=.5)
	circleOut=plt.Circle((this_x,y),r+1,fill=False,color='k',alpha=.5)
	
	if i==which_circle:
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

			import itertools
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

print(final_power)
if testing:
	print('Correct answer is 89359.9')

			# ax1.imshow(image_copy,origin='lower')

			# ax1.scatter(int(this_x+r*np.cos(thetas[max_arg-1])),
			#             int(y+r*np.sin(thetas[max_arg-1])),
			#             c='y')
			# ax1.scatter(int(this_x+r*np.cos(thetas[max_arg+1])),
			#             int(y+r*np.sin(thetas[max_arg+1])),
			#             c='y') 
			# ax1.scatter(int(this_x+r*np.cos(thetas[max_arg])),
			#             int(y+r*np.sin(thetas[max_arg])),
			#             c='r')

			# edge_ind_pair=[int(this_x+r*np.cos(theta_min)),int(y+r*np.sin(theta_min))]
			# delta_x=edge_ind_pair[0]-this_x
			# delta_y=edge_ind_pair[1]-y

			# bottom_ind_pair=[this_x-delta_x*back_height_percentage,y-delta_y*back_height_percentage]
			# bottom_left_ind_pair=[bottom_ind_pair[0]-delta_y*width_percentage,
			#                       bottom_ind_pair[1]+delta_x*width_percentage]
			# bottom_right_ind_pair=[bottom_ind_pair[0]+delta_y*width_percentage,
			#                       bottom_ind_pair[1]-delta_x*width_percentage] 
			# triangle=plt.Polygon([bottom_left_ind_pair,bottom_right_ind_pair,edge_ind_pair],
			#                      color='r',alpha=.5,fc=None)
			# ax1.add_artist(triangle)

			# ax2.scatter(thetas / (np.pi / 180),costs)
			# ax2.axvline(theta_min / (np.pi / 180),c='r')
			# ax2.set_xlabel('angle')
			# ax2.set_ylabel('cost')

	# ax1.set_xlim(x-r*2,x+r*2*num_circles)
	# ax1.set_ylim(y-r*2,y+r*2)

	# plt.show()
