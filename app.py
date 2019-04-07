#!/usr/bin/python2
# -*- coding: utf-8 -*-

# sudo pip install tornado

from __future__ import print_function
import tornado.ioloop
import tornado.web
import tornado.websocket

import threading
import time
import queue as Queue

import numpy as np
import cv2
import io


# debug = True: set for a blink signal, no GPIO usage
# debug = False: set for GPIO usage

debug = True


# messages from Periphaeral Class to Websocket
sendQueue= Queue.Queue()


def detect_text(path):
    """Detects text in the file."""
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print('Texts:')

    for text in texts:
        print('\n"{}"'.format(text.description))

        vertices = (['({},{})'.format(vertex.x, vertex.y)
                    for vertex in text.bounding_poly.vertices])

        print('bounds: {}'.format(','.join(vertices)))



def detectShape(c):
    shape = 'unknown'
    # calculate perimeter using
    peri = cv2.arcLength(c, True)
    # apply contour approximation and store the result in vertices
    vertices = cv2.approxPolyDP(c, 0.04 * peri, True)

    # If the shape it triangle, it will have 3 vertices
    if len(vertices) == 3:
        shape = 'triangle'

    # if the shape has 4 vertices, it is either a square or
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
            print("X-sq-axis", x)
            print("Y-sq-axis", y)
        else:
            shape = "rectangle"
            print("X-rec-axis", x)
            print("Y-rec-axis", y)

    # if the shape is a pentagon, it will have 5 vertices
    elif len(vertices) == 5:
        shape = "pentagon"

    # otherwise, we assume the shape is a circle
    else:
        shape = "circle"

    # return the name of the shape
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
        # compute the moment of contour
        M = cv2.moments(c)
    #     print(M)
        # From moment we can calculte area, centroid etc
        # The center or centroid can be calculated as follows
        cX = int(M['m10'] / M['m00'])
        cY = int(M['m01'] / M['m00'])

        # call detectShape for contour c
        shape = detectShape(c)

        # Outline the contours
        cv2.drawContours(image, [c], -1, (0, 255, 0), 2)

        # Write the name of shape on the center of shapes
        # cv2.putText(image, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX,
        #             0.5, (255, 255, 255), 2)
        
        # cv2.imshow('frame', image)
        myshapes.append(shape)
    
    return myshapes

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write( """<!DOCTYPE html>
<html>
  <head>
    <!--Import Google Icon Font-->
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <!--Import materialize.css-->
    <!-- Compiled and minified CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css">

  <script src="https://aframe.io/releases/0.9.0/aframe.min.js"></script>


    <!--Let browser know website is optimized for mobile-->
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>

<style>

@media (min-width:1025px) {
     /* hi-res laptops and desktops */ 
    #pattern{
    position: absolute;
    right: -6%;
    top: 68%;
    }
}   

@media (min-width:1281px) {
     /* hi-res laptops and desktops */ 
    #pattern{
    position: absolute;
    right: -6%;
    top: 70%;
    }
}   

@media (min-width:641px)  { /* portrait tablets, portrait iPad, landscape e-readers, landscape 800x480 or 854x480 phones */
    #pattern{
        position: absolute;
    bottom: -16%;
    }

}








</style>

  </head>

  <body style="background:#e0e0e038;    overflow: hidden;">
<div class="container-fluid">
    
        <div id="header" style="font-size:12rem;position:absolute;left:5%;">
                 REDESIGN THE WORLD
        </div>
        <button class="btn waves-effect waves-light red modal-trigger" style="
    position: absolute;
    left: 7%;
    width: 15vw;
    height: 7vh;
    font-size: 25px;
    bottom: 16%;
" data-target="modal1" id="start">Let's Start!</button>
        <button class="btn waves-effect waves-light blue modal-trigger" style="
    position: absolute;
    left: 28%;
    width: 15vw;
    height: 7vh;
    font-size: 25px;
    bottom: 16%;
" data-target="modal2" id="redesign" onclick="test()">RE:DESIGN</button>

        <img id ="pattern" src="./pattern.png"/>
        <div id="modal1" class="modal">
                <div class="modal-content">
                  <h4>Capture your Design</h4>
                  <video id="capvid" style="    width: 28vw;
                  position: relative;
                  left: 25%;"></video>
                </div>
                <div class="modal-footer">
                  <a href="#!" class="modal-close waves-effect waves-green btn-flat" id="snap">Agree</a>
                </div>
        </div>
        <div id="modal2" class="modal" style="z-index: 1003;
        display: block;
        opacity: 1;
        top: 15%;
transform: scaleX(1.4) scaleY(1.4);
overflow: hidden;">
                <div class="modal-content" style="">
                  <h4>Visualize</h4>
                    <div id="myscene" class="container" style="width:auto;height:60vh;">
                        
                    </div>
                </div>
                <div class="modal-footer"">
                  <a href="#!" class="modal-close waves-effect waves-green btn-flat" id="snap">Agree</a>
                </div>
        </div>
    </div>
    

    <!--JavaScript at end of body for optimized loading-->
     <!-- Compiled and minified JavaScript -->
     <script
  src="https://code.jquery.com/jquery-3.3.1.min.js"
  integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8="
  crossorigin="anonymous"></script>

     <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js"></script>
      <script>
$(document).ready(function(){
    $('.modal').modal()
    $('.modal').modal({'dismissible':true})

document.getElementById('start').addEventListener('click',function(){
    const vid =  document.getElementById('capvid');
    navigator.mediaDevices.getUserMedia({video: true}) // request cam
.then(stream => {
  vid.srcObject = stream; // don't use createObjectURL(MediaStream)
  return vid.play(); // returns a Promise
})
.then(()=>{ // enable the button
  const btn = document.getElementById('snap');
  btn.disabled = false;
  btn.onclick = e => {
    takeASnap()
    .then(download);
  };
});

function takeASnap(){
  const canvas = document.createElement('canvas'); // create a canvas
  const ctx = canvas.getContext('2d'); // get its context
  canvas.width = vid.videoWidth; // set its size to the one of the video
  canvas.height = vid.videoHeight;
  ctx.drawImage(vid, 0,0); // the video
  return new Promise((res, rej)=>{
    canvas.toBlob(res, 'image/jpeg'); // request a Blob from the canvas
  });
}
function download(blob){
  // uses the <a download> to download a Blob
  let a = document.createElement('a'); 
  a.href = URL.createObjectURL(blob);
  a.download = 'screenshot.jpg';
  document.body.appendChild(a);
  a.click();
}
});
 



  });


    
    "use strict";
   
    console.log("starting...");
    var addr = "ws://" + window.location.hostname + ":" + window.location.port + "/ws";
    console.log(addr);
    var websocket = new WebSocket( addr );
   
    websocket.onmessage = function(e){
        var server_message = e.data;
     console.log(server_message);
     if(server_message[0]=='[' ){
        var html='<a-scene  camera look-controls wasd-controls>'
         var myshapes = eval(server_message)
         
         for(let i=0;i<myshapes.length;i++){
             if(myshapes[i] == "rectangle"){
                 html += '<a-box id="rectangle" position="0.9 0.6 -2.9" rotation ="0 0 0" scale="0.5 1.0 1.0" color="#4CC3D9"></a-box>';
             }
             else if(myshapes[i] == "square"){
                 html += '<a-box id="square" position="-0.8 0.526 -2.8" rotation ="0 0 0" scale="0.5 0.5 0.5" color="green"></a-box>'
             }
             else if(myshapes[i] == "circle"){
                 html += '<a-sphere position="1 0.654 -5" scale="0.5 0.5 0.5" radius="1.25" color="#EF2D5E"></a-sphere>'         
             }else if(myshapes[i] == "pentagon"){
                 html += '<a-dodecahedron position="-0.7 0.5 -4.9" color="#FF926B" radius="5" scale="0.1 0.1 0.1"></a-dodecahedron>' 
             }else if(myshapes[i] == "triangle"){
                 html += '<a-cone color="brown" position="-0.03 0.4 -4" radius-bottom="2" radius-top="0" scale="0.2 0.7 0.2"></a-cone>' 
             }
         }
         html += '<a-plane position="0 0 -4" rotation="-90 0 0" width="4" height="4" color="#7BC8A4"></a-plane> <a-sky color="#ECECEC"></a-sky>'
        html += '  </a-scene>'
        document.getElementById('myscene').innerHTML = html;
     }

       
      
       

    }
   
    websocket.onopen = function(){
       console.log('Connection open!');
  
    }
   
    websocket.onclose = function(){
       console.log('Connection closed');
 
    }
    
    function test() {
             
                websocket.send("tested") ;
         
    }
  </script>
    </body>
</html>""" )
 
