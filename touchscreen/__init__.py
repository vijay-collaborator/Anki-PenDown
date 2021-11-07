# -*- coding: utf-8 -*-
# Copyright: Michal Krassowski <krassowski.michal@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""
This plugin adds the function of touchscreen, similar that one implemented in AnkiDroid.

It adds a "view" menu entity (if it doesn't exist) with options like:

    switching touchscreen
    modifying some of the colors


If you want to contribute visit GitHub page: https://github.com/krassowski/Anki-TouchScreen
Also, feel free to send me bug reports or feature requests.

Copyright: Michal Krassowski <krassowski.michal@gmail.com>
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html,
Important parts of Javascript code inspired by http://creativejs.com/tutorials/painting-with-pixels/index.html
"""

__addon_name__ = "TouchScreen"
__version__ = "0.3.1"

from aqt import mw, dialogs
from aqt.utils import showWarning


from anki.lang import _
from anki.hooks import addHook

from PyQt5.QtWidgets import QAction, QMenu, QColorDialog, QMessageBox, QInputDialog
from PyQt5 import QtCore
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSlot as slot

# This declarations are there only to be sure that in case of troubles
# with "profileLoaded" hook everything will work.

ts_state_on = False
ts_profile_loaded = False

ts_color = "#272828"
ts_line_width = 4
ts_opacity = 0.7
ts_default_review_html = mw.reviewer.revHtml


@slot()
def ts_change_color():
    """
    Open color picker and set chosen color to text (in content)
    """
    global ts_color
    qcolor_old = QColor(ts_color)
    qcolor = QColorDialog.getColor(qcolor_old)
    if qcolor.isValid():
        ts_color = qcolor.name()
        execute_js("color = '" + ts_color + "'; update_pen_settings()")
        ts_refresh()


@slot()
def ts_change_width():
    global ts_line_width
    value, accepted = QInputDialog.getDouble(mw, "Touch Screen", "Enter the width:", ts_line_width)
    if accepted:
        ts_line_width = value
        execute_js("line_width = '" + str(ts_line_width) + "'; update_pen_settings()")
        ts_refresh()


@slot()
def ts_change_opacity():
    global ts_opacity
    value, accepted = QInputDialog.getDouble(mw, "Touch Screen", "Enter the opacity (100 = transparent, 0 = opaque):", 100 * ts_opacity, 0, 100, 2)
    if accepted:
        ts_opacity = value / 100
        execute_js("canvas.style.opacity = " + str(ts_opacity))
        ts_refresh()


@slot()
def ts_about():
    """
    Show "about" window.
    """
    ts_about_box = QMessageBox()
    ts_about_box.setText(__addon_name__ + " " + __version__ + __doc__)
    ts_about_box.setGeometry(300, 300, 250, 150)
    ts_about_box.setWindowTitle("About " + __addon_name__ + " " + __version__)

    ts_about_box.exec_()


def ts_save():
    """
    Saves configurable variables into profile, so they can
    be used to restore previous state after Anki restart.
    """
    mw.pm.profile['ts_state_on'] = ts_state_on
    mw.pm.profile['ts_color'] = ts_color
    mw.pm.profile['ts_line_width'] = ts_line_width
    mw.pm.profile['ts_opacity'] = ts_opacity


def ts_load():
    """
    Load configuration from profile, set states of checkable menu objects
    and turn on night mode if it were enabled on previous session.
    """
    global ts_state_on, ts_color, ts_profile_loaded, ts_line_width, ts_opacity

    try:
        ts_state_on = mw.pm.profile['ts_state_on']
        ts_color = mw.pm.profile['ts_color']
        ts_line_width = mw.pm.profile['ts_line_width']
        ts_opacity = mw.pm.profile['ts_opacity']
    except KeyError:
        ts_state_on = False
        ts_color = "#f0f"
        ts_line_width = 4
        ts_opacity = 0.8
    ts_profile_loaded = True

    if ts_state_on:
        ts_on()

    assure_plugged_in()


def execute_js(code):
    web_object = mw.reviewer.web
    web_object.eval(code)


def assure_plugged_in():
    global ts_default_review_html

    if not mw.reviewer.revHtml == custom:
        ts_default_review_html = mw.reviewer.revHtml
        mw.reviewer.revHtml = custom

def resize_js():
    execute_js("setTimeout(resize, 101);");
    
def clear_blackboard():
    assure_plugged_in()

    if ts_state_on:
        execute_js("clear_canvas();");
        # is qFade the reason for having to wait?
        execute_js("setTimeout(resize, 101);");

def ts_onload():
    """
    Add hooks and initialize menu.
    Call to this function is placed on the end of this file.
    """
    addHook("unloadProfile", ts_save)
    addHook("profileLoaded", ts_load)
    addHook("showQuestion", clear_blackboard)
    addHook("showAnswer", resize_js)
    ts_setup_menu()


ts_blackboard = u"""
<div id="canvas_wrapper">
    <!--
    canvas needs touch-action: none so that it doesn't fire bogus
    pointercancel events. See:
    https://stackoverflow.com/questions/59010779/pointer-event-issue-pointercancel-with-pressure-input-pen
    -->
    <canvas id="main_canvas" width="100" height="100" style="touch-action: none"></canvas>
</div>
<div id="pencil_button_bar">
    <input type="button" class="active" onclick="active=!active;switch_visibility();switch_class(this, 'active');" value="\u270D" title="Toggle visiblity">
	<input type="button" class="" onclick="switch_drawing_mode();switch_class(this, 'active');" value="漢字" title="Toggle calligrapher">
    <input type="button" onclick="ts_undo();" value="\u21B6" title="Undo the last stroke" id="ts_undo_button">
    <input type="button" class="active" onclick="clear_canvas();" value="\u2715" title="Clean whiteboard">
</div>
<style>
#canvas_wrapper, #main_canvas
{
    position:absolute;
    top: 0px;
    left: 0px;
    z-index: 999;
	touch-action: none;
}
#main_canvas{
    opacity: """ + str(ts_opacity) + """;
	//pointer-events:none
	
}
.night_mode #pencil_button_bar input[type=button].active
{
    -webkit-filter: grayscale(0);
    filter: none;
    color: #fff!important;
}
#pencil_button_bar input[type=button].active
{
    -webkit-filter: grayscale(0);
    filter: none;
    color: black!important;
}
#pencil_button_bar
{
    position: fixed;
    top: 1px;
    right: 1px;
    z-index: 1000;
    font-family: "Arial Unicode MS", unifont, "Everson Mono", tahoma, arial;
}
#pencil_button_bar input[type=button]
{
    filter: gray;
    -webkit-filter: grayscale(1);
    filter: grayscale(1);
    border: 1px solid black;
    margin: 0 1px;
    display: inline-block;
    float: left;
    width: 90px!important;
    font-size: 130%;
    line-height: 130%;
    height: 50px;
    border-radius: 8px;
    background-color: rgba(250,250,250,0.5)!important;
    color: #ccc!important;
}
.night_mode #pencil_button_bar input[type=button]{
    background-color: rgba(10,10,10,0.5)!important;
    border-color: #ccc;
    color: #444!important;
    text-shadow: 0 0 1px rgba(5, 5, 5, 0.9);
}
#canvas_wrapper
{
    height: 100px
}
</style>

<script>
var visible = true;
var canvas = document.getElementById('main_canvas');
var wrapper = document.getElementById('canvas_wrapper');
var ts_undo_button = document.getElementById('ts_undo_button');
var ctx = canvas.getContext('2d');
var arrays_of_points = [ ];
var color = '#fff';
var calligraphy = false;
var line_type_history = [ ];
var line_width = 4;

canvas.onselectstart = function() { return false; };
wrapper.onselectstart = function() { return false; };

function switch_visibility()
{
	stop_drawing();
    if (visible)
    {
        canvas.style.display='none';
    }
    else
    {
        canvas.style.display='block';
    }
    visible = !visible;
}

//Initialize event listeners at the start;
canvas.addEventListener("pointerdown", pointerDownLine);
canvas.addEventListener("pointermove", pointerMoveLine);
window.addEventListener("pointerup", pointerUpLine);
canvas.addEventListener("pointerdown", pointerDownCaligraphy);
canvas.addEventListener("pointermove", pointerMoveCaligraphy);
window.addEventListener("pointerup", pointerUpCaligraphy);

function switch_drawing_mode()
{
    stop_drawing();
    calligraphy = !calligraphy;
}

