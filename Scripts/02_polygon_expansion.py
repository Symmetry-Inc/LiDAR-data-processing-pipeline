import sys
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point, LineString

"""
Read polygons created by the script "create_footprint_polygons.py".
See, which of the polygons neighbor each other (edges come within couple of meters to touching), and dilate each polygon while keeping this in mind.
Edges that would touch the neighboring polygon's edges, will not expand over the half-way point between the two.
"""

process_all_buildings       = True # if 'True' process all buildings in input file. If 'false', process only a single building defined by 'target_building'
target_building             = "building_349.obj"
input_filename              = "S:/OSS/Data/Footprints/test_footprint_0m_dilation.txt"
output_filename             = "S:/OSS/Data/Footprints/test_footprint_2_0m_dilation.txt"
neighbor_distance_threshold = 2.0
dilation_amount             = 2.0
visualize_results           = True
output_results_to_file      = True


def main():

    original_polygons = []
    output_visualization_x = []
    output_visualization_y = []
    original_visualization_x = []
    original_visualization_y = []
                  
    with open(output_filename, 'w') as output_file:
        # First, read all the lines from the input file into a list
        with open(input_filename, 'r') as input_file:
            original_polygons = input_file.readlines()
            
        original_polygons = simplify_polygons(original_polygons)
            
        # Second, iterate over the lines, and for each polygon, iterate over them again, looking for polygons that come sufficiently close to each other        
        for dilating_polygon_number in range(len(original_polygons)):
                
            words_1 = original_polygons[dilating_polygon_number].split()
            dilating_polygon_obj_name = words_1[0]
            if process_all_buildings == False and dilating_polygon_obj_name != target_building: 
                continue            

            dilating_polygon = []
            neighbor_indices = []
            neighbor_names = []
            dilating_polygon_pc_name = words_1[1]
            for point_number in range(2,len(words_1), 2):
                # Get node coordinates...
                dilating_polygon.append( [float(words_1[point_number]), float(words_1[point_number+1])] )

            # Find all nearby buildings that the dilating polygon should be careful about
            for potential_neighbor_number in range(len(original_polygons)):
                # Get all the other polygons...
                if potential_neighbor_number == dilating_polygon_number:
                    continue
                potential_neighbor_polygon = []
                words_2 = original_polygons[potential_neighbor_number].split()
                potential_neighbor_obj_name = words_2[0]
                for point_number in range(2,len(words_2), 2):
                    potential_neighbor_polygon.append( [float(words_2[point_number]), float(words_2[point_number+1])] )
                # Compare the two polygons. Pick one edge from the first, compare it to every edge in the second, then move to the next edge in the first, and so on.
                neighborness_confirmed = False
                for point_iterator in range(len(dilating_polygon)):
                    # For each dilating polygon point...
                    # Since the line segments do not cross, the closest point on either edge to the other edge has to be one of the end-points.
                    A = dilating_polygon[point_iterator]
                    for edge_iterator in range(0, len(potential_neighbor_polygon)-1):
                        # Compare the dilating polygon node (and its follow-up node) to every edge of the potential neighbor polygon to find out if it is an actual neighbor...
                        edge = [potential_neighbor_polygon[edge_iterator], potential_neighbor_polygon[edge_iterator+1]]
                        B = edge[0]
                        C = edge[1]
                        # Compare each of the 4 points against the other edge, calculating the nearest distance.                    
                        dist_A_to_BC = shortest_distance_from_point_to_line_segment(B[0], B[1], C[0], C[1], A[0], A[1])
                        if dist_A_to_BC < neighbor_distance_threshold:
                            neighborness_confirmed = True
                            break
                    if neighborness_confirmed == True:
                        break
                if neighborness_confirmed == False:
                    for point_iterator in range(len(potential_neighbor_polygon)):
                        # For each dilating polygon point...
                        # Since the line segments do not cross, the closest point on either edge to the other edge has to be one of the end-points.
                        A = potential_neighbor_polygon[point_iterator]
                        for edge_iterator in range(0, len(dilating_polygon)-1):
                            # Compare the dilating polygon node (and its follow-up node) to every edge of the potential neighbor polygon to find out if it is an actual neighbor...
                            edge = [dilating_polygon[edge_iterator], dilating_polygon[edge_iterator+1]]
                            B = edge[0]
                            C = edge[1]
                            # Compare each of the 4 points against the other edge, calculating the nearest distance.                    
                            dist_A_to_BC = shortest_distance_from_point_to_line_segment(B[0], B[1], C[0], C[1], A[0], A[1])
                            if dist_A_to_BC < neighbor_distance_threshold:
                                neighborness_confirmed = True
                                break
                        if neighborness_confirmed == True:
                            break
                if neighborness_confirmed == True:
                    neighbor_names.append(potential_neighbor_obj_name)
                    neighbor_indices.append(potential_neighbor_number)

            print("Neighbors for", dilating_polygon_obj_name, "- ", neighbor_names)
           
            # Dilate the polygon while taking care not to intersect the neighbors
            dilated_x, dilated_y = dilate_polygon_with_neighbors(dilating_polygon, original_polygons, neighbor_indices)
         
            # Output results
            if visualize_results == True:
                vis_data_x = []
                vis_data_y = []
                for i in range(len(dilated_x)):
                    vis_data_x.append(dilated_x[i])
                    vis_data_y.append(dilated_y[i])
                output_visualization_x.append(np.asarray(vis_data_x))
                output_visualization_y.append(np.asarray(vis_data_y))
    
            polygon_string = dilating_polygon_obj_name + " " + dilating_polygon_pc_name
            for i in range(len(dilated_x)):
                polygon_string += " " + str(dilated_x[i]) + " " + str(dilated_y[i])
            polygon_string += "\n"
            
            if output_results_to_file == True:
                output_file.write(polygon_string)
                                
        if visualize_results == True:            
            for dilating_polygon_number in range(len(original_polygons)):
                dilating_polygon_x = []
                dilating_polygon_y = []
                words_1 = original_polygons[dilating_polygon_number].split()
                for point_number in range(2,len(words_1), 2):
                    dilating_polygon_x.append( float(words_1[point_number]) )
                    dilating_polygon_y.append( float(words_1[point_number+1]) )
                dilating_polygon_x.append( float(words_1[2]) )
                dilating_polygon_y.append( float(words_1[3]) )
                original_visualization_x.append(np.asarray(dilating_polygon_x))
                original_visualization_y.append(np.asarray(dilating_polygon_y))
                
            plt.title("Polygons")
            plt.xlabel("X axis")
            plt.ylabel("Y axis")
            for i in range(len(output_visualization_x)):
                plt.plot(output_visualization_x[i], output_visualization_y[i], color="red")
            for i in range(len(original_visualization_x)):
                plt.plot(original_visualization_x[i], original_visualization_y[i], color="black")
            plt.show()        