runMessageSend = True        
class ClientWebSocketHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, args, kwargs):
        tornado.websocket.WebSocketHandler.__init__(self, args, kwargs)
        print("ClientWebSocketHandler.init")
        
        self.my_thread = threading.Thread(target = self.run)
        self.my_thread.start()
        
    def run(self):
        while runMessageSend:
            try:
                s = sendQueue.get(block=True, timeout=0.1)
            except Exception:
                continue  
            if self.ws_connection is None:
                print("discard ", s)  
            else:
                print("send ", s)  
                try:
                    self.write_message(s )
                except Exception:
                    pass
            
    def open(self, *args, **kwargs):
        print("open", args, kwargs)

    def on_close(self, *args, **kwargs):
        print ("on_close", args, kwargs)

    def on_message(self, m):
        print ( "received", m )
        if m == "tested":
            shapes_in_pic = detect_myshapes('n7.jpg')
            self.write_message(str(shapes_in_pic))
            

        
def make_app():
    return tornado.web.Application(
                 [ 
                     (r"/"  , MainHandler), 
                     (r"/ws", ClientWebSocketHandler), 
                 ]
                )

if __name__ == "__main__":
    print("start")
    app = make_app()
    app.listen(8080)
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        peripheral.stop()
        runMessageSend = False
        tornado.ioloop.IOLoop.current().stop()
    print("stopped")