function switch_class(e,c)
{
    var reg = new RegExp('(\\\s|^)' + c + '(\\s|$)');
    if (e.className.match(new RegExp('(\\s|^)' + c + '(\\s|$)')))
    {
        e.className = e.className.replace(reg, '');
    }
    else
    {
        e.className += c;
    }
}
function resize() {
    
    var card = document.getElementsByClassName('card')[0]
    
    // Run again until card is loaded
    if (!card){
        window.setTimeout(resize, 100)
        return;
        
    }
    // Check size of page without canvas
    canvas_wrapper.style.display='none';
    ctx.canvas.width = Math.max(card.scrollWidth, document.documentElement.clientWidth);
    ctx.canvas.height = Math.max(document.documentElement.scrollHeight, document.documentElement.clientHeight);
    
    canvas_wrapper.style.display='block';
    
    
    /* Get DPR with 1 as fallback */
    var dpr = window.devicePixelRatio || 1;
    
    /* CSS size is the same */
    canvas.style.height = ctx.canvas.height + 'px';
    wrapper.style.width = ctx.canvas.width + 'px';
    
    /* Increase DOM size and scale */
    ctx.canvas.width *= dpr;
    ctx.canvas.height *= dpr;
    ctx.scale(dpr, dpr);
    
	update_pen_settings()
    
}


window.addEventListener('resize', resize);
window.addEventListener('load', resize);
window.requestAnimationFrame(draw_last_line_segment);

var isPointerDown = false;
var mouseX = 0;
var mouseY = 0;
var active = true;

function update_pen_settings(){
    ctx.lineJoin = ctx.lineCap = 'round';
    ctx.lineWidth = line_width;
    ctx.strokeStyle = color;
    ts_redraw()
}

function ts_undo(){
	stop_drawing();
    switch (line_type_history.pop()) {
        case 'C'://Calligraphy
            strokes.pop();    
            break;
        case 'L'://Simple Lines
            arrays_of_points.pop()
            break;
        default://how did you get here??
            console.log("Unrecognized line type for undo") 
            break;
    }
    
    if(!line_type_history.length)
    {
        ts_undo_button.className = ""
    }
    ts_redraw()
}

function ts_redraw() {
	pleaseRedrawEverything = true;
}

function clear_canvas()
{
	//don't continue to put points into an empty array(pointermove) if clearing while drawing on the canvas
	stop_drawing();
    arrays_of_points = [];
    strokes = [];
    line_type_history = [];
	ts_redraw();
}

function stop_drawing() {
	isPointerDown = false;
	drawingWithPressurePenOnly = false;
}

function start_drawing() {
    ts_undo_button.className = "active"
    isPointerDown = true;
}

function draw_last_line_segment() {
    window.requestAnimationFrame(draw_last_line_segment);
    draw_upto_latest_point_async(lastLine, lastPoint)
}

var lastLine = 0;
var lastPoint = 0;
var p1,p2,p3;

async function draw_path_at_some_point_async(startX, startY, midX, midY, endX, endY, lineWidth) {
		ctx.beginPath();
		ctx.moveTo((startX + (midX - startX) / 2), (startY + (midY - startY)/ 2));
		ctx.quadraticCurveTo(midX, midY, (midX + (endX - midX) / 2), (midY + (endY - midY)/ 2));
		//ctx.lineTo(endX, endY);
		ctx.lineWidth = lineWidth;
		ctx.stroke();
};
//Weird bug or feature of canvas?? : ending of the previous line gets a tiny bit wider at the end when a new line is drawn
var pleaseRedrawEverything = false;
async function draw_upto_latest_point_async(startLine, startPoint){
	//Don't keep redrawing the same last point over and over
	if(!pleaseRedrawEverything && 
    startLine == arrays_of_points.length-1 && startPoint == arrays_of_points[startLine].length-1) return;
	
	var fullRedraw = false;//keep track if this call started a full redraw to unset pleaseRedrawEverything flag later.
	if (pleaseRedrawEverything) {// erase everything and draw from start
	fullRedraw = true;
	startLine = 0;
	startPoint = 0;
	ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
	}

	for(var i = startLine; i < arrays_of_points.length; i++){ //Draw Lines
		lastLine = i;
		///0,0,0; 0,0,1; 0,1,2 or x+1,x+2,x+3
		//take the 2 previous points in addition to current one at the start of the loop.
		p2 = arrays_of_points[i][startPoint > 1 ? startPoint-2 : 0];
		p3 = arrays_of_points[i][startPoint > 0 ? startPoint-1 : 0];
        for(var j = startPoint; j < arrays_of_points[i].length; j++){
			lastPoint = j;//track which point was last drawn so we can pick up where we left off on the next refresh.
			p1 = p2;
			p2 = p3;
			p3 = arrays_of_points[i][j];
			draw_path_at_some_point_async(p1[0],p1[1],p2[0],p2[1],p3[0],p3[1],p3[2]);
        }
		startPoint = 0;
    }

	if (fullRedraw) {//finished full redraw, now can unset redraw all flag so no more full redraws until necesarry
    for(var i = 0; i < strokes.length; i++){//Draw Calligraphy Strokes by redrawing everything, to erase guide line
        strokes[i].draw(WEIGHT, ctx);//TODO don't redraw everything just to erase the guide line
    }
    pleaseRedrawEverything = false;
	fullRedraw = false;
    lastLine = 0;
    lastPoint = 0;
	}
}

var drawingWithPressurePenOnly = false; // hack for drawing with 2 main pointers when using a presure sensitive pen

function pointerDownLine(e) {
	if (!e.isPrimary || calligraphy) { return; }
	if (e.pointerType[0] == 'p') { drawingWithPressurePenOnly = true }
	else if ( drawingWithPressurePenOnly) { return; }
    if(!isPointerDown){
        event.preventDefault();
        arrays_of_points.push([[
			e.offsetX,
			e.offsetY,
			e.pointerType[0] == 'p' ? (0.5 + e.pressure * line_width * 2) : line_width]]);
        start_drawing();
    }
}

function pointerMoveLine(e) {
	if (!e.isPrimary || calligraphy) { return; }
	if (e.pointerType[0] != 'p' && drawingWithPressurePenOnly) { return; }
    if (isPointerDown && active) {
        arrays_of_points[arrays_of_points.length-1].push([
			e.offsetX,
			e.offsetY,
			e.pointerType[0] == 'p' ? (0.5 + e.pressure * line_width * 2) : line_width]);
    }
}

function pointerUpLine(e) {
    /* Needed for the last bit of the drawing. */
	if (!e.isPrimary || calligraphy) { return; }
	if (e.pointerType[0] != 'p' && drawingWithPressurePenOnly) { return; }
     if (isPointerDown && active) {
        arrays_of_points[arrays_of_points.length-1].push([
			e.offsetX,
			e.offsetY,
			e.pointerType[0] == 'p' ? (e.pressure * line_width * 2) : line_width]);
        line_type_history.push('L');//Add new Simple line marker to shared history
    } 
	stop_drawing();
}

document.addEventListener('keyup', function(e) {
    // alt + Z or z
    if ((e.keyCode == 90 || e.keyCode == 122) && e.altKey) {
		e.preventDefault();
        ts_undo();
    }
    // /
    if (e.key === "/") {
        clear_canvas();
    }
	// ,
    if (e.key === ",") {
        switch_visibility();
    }
    // alt + C or c
    if ((e.key === "c" || e.key === "C") && e.altKey) {
        switch_drawing_mode();
    }
})

/*
 -------------------------------- Caligrapher ------------------------------------------
 Created By: August Toman-Yih
 Git Repository: https://github.com/atomanyih/Calligrapher
*/
/* ------------------------------        script.js        -----------------------------*/
//Modified to work with current canvas and board
//share the same canvas with pressure drawing
 /*var canvas = document.getElementById('canvas'),
    width = canvas.width,
    height = canvas.height,
    context = canvas.getContext("2d");
	*/

function drawCircle(x,y,r,ctx) {
    ctx.beginPath();
    ctx.arc(x,y,r, 0, 2*Math.PI,false);
    //ctx.fill();
    ctx.stroke();
}

function drawLine(x0,y0,x1,y1,ctx) {
    ctx.beginPath();
    ctx.moveTo(x0,y0);
    ctx.lineTo(x1,y1);
    ctx.stroke();
}


//FIXME REORGANIZE EBERYTING
//--- constants ---//
RESOLUTION = 4; 
WEIGHT = 15;
MIN_MOUSE_DIST = 5;
SPLIT_THRESHOLD = 8;
SQUARE_SIZE = 300;
    
//--- variables ---//
strokes = [];
points = [];
lines = [];
currentPath = [];
errPoint = [];
//use shared isPointerDown instead
//mouseDown = false;

// // share update function with pressure drawing so they don't clearRect eachother
// function update() {
//     ctx.clearRect(0,0,ctx.canvas.width,ctx.canvas.height);
//     for(var i = 0; i<strokes.length; i++)
//         strokes[i].draw(WEIGHT,ctx);
// }