def simplify_polygons(polygons):
    """
    Go through each polygon in the input list (Each element is a polygon defined by x/y coordinate pairs, and the two first elements of each are file names).
    If any node is too close to each other, combine them to a mid-point node.
    
    Parameters
    ----------
    polygons : string
        All of the text read from the input polygon file. Each line defines a single buildings.
        
    Returns
    -------
    output_polygons : string
        Version of the input string, with nodes that are too close to each other combined
    """
    polygon_simplification_distance_threshold = 0.5 # Squared distance between two successive nodes in a polygon, below which they get combined to a single node in their mid-point
    output_polygons = []
    for polygon_line in polygons:
        simplified_polygon = []
        words = polygon_line.split()
        output_line = words[0] + " " + words[1] # Object and point cloud filenames
        polygon = []
        for point_number in range(2,len(words), 2):
            polygon.append( [float(words[point_number]), float(words[point_number+1])] )
        last_position = [0,0]
        for node_number in range(len(polygon)):
            position = [polygon[node_number][0], polygon[node_number][1]]
            distance_squared = ((last_position[0]-position[0])*(last_position[0]-position[0])) + ((last_position[1]-position[1])*(last_position[1]-position[1]))
            if distance_squared < polygon_simplification_distance_threshold:
                # Modify previous node position to the halfway point between the two, and skip adding this node
                old_x = simplified_polygon[-1][0]
                old_y = simplified_polygon[-1][1]
                new_x = old_x + ((position[0]-old_x)/2.0)
                new_y = old_y + ((position[1]-old_y)/2.0)
                simplified_polygon[-1][0] = new_x
                simplified_polygon[-1][1] = new_y
            else:
                simplified_polygon.append(position)
            last_position = position
            
        #print("from %d to %d" % (len(polygon), len(simplified_polygon)) )
        for node in simplified_polygon:
            output_line = output_line + " " + str(node[0]) + " " + str(node[1])
        output_polygons.append(output_line)
    return output_polygons
    

def shortest_distance_from_point_to_line_segment(x1, y1, x2, y2, x3, y3):
    """
    Returns the shortest distance from a point (x3,y3) to a line segment (x1,y1)->(x2,y2)
    """
    px = x2-x1
    py = y2-y1
    norm = px*px + py*py
    u =  ((x3 - x1) * px + (y3 - y1) * py) / float(norm)
    if u > 1:
        u = 1
    elif u < 0:
        u = 0
    x = x1 + u * px
    y = y1 + u * py
    dx = x - x3
    dy = y - y3
    dist = (dx*dx + dy*dy)**.5

    return dist


def project_point_to_line(point, line):
    """
    Get point on the line where a perpendicular line, which also passes through the input point, crosses it
    """
    x = np.array(point.coords[0])
    u = np.array(line.coords[0])
    v = np.array(line.coords[len(line.coords)-1])
    n = v - u
    n /= np.linalg.norm(n, 2)
    projection = u + n*np.dot(x - u, n)
    return projection


