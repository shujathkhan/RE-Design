


import numpy as np
import cv2

mydata = {}
def detectShape(c):
    shape = 'unknown'
    # calculate perimeter using
    peri = cv2.arcLength(c, True)
    # apply contour approximation and store the result in vertices
    vertices = cv2.approxPolyDP(c, 0.04 * peri, True)

    # If the shape it triangle, it will have 3 vertices
    if len(vertices) == 3:
        shape = 'triangle'
    #  i/f/ the shape has 4 vertices, it is either a square or
    # a rectangle
    elif len(vertices) == 4:
        # using the boundingRect method calculate the width and height
        # of enclosing rectange and then calculte aspect ratio

        x, y, width, height = cv2.boundingRect(vertices)
        
        aspectRatio = float(width) / height

        # a square will have an aspect ratio that is approximately
        # equal to one, otherwise, the shape is a rectangle
        if aspectRatio >= 0.95 and aspectRatio <= 1.05:
            shape = "square"
        
            # print("X-sq-axis", x)
            # print("Y-sq-axis", y)
        else:
            shape = "rectangle"
            # print("X-rec-axis", x)
            # print("Y-rec-axis", y)

    # if the shape is a pentagon, it will have 5 vertices
    elif len(vertices) == 5:
        shape = "pentagon"


    # otherwise, we assume the shape is a circle
    else:
        shape = "circle"
        centers, radius = cv2.minEnclosingCircle(c)
        print(centers,radius)



    # return the name of the shape
    if shape == "square":
        return shape, x, y, width, height
    elif shape == "rectangle":
        return shape, x, y, width, height
    elif shape == "circle":
        return shape, centers,radius
    else :
        return shape


def detect_myshapes(img_url):
    myshapes =[]
    image = cv2.imread(img_url)
    grayScale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sigma = 0.33
    v = np.median(grayScale)
    low = int(max(0, (1.0 - sigma) * v))
    high = int(min(255, (1.0 + sigma) * v))

    edged = cv2.Canny(grayScale, low, high)
    (_, cnts, _) = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


    for c in cnts:
        # cox1 = mpute the moment of contour
        M = cv2.moments(c)
    #     print(M)
        # From moment we can calculte area, centroid etc
        # The center or centroid can be calculated as follows
        cX = int(M['m10'] / M['m00'])
        cY = int(M['m01'] / M['m00'])

        # call detectShape for contour c
        shape = detectShape(c) 

        # Outline the contours
        # x2 = x + width
        # y2 = y + height 
        cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
 
        # Write the name of shape on the center of shapes
        # cv2.putText(image, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX,
        #             0.5, (255, 255, 255), 2)
        
        # cv2.imshow('frame', image)
        
        myshapes.append(shape)
    
    return myshapes

sh = detect_myshapes('n7.jpg')
print(sh)