function drawCurrentPath() {//maybe will have issues with this due to not clearing the screen and redrawing all stokes each time
    ctx.beginPath();
    ctx.moveTo(currentPath[0][0],currentPath[0][1]);
    for(var i = 1; i<currentPath.length; i++) 
        ctx.lineTo(currentPath[i][0],currentPath[i][1]);
    ctx.stroke();
}

function pointerDownCaligraphy(e) {
    if (!e.isPrimary || !calligraphy) { return; }
    event.preventDefault();//don't paint anything when clicking on buttons, especially for undo to work
    start_drawing();
};

function pointerMoveCaligraphy(e) {
    if (!e.isPrimary || !calligraphy) { return; }
    if(isPointerDown) {
        var mousePos = [e.offsetX, e.offsetY];
        if(currentPath.length != 0) {
            if(getDist(mousePos,currentPath[currentPath.length-1])>=MIN_MOUSE_DIST)
                currentPath.push(mousePos);
            drawCurrentPath();
        } else
            currentPath.push(mousePos);
    } 
};

function pointerUpCaligraphy(e) {
    if (!e.isPrimary || !calligraphy || !currentPath.length) { return; }
    stop_drawing();
    points = currentPath;
    
    var curves = fitStroke(points);
    
    strokes.push(new Stroke(curves));
    
    line_type_history.push('C');//Add new Caligragraphy line marker to shared history
    currentPath = [];// clear the array on pointer up so it doesnt enter new lines when clicking on buttons
    ts_redraw();
};

// // handled in ts_undo()
// keydown = function(event) {
//     var k = event.keyCode;
//     console.log(k);
//     if(k==68) {
//         strokes.pop();
//     }
//     update();
// };
//
//window.addEventListener("keydown",keydown,true);
//
//update();

/* ------------------------------Unchanged Caligrapher Code------------------------------*/
/* ------------------------------        Corners.js        ------------------------------*/
/**
 * @classDescription        A shape made out of bezier curves. Hopefully connected
 * @param {Array} sections
 */
 function BezierShape(sections) {
    this.sections = sections;
    this.name = ""; //optional
    this.skeleton = [];
}

BezierShape.prototype.copy = function() {
    var newSections = [],
        newSkeleton = [];
    for(var i in this.sections) {
        newSections[i] = [];
        for(var j = 0; j<4; j++) {
            newSections[i][j] = this.sections[i][j].slice(0);
        }
    }
    for(var i in this.skeleton)
        newSkeleton[i] = this.skeleton[i].copy();
    
    var copy = new BezierShape(newSections);
    copy.name = this.name;
    copy.skeleton = newSkeleton;
    return copy;
};

/**
 * Draws the BezierShape NO SCALING OR NUFFIN. Probably only used internally
 * @param {Object} ctx
 */
BezierShape.prototype.draw = function(ctx) {
    var x = this.sections[0][0][0], //ew
        y = this.sections[0][0][1];
    ctx.beginPath();
    ctx.moveTo(x,y);
    for(var i = 0; i < this.sections.length; i++) {
        var b = this.sections[i];
        ctx.bezierCurveTo(b[1][0],b[1][1],b[2][0],b[2][1],b[3][0],b[3][1]);
    }
    ctx.closePath();
    
    ctx.fill();
};

function Bone(points,offset) {
    this.points = points;
    this.offset = offset;
}

Bone.prototype.copy = function() {
    var nP = [];
    for(var i in this.points)
        nP[i] = this.points[i].slice(0);
    return new Bone(nP,this.offset);
};

function drawCornerScaled(corner,pos,dir,width,height,ctx) { //FIXME degree, radian inconsistency
    ctx.save();
    ctx.translate(pos[0],pos[1]);
    ctx.rotate(dir);
    ctx.scale(height,width);
    
    corner.draw(ctx);
    ctx.restore();
}

function drawCorner(corner,pos,dir,width,ctx) {
    drawCornerScaled(corner,pos,dir,width,width,ctx);
}

function drawDICorner(corner,attrs,width,ctx) {
    if(corner == null)
        return;
    
    // corner rotation
    var pos = attrs.point,
        inAngle = attrs.inAngle-corner.skeleton["armA"].offset, //This is so the whole corner is rotated //FIXME a little gross
        outAngle = attrs.outAngle,
        c = setBoneAngles(corner,[["armB",(outAngle-inAngle)/180*Math.PI]]); 

    drawCorner(c,pos,inAngle/180*Math.PI,width,ctx);
}



// HERE ARE SOME CORNERS // some may need to be rotated
kappa = 0.5522847498;
// Circle-ish thing. Not a corner.
CIRCLE = new BezierShape([
    [[-5,0],[-5,-5*kappa],[-5*kappa,-5],[0,-5]],
    [[0,-5],[5*kappa,-5],[5,-5*kappa],[5,0]],
    [[5,0],[5,5*kappa],[5*kappa,5],[0,5]],
    [[0,5],[-5*kappa,5],[-5,5*kappa],[-5,0]]
]);
                
        
C1 = new BezierShape([
     [[15,6],  [-3,4],     [-11,5],   [-20,0]]
    ,[[-20,0],  [-15,-5],  [4,-9],    [13,-5]]
    ,[[13,-5], [20,0],     [21,8],    [15,6]]
]);
C1.name = "C1";

C2 = new BezierShape([
     [[2,5],    [-2,5],     [-12,2],    [-13,-2]]
    ,[[-13,2],  [-7,-5],    [0,-5],     [2,-5]]
    ,[[2,-5],   [3,-5],     [3,5],      [2,5]]
]);
C2.name = "C2";

C3 = new BezierShape([
    [[-8,5],    [-10,5],    [-10,-5],   [-8,-5]]
   ,[[-8,-5],   [3,-5],     [15,0],     [15,5]]
   ,[[15,5],    [10,7],     [2,5],      [-8,5]]
]);
C3.name = "C3";

C4 = new BezierShape([
    [[0,5],     [-2,5],     [-4,7],     [-5,8]]
   ,[[-5,8],    [-7,10],    [-9,12],    [-8,5]]
   ,[[-8,5],    [-7,3],     [-5,-5],    [0,-5]]
   ,[[0,-5],    [3,-5],     [3,5],      [0,5]]
]);
C4.name = "C4";

C5 = new BezierShape([
    [[0,-5],    [-3,-5],    [-3,5],     [0,5]]
   ,[[0,5],     [8,5],      [10,5],     [15,2]]
   ,[[15,2],    [12,-2],    [-2,-5],    [0,-5]]
]);
C5.name = "C5";

C6 = new BezierShape([
    [[0,5],     [-6,6],     [-8,7],     [-12,8]]
    ,[[-12,8],  [-13,9],    [-13,7],    [-12,6]]
    ,[[-12,6],  [-10,3],    [-5,-4],    [0,-5]]
    ,[[0,-5],   [3,-5],     [3,5],      [0,5]]
]);
C6.name = "C6";

C7 = new BezierShape([
    [[-5,-5],[0,-5],[11,-7],[15,-6]]
    ,[[15,-6],[17,-5],[2,4],[1,5]]
    ,[[1,5],[0,5],[0,5],[-5,5]]
    ,[[-5,5],[-8,5],[-8,-5],[-5,-5]]
]);
C7.name = "C7";

SI_CORNERS = [C1,C2,C3,C4,C5,C6,C7];

C8 = new BezierShape([
    [[-13,3],   [-20,3],    [-20,-3],   [-13,-3]],
    [[-13,-3],  [-5,-5],    [-6,-7],    [-4,-8]],
    [[-4,-8],   [0,-8],     [12,3],     [7,5]],
    [[7,5],     [5,6],      [5,8],      [3,13]],
    [[3,13],    [3,20],     [-3,20],    [-3,13]],
    [[-3,13],   [-5,5],     [-10,5],    [-13,3]]
]);
C8.name = "C8";
C8.skeleton["armA"] = new Bone([[0,0],[0,1],[0,2],[0,3],[1,0],[1,1],[5,2],[5,3]],0);
C8.skeleton["armB"] = new Bone([[4,0],[4,1],[4,2],[4,3],[3,2],[3,3],[5,0],[5,1],
                                [1,2],[1,3],[2,0],[2,1]],90);

C8R = horizFlipCopy(C8);