def check_intersection_with_neighbor(p0, p1, polygon_list, neighbor_indices):
    """
    Check using Shapely if the line segment p0p1 crosses any of the neighboring polygon edges, and return the crossing point if so.
    """
    dilation_line = LineString([p0, p1])
    #print("Checking intersection for", p0, "-", p1, "against neighbors")
    intersection_found = False
    intersection_data = []
    for neighbor_index in range(len(neighbor_indices)):
        words = polygon_list[neighbor_indices[neighbor_index]].split()
        neighbor_polygon = []
        for node_number in range(2,len(words), 2):
            neighbor_polygon.append( [float(words[node_number]), float(words[node_number+1])] )
        for node_number in range(0,len(neighbor_polygon)):
            node_0 = neighbor_polygon[node_number-1]
            node_1 = neighbor_polygon[node_number]
            neighbor_line = LineString([(node_0[0], node_0[1]), (node_1[0], node_1[1])])
            if dilation_line.intersects(neighbor_line) == True:
                intersection_found = True
                intersection_point = dilation_line.intersection(neighbor_line)
                intersection_point = np.array([intersection_point.x, intersection_point.y])
                intersection_data.append([intersection_point, neighbor_line])
    
    return intersection_found, intersection_data


def add_midway_nodes(next_dilated_x, next_dilated_y, current_undilated_node_number, undilated_list_x, undilated_list_y, dilated_list_x, dilated_list_y, polygon_list, neighbor_indices):
    """
    Check, if an intersection with a neighbor polygon is created, if (to_be_added_x,to_be_added_y) is added to the list of dilated points.
    If so, create a new node before it in such a position that the resulting polygon line will not have that intersection.
    'next_dilated_x/y' is the next dilated corner point to be added. The end coordinates. This function checks, if new nodes need to be added before it.
    'current_undilated_node_number' is the node index (in x/y_coordinates) of the undilated version of the 'to_be_added_x/y' node.
    'undilated_list_x/y' are lists with the undilated original polygon points (since corners get split into two, dilated_x/y lists are longer)
    'dilated_list_x/y' are lists with the already dilated polygon points added
    """
    intersection_found = False
    midway_x_1 = None
    midway_y_1 = None
    midway_x_2 = None
    midway_y_2 = None
    if len(dilated_list_x) > 0:
        # Starting coordinates
        previous_dilated_x = dilated_list_x[-1]
        previous_dilated_y = dilated_list_y[-1]
        intersection_found, intersections_data = check_intersection_with_neighbor([previous_dilated_x, previous_dilated_y], [next_dilated_x, next_dilated_y], polygon_list, neighbor_indices)
        if intersection_found == True:
            # Intersection found. 
            # Find the point on the intersected neighbor edge that is closest to the undilated polygon edge.
            # Use the intersected neighbor edge end-points instead of the intersection point, because the edge might not be one that is parallel-ish to the polygon edge, and so, the nearest end-point is better
            print("  >Need to add a midway point")
            #intersection_point = intersections_data[0][0]
            neighbor_line = intersections_data[0][1]            
            neighbor_points = list(neighbor_line.coords)
            neighbor_point_0 = neighbor_points[0]
            neighbor_point_1 = neighbor_points[1]
            dist_0 = shortest_distance_from_point_to_line_segment( undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1], 
                                                                   undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number], 
                                                                   neighbor_point_0[0], neighbor_point_0[1])
            dist_1 = shortest_distance_from_point_to_line_segment( undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1], 
                                                                   undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number], 
                                                                   neighbor_point_1[0], neighbor_point_1[1])
            if dist_0 < dist_1:
                nearest_point = neighbor_point_0
            else:
                nearest_point = neighbor_point_1
            # Draw a perpendicular line from the chosen closest neighbor point to the undilated polygon edge
            line = LineString( [(undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1]), 
                                (undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number])] )
            point = Point(nearest_point[0], nearest_point[1])
            projected_point = project_point_to_line(point, line)
            # Get the midway point on the drawn line, a new node will be created at that point
            midway_x_1 = projected_point[0] + ((nearest_point[0]-projected_point[0])/2.0)
            midway_y_1 = projected_point[1] + ((nearest_point[1]-projected_point[1])/2.0)
        
            # Draw a new line from the goal coordinates to the new midway point, and see if that line intersects the neighbor polygon.
            #intersection_found, intersections_data = check_intersection_with_neighbor([next_dilated_x, next_dilated_y], [midway_x_1, midway_y_1], polygon_list, neighbor_indices)
            intersection_found, intersections_data = check_intersection_with_neighbor([previous_dilated_x, previous_dilated_y], [midway_x_1, midway_y_1], polygon_list, neighbor_indices)
            if intersection_found == True:
                print("  >Need to add a second midway point")
                #intersection_point = intersections_data[0][0]
                neighbor_line = intersections_data[0][1]
                neighbor_points = list(neighbor_line.coords)
                neighbor_point_0 = neighbor_points[0]
                neighbor_point_1 = neighbor_points[1]
                dist_0 = shortest_distance_from_point_to_line_segment( undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1], 
                                                                       undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number], 
                                                                       neighbor_point_0[0], neighbor_point_0[1])
                dist_1 = shortest_distance_from_point_to_line_segment( undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1], 
                                                                       undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number], 
                                                                       neighbor_point_1[0], neighbor_point_1[1])
                if dist_0 < dist_1:
                    nearest_point = neighbor_point_0
                else:
                    nearest_point = neighbor_point_1
                line = LineString( [(undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1]), 
                                    (undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number])] )
                point = Point(nearest_point[0], nearest_point[1])
                projected_point = project_point_to_line(point, line)
                midway_x_2 = projected_point[0] + ((nearest_point[0]-projected_point[0])/2.0)
                midway_y_2 = projected_point[1] + ((nearest_point[1]-projected_point[1])/2.0)
            
    return midway_x_1, midway_y_1, midway_x_2, midway_y_2