/*C9 = new BezierShape([ //TODO fix corner so that stem moves depending on angle
    [[-3,-10],  [-3,-15],   [3,-15],    [3,-10]],
    [[3,-10],   [5,-5],     [6,6],      [0,11]],
    [[0,11],    [-5,15],    [-3,5],     [-10,3]],
    [[-10,3],   [-15,3],    [-15,-3],   [-10,-3]],
    [[-10,-3],  [-5,-5],    [-5,-7],    [-3,-10]]
]);
C9.name = "C9";
C9.skeleton["armA"] = new Bone([[0,0],[0,1],[0,2],[0,3],[1,0],[1,1],[4,2],[4,3]],90);
C9.skeleton["armB"] = new Bone([[3,0],[3,1],[3,2],[3,3],[4,0],[4,1],[2,2],[2,3]],180);*/

C9 = new BezierShape([ //note, 90º angles look a little weird
   [[-4,-12],[-4,-15],[4,-15],[5,-12]],
   [[5,-12],[5,-2],[6,3],[1,8]],
   [[-1,8],[-3,11],[-4,2],[-12,-5]],
   [[-12,-5],[-15,-7],[-15,-9],[-10,-8]],
   [[-10,-8],[-6,-8],[-4,-7],[-4,-12]] 
]);
C9.name = "C9";
C9.skeleton["armA"] = new Bone([[0,0],[0,1],[0,2],[0,3],[1,0],[1,1],[4,2],[4,3],[1,2]],90); //not that this actually matters
C9.skeleton["armB"] = new Bone([[3,0],[3,1],[3,2],[3,3],[4,0],[4,1],[2,2],[2,3]],210);

C9R = vertFlipCopy(C9);

C10 = new BezierShape([
    [[-5,5],[-6,5],[-6,-5],[-5,-5]],
    [[-5,-5],[-2,-7],[2,-7],[5,-5]],
    [[5,-5],[6,-5],[6,5],[5,5]],
    [[5,5],[2,7],[-2,7],[-5,5]]
]);

C10.name = "C10";
C10.skeleton["armA"] = new Bone([[0,0],[0,1],[0,2],[0,3],[1,0],[1,2],[3,2],[3,3]],0);
C10.skeleton["armB"] = new Bone([[2,0],[2,1],[2,2],[2,3],[3,0],[3,1],[1,2],[1,3]],0);

function linInterpolate(y0,y1,mu) {
    return y0*(1-mu) + y1*mu;
}

function cosInterpolate(y0,y1,mu) {
    var mu2 = (1-Math.cos(mu*Math.PI))/2;
    return y0*(1-mu2)+y1*mu2;
}

/**
 * Returns a function that linearly interpolates between the values given
 */
function linFunction(points) {
    return function(t) {
        if(t==0)
            return points[0][1];
        for(var i = 1; i<points.length; i++) {
            var p0 = points[i-1],
                p1 = points[i];
            if(t<=p1[0] && t>p0[0]) {
                var mu = (t-p0[0])/(p1[0]-p0[0]);
                return linInterpolate(p0[1],p1[1],mu); //cubic might be better
            }
        }
    };
}

/**
 * Returns a function that cosine interpolates between the values given
 */
function cosFunction(points) {
    return function(t) {
        if(t==0)
            return points[0][1];
        for(var i = 1; i<points.length; i++) {
            var p0 = points[i-1],
                p1 = points[i];
            if(t<=p1[0] && t>p0[0]) {
                var mu = (t-p0[0])/(p1[0]-p0[0]);
                return cosInterpolate(p0[1],p1[1],mu); //cubic might be better
            }
        }
    };
}

//example thickness functions
function one(t) {
    return 1;
}

function test(t) {
    return t;
}

//These are ugly
SEGMENT_I = cosFunction([[0,1],[.5,.7],[1,1]]); //FIXME, sometimes extends past corners
SEGMENT_II = linFunction([[0,1],[.5,.8],[1,.2]]); //kinda ugly :||
SEGMENT_III = linFunction([[0,.2],[.5,.8],[1,1]]);

HEN = [C2,SEGMENT_I,C3];
SHU1 = [C4,SEGMENT_I,C5];
SHU2 = [C4,SEGMENT_II];
NA = [C6,SEGMENT_I,C7];
DIAN = [C1];
OTHER = [C4,SEGMENT_II];

function RAND(t) {
    return Math.random();
}

function setBoneAngles(c,dirList) {
    var c = c.copy();
    
    for(var i in dirList) {
        var dir = dirList[i][1],
            bone = dirList[i][0];
        for(var j in c.skeleton[bone].points) {
            var p = c.skeleton[bone].points[j],
                offset = c.skeleton[bone].offset/180*Math.PI,
                vec = c.sections[p[0]][p[1]];
            //console.log(vec);
            console.log(dir-offset);
            //console.log(rotate(vec,dir-offset));
            c.sections[p[0]][p[1]] = rotate(vec,dir-offset);
            
        }
    }
    
    return c;
}

function vertFlipCopy(c) {
    var c = c.copy();
    
    for(var i in c.sections){
        for(var j in c.sections[i]) {
            c.sections[i][j][1] = -c.sections[i][j][1];
        }
    }
    for(var i in c.skeleton) {
        c.skeleton[i].offset = 360 - c.skeleton[i].offset;
    }
    return c
}

function horizFlipCopy(c) {
    var c = c.copy();
    
    for(var i in c.sections){
        for(var j in c.sections[i]) {
            c.sections[i][j][0] = -c.sections[i][j][0];
        }
    }
    for(var i in c.skeleton) {
        c.skeleton[i].offset = 180 - c.skeleton[i].offset;
        if(c.skeleton[i].offset<0)
            c.skeleton[i].offset += 360;
    }
    return c
}

/* ------------------------------        bezier.js        ------------------------------*/

//TODO use vectors for everything so it's less stupid

// Generalized recurvsive BEZIER FUNCTIONS (why am I doing it this way I don't know)
/**
 * returns a point on the bezier curve
 * @param {Array} ps    Control points of bezier curve
 * @param {Numeric} t   Location along bezier curve [0,1]  
 * @return {Array}      Returns the point on the bezier curve
 */
 function bezierPos(ps, t) {
    var size = ps.length;
    if(size == 1)
        return ps[0];
        
        //WARNING, changed direction on this. May cause problems
    var bx = (t) * bezierPos(ps.slice(1),t)[0] + (1-t) * bezierPos(ps.slice(0,size-1),t)[0],
        by = (t) * bezierPos(ps.slice(1),t)[1] + (1-t) * bezierPos(ps.slice(0,size-1),t)[1];
        
    return [bx,by];
}

function bezierSlo(ps, t) {
    var size = ps.length;
    
    if(size == 1)
        return ps[0];
        
    var dx = bezierPos(ps.slice(0,size-1),t)[0] - bezierPos(ps.slice(1),t)[0] ,
        dy = bezierPos(ps.slice(0,size-1),t)[1] - bezierPos(ps.slice(1),t)[1];
        
    return dy/dx;
}

// Bezier function class. Meant simply as a math thing (no drawing or any bullshit)
/**
 * @class Bezier function class.
 * @return {Bezier} Returns the bezier function
 */
function Bezier(controlPoints) {
    this.order = controlPoints.length-1; //useful? or obtuse? //Answer: not used anywhere
    this.controlPoints = controlPoints; 
}

Bezier.prototype.getStart = function() {
    return this.controlPoints[0];
};

Bezier.prototype.getEnd = function() {
    return this.controlPoints[this.order];
};

Bezier.prototype.getPoint = function(t) {
    return bezierPos(this.controlPoints,t);
};

Bezier.prototype.drawPlain = function(ctx) {
    if(this.order == 3) {
        var c = this.controlPoints;
        ctx.beginPath();
        ctx.moveTo(c[0][0],c[0][1]);
        ctx.bezierCurveTo(c[1][0],c[1][1],c[2][0],c[2][1],c[3][0],c[3][1]);
        ctx.stroke();
    }
        
};

Bezier.prototype.getDerivativeVector = function(t) {
    var size = 0.001,
        p0 = null,
        p1 = null;
    if(t<size) {
        p0 = bezierPos(this.controlPoints,t);
        p1 = bezierPos(this.controlPoints,t+2*size);
    } else if (1-t<size) {
        p0 = bezierPos(this.controlPoints,t-2*size);
        p1 = bezierPos(this.controlPoints,t);
    } else {
        p0 = bezierPos(this.controlPoints,t-size);
        p1 = bezierPos(this.controlPoints,t+size); 
    }
    return sub(p1,p0);
};

Bezier.prototype.getTangentVector = function(t) {
    return normalize(this.getDerivativeVector(t));
};

Bezier.prototype.getLength = function() {
    var res = 50, //FIXME: can't use resolution :|| that would be circular
        len = 0,
        point = this.getStart();
    for(var i = 0; i <= res; i++){
        var t = i/res;
        len += getDist(point,this.getPoint(t));
        point = this.getPoint(t);
    }
    return len;
};