def add_midway_nodes_2(goal_x, goal_y, current_undilated_node_number, undilated_list_x, undilated_list_y, dilated_list_x, dilated_list_y, polygon_list, neighbor_indices):
    """
    Check, if an intersection with a neighbor polygon is created, if (to_be_added_x,to_be_added_y) is added to the list of dilated points.
    If so, create a new node before it in such a position that the resulting polygon line will not have that intersection.
    'goal_x/y' is the next dilated corner point to be added. The end coordinates. This function checks, if new nodes need to be added between it and the start point (last entry in the dilated_x/y list).
    'current_undilated_node_number' is the node index (in x/y_coordinates) of the undilated version of the 'to_be_added_x/y' node.
    'undilated_list_x/y' are lists with the undilated original polygon points (since corners get split into two, dilated_x/y lists are longer)
    'dilated_list_x/y' are lists with the already dilated polygon points added
    """
    intersection_found = False
    midway_nodes_forward = []
    midway_nodes_forward.append( [dilated_list_x[-1], dilated_list_y[-1]] )
    midway_nodes_backward = []
    midway_nodes_backward.append( [goal_x, goal_y] )
    if len(dilated_list_x) > 0:
        # First, look for intersections, when a line is drawn from start point to goal point
        start_x = dilated_list_x[-1]
        start_y = dilated_list_y[-1]
        intersection_found, intersections_data = check_intersection_with_neighbor([start_x, start_y], [goal_x, goal_y], polygon_list, neighbor_indices)
        if intersection_found == True:
            # Intersection found. Move from the intersection point towards the dilating polygon line so that the intersection disappears.
            points_added = 0
            #previously_chosen_nearest_point = [0, 0] # Make sure that the algorithm won't get stuck
            trying_to_move_forward = True # Moving forward -> start_point or latest midway_node_forward towards
            
            while intersection_found == True:
                if trying_to_move_forward == True:
                    # Moving forward from start point towads goal point
                    
                    #print("  >Looking to add forward-direction midway point #%d" % points_added)
                    new_extra_point_x = None
                    new_extra_point_y = None
                    smallest_distance = sys.float_info.max
                    nearest_point = None
                    intersected_neighbor_line = None
                    #print("    Previous nearest point to avoid:", previously_chosen_nearest_point)
                    
                    # Choose the nearest intersection and get the intersected line
                    for intersection_number in range(len(intersections_data)):
                        intersection_point = intersections_data[intersection_number][0] # Coordinates of where the intersection occurs
                        dx = midway_nodes_forward[-1][0] - intersection_point[0]
                        dy = midway_nodes_forward[-1][1] - intersection_point[1]
                        dist_from_forward_node_to_intersection = (dx*dx + dy*dy)**.5
                        if dist_from_forward_node_to_intersection < smallest_distance:
                            smallest_distance = dist_from_forward_node_to_intersection
                            nearest_point = intersection_point
                            intersected_neighbor_line = intersections_data[intersection_number][1] # LineString presentation of the edge in neighbor polygon that gets intersected
                    
                    # From the intersected neighbor line, get the end-node nearest to the undilated polygon line
                    neighbor_points = list(intersected_neighbor_line.coords)
                    neighbor_point_0 = neighbor_points[0]
                    neighbor_point_1 = neighbor_points[1]
                    dist_to_line_from_node_0 = shortest_distance_from_point_to_line_segment( undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1], 
                                                                                             undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number], 
                                                                                             neighbor_point_0[0], neighbor_point_0[1])
                    dist_to_line_from_node_1 = shortest_distance_from_point_to_line_segment( undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1], 
                                                                                             undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number], 
                                                                                             neighbor_point_1[0], neighbor_point_1[1])
                    if dist_to_line_from_node_0 < dist_to_line_from_node_1:
                        nearest_point = neighbor_point_0
                    else:
                        nearest_point = neighbor_point_1
                                        
                    # Draw a perpendicular line from the chosen closest neighbor point to the undilated polygon edge
                    point = Point(nearest_point[0], nearest_point[1])
                    line = LineString( [(undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1]), 
                                        (undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number])] )
                    projected_point = project_point_to_line(point, line)
                    
                    # Get the midway point on the drawn line, a new node will be created at that point
                    new_extra_point_x = projected_point[0] + ((nearest_point[0]-projected_point[0])/2.0)
                    new_extra_point_y = projected_point[1] + ((nearest_point[1]-projected_point[1])/2.0)
                    #print("        Resulting extra point is [%f, %f]" % (new_extra_point_x, new_extra_point_y) )
                    midway_nodes_forward.append([new_extra_point_x, new_extra_point_y])
                    points_added += 1

                    # Flip directions, try to move from the latest goal-side node towards this latest start-side node. NOTE: goal-side nodes are appended to the start of the list to keep order correct
                    trying_to_move_forward = False
                    intersections_data = []
                    intersection_found = False
                    intersection_found, intersections_data = check_intersection_with_neighbor( [midway_nodes_backward[0][0], midway_nodes_backward[0][1]], 
                                                                                               [new_extra_point_x, new_extra_point_y], 
                                                                                               polygon_list, neighbor_indices )
                else:
                    # Moving backward from goal point towards start point
                    #print("  >Looking to add backward-direction midway point #%d" % points_added)
                    new_extra_point_x = None
                    new_extra_point_y = None
                    smallest_distance = sys.float_info.max
                    nearest_point = None
                    intersected_neighbor_line = None
                    #print("    Previous nearest point to avoid:", previously_chosen_nearest_point)
                    
                    # Choose the nearest intersection and get the intersected line
                    for intersection_number in range(len(intersections_data)):
                        intersection_point = intersections_data[intersection_number][0] # Coordinates of where the intersection occurs
                        dx = midway_nodes_backward[0][0] - intersection_point[0]
                        dy = midway_nodes_backward[0][1] - intersection_point[1]
                        dist_from_backward_node_to_intersection = (dx*dx + dy*dy)**.5
                        if dist_from_backward_node_to_intersection < smallest_distance:
                            smallest_distance = dist_from_backward_node_to_intersection
                            nearest_point = intersection_point
                            intersected_neighbor_line = intersections_data[intersection_number][1] # LineString presentation of the edge in neighbor polygon that gets intersected
                    
                    # From the intersected neighbor line, get the end-node nearest to the undilated polygon line
                    neighbor_points = list(intersected_neighbor_line.coords)
                    neighbor_point_0 = neighbor_points[0]
                    neighbor_point_1 = neighbor_points[1]
                    dist_to_line_from_node_0 = shortest_distance_from_point_to_line_segment( undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1], 
                                                                                             undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number], 
                                                                                             neighbor_point_0[0], neighbor_point_0[1])
                    dist_to_line_from_node_1 = shortest_distance_from_point_to_line_segment( undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1], 
                                                                                             undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number], 
                                                                                             neighbor_point_1[0], neighbor_point_1[1])
                    if dist_to_line_from_node_0 < dist_to_line_from_node_1:
                        nearest_point = neighbor_point_0
                    else:
                        nearest_point = neighbor_point_1
                   
                    # Draw a perpendicular line from the chosen closest neighbor point to the undilated polygon edge
                    point = Point(nearest_point[0], nearest_point[1])
                    line = LineString( [(undilated_list_x[current_undilated_node_number-1], undilated_list_y[current_undilated_node_number-1]), 
                                        (undilated_list_x[current_undilated_node_number], undilated_list_y[current_undilated_node_number])] )
                    projected_point = project_point_to_line(point, line)
                    
                    # Get the midway point on the drawn line, a new node will be created at that point
                    new_extra_point_x = projected_point[0] + ((nearest_point[0]-projected_point[0])/2.0)
                    new_extra_point_y = projected_point[1] + ((nearest_point[1]-projected_point[1])/2.0)
                    #print("        Resulting extra point is [%f, %f]" % (new_extra_point_x, new_extra_point_y) )
                    midway_nodes_backward.insert(0, [new_extra_point_x, new_extra_point_y])
                    points_added += 1
                    
                    # Flip directions, try to move from the latest goal-side node towards this latest start-side node. NOTE: goal-side nodes are appended to the start of the list to keep order correct
                    trying_to_move_forward = True
                    intersections_data = []
                    intersection_found = False
                    intersection_found, intersections_data = check_intersection_with_neighbor( [midway_nodes_forward[-1][0], midway_nodes_forward[-1][1]], 
                                                                                               [new_extra_point_x, new_extra_point_y], 
                                                                                               polygon_list, neighbor_indices )
                    
                    
        midway_nodes = midway_nodes_forward[1:] + midway_nodes_backward[:-1]
        print("  Total midway points added:", len(midway_nodes))
            
    return midway_nodes