Bezier.prototype.getLengthAt = function(t) {
    return getLengthAtWithStep(t,0.01);
};

Bezier.prototype.getLengthAtWithStep = function(t,s) {
    var tt = 0,
        len = 0,
        point = this.getStart();
    while(tt <= t) {
        var newPoint = this.getPoint(tt);
        len += getDist(point,newPoint);
        point = newPoint;
        t += s;
    }
    return len;
};

Bezier.prototype.getPointByLength = function(l) {//doesn't actually return a point. bad name
    var t = 0,
        len = 0,
        point = this.getStart();
    while(len < l) {
        var newPoint = this.getPoint(t);
        len += getDist(point,newPoint);
        point = newPoint;
        t += 0.01;
        if(t>=1)
            return 1; //so we don't extrapolate or anything stupid
    }
    return t;
};

Bezier.prototype.getPointByLengthBack = function(l) {//doesn't actually return a point. bad name
    var t = 1,
        len = 0,
        point = this.getEnd();
    while(len < l) {
        var newPoint = this.getPoint(t)
        len += getDist(point,newPoint);
        point = newPoint;
        t -= 0.01;
        if(t<=0)
            return 1; //so we don't extrapolate or anything stupid
    }
    return t;
};

function getSlopeVector(slope,length) {
    var x = length * Math.cos(Math.atan(slope)),
        y = length * Math.sin(Math.atan(slope));
    return [x,y];
}

function scalePoint(s0,s1,p0,p1,v) { //Could probs be simplified, also currently not used
    var xScale = (p1[0]-p0[0])/(s1[0]-s0[0]), //scaling factos
        yScale = (p1[1]-p0[1])/(s1[1]-s0[1]),
        x = p0[0]+xScale*(v[0]-s0[0]), //Scaled x and y
        y = p0[1]+yScale*(v[1]-s0[1]);
    return [x,y];
}

//Draws a bezier curve scaled between the two points (good idea? bad idea? dunno.) 
/**
 * @param {Bezier}  curve   The bezier curve to be drawn
 * @param {Numerical} wid   Nominal width
 * @param {Function} wF     Width function
 * @param {Context} ctx     Context to draw to
 */
//FIXME width function gets "bunched up" around control points (detail below)
//      the bezier calculation means that more of t is spent near control points. turn on debug to see
//      this is good for detail b/c it means higher resolution at tight curves (a happy accident)
//      but the width contour gets a bit bunched up. solution: instead of wF(t), use wF(currentLength/totalLength)

//FIXME Ugly (code)
function drawBezier(curve,wid,wF,ctx) { 
    var length = curve.getLength(),
        numPoints = Math.round(length/RESOLUTION),
        leftPoints = [],
        rightPoints = [],
        currentPoint = sub(scale(curve.getStart(),2),curve.controlPoints[1]);

    for(var i = 0; i <= numPoints; i++){
        var t = i/numPoints,
            centerPoint = curve.getPoint(t)
            offset = scale(perpNorm(sub(centerPoint,currentPoint)),wF(t)*wid/2);
            
        leftPoints.push(add(centerPoint,offset));
        rightPoints.push(sub(centerPoint,offset));
        currentPoint = centerPoint;

    }
    //Drawing the polygon
    var s = leftPoints[0];
    ctx.beginPath();
    ctx.moveTo(s[0],s[1]); //starting from start center
    for(var i = 0; i < leftPoints.length; i++){
        var p = leftPoints[i];
        ctx.lineTo(p[0],p[1]);
    }
    for(var i = rightPoints.length-1; i >= 0; i--){
        var p = rightPoints[i];
        ctx.lineTo(p[0],p[1]);
    }
    ctx.closePath();
    ctx.fill();
}

function drawBezierTransformed(p0,p1,curve,wid,wF,ctx) {
    var s0 = curve.getStart(),
        s1 = curve.getEnd(),
        xScale = (p1[0]-p0[0])/(s1[0]-s0[0]), //scaling factos
        yScale = (p1[1]-p0[1])/(s1[1]-s0[1]),
        controlPoints = [];
        
    for(var i = 0; i <= curve.order; i++) {
        var p = curve.controlPoints[i],
            x = p0[0]+xScale*(p[0]-s0[0]), //Scaled x and y
            y = p0[1]+yScale*(p[1]-s0[1]);
        controlPoints[i] = [x,y];
    }
    drawBezier(new Bezier(controlPoints),wid,wF,ctx);
        
}

/* ------------------------------        curveFitting.js        ------------------------------*/
function getLengths(chord) {
    var lens = [0]; //first is 0
    
    for(var i = 1; i<chord.length; i++)
        lens[i] = lens[i-1]+getDist(chord[i],chord[i-1]);
    return lens;
}

function normalizeList(lens) {
    for(var i = 1; i<lens.length; i++)
        lens[i] = lens[i]/lens[lens.length-1];
    return lens;
}

function findListMax(list) {
    var iMax = 0,
        max = list[0];
    for(var i = 0; i<list.length; i++) {
        if(max<list[i]) {
            iMax = i;
            max = list[i];
        }
    }
    return [iMax,max];       
}

function findListMin(list) {
    var iMin = 0,
        min = list[0];
    for(var i in list) {
        if(min>list[i]) {
            iMin = i;
            min = list[i];
        }
    }
    return [iMin,min];
}

function parameterize(chord) {
    /*var lens = getLengths(chord);
    return normalizeList(lens);*/
    var lens = [0]; //first is 0
    
    for(var i = 1; i<chord.length; i++)
        lens[i] = lens[i-1]+getDist(chord[i],chord[i-1]);
    for(var i = 1; i<chord.length; i++)
        lens[i] = lens[i]/(lens[chord.length-1]);
    return lens;
    
}

function parameterizeByLength(chord, curve) {
    var lens = getLengths(chord),
        ts = [0];
    for(var i = 1; i<chord.length; i++) {
        ts[i] = curve.getPointByLength(lens[i]);
    }
    return normalizeList(ts);
}

function coefficientHelper(chord,ts) { //bad name
    var c00 = 0, c01 = 0, c02x = 0, c02y = 0,
        c10 = 0, c11 = 0, c12x = 0, c12y = 0,
        x0 = chord[0][0],
        y0 = chord[0][1],
        x3 = chord[chord.length-1][0],
        y3 = chord[chord.length-1][1];
        
    for(var i = 0; i<ts.length; i++) {
        var t = ts[i],
            px = chord[i][0],
            py = chord[i][1];
        c00 += 3*Math.pow(t,2)*Math.pow(1-t,4); //I'm doing it the dumb way cause it's easier to read
        c01 += 3*Math.pow(t,3)*Math.pow(1-t,3);
        c02x += t*Math.pow(1-t,2)*(px - Math.pow(1-t,3) * x0 - Math.pow(t,3) * x3);
        c02y += t*Math.pow(1-t,2)*(py - Math.pow(1-t,3) * y0 - Math.pow(t,3) * y3);
        
        c10 += 3*Math.pow(t,3)*Math.pow(1-t,3);
        c11 += 3*Math.pow(t,4)*Math.pow(1-t,2);
        c12x += Math.pow(t,2)*(1-t)*(px - Math.pow(1-t,3) * x0 - Math.pow(t,3) * x3);
        c12y += Math.pow(t,2)*(1-t)*(py - Math.pow(1-t,3) * y0 - Math.pow(t,3) * y3);
    }
    return [[[c00,c01,c02x],[c10,c11,c12x]],
            [[c00,c01,c02y],[c10,c11,c12y]]];
}

function leastSquaresFit(chord,ts) { //IT FUCKIN WORKS FUCK YEAAAAAAAH
    if(chord.length < 4) {
        var c1 = chord[0],
            c4 = chord[chord.length-1],
            c2 = midpoint(c1,c4,0.25),
            c3 = midpoint(c1,c4,0.75);
        return new Bezier([c1,c2,c3,c4]);
    }
    var cs = coefficientHelper(chord,ts),
        xs = gaussianElimination(cs[0]),
        ys = gaussianElimination(cs[1]);
    
    return new Bezier([chord[0], [xs[0],ys[0]], [xs[1],ys[1]], chord[chord.length-1]]);
}

function getMaxErrorPoint(chord,ts,curve) {
    var max = 0,
        iMax = 0;
    for(var i = 0; i<ts.length; i++) {
        var dist = getDist(curve.getPoint(ts[i]),chord[i]);
        if(dist > max) {
            max = dist;
            iMax = i;
        }
    }
    return [iMax,max];
}

function fitStroke(chord) {
    var chords = splitChord(chord,detectCorners(chord)),
        curves = [];
        
    for(var i in chords) {
        var ts = parameterize(chords[i]),
            curve = leastSquaresFit(chords[i],ts);
        curves.push(curve);
    }
    
    return curves;
}

function splitCurve(chord,ts,curve) { //TODO FIGURE THIS FUCKING SHIT OUT
    var errs = [];
    for(var i = 1; i<chord.length; i++) {
        var chord1 = chord.slice(0,i+1),
            chord2 = chord.slice(i),
            ts1    = parameterize(chord1),
            ts2    = parameterize(chord2),
            curve1 = leastSquaresFit(chord1,ts1),
            curve2 = leastSquaresFit(chord2,ts2);
        errs.push(sumSquaredError(chord1,ts1,curve1) +
                  sumSquaredError(chord2,ts2,curve2));
    }
    //console.log(errs);
    return findListMin(errs);
}

function splitCurveAt(chord,i) {
    var chord1 = chord.slice(0,i+1),
        chord2 = chord.slice(i),
        ts1    = parameterize(chord1),
        ts2    = parameterize(chord2),
        curve1 = leastSquaresFit(chord1,ts1),
        curve2 = leastSquaresFit(chord2,ts2);
    return [curve1,curve2];
}

function sumSquaredError(chord,ts,curve) {
    var sum = 0;
    for(var i in chord) {
        sum += Math.pow(getDist(chord[i],curve.getPoint(ts[i])),2);
    }
    return sum;
}

// corner detection?

function detectCorners(chord) {
    var segmentLength = 30,
        angleThreshold = 135,
        indices = [];
    for(var i = 1; i<chord.length-1; i++) {
        var angle = getSmallerAngle(getAngleBetween(sub(chord[i-1],chord[i]), sub(chord[i+1],chord[i])))*180/Math.PI;

        if(angle<=angleThreshold) {
            indices.push(i);
        }
    }
    
    return indices;
}

//returns the shortest segment of the chord that is at least the given length
function getChordSegmentByLength(chord,length) {
    var dist = 0;
    var i = 0;
    while(dist<length) {
        i++;
        if(i >= chord.length) //if it's not long enough just return the whole thing
            return chord; 
        dist+=getDist(chord[i],chord[i-1]); 
    }
    return chord.slice(0,i);
}

function splitChord(chord,indices) {
    var newChords = [],
        ind = 0;
    for(var i in indices) {
        newChords.push(chord.slice(ind,indices[i]+1));
        ind = indices[i];
    }
    newChords.push(chord.slice(ind));
    return newChords;
}

function chordPrint(chord) {
    var s = "| ";
    for(var i in chord) {
        s+= chord[i] + " | ";
    }
    console.log(s);
}

/* ------------------------------        strokeDrawing.js        ------------------------------*/

//Stroke drawing and analysis
//Basically, a "stroke" will be a collection of segments
//the segments when drawn will be assigned corners and types and stuff

function drawSegment(wF,segment,width,ctx) {
    drawBezier(segment,width,wF,ctx);
    ctx.fillStyle = "rgba(0,0,0,1)";
}



function drawBasicStroke(segment,width,ctx) { //TODO
    var attrs = getSegmentAttributes(segment),
        comps = checkRules2(attrs,RULE_BS);
    
    //corners
    if(comps.length == 1){ //dian
        var point = midpoint(attrs.startPoint,attrs.endPoint,0.5);  //FIXME these stupid width division factors
        drawCornerScaled(comps[0],point,degToRad(attrs.startAngle),width/13,attrs.length/20,ctx);
    } else {
        drawCorner(comps[0],attrs.startPoint,degToRad(attrs.startAngle),width/10,ctx);
        if(comps.length == 3) {
            drawCorner(comps[2],attrs.endPoint,degToRad(attrs.endAngle),width/10,ctx);
        }
        
        drawSegment(comps[1],segment,width,ctx);
    }
}

function Stroke(segments) {
    this.segments = segments;
}

Stroke.prototype.drawPlain = function(ctx) {
    var x = this.segments[0].getStart()[0],
        y = this.segments[0].getStart()[1];
    ctx.moveTo(x,y);
    for(var i = 0; i < this.segments.length; i++) {
        var b = this.segments[i].controlPoints;
        ctx.bezierCurveTo(b[1][0],b[1][1],b[2][0],b[2][1],b[3][0],b[3][1]);
    }
    ctx.stroke();      
};

Stroke.prototype.draw = function(width, ctx) {
    if(this.segments.length == 1){ //Basic Stroke
        drawBasicStroke(this.segments[0],width,ctx);
    } else { //Compound stroke
        drawCompoundStroke(this,width,ctx);
    }
};

function drawCompoundStroke(stroke,width,ctx) { //FIXME copypasta
    var numSegments = stroke.segments.length;

    //corners
    var attrs = getSegmentAttributes(stroke.segments[0]),
        corners = [];
    
    var corner = checkRules2(attrs,RULE_CC_START);//checkRules(attrs,COMPOUND_CORNER_START);
    if(corner != null)
        drawCorner(corner,attrs.startPoint,attrs.startAngle/180*Math.PI,width/10,ctx);
    corners.push(corner);
    
    for(var i = 1; i<numSegments; i++) {
        attrs = getCornerAttributes(stroke.segments[i-1],stroke.segments[i]);
        corner = checkRules2(attrs,RULE_CC_MID);//checkRules(attrs,COMPOUND_CORNER_MID);
        if(corner != null)
            drawDICorner(corner,attrs,width/10,ctx);
        corners.push(corner);
    }
    attrs = getSegmentAttributes(stroke.segments[numSegments-1]);
    corner = checkRules2(attrs,RULE_CC_END);//checkRules(attrs,COMPOUND_CORNER_END);
    if(corner != null)
        drawCorner(corner,attrs.endPoint,attrs.endAngle/180*Math.PI,width/10,ctx);
    corners.push(corner);
    
    //SEGMENTS FIXME gross code
    
    if(corners[0] == null)
        drawSegment(SEGMENT_III,stroke.segments[0],width,ctx);
    else
        drawSegment(SEGMENT_I,stroke.segments[0],width,ctx);
    for(var i = 1; i<numSegments-1; i++) {
        drawSegment(SEGMENT_I,stroke.segments[i],width,ctx); //FIXME only segment I. this is not done!
    }
    if(corners[numSegments] == null)
        drawSegment(SEGMENT_II,stroke.segments[numSegments-1],width,ctx);
    else
        drawSegment(SEGMENT_I,stroke.segments[numSegments-1],width,ctx);
    ctx.fillStyle = "rgba(0,0,0,1)";
    
}

function inRange(num,range) {
    return num >= range[0] && num < range[1];
}

function inRanges(num,ranges) {
    for(var i = 0; i<ranges.length; i++) {
        if(inRange(num,ranges[i]))
            return true;
    }
    return false;
}

function getSegmentAttributes(seg) {
    var attrs = {
        "startAngle" : getSegAngleStart(seg) *180/Math.PI,
        "endAngle" : getSegAngleEnd(seg) * 180/Math.PI,
        "startPoint" : seg.getStart(),
        "endPoint" : seg.getEnd(),
        "length" : seg.getLength()
    };
    return attrs;
}

function getCornerAttributes(inSeg, outSeg) {
    var attrs = {
        "inAngle" : getSegAngleEnd(inSeg) * 180/Math.PI,
        "outAngle" : getSegAngleStart(outSeg) * 180/Math.PI,
        "point" : inSeg.getEnd()
    };
    attrs.betweenAngle = getInnerAngle(attrs.inAngle,attrs.outAngle);
    console.log(attrs.inAngle,attrs.outAngle);
    console.log(attrs.betweenAngle);
    return attrs;
}

function getInnerAngle(inAngle, outAngle) { //If outAngle is past inAngle, then it's negative
    inAngle = reduceAngleDeg(inAngle+180);
    var ang = Math.abs(getSmallerAngleDeg(inAngle - outAngle));
    if(inAngle>outAngle){
        if(inAngle-180<outAngle)
            return ang;
        return -ang;
    } else {
        if(outAngle-180<inAngle)
            return -ang;
        return ang;
    }
        
}

function innerAngleHelper(angle) { //if it's negative then it is the other angle
    if(angle>180)
        return angle-360;
    return angle;
}

function checkRule(obj,rule) {
    if(rule[0] == "Result")
        return rule[1];
    console.log(rule[0]);
    if(inRange(obj[rule[0]],rule[1]))
        return checkRule(obj,rule[2]);
    return null;
}