def remove_duplicate_nodes(input_x, input_y):
    # Similar or same to simplify_polygons()
    tmp_x = []
    tmp_y = []
    for node_number in range(-1, len(input_x)-1):
        dx = input_x[node_number+1] - input_x[node_number]
        dy = input_y[node_number+1] - input_y[node_number]
        dist = (dx*dx + dy*dy)**.5
        #print("Distance: %f" % dist )
        if dist > 0.001:
            tmp_x.append(input_x[node_number+1])
            tmp_y.append(input_y[node_number+1])
    input_x = tmp_x
    input_y = tmp_y
    return input_x, input_y


def remove_self_intersections(input_x, input_y):
    """
    Go through the input polygon, and see if any of the edges get intersected by the other edges.
    If intersections are found, create a new node in the intersection point, and erase all nodes in between.
    NOTE: if the check starts inside a loop, e.g. a building exterior corners that are under 180 degrees, the loop might be preserved, while the rest of the building is erased!
    """
    
    input_x, input_y = remove_duplicate_nodes(input_x, input_y)    
    
    #print("input length: %d" % len(input_x))
    if len(input_x) > 8:
        # Move the starting point of the polygon until 5 successive edges can be found without 3-edge intersections, and set the middle one as the first edge.
        # Looking at the actual polygons, there are several corners that are more than 3 edges long, leading to that long list of tests below...
        for node_number in range(4, len(input_x)-4):
            edge_0 = LineString( [(input_x[node_number-4], input_y[node_number-4]), (input_x[node_number-3], input_y[node_number-3])] )
            edge_1 = LineString( [(input_x[node_number-3], input_y[node_number-3]), (input_x[node_number-2], input_y[node_number-2])] )
            edge_2 = LineString( [(input_x[node_number-2], input_y[node_number-2]), (input_x[node_number-1], input_y[node_number-1])] )
            edge_3 = LineString( [(input_x[node_number-1], input_y[node_number-1]), (input_x[node_number],   input_y[node_number])] )
            edge_4 = LineString( [(input_x[node_number],   input_y[node_number]),   (input_x[node_number+1], input_y[node_number+1])] )
            edge_5 = LineString( [(input_x[node_number+1], input_y[node_number+1]), (input_x[node_number+2], input_y[node_number+2])] )
            edge_6 = LineString( [(input_x[node_number+2], input_y[node_number+2]), (input_x[node_number+3], input_y[node_number+3])] )
            if edge_0.intersects(edge_2) == True:
                continue
            if edge_0.intersects(edge_3) == True:
                continue
            if edge_0.intersects(edge_4) == True:
                continue
            if edge_0.intersects(edge_5) == True:
                continue
            if edge_0.intersects(edge_6) == True:
                continue
            
            if edge_1.intersects(edge_3) == True:
                continue
            if edge_1.intersects(edge_4) == True:
                continue
            if edge_1.intersects(edge_5) == True:
                continue
            if edge_1.intersects(edge_6) == True:
                continue
            
            if edge_2.intersects(edge_4) == True:
                continue
            if edge_2.intersects(edge_5) == True:
                continue
            if edge_2.intersects(edge_6) == True:
                continue
            
            if edge_3.intersects(edge_5) == True:
                continue
            if edge_3.intersects(edge_6) == True:
                continue
            
            if edge_4.intersects(edge_6) == True:
                continue
            
            # No intersection was found, select node[node_number] as the starting node, and modify the coordinate lists accordingly
            #print("Moving polygon start point to node_number %d" % node_number)
            tmp_x = input_x[:node_number]
            input_x = input_x[node_number:] + tmp_x
            tmp_y = input_y[:node_number]
            input_y = input_y[node_number:] + tmp_y
            break

    # Loop through the polygon, simplifying it        
    found_intersection = True
    intersection_point = []
    first_clip_node_number = -1
    last_clip_node_number = -1
    while found_intersection == True:
        #print("loop_start: 'found_intersection':", found_intersection)
        found_intersection = False
        for node_number in range(len(input_x)-1):
            if found_intersection == True:
                break
            current_edge = LineString( [(input_x[node_number], input_y[node_number]), (input_x[node_number+1], input_y[node_number+1])] )
            for test_node_number in range(len(input_x)-1):
                if test_node_number >= node_number-1 and test_node_number <= node_number+1:
                    continue
                #print("Testing %d" % test_node_number)
                test_edge = LineString( [(input_x[test_node_number], input_y[test_node_number]), (input_x[test_node_number+1], input_y[test_node_number+1])] )
                if test_edge.intersects(current_edge) == True:
                    # Create a new node at intersection point, and erase the nodes between them (in whichever direction there are less of them)
                    found_intersection = True
                    intersection_point = test_edge.intersection(current_edge)
                    #print("  Found a new loop, trying to remove. node_number=%d, test_node_number=%d" % (node_number, test_node_number) )
                    diff = abs(test_node_number-node_number)
                    #print("    Diff: %d, total nodes: %d" % (diff, len(input_x)) )
                    if diff < (len(input_x)/2.0):
                        # Most polygon nodes are outside the two nodes (loop is between them)
                        if node_number < test_node_number:
                            first_clip_node_number = node_number+1
                            last_clip_node_number = test_node_number
                        else:
                            first_clip_node_number = test_node_number+1
                            last_clip_node_number = node_number
                        #print("    --> Erasing between. First clip number=%d,last clip number=%d" % (first_clip_node_number, last_clip_node_number) )
                        # Create the new node right before the node[first_clip_node_number] (and update the clip numbers)
                        new_x = intersection_point.x
                        new_y = intersection_point.y
                        input_x.insert(first_clip_node_number, new_x)
                        input_y.insert(first_clip_node_number, new_y)
                        first_clip_node_number += 1
                        last_clip_node_number += 1               
                        input_x = input_x[:first_clip_node_number] + input_x[last_clip_node_number+1:]
                        input_y = input_y[:first_clip_node_number] + input_y[last_clip_node_number+1:]
                    else:
                        # Most polygon nodes are between the two nodes, erasure wraps around
                        if node_number < test_node_number:
                            first_clip_node_number = test_node_number # In the end of polygon chain, but first to be deleted
                            last_clip_node_number = node_number
                        else:
                            first_clip_node_number = node_number
                            last_clip_node_number = test_node_number
                        #print("    --> Erasing outside. First clip number=%d,last clip number=%d" % (first_clip_node_number, last_clip_node_number) )
                        # Some issue with the new node creation, fix later. For now, combine loose ends right before returning from the function
                        first_clip_node_number += 1
                        input_x = input_x[:first_clip_node_number]
                        input_x = input_x[last_clip_node_number:] 
                        input_y = input_y[:first_clip_node_number]
                        input_y = input_y[last_clip_node_number:]
                        
                    break
    if input_x[0] != input_x[len(input_x)-1]:
        # Fix for when looping around the polygon
        input_x.append(input_x[0])
        input_y.append(input_y[0])  
        
    return input_x, input_y