function checkRules(obj,ruleset) { //checks all rules, no shortcircuiting currently
    var results = [];
    console.log("Checking rules");
    for(var i = 0; i<ruleset.length-1; i++) {
        var result = checkRule(obj,ruleset[i]);
        if(result != null)
            results.push(result);
    }
    if(results.length > 1)
        throw "Overlapping conditions";
    if(results.length == 1)
        return results[0];
    console.log("no result");
    return ruleset[ruleset.length-1]; //default
}

function checkRules2(obj,ruleset) {
    var results = [];
    console.log("Checking rules");
    for(var i = 0; i<ruleset.length; i++) {
        if(ruleset[i].check(obj))
            return ruleset[i].result;
    }
    console.log("No Result");
    return null
}

function Rule(result,condition) {
    this.condition = condition;
    this.result = result;
}

Rule.prototype.check = function(attrs) {
    return checkCond(attrs,this.condition);
}

function checkCond(attrs,cond) {
    var op = OPERATIONS[cond[1]],
        val = attrs[cond[0]];
    console.log("Op:",cond[1]);
    console.log(cond[0],val);
    return op(attrs,val,cond.slice(2));
}


TH1 = 60;
TH2 = 40;

OPERATIONS = {
    "TRUE" : function(a,n,r) {
        return true;
    },
    "IN_RANGE" : function(a,n,r) {
        for(var i in r)
            if(n>=r[i][0] && n<r[i][1])
                return true;
            return false;
    },
    "GREATER_THAN" : function(a,n,r) {
        return n>=r;
    },
    "LESS_THAN" : function(a,n,r) {
        return n<r;
    },
    "OR" : function(a,n,c) {
        for(var i in c)
            if(checkCond(a,c[i]))
                return true; 
            return false;
    },
    "AND" : function(a,n,c) {
        for(var i in c) 
            if(!checkCond(a,c[i]))
                return false; 
            return true;
    }
};

RULE_CC_START = [
    new Rule(C2, ["startAngle", "IN_RANGE", [0,10], [350,360]]),
    new Rule(C4, ["startAngle", "IN_RANGE", [80,350]])
];

RULE_CC_END = [
    new Rule(C3, ["endAngle", "IN_RANGE", [0,10], [350,360]]),
    new Rule(C7, ["endAngle", "IN_RANGE", [10,80]]),
    new Rule(C5, ["engAngle", "IN_RANGE", [80,100]])
];

RULE_CC_MID = [
    new Rule(C8, ["", "AND", ["inAngle", "IN_RANGE",[0,45],[315,360]],
                             ["betweenAngle", "IN_RANGE",[0,180]]]),
    new Rule(C8R,["", "AND", ["inAngle", "IN_RANGE", [60,170]], //a little ugly :| but accurate?
                            ["betweenAngle", "IN_RANGE",[-180,0]]]), 
    new Rule(C9, ["", "AND", ["inAngle", "IN_RANGE", [45,145]],
                             ["betweenAngle","IN_RANGE", [0,180]]]),
    new Rule(C9R,["", "AND", ["inAngle", "IN_RANGE", [0,60], [240,360]],
                            ["betweenAngle","IN_RANGE",[-180,0]]])
];

RULE_BS = [ //TODO, fix the "default" case
    new Rule(DIAN,["length","LESS_THAN",TH2]),
    new Rule(HEN,["startAngle","IN_RANGE",[0,10],[350,360]]),
    new Rule(SHU1,["", "AND", ["startAngle","IN_RANGE",[80,100]],
                              ["length","GREATER_THAN",TH1]]),
    new Rule(SHU2,["", "AND", ["startAngle","IN_RANGE",[80,100]],
                              ["length","IN_RANGE",[TH2,TH1]]]), //to prevent overlap
    new Rule(NA,["startAngle","IN_RANGE",[10,80]]),
    new Rule(OTHER,["","TRUE"])
];

// Rules
BASIC_STROKE = [
    ["startAngle", [0,10]]
];

COMPOUND_CORNER_START = [
    ["startAngle",   [0,10],    ["Result",C2]],
    ["startAngle",   [80,350],  ["Result",C4]],
    ["startAngle",   [350,360], ["Result",C2]],
    null
    ];

COMPOUND_CORNER_MID = [
    ["inAngle",     [0,45], ["betweenAngle", [0,180], ["Result", C8]]],
    ["inAngle",     [315,360], ["betweenAngle", [0,180], ["Result", C8]]],
    ["inAngle",     [45,135], ["betweenAngle", [-180,-90], ["Result", C8R]]],
    ["inAngle",     [45,135], ["betweenAngle", [0,180], ["Result", C9]]],
    ["inAngle",     [45,180], ["betweenAngle", [-90,0], ["Result", C9R]]],
    ["inAngle",     [0,45], ["betweenAngle", [-180,0], ["Result", C9R]]],
    ["inAngle",     [315,360], ["betweenAngle", [-180,0], ["Result", C9R]]],
    null
];

COMPOUND_CORNER_END = [
    ["endAngle",   [0,10],    ["Result",C3]],
    ["endAngle",   [10,80],   ["Result",C7]],
    ["endAngle",   [80,100],  ["Result",C5]],
    null
    ];
   
/* ------------------------------        examples.js        ------------------------------*/

// (ugly) Character examples for testing

//compound stroke
CSTROKE_1 = new Stroke([
    new Bezier([[50,110],[60,110],[190,100],[200,90]]),
    new Bezier([[200,90],[205,90],[200,150],[195,150]]),
    new Bezier([[195,150],[170,160],[120,150],[100,150]])
])

/* ------------------------------        Character.js        ------------------------------*/
// Angle test distance
var ANG_DIST = 0.3;

function getSegAngleStart(curve) {
    var start = curve.getStart(),
        point = curve.getPoint(curve.getPointByLength(20)),//curve.getPoint(ANG_DIST),
        dir   = getAngle(sub(point,start));
    if(dir<0)                   //No like
        dir += 2*Math.PI;
    return dir;
}

function getSegAngleEnd(curve) {
    var end = curve.getEnd(),
        point = curve.getPoint(curve.getPointByLengthBack(20)),//curve.getPoint(1-ANG_DIST),
        dir   = getAngle(sub(end,point)); //different from counterpart, maybe bad?
    if(dir<0)
        dir += 2*Math.PI;
    return dir;
}

/* ------------------------------        Math.js        ------------------------------*/

/*
 * A bunch of stuff
 */

 function vectorSum(v1, c, v2) {
    var result = [];
    for (var i = 0; i < v1.length; i++)
        result[i] = v1[i] + c * v2[i];
    return result;
}

/**
 * Prints a matrix in row,column format
 */
function matrixPrint(matrix) {
    for (var i = 0; i < matrix.length; i++) {
        console.log(matrix[i]);
    }
}

function zeroes(r, c) {
    var m = [];
    for (var i = 0; i < r; i++) {
        m[i] = [];
        for (var j = 0; j < c; j++)
            m[i][j] = 0;
    }
    return m;
}

//Basic matrix operations
function transpose(m) {
    var result = zeroes(m[0].length, m.length);
    for (var r = 0; r < result.length; r++) {
        for(var c = 0; c < result[0].length; c++) {
            result[r][c] = m[c][r];
        }
    }
    return result;
}

function matrixMult(m1,m2) {
    if(m1[0].length != m2.length)
        throw "Matrix dimension mismatch. Cannot multiply";
    
    var result = zeroes(m1.length,m2[0].length);
    
    for(var r = 0; r<result.length; r++) {
        for(var c = 0; c<result[0].length; c++) {
            result[r][c]=mMultHelper(m1,m2,r,c);
        }
    }
    return result;
}

function mMultHelper(m1,m2,r,c) { //does dot producting BS
    var result = 0;
    for(var i = 0; i<m1.length; i++)
        result += m1[r][i]*m2[i][c];
    return result;
}

//probably will never be used
function rowProduct(m,r) {
    var result = 1;
    for(var i = 0; i<m[0].length; i++)
        result *= m[r][i];
    return result;
}

function colProduct(m,c) {
    var result = 1;
    for(var i = 0; i<m.length; i++)
        result *= m[i][c];
    return result;
}

/** indexed row,column 
 *  DOES NOT DO ANY LEGITIMACY CHECKS OR ANYTHING
 * @param {Object} matrix
 */
function gaussianElimination1(matrix) {
    matrix = matrix.slice(0); //shallow copy (it's cool cause it's ints)
    
    for(var i = 0; i<matrix.length; i++) {//each row get the first coeffecient
        var temp = gElHelper1(matrix[i]),
            p = temp[0],
            a = temp[1];
            
        for(var j = 0; j<matrix.length; j++) { //remove from other rows
            var b = matrix[j][p];
            
            if(b != 0 && i != j)
                matrix[j] = vectorSum(matrix[j],-b/a,matrix[i]);
        }
    }

    //This part assumes that you end up with something in almost row echelon form (coeffecients may not be 1)    
    var result = [],
        numVars = matrix[0].length-1;
    for(var i = 0; i<numVars; i++) { //grabbing the results
        result[i] = matrix[i][numVars]/matrix[i][i];
    }
    return result;
    
    
}
//Helper function returns the first position of a nonzero coeffecient and the coefficient itself
function gElHelper1(vector) {
    for(var i = 0; i<vector.length; i++)
        if(vector[i] != 0)
            return [i,vector[i]];
    return -1
}