def dilate_polygon_with_neighbors(polygon, polygon_list, neighbor_indices):
    """
    dilate the input polygon as with the function 'dilate_polygon()', but control the dilation amount for the edges that are near other polygons.
    The first element in "neighbor_indices" is the input polygon itself.
    """
    normals = []
    dilated_list_x = []
    dilated_list_y = []
    undilated_list_x = []
    undilated_list_y = []
    for i in range(len(polygon)):
        undilated_list_x.append(polygon[i][0])
        undilated_list_y.append(polygon[i][1])

    # Remove duplicate nodes - this at the start of the algorithm does naughty things.
    undilated_list_x, undilated_list_y = remove_duplicate_nodes(undilated_list_x, undilated_list_y)    
   
    
    # Calculate polygon edge normals. First normal will be between then first and last node of the polygon.    
    for i in range(len(undilated_list_x)): # Ignoring the last node, which is the same as the first node
        x1 = undilated_list_x[i]
        y1 = undilated_list_y[i]
        if i < len(undilated_list_x)-1:
            x2 = undilated_list_x[i+1]
            y2 = undilated_list_y[i+1]
        else:
            x2 = undilated_list_x[0]
            y2 = undilated_list_y[0]
        
        halfway_x = x1 + 0.5*(x2-x1)
        halfway_y = y1 + 0.5*(y2-y1)
        
        dx = x2 - x1
        dy = y2 - y1
        n1x = -dy
        n1y = dx
        n2x = dy
        n2y = -dx
        test_point_x = halfway_x + n1x
        test_point_y = halfway_y + n1y
        cross_product = ((x2-x1)*(test_point_y-y1))-((y2-y1)*(test_point_x-x1))
        if cross_product < 0:
            chosen_normal = [n1x,n1y]
        elif cross_product == 0:
            # Should never end up here, unless the angle between polygon components is 180 degrees.
            print("Found a 180-degree angle in the footprint polygon!")
            chosen_normal = [n1x, n1y] # Just to avoid an error, should add error handling...
        else:
            chosen_normal = [n2x, n2y]
        normals.append(chosen_normal)
  
    # For each corner, calculate normalized vertex normals, and dilate node positions along them by a set amount (creating 2 dilated nodes from each original corner node)
    for undilated_corner_number in range(len(undilated_list_x)):
        print("Processing corner #%d" % undilated_corner_number)
        n1x = normals[undilated_corner_number-1][0]
        n1y = normals[undilated_corner_number-1][1]
        n2x = normals[undilated_corner_number][0]
        n2y = normals[undilated_corner_number][1]
        
        # First new node dilated from the target corner
        vn_1 = np.array([n1x, n1y])
        normalized_vn_1 = vn_1 / np.sqrt(np.sum(vn_1**2))
        new_x_1 = undilated_list_x[undilated_corner_number] + normalized_vn_1[0] * dilation_amount
        new_y_1 = undilated_list_y[undilated_corner_number] + normalized_vn_1[1] * dilation_amount  
        
        # Before setting the dilated corners, check if the line drawn when moving to it from the corner point crosses a neighbor polygon, and if so, adjust the dilated point to the two polygons' half-way point.
        # Also, before adding the first node, check if the line drawn to it from the previous corner of the polygon would cross a neighbor, and if so, add an extra node to avoid that.
        intersection_found, intersections_data = check_intersection_with_neighbor( [undilated_list_x[undilated_corner_number], undilated_list_y[undilated_corner_number]], 
                                                                                   [new_x_1, new_y_1], 
                                                                                   polygon_list, neighbor_indices )
        if intersection_found == True:
            print("  First new node from the corner is shortened.")
            # Adjust the dilated node so that it is positioned halfway between the two polygons
            intersection_point = intersections_data[0][0]
            new_x_1 = undilated_list_x[undilated_corner_number] + ((intersection_point[0]-undilated_list_x[undilated_corner_number])/2.0)
            new_y_1 = undilated_list_y[undilated_corner_number] + ((intersection_point[1]-undilated_list_y[undilated_corner_number])/2.0)
        else:
            print("  First new node from the corner is OK as is.")
        
        if undilated_corner_number > 0:
            # Check the line drawn to the new point for intersections
            print("  Add inbetween nodes?")
            midway_nodes = add_midway_nodes_2( new_x_1, new_y_1, 
                                               undilated_corner_number, 
                                               undilated_list_x, undilated_list_y, 
                                               dilated_list_x, dilated_list_y, 
                                               polygon_list, neighbor_indices )                
            for extra_node_number in range(len(midway_nodes)):
                dilated_list_x.append(midway_nodes[extra_node_number][0])
                dilated_list_y.append(midway_nodes[extra_node_number][1])
        else:
            print("  First node in polygon, no place for inbetween nodes.")
        dilated_list_x.append(new_x_1)
        dilated_list_y.append(new_y_1)
    
        # Repeat the process to the second node dilated from the target corner
        vn_2 = np.array([n2x, n2y])
        normalized_vn_2 = vn_2 / np.sqrt(np.sum(vn_2**2))
        new_x_2 = undilated_list_x[undilated_corner_number] + normalized_vn_2[0] * dilation_amount
        new_y_2 = undilated_list_y[undilated_corner_number] + normalized_vn_2[1] * dilation_amount
        intersection_found, intersections_data = check_intersection_with_neighbor( [undilated_list_x[undilated_corner_number], undilated_list_y[undilated_corner_number]], 
                                                                                   [new_x_2, new_y_2], 
                                                                                   polygon_list, neighbor_indices )
        if intersection_found == True:
            print("  Second new node from the corner is shortened.")
            intersection_point = intersections_data[0][0]
            new_x_2 = undilated_list_x[undilated_corner_number] + ((intersection_point[0]-undilated_list_x[undilated_corner_number])/2.0)
            new_y_2 = undilated_list_y[undilated_corner_number] + ((intersection_point[1]-undilated_list_y[undilated_corner_number])/2.0)
        else:
            print("  Second new node from the corner is OK as is.")
    
        print("  Add inbetween nodes?")
        midway_nodes = add_midway_nodes_2( new_x_2, new_y_2, 
                                          undilated_corner_number, 
                                          undilated_list_x, undilated_list_y, 
                                          dilated_list_x, dilated_list_y, 
                                          polygon_list, neighbor_indices )                
        for extra_node_number in range(len(midway_nodes)):
            dilated_list_x.append(midway_nodes[extra_node_number][0])
            dilated_list_y.append(midway_nodes[extra_node_number][1])    
        dilated_list_x.append(new_x_2)
        dilated_list_y.append(new_y_2)    
        
                
    # Add the final node to the polygon.
    #print("Close the dilated polygon.")
    midway_nodes = add_midway_nodes_2( dilated_list_x[0], dilated_list_y[0], 
                                       len(undilated_list_x)-1, 
                                       undilated_list_x, undilated_list_y, 
                                       dilated_list_x, dilated_list_y, 
                                       polygon_list, neighbor_indices )                
    for extra_node_number in range(len(midway_nodes)):
        dilated_list_x.append(midway_nodes[extra_node_number][0])
        dilated_list_y.append(midway_nodes[extra_node_number][1])
    dilated_list_x.append(dilated_list_x[0])
    dilated_list_y.append(dilated_list_y[0])
    
    # Run through the dilated polygon, and remove any internal loops (created at corners)
    dilated_list_x, dilated_list_y = remove_self_intersections(dilated_list_x, dilated_list_y)

    return dilated_list_x, dilated_list_y


if __name__ == '__main__':
    main()