function gaussianElimination(matrix) {
    matrix = matrix.slice(0);
    var numRows = matrix.length,
        numCols = matrix[0].length,
        sol = [];
        
    //matrixPrint(matrix);
    
    for(var c = 0; c<numRows; c++) {
        var iMax = gElHelper(matrix,c);
        
        if(matrix[iMax][c] == 0)
            throw "Matrix is singular"
        swapRows(matrix,c,iMax);
        
        for(var d = c+1; d<numRows; d++) {
            var mult = matrix[d][c]/matrix[c][c];
            
            matrix[d] = vectorSum(matrix[d],-mult,matrix[c]);
        }
    }
    
    for(var r = 0; r<numRows; r++) {
        var i = numRows-r-1;
        
        for(var s = r+1; s<numRows; s++) {
            var mult = -matrix[s][i]/matrix[r][i]
            matrix[s] = vectorSum(matrix[s],mult,matrix[r]);
        }
        sol.push(matrix[r][numCols-1]/matrix[r][i]);
    }
    
    return sol.reverse();
}
//Helper function finds the pos of the max in the column
function gElHelper(matrix,c) {
    var iMax = 0;
    for(var i = c; i<matrix.length; i++) {
        if(Math.abs(matrix[i][c])>Math.abs(matrix[iMax][c]))
            iMax = i;
    }
    return iMax
}

function swapRows(matrix,r0,r1) {
    var i = matrix[r0];
    matrix[r0]=matrix[r1];
    matrix[r1]=i;
    return matrix;
}

/* ------------------------------        Vector.js        ------------------------------*/

// Math
function truncate(vector, max) {
    var mag = getMag(vector);
    if(mag > max)
        return scale(vector,max/mag);
    return vector;
}

function perp(vector) {
    return [vector[1],-vector[0]];
}

function perpNorm(vector) {
    return normalize(perp(vector));
}

function normalize(vector) {
    //if(vector[0]==0 && vector[1]==0)
    //    return [0,1];
    var mag = getMag(vector);
    return scale(vector,1/mag);
}

function normalizeTo(vector,mag) {
    return scale(normalize(vector),mag);
}

function projectedLength(vector,along) {
    return dot(vector,along)/getMag(along);
}

function project(vector,along) {
    
}

function scale(vector,factor) {
    return [vector[0]*factor,vector[1]*factor];
}

function add(vector1, vector2) {
    return [vector1[0]+vector2[0],vector1[1]+vector2[1]];
}

function sub(vector1, vector2) {
    return [vector1[0]-vector2[0],vector1[1]-vector2[1]];
}

function getMag(vector) {
    return getDist([0,0],vector);
}
    
function getDist(vector1,vector2) {
    return Math.sqrt(Math.pow((vector2[0]-vector1[0]),2)+Math.pow((vector2[1]-vector1[1]),2));
}

function getAngle(vector) {
    var quad = 0;
    if(vector[0]===0) // because 0 and -0 are not always the same
        vector[0] = +0;
    if(vector[0]<0)
        quad = Math.PI;
    else if(vector[0]>0 && vector[1]<0)
        quad = 2*Math.PI;
    return reduceAngle(Math.atan(vector[1]/vector[0])+quad);
}

function getAngleBetween(vector1,vector2) {
    return Math.abs(getAngle(vector1)-getAngle(vector2));
}

function getSmallerAngle(angle) {
    if(angle > Math.PI)
        return 2*Math.PI-angle;
    if(angle < -Math.PI)
        return -2*Math.PI-angle
    return angle;
}

function getSmallerAngleDeg(angle) {
    if(angle > 180)
        return 360-angle;
    if(angle < -180)
        return -360-angle;
    return angle;
}

function radToDeg(angle) {
    return angle*180/Math.PI;
}

function degToRad(angle) {
    return angle*Math.PI/180;
}

function reduceAngle(angle) {
    return angle-Math.floor(angle/(2*Math.PI))*2*Math.PI;
}

function reduceAngleDeg(angle) {
    return angle-Math.floor(angle/360)*360;
}

function dot(vector1,vector2) {
    return vector1[0]*vector2[0]+vector1[1]*vector2[1];
}

function point(vector,dir) {
    var mag = getMag(vector);
    return [Math.cos(dir)*mag,Math.sin(dir)*mag];
}

function rotate(v,rad) {
    var ang = getAngle(v);
    if(v[0] == 0 && v[1] == -8) {
        console.log(v);
        console.log("!");
        console.log(ang);
        console.log(rad);
        console.log(point(v,rad+ang));
    }
    return point(v,rad+ang);
}

function midpoint(p1,p2,t) {
    return add(scale(p1,1-t),scale(p2,t));
}


function drawVector(vector,pos,ctx) {
    ctx.beginPath();
    ctx.moveTo(pos[0],pos[1]);
    ctx.lineTo(pos[0]+vector[0],pos[1]+vector[1]);
    ctx.stroke();
}


</script>
"""


def custom(*args, **kwargs):
    global ts_state_on
    default = ts_default_review_html(*args, **kwargs)
    if not ts_state_on:
        return default
    output = (
        default +
        ts_blackboard + 
        "<script>color = '" + ts_color + "'</script>" +
        "<script>line_width = '" + str(ts_line_width) + "'</script>"
    )
    return output


mw.reviewer.revHtml = custom


def ts_on():
    """
    Turn on
    """
    if not ts_profile_loaded:
        showWarning(TS_ERROR_NO_PROFILE)
        return False

    global ts_state_on
    ts_state_on = True
    ts_menu_switch.setChecked(True)
    return True


def ts_off():
    """
    Turn off
    """
    if not ts_profile_loaded:
        showWarning(TS_ERROR_NO_PROFILE)
        return False

    global ts_state_on
    ts_state_on = False
    ts_menu_switch.setChecked(False)
    return True


@slot()
def ts_switch():
    """
    Switch TouchScreen.
    """

    if ts_state_on:
        ts_off()
    else:
        ts_on()

    # Reload current screen.

    if mw.state == "review":
        mw.moveToState('overview')
        mw.moveToState('review')
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()
    if mw.state == "overview":
        mw.overview.refresh()


def ts_refresh():
    """
    Refresh display by reenabling night or normal mode.
    """
    if ts_state_on:
        ts_on()
    else:
        ts_off()


def ts_setup_menu():
    """
    Initialize menu. If there is an entity "View" in top level menu
    (shared with other plugins, like "Zoom" of R. Sieker) options of
    the addon will be placed there. In other case it creates that menu.
    """
    global ts_menu_switch

    try:
        mw.addon_view_menu
    except AttributeError:
        mw.addon_view_menu = QMenu(_(u"&View"), mw)
        mw.form.menubar.insertMenu(mw.form.menuTools.menuAction(),
                                    mw.addon_view_menu)

    mw.ts_menu = QMenu(_('&Touchscreen'), mw)

    mw.addon_view_menu.addMenu(mw.ts_menu)

    ts_menu_switch = QAction(_('&Enable touchscreen mode'), mw, checkable=True)
    ts_menu_color = QAction(_('Set &pen color'), mw)
    ts_menu_width = QAction(_('Set pen &width'), mw)
    ts_menu_opacity = QAction(_('Set pen &opacity'), mw)
    ts_menu_about = QAction(_('&About...'), mw)

    ts_toggle_seq = QKeySequence("Ctrl+r")
    ts_menu_switch.setShortcut(ts_toggle_seq)

    mw.ts_menu.addAction(ts_menu_switch)
    mw.ts_menu.addAction(ts_menu_color)
    mw.ts_menu.addAction(ts_menu_width)
    mw.ts_menu.addAction(ts_menu_opacity)
    mw.ts_menu.addSeparator()
    mw.ts_menu.addAction(ts_menu_about)

    ts_menu_switch.triggered.connect(ts_switch)
    ts_menu_color.triggered.connect(ts_change_color)
    ts_menu_width.triggered.connect(ts_change_width)
    ts_menu_opacity.triggered.connect(ts_change_opacity)
    ts_menu_about.triggered.connect(ts_about)


TS_ERROR_NO_PROFILE = "No profile loaded"

#
# ONLOAD SECTION
#

ts_onload()
