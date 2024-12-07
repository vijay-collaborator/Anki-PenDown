# -*- coding: utf-8 -*-
# Copyright: Michal Krassowski <krassowski.michal@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""
Initially based on the Anki-TouchScreen addon, updated ui and added pressure pen/stylus capabilities, perfect freehand(line smoothing) and calligrapher functionality.


It adds an AnkiDraw menu entity with options like:

    switching AnkiDraw
    modifying some of the colors
    thickness
    toolbar settings


If you want to contribute visit GitHub page: https://github.com/Rytisgit/Anki-StylusDraw
Also, feel free to send me bug reports or feature requests.

Copyright: Michal Krassowski <krassowski.michal@gmail.com>
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html,
Important parts of Javascript code inspired by http://creativejs.com/tutorials/painting-with-pixels/index.html
"""

__addon_name__ = "AnkiDraw"
__version__ = "1.3"

from pathlib import Path

from aqt import mw
from aqt.utils import showWarning

from anki.lang import _
from anki.hooks import addHook

from aqt.qt import QAction, QMenu, QColorDialog, QMessageBox, QInputDialog, QLabel,\
   QPushButton, QDialog, QVBoxLayout, QComboBox, QHBoxLayout, QSpinBox, QCheckBox
from aqt.qt import QKeySequence,QColor
from aqt.qt import pyqtSlot as slot

# Load extra JS libraries from external files to simplify the __init__.py
file = Path(__file__)
with open(file.with_name("Caligrapher.js"), encoding="utf8") as f:
    caligrapher_js = f.read()
with open(file.with_name("PerfectFreehand.js"), encoding="utf8") as f:
    perfect_freehand_js = f.read()
# This declarations are there only to be sure that in case of troubles
# with "profileLoaded" hook everything will work.

ts_state_on = False
ts_profile_loaded = False
ts_auto_hide = True
ts_auto_hide_pointer = True
ts_default_small_canvas = False
ts_zen_mode = False
ts_follow = False
ts_ConvertDotStrokes = True

ts_color = "#272828"
ts_line_width = 4
ts_opacity = 0.7
ts_location = 1
ts_x_offset = 2
ts_y_offset = 2
ts_small_width = 500
ts_small_height = 500
ts_background_color = "#FFFFFF00"
ts_orient_vertical = True
ts_default_review_html = mw.reviewer.revHtml

ts_default_VISIBILITY = "true"
ts_default_PerfFreehand = "false"
ts_default_Calligraphy = "false"

def ts_save():
    """
    Saves configurable variables into profile, so they can
    be used to restore previous state after Anki restart.
    """
    mw.pm.profile['ts_state_on'] = ts_state_on
    mw.pm.profile['ts_color'] = ts_color
    mw.pm.profile['ts_line_width'] = ts_line_width
    mw.pm.profile['ts_opacity'] = ts_opacity
    mw.pm.profile['ts_default_ConvertDotStrokes'] = ts_ConvertDotStrokes
    mw.pm.profile['ts_auto_hide'] = ts_auto_hide
    mw.pm.profile['ts_auto_hide_pointer'] = ts_auto_hide_pointer
    mw.pm.profile['ts_default_small_canvas'] = ts_default_small_canvas
    mw.pm.profile['ts_zen_mode'] = ts_zen_mode
    mw.pm.profile['ts_follow'] = ts_follow
    mw.pm.profile['ts_location'] = ts_location
    mw.pm.profile['ts_x_offset'] = ts_x_offset
    mw.pm.profile['ts_y_offset'] = ts_y_offset
    mw.pm.profile['ts_small_height'] = ts_small_height
    mw.pm.profile['ts_background_color'] = ts_background_color
    mw.pm.profile['ts_small_width'] = ts_small_width
    mw.pm.profile['ts_orient_vertical'] = ts_orient_vertical

def ts_load():
    """
    Load configuration from profile, set states of checkable menu objects
    and turn on night mode if it were enabled on previous session.
    """
    global ts_state_on, ts_color, ts_profile_loaded, ts_line_width, ts_opacity, ts_ConvertDotStrokes, ts_auto_hide, ts_auto_hide_pointer, ts_default_small_canvas, ts_zen_mode, ts_follow, ts_orient_vertical, ts_y_offset, ts_x_offset, ts_location, ts_small_width, ts_small_height, ts_background_color
    try:
        ts_state_on = mw.pm.profile['ts_state_on']
        ts_color = mw.pm.profile['ts_color']
        ts_line_width = mw.pm.profile['ts_line_width']
        ts_opacity = mw.pm.profile['ts_opacity']
        ts_auto_hide = mw.pm.profile['ts_auto_hide']
        ts_auto_hide_pointer = mw.pm.profile['ts_auto_hide_pointer']
        ts_default_small_canvas = mw.pm.profile['ts_default_small_canvas']
        ts_zen_mode = mw.pm.profile['ts_zen_mode']
        ts_follow = mw.pm.profile['ts_follow']
        ts_ConvertDotStrokes = bool(mw.pm.profile['ts_default_ConvertDotStrokes'])#fix for previously being a string value, defaults string value to true bool, will be saved as true or false bool after
        ts_orient_vertical = mw.pm.profile['ts_orient_vertical']
        ts_y_offset = mw.pm.profile['ts_y_offset']
        ts_small_width = mw.pm.profile['ts_small_width']
        ts_small_height = mw.pm.profile['ts_small_height']
        ts_background_color = mw.pm.profile['ts_background_color']
        ts_x_offset = mw.pm.profile['ts_x_offset']
        ts_location = mw.pm.profile['ts_location']
    except KeyError:
        ts_state_on = False
        ts_color = "#272828"
        ts_line_width = 4
        ts_opacity = 0.8
        ts_auto_hide = True
        ts_auto_hide_pointer = True
        ts_default_small_canvas = False
        ts_zen_mode = False
        ts_follow = False
        ts_ConvertDotStrokes = True
        ts_orient_vertical = True
        ts_y_offset = 2
        ts_small_width = 500
        ts_small_height = 500
        ts_background_color = "#FFFFFF00"
        ts_x_offset = 2
        ts_location = 1

    ts_profile_loaded = True
    ts_menu_auto_hide.setChecked(ts_auto_hide)
    ts_menu_auto_hide_pointer.setChecked(ts_auto_hide_pointer)
    ts_menu_small_default.setChecked(ts_default_small_canvas)
    ts_menu_zen_mode.setChecked(ts_zen_mode)
    ts_menu_follow.setChecked(ts_follow)
    ts_menu_dots.setChecked(ts_ConvertDotStrokes)
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
    execute_js("if (typeof resize === 'function') { setTimeout(resize, 101); }");
    
def clear_blackboard():
    assure_plugged_in()

    if ts_state_on:
        execute_js("if (typeof clear_canvas === 'function') { clear_canvas(); }")
        # is qFade the reason for having to wait?
        execute_js("if (typeof resize === 'function') { setTimeout(resize, 101); }");

def blackboard_html():
    return u"""
<div id="canvas_wrapper">
    <canvas id="secondary_canvas" width="100" height="100" ></canvas>
    <canvas id="main_canvas" width="100" height="100"></canvas>

    <div id="pencil_button_bar">
        <!-- SVG icons from https://github.com/tabler/tabler-icons/ -->
        <button id="ts_visibility_button" class="active" title="Toggle visiblity (, comma)"
              onclick="switch_visibility();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M4 20h4l10.5 -10.5a1.5 1.5 0 0 0 -4 -4l-10.5 10.5v4"></path><path d="M13.5 6.5l4 4"></path></svg>
        </button>

        <button id="ts_perfect_freehand_button" title="Perfect Freehand (Alt + x)"
              onclick="switch_perfect_freehand()" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M8 20l10.5 -10.5a2.828 2.828 0 1 0 -4 -4l-10.5 10.5v4h4z"></path><path d="M13.5 6.5l4 4"></path><path d="M16 18h4m-2 -2v4"></path></svg>
        </button>

        <button id="ts_kanji_button" title="Toggle calligrapher (Alt + c)"
              onclick="switch_drawing_mode();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M3 21v-4a4 4 0 1 1 4 4h-4"></path><path d="M21 3a16 16 0 0 0 -12.8 10.2"></path><path d="M21 3a16 16 0 0 1 -10.2 12.8"></path><path d="M10.6 9a9 9 0 0 1 4.4 4.4"></path></svg>
        </button>

        <button id="ts_undo_button" title="Undo the last stroke (Alt + z)"
              onclick="ts_undo();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M4.05 11a8 8 0 1 1 .5 4m-.5 5v-5h5"></path></svg>
        </button>

        <button class="active" title="Clean canvas (. dot)"
              onclick="clear_canvas();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M4 7h16"></path><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12"></path><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3"></path><path d="M10 12l4 4m0 -4l-4 4"></path></svg>

        <button id="ts_switch_fullscreen_button" class="active" title="Toggle fullscreen canvas(Alt + b)"
              onclick="switch_small_canvas();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M9.00002 3.99998H4.00004L4 9M20 8.99999V4L15 3.99997M15 20H20L20 15M4 15L4 20L9.00002 20"></path></svg>
        </button>
    </div>
</div>
"""

def get_css_for_toolbar_location(location, x_offset, y_offset, orient_column, canvas_width, canvas_height, background_color):
    orient = "column" if orient_column else "row"
    switch = {
        0: f"""
                        --button-bar-pt: {y_offset}px;
                        --button-bar-pr: unset;
                        --button-bar-pb: unset;
                        --button-bar-pl: {x_offset}px;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
        1: f"""
                        --button-bar-pt: {y_offset}px;
                        --button-bar-pr: {x_offset}px;
                        --button-bar-pb: unset;
                        --button-bar-pl: unset;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
        2: f"""
                        --button-bar-pt: unset;
                        --button-bar-pr: unset;
                        --button-bar-pb: {y_offset}px;
                        --button-bar-pl: {x_offset}px;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
        3: f"""
                        --button-bar-pt: unset;
                        --button-bar-pr: {x_offset}px;
                        --button-bar-pb: {y_offset}px;
                        --button-bar-pl: unset;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
    }
    return switch.get(location, """
                        --button-bar-pt: 2px;
                        --button-bar-pr: 2px;
                        --button-bar-pb: unset;
                        --button-bar-pl: unset;
                        --button-bar-orientation: column;
                        --small-canvas-height: 500;
                        --small-canvas-width: 500;
                        --background-color: #FFFFFF00;
                    """)

def get_css_for_auto_hide(auto_hide, zen):
    return "none" if auto_hide or zen else "flex"

def get_css_for_zen_mode(hide):
    return "none" if hide else "flex"

def get_css_for_auto_hide_pointer(auto_hide):
    return "none" if auto_hide else "default"

def blackboard_css():
    return u"""
<style>
:root {
  """ + get_css_for_toolbar_location( ts_location, ts_x_offset, ts_y_offset, ts_orient_vertical, ts_small_width, ts_small_height, ts_background_color) + """
}
body {
  overflow-x: hidden; /* Hide horizontal scrollbar */
}
/*
    canvas needs touch-action: none so that it doesn't fire bogus
    pointercancel events. See:
    https://stackoverflow.com/questions/59010779/pointer-event-issue-pointercancel-with-pressure-input-pen
*/
#canvas_wrapper, #main_canvas, #secondary_canvas {
   z-index: 999;/* add toggle?*/
  touch-action: none;/*add toggle*/
  
  position:var(--canvas-bar-position);
  top: var(--canvas-bar-pt);
  right: var(--canvas-bar-pr);
  bottom: var(--canvas-bar-pb);
  left: var(--canvas-bar-pl);
  }
#main_canvas, #secondary_canvas {
  background: var(--background-color);
  opacity: """ + str(ts_opacity) + """;
  border-style: none;
  border-width: 1px;
}
#pencil_button_bar {
  position: fixed;
  display: """+get_css_for_zen_mode(ts_zen_mode)+""";
  flex-direction: var(--button-bar-orientation);
  opacity: .5;
  top: var(--button-bar-pt);
  right: var(--button-bar-pr);
  bottom: var(--button-bar-pb);
  left: var(--button-bar-pl);
  z-index: 8000;
  transition: .5s;
} #pencil_button_bar:hover { 
  opacity: 1;
} #pencil_button_bar > button {
  margin: 2px;
} #pencil_button_bar > button > svg {
  width: 2em;
} #pencil_button_bar > button:hover > svg {
  filter: drop-shadow(0 0 4px #000);
} #pencil_button_bar > button.active > svg > path {
  stroke: #000;
} .night_mode #pencil_button_bar > button.active > svg > path {
  stroke: #eee;
} #pencil_button_bar > button > svg > path {
  stroke: #888;
} .night_mode #pencil_button_bar > button > svg > path {
  /*stroke: #888;*/
}
.nopointer {
  cursor: """+get_css_for_auto_hide_pointer(ts_auto_hide_pointer)+""" !important;
} 
.touch_disable > button:not(:first-child){
    display: none;
}
.nopointer #pencil_button_bar
{
  display: """+get_css_for_auto_hide(ts_auto_hide, ts_zen_mode)+""";
}
</style>"""

def blackboard_js():
    return u"""
// Generated HTML set from python qt ui
var visible = """ + ts_default_VISIBILITY + """;
var perfectFreehand = """ + ts_default_PerfFreehand +""";
var convertDotStrokes = """ + str(ts_ConvertDotStrokes).lower() + """;
var small_canvas = """ +  str(ts_default_small_canvas).lower() + """;
var fullscreen_follow = """ + str(ts_follow).lower() + """;
var calligraphy = """ + ts_default_Calligraphy + """;
var color = """ + "\'" + str(ts_color) + "\'" + """;
var line_width = """ + str(ts_line_width) + """;

// HTML references
var canvas = document.getElementById('main_canvas');
var wrapper = document.getElementById('canvas_wrapper');
var optionBar = document.getElementById('pencil_button_bar');
var ts_undo_button = document.getElementById('ts_undo_button');
var ctx = canvas.getContext('2d');
var secondary_canvas = document.getElementById('secondary_canvas');
var secondary_ctx = secondary_canvas.getContext('2d');
var ts_visibility_button = document.getElementById('ts_visibility_button');
var ts_kanji_button = document.getElementById('ts_kanji_button');
var ts_perfect_freehand_button = document.getElementById('ts_perfect_freehand_button');
var ts_switch_fullscreen_button = document.getElementById('ts_switch_fullscreen_button');

// Arrays to save point values from strokes
var arrays_of_points = [ ];
var line_type_history = [ ];
var perfect_cache = [ ];


canvas.onselectstart = function() { return false; };
secondary_canvas.onselectstart = function() { return false; };
wrapper.onselectstart = function() { return false; };

function switch_perfect_freehand()
{
    stop_drawing();
    perfectFreehand = !perfectFreehand;
    if(perfectFreehand)
    {
        ts_perfect_freehand_button.className = 'active';
        ts_kanji_button.className = '';
        calligraphy = false;
    }
    else{
        ts_perfect_freehand_button.className = '';
    }
    ts_redraw()
}

function switch_small_canvas()
{
    stop_drawing();
    
    small_canvas = !small_canvas;
    if(!small_canvas)
    {
        ts_switch_fullscreen_button.className = 'active';
    }
    else{
        ts_switch_fullscreen_button.className = '';
    }
    resize();
}

function switch_visibility()
{
	stop_drawing();
    if (visible)
    {
        canvas.style.display='none';
        secondary_canvas.style.display=canvas.style.display;
        ts_visibility_button.className = '';
        optionBar.className = 'touch_disable';
    }
    else
    {
        canvas.style.display='block';
        secondary_canvas.style.display=canvas.style.display;
        ts_visibility_button.className = 'active';
        optionBar.className = '';
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
    if(calligraphy)
    {
        ts_kanji_button.className = 'active';
        ts_perfect_freehand_button.className = '';
        perfectFreehand = false;
    }
    else{
        ts_kanji_button.className = '';
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
    canvas.style["border-style"] = "none";
    document.documentElement.style.setProperty('--canvas-bar-pt', '0px');
    document.documentElement.style.setProperty('--canvas-bar-pr', '0px');
    document.documentElement.style.setProperty('--canvas-bar-pb', 'unset');
    document.documentElement.style.setProperty('--canvas-bar-pl', 'unset');
    document.documentElement.style.setProperty('--canvas-bar-position', 'absolute');
    
    if(!small_canvas && !fullscreen_follow){
        ctx.canvas.width = Math.max(card.scrollWidth, document.documentElement.clientWidth);
        ctx.canvas.height = Math.max(document.documentElement.scrollHeight, document.documentElement.clientHeight);        
    }
    else if(small_canvas){
        ctx.canvas.width = Math.min(document.documentElement.clientWidth, 
        getComputedStyle(document.documentElement).getPropertyValue('--small-canvas-width'));
        ctx.canvas.height = Math.min(document.documentElement.clientHeight, 
        getComputedStyle(document.documentElement).getPropertyValue('--small-canvas-height'));
        canvas.style["border-style"] = "dashed";
        document.documentElement.style.setProperty('--canvas-bar-pt', 
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pt'));
        document.documentElement.style.setProperty('--canvas-bar-pr', 
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pr'));
        document.documentElement.style.setProperty('--canvas-bar-pb', 
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pb'));
        document.documentElement.style.setProperty('--canvas-bar-pl', 
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pl'));
        document.documentElement.style.setProperty('--canvas-bar-position', 'fixed');
    }
    else{
        document.documentElement.style.setProperty('--canvas-bar-position', 'fixed');
        ctx.canvas.width = document.documentElement.clientWidth-1;
        ctx.canvas.height = document.documentElement.clientHeight-1;
    }
    secondary_ctx.canvas.width = ctx.canvas.width;
    secondary_ctx.canvas.height = ctx.canvas.height;
    canvas_wrapper.style.display='block';
    
    
    
    /* Get DPR with 1 as fallback */
    var dpr = window.devicePixelRatio || 1;
    
    /* CSS size is the same */
    canvas.style.height = ctx.canvas.height + 'px';
    wrapper.style.width = ctx.canvas.width + 'px';
    secondary_canvas.style.height = canvas.style.height;
    secondary_canvas.style.width = canvas.style.width;
    
    /* Increase DOM size and scale */
    ctx.canvas.width *= dpr;
    ctx.canvas.height *= dpr;
    ctx.scale(dpr, dpr);
    secondary_ctx.canvas.width *= dpr;
    secondary_ctx.canvas.height *= dpr;
    secondary_ctx.scale(dpr, dpr);
    
	update_pen_settings()
    
}


window.addEventListener('resize', resize);
window.addEventListener('load', resize);
window.requestAnimationFrame(draw_last_line_segment);

var isPointerDown = false;
var mouseX = 0;
var mouseY = 0;

function update_pen_settings(){
    ctx.lineJoin = ctx.lineCap = 'round';
    ctx.lineWidth = line_width;
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    secondary_ctx.lineJoin = ctx.lineJoin;
    secondary_ctx.lineWidth = ctx.lineWidth;
    secondary_ctx.strokeStyle = ctx.strokeStyle;
    secondary_ctx.fillStyle = ctx.fillStyle;
    ts_redraw()
}

function ts_undo(){
	stop_drawing();
    switch (line_type_history.pop()) {
        case 'C'://Calligraphy
            strokes.pop();    
            break;
        case 'L'://Simple Lines
            var index = arrays_of_points.length-1
            arrays_of_points.pop()
            perfect_cache[index] = null;
            break;
        default://how did you get here??
            //console.log("Unrecognized line type for undo") 
            break;
    }
    
    if(!line_type_history.length)
    {
        clear_canvas()
        ts_undo_button.className = ""
    }
    else
    {
        ts_redraw()
    }
    
}

function ts_redraw() {
	pleaseRedrawEverything = true;
}

function ts_clear() {
	pleaseRedrawEverything = true;
    fullClear = true;
}

function clear_canvas()
{
	//don't continue to put points into an empty array(pointermove) if clearing while drawing on the canvas
	stop_drawing();
    arrays_of_points = [];
    strokes = [];
    perfect_cache = [];
    line_type_history = [];
	ts_clear();
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
    draw_upto_latest_point_async(nextLine, nextPoint, nextStroke);
}

var nextLine = 0;
var nextPoint = 0;
var nextStroke = 0;
var p1,p2,p3;

function is_last_path_and_currently_drawn(i){
    return (isPointerDown && arrays_of_points.length-1 == i)//the path is complete unless its the last of the array and the pointer is still down
}

function all_drawing_finished(i){
    return (!isPointerDown && arrays_of_points.length-1 == i)//the path is complete unless its the last of the array and the pointer is still down
}

async function draw_path_at_some_point_async(startX, startY, midX, midY, endX, endY, lineWidth) {
		ctx.beginPath();
		ctx.moveTo((startX + (midX - startX) / 2), (startY + (midY - startY)/ 2));//midpoint calculation for x and y
		ctx.quadraticCurveTo(midX, midY, (midX + (endX - midX) / 2), (midY + (endY - midY)/ 2));
		ctx.lineWidth = lineWidth;
		ctx.stroke();
};

var pleaseRedrawEverything = false;
var fullClear = false;
async function draw_upto_latest_point_async(startLine, startPoint, startStroke){
	//Don't keep redrawing the same last point over and over
	//if(!pleaseRedrawEverything && 
    //(startLine == arrays_of_points.length && startPoint == arrays_of_points[startLine-1].length) && 
    //(startStroke == strokes.length)) return;

	var fullRedraw = false;//keep track if this call started a full redraw to unset pleaseRedrawEverything flag later.
	if (pleaseRedrawEverything) {// erase everything and draw from start
	fullRedraw = true;
	startLine = 0;
	startPoint = 0;
    startStroke = 0;
	ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
	}

	for(var i = startLine; i < arrays_of_points.length; i++){ //Draw Lines
        var needPerfectDraw = false;
		nextLine = i;
		///0,0,0; 0,0,1; 0,1,2 or x+1,x+2,x+3
		//take the 2 previous points in addition to current one at the start of the loop.
		p2 = arrays_of_points[i][startPoint > 1 ? startPoint-2 : 0];
		p3 = arrays_of_points[i][startPoint > 0 ? startPoint-1 : 0];
        for(var j = startPoint; j < arrays_of_points[i].length; j++){
			nextPoint = j + 1;//track which point was last drawn so we can pick up where we left off on the next refresh.
			p1 = p2;
			p2 = p3;
			p3 = arrays_of_points[i][j];
            if(!perfectFreehand){
                draw_path_at_some_point_async(p1[0],p1[1],p2[0],p2[1],p3[0],p3[1],p3[3]);
            }
            else {needPerfectDraw = true;}
        }
        if(needPerfectDraw) { 
                var path = !perfect_cache[i] || is_last_path_and_currently_drawn(i)  
                    ? new Path2D(
                            getFreeDrawSvgPath(
                                arrays_of_points[i],
                                !is_last_path_and_currently_drawn(i)))
                    : perfect_cache[i]
                perfect_cache[i] = path
                ctx.fill(path);
        }     
        if(all_drawing_finished(i)){
                nextLine++;
                nextPoint = 0;
            }
        startPoint = 0;
    }
    //Draw Calligraphy Strokes one by one starting from the given point
    for(var i = startStroke; i < strokes.length; i++){
        nextStroke = i+1;
        strokes[i].draw(WEIGHT, ctx);
    }

	if (fullRedraw) {//finished full redraw, now can unset redraw all flag so no more full redraws until necessary
    pleaseRedrawEverything = false;
	fullRedraw = false;
    nextPoint = strokes.length == 0 ? 0 : nextPoint;//reset next point if out of lines
    nextStroke = strokes.length == 0 ? 0 : nextStroke;//reset for undo as well
        if(fullClear){// start again from 0.
            nextLine = 0;
            nextStroke = 0;
            fullClear = false;
        }
	}
}

var drawingWithPressurePenOnly = false; // hack for drawing with 2 main pointers when using a presure sensitive pen

function pointerDownLine(e) {
    wrapper.classList.add('nopointer');
	if (!e.isPrimary || calligraphy) { return; }
	if (e.pointerType[0] == 'p') { drawingWithPressurePenOnly = true }
	else if ( drawingWithPressurePenOnly) { return; }
    if(!isPointerDown){
        event.preventDefault();
        arrays_of_points.push([[
			e.offsetX,
			e.offsetY,
            e.pointerType[0] == 'p' ? e.pressure : 2,
			e.pointerType[0] == 'p' ? (1.0 + e.pressure * line_width * 2) : line_width]]);
        line_type_history.push('L');//Add new Simple line marker to shared history
        start_drawing();
    }
}

function pointerMoveLine(e) {
	if (!e.isPrimary || calligraphy) { return; }
	if (e.pointerType[0] != 'p' && drawingWithPressurePenOnly) { return; }
    if (isPointerDown) {
        arrays_of_points[arrays_of_points.length-1].push([
			e.offsetX,
			e.offsetY,
            e.pointerType[0] == 'p' ? e.pressure : 2,
			e.pointerType[0] == 'p' ? (1.0 + e.pressure * line_width * 2) : line_width]);
    }
}

function pointerUpLine(e) {
    wrapper.classList.remove('nopointer');
    /* Needed for the last bit of the drawing. */
	if (!e.isPrimary || calligraphy) { return; }
	if (e.pointerType[0] != 'p' && drawingWithPressurePenOnly) { return; }
    if (isPointerDown) {
        arrays_of_points[arrays_of_points.length-1].push([
			e.offsetX,
			e.offsetY,
            e.pointerType[0] == 'p' ? e.pressure : 2,
			e.pointerType[0] == 'p' ? (1.0 + e.pressure * line_width * 2) : line_width]);
    } 
	stop_drawing();
    if(perfectFreehand) ts_redraw();
}

document.addEventListener('keyup', function(e) {
    // alt + Z or z
    if ((e.keyCode == 90 || e.keyCode == 122) && e.altKey) {
		e.preventDefault();
        ts_undo();
    }
    // /
    if (e.key === ".") {
        clear_canvas();
    }
	// ,
    if (e.key === ",") {
        switch_visibility();
    }
    // alt + C or c
    if ((e.key === "c" || e.key === "C") && e.altKey) {
        e.preventDefault();
        switch_drawing_mode();
    }
        // alt + X or x
    if ((e.key === "x" || e.key === "X") && e.altKey) {
        e.preventDefault();
        switch_perfect_freehand();
    }
    if ((e.key === "b" || e.key === "B") && e.altKey) {
        e.preventDefault();
        switch_small_canvas();
    }
})
// ----------------------------------------- Perfect Freehand -----------------------------------------

// The rest of the code gets loaded in from PerfectFreehand.js

function med(A, B) {
  return [(A[0] + B[0]) / 2, (A[1] + B[1]) / 2];
}

// Trim SVG path data so number are each two decimal points. This
// improves SVG exports, and prevents rendering errors on points
// with long decimals.
const TO_FIXED_PRECISION = /(\s?[A-Z]?,?-?[0-9]*\.[0-9]{0,2})(([0-9]|e|-)*)/g;

function getSvgPathFromStroke(points){
  if (!points.length) {
    return "";
  }

  const max = points.length - 1;

  return points
    .reduce(
      (acc, point, i, arr) => {
        if (i === max) {
          acc.push(point, med(point, arr[0]), "L", arr[0], "Z");
        } else {
          acc.push(point, med(point, arr[i + 1]));
        }
        return acc;
      },
      ["M", points[0], "Q"],
    )
    .join(" ")
    .replace(TO_FIXED_PRECISION, "$1");
}

function getFreeDrawSvgPath(inputPoints, complete) {
  // Consider changing the options for simulated pressure vs real pressure
  const options = {
    simulatePressure: inputPoints[0][2] > 1,
    size: line_width,
    thinning: 0.6,
    smoothing: 0.5,
    streamline: 0.5,
    easing: (t) => Math.sin((t * Math.PI) / 2), // https://easings.net/#easeOutSine
    last: complete, // LastCommittedPoint is added on pointerup
  };

  return getSvgPathFromStroke(getStroke(inputPoints, options));
}
/*
 -------------------------------- Caligrapher ------------------------------------------
 Created By: August Toman-Yih
 Git Repository: https://github.com/atomanyih/Calligrapher
*/
/* ------------------------------        script.js        -----------------------------*/

// The rest of the code gets loaded in from Caligrapher.js

//Modified to work with current canvas and board
//share the same canvas with pressure drawing
 /*var canvas = document.getElementById('canvas'),
    width = canvas.width,
    height = canvas.height,
    context = canvas.getContext("2d");
	*/

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

function drawCurrentPath() {
    secondary_ctx.beginPath();
    secondary_ctx.moveTo(currentPath[0][0],currentPath[0][1]);
    for(var i = 1; i<currentPath.length; i++) {
        secondary_ctx.lineTo(currentPath[i][0],currentPath[i][1]);
    } 
    secondary_ctx.stroke();
}

function pointerDownCaligraphy(e) {
    wrapper.classList.add('nopointer');
    if (!e.isPrimary || !calligraphy) { return; }
    event.preventDefault();//don't paint anything when clicking on buttons, especially for undo to work
    line_type_history.push('C');//Add new Caligragraphy line marker to shared history
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
    wrapper.classList.remove('nopointer');
    stop_drawing();
    if (!e.isPrimary || !calligraphy || !currentPath.length) { return; }
    points = currentPath;
    
    var curves = fitStroke(points);
    
    strokes.push(new Stroke(curves));
    
    currentPath = [];// clear the array on pointer up so it doesnt enter new lines when clicking on buttons
    secondary_ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);//clear the guide line in second canvas
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
"""

def custom(*args, **kwargs):
    global ts_state_on
    default = ts_default_review_html(*args, **kwargs)
    if not ts_state_on:
        return default
    output = (
        default +
        blackboard_html() +
        blackboard_css() +
        "<script>" +
        blackboard_js() + 
        caligrapher_js +
        perfect_freehand_js+
        "</script>"
    )
    return output
mw.reviewer.revHtml = custom

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
        execute_js("color = '" + ts_color + "';")
        execute_js("if (typeof update_pen_settings === 'function') { update_pen_settings(); }")

@slot()
def ts_change_width():
    global ts_line_width
    value, accepted = QInputDialog.getDouble(mw, "AnkiDraw", "Enter the width:", ts_line_width)
    if accepted:
        ts_line_width = value
        execute_js("line_width = '" + str(ts_line_width) + "';")
        execute_js("if (typeof update_pen_settings === 'function') { update_pen_settings(); }")

@slot()
def ts_change_opacity():
    global ts_opacity
    value, accepted = QInputDialog.getDouble(mw, "AnkiDraw", "Enter the opacity (0 = transparent, 100 = opaque):", 100 * ts_opacity, 0, 100, 2)
    if accepted:
        ts_opacity = value / 100
        execute_js("canvas.style.opacity = " + str(ts_opacity))

class CustomDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AnkiDraw Toolbar And Canvas")

        self.combo_box = QComboBox()
        self.combo_box.addItem("Top-Left")
        self.combo_box.addItem("Top-Right")
        self.combo_box.addItem("Bottom-Left")
        self.combo_box.addItem("Bottom-Right")

        combo_label = QLabel("Location:")

        range_label = QLabel("Offset:")

        start_range_label = QLabel("X Offset:")
        self.start_spin_box = QSpinBox()
        self.start_spin_box.setRange(0, 1000)

        small_width_label = QLabel("Non-Fullscreen Canvas Width:")
        self.small_width_spin_box = QSpinBox()
        self.small_width_spin_box.setRange(0, 9999)

        small_height_label = QLabel("Non-Fullscreen Canvas Height:")
        self.small_height_spin_box = QSpinBox()
        self.small_height_spin_box.setRange(0, 9999)

        end_range_label = QLabel("Y Offset:")
        self.end_spin_box = QSpinBox()
        self.end_spin_box.setRange(0, 1000)

        range_layout = QVBoxLayout()

        small_height_layout = QHBoxLayout()
        small_height_layout.addWidget(small_height_label)
        small_height_layout.addWidget(self.small_height_spin_box)

        small_width_layout = QHBoxLayout()
        small_width_layout.addWidget(small_width_label)
        small_width_layout.addWidget(self.small_width_spin_box)

        color_layout = QHBoxLayout()
        self.color_button = QPushButton("Select Color")
        self.color_button.clicked.connect(self.select_color)

        self.color_label = QLabel("Background color: #FFFFFF00")  # Initial color label

        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_button)

        start_layout = QHBoxLayout()
        start_layout.addWidget(start_range_label)
        start_layout.addWidget(self.start_spin_box)

        end_layout = QHBoxLayout()
        end_layout.addWidget(end_range_label)
        end_layout.addWidget(self.end_spin_box)
        range_layout.addLayout(start_layout)
        range_layout.addLayout(end_layout)
        range_layout.addLayout(small_width_layout)
        range_layout.addLayout(small_height_layout)
        

        checkbox_label2 = QLabel("Orient vertically:")
        self.checkbox2 = QCheckBox()

        checkbox_layout2 = QHBoxLayout()
        checkbox_layout2.addWidget(checkbox_label2)
        checkbox_layout2.addWidget(self.checkbox2)

        accept_button = QPushButton("Accept")
        cancel_button = QPushButton("Cancel")
        reset_button = QPushButton("Default")

        accept_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        reset_button.clicked.connect(self.reset_to_default)

        button_layout = QHBoxLayout()
        button_layout.addWidget(accept_button)
        button_layout.addWidget(reset_button)
        button_layout.addWidget(cancel_button)
        

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(combo_label)
        dialog_layout.addWidget(self.combo_box)
        dialog_layout.addWidget(range_label)
        dialog_layout.addLayout(range_layout)
        dialog_layout.addLayout(checkbox_layout2)
        dialog_layout.addLayout(color_layout)
        dialog_layout.addLayout(button_layout)
        
        self.setLayout(dialog_layout)

    def set_values(self, combo_index, start_value, end_value, checkbox_state2, width, height, background_color):
        self.combo_box.setCurrentIndex(combo_index)
        self.start_spin_box.setValue(start_value)
        self.small_height_spin_box.setValue(height)
        self.small_width_spin_box.setValue(width)
        self.end_spin_box.setValue(end_value)
        self.checkbox2.setChecked(checkbox_state2)
        self.color_label.setText(f"Background color: {background_color}")

    def reset_to_default(self):
        self.combo_box.setCurrentIndex(1)
        self.start_spin_box.setValue(2)
        self.end_spin_box.setValue(2)
        self.small_height_spin_box.setValue(500)
        self.small_width_spin_box.setValue(500)
        self.checkbox2.setChecked(True)
        self.color_label.setText("Background color: #FFFFFF00")  # Reset color label

    def select_color(self):
        color_dialog = QColorDialog()
        qcolor_old = QColor(self.color_label.text()[-9:-2])
        color = color_dialog.getColor(qcolor_old, options=QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            self.color_label.setText(f"Background color: {(color.name()+color.name(QColor.NameFormat.HexArgb)[1:3]).upper()}")  # Update color label

@slot()
def ts_change_toolbar_settings():
    global ts_orient_vertical, ts_y_offset, ts_x_offset, ts_location, ts_small_width, ts_small_height, ts_background_color
    
    dialog = CustomDialog()
    dialog.set_values(ts_location, ts_x_offset, ts_y_offset, ts_orient_vertical, ts_small_width, ts_small_height, ts_background_color) 
    result = dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        ts_location = dialog.combo_box.currentIndex()
        ts_x_offset = dialog.start_spin_box.value()
        ts_y_offset = dialog.end_spin_box.value()
        ts_small_height = dialog.small_height_spin_box.value()
        ts_background_color = dialog.color_label.text()[-9:]
        ts_small_width = dialog.small_width_spin_box.value()
        ts_orient_vertical = dialog.checkbox2.isChecked()
        ts_switch()
        ts_switch()

@slot()
def ts_dots():
    """
    Switch dot conversion.
    """
    global ts_ConvertDotStrokes
    ts_ConvertDotStrokes = not ts_ConvertDotStrokes
    execute_js("convertDotStrokes = " + str(ts_ConvertDotStrokes).lower() + ";")
    execute_js("if (typeof resize === 'function') { resize(); }")

@slot()
def ts_change_auto_hide_settings():
    """
    Switch auto hide toolbar setting.
    """
    global ts_auto_hide
    ts_auto_hide = not ts_auto_hide
    ts_switch()
    ts_switch()

@slot()
def ts_change_follow_settings():
    """
    Switch whiteboard follow screen.
    """
    global ts_follow
    ts_follow = not ts_follow
    execute_js("fullscreen_follow = " + str(ts_follow).lower() + ";")
    execute_js("if (typeof resize === 'function') { resize(); }")

@slot()
def ts_change_small_default_settings():
    """
    Switch default small canvas mode setting.
    """
    global ts_default_small_canvas
    ts_default_small_canvas = not ts_default_small_canvas
    ts_switch()
    ts_switch()

@slot()
def ts_change_zen_mode_settings():
    """
    Switch default zen mode setting.
    """
    global ts_zen_mode
    ts_zen_mode = not ts_zen_mode
    ts_switch()
    ts_switch()
    
@slot()
def ts_change_auto_hide_pointer_settings():
    """
    Switch auto hide pointer setting.
    """
    global ts_auto_hide_pointer
    ts_auto_hide_pointer = not ts_auto_hide_pointer
    ts_switch()
    ts_switch()

def checkProfile():
    if not ts_profile_loaded:
        showWarning("No profile loaded")
        return False

def ts_on():
    """
    Turn on
    """
    checkProfile()

    global ts_state_on
    ts_state_on = True
    ts_menu_switch.setChecked(True)
    return True

def ts_off():
    """
    Turn off
    """
    checkProfile()

    global ts_state_on
    ts_state_on = False
    ts_menu_switch.setChecked(False)
    return True

@slot()
def ts_switch():
    """
    Switch AnkiDraw.
    """

    if ts_state_on:
        ts_off()
    else:
        ts_on()


    # Reload current screen.

    if mw.state == "review":
        #mw.moveToState('overview')
        mw.moveToState('review')
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()
    if mw.state == "overview":
        mw.overview.refresh()

def ts_setup_menu():
    """
    Initialize menu. 
    """
    global ts_menu_switch, ts_menu_dots, ts_menu_auto_hide, ts_menu_auto_hide_pointer, ts_menu_small_default, ts_menu_zen_mode, ts_menu_follow

    try:
        mw.addon_view_menu
    except AttributeError:
        mw.addon_view_menu = QMenu("""&AnkiDraw""", mw)
        mw.form.menubar.insertMenu(mw.form.menuTools.menuAction(),
                                    mw.addon_view_menu)

    # mw.ts_menu = QMenu(_('&AnkiDraw'), mw)

    # mw.addon_view_menu.addMenu(mw.ts_menu)

    ts_menu_switch = QAction("""&Enable Ankidraw""", mw, checkable=True)
    ts_menu_dots = QAction("""Convert &dot strokes on PF mode""", mw, checkable=True)
    ts_menu_auto_hide = QAction("""Auto &hide toolbar when drawing""", mw, checkable=True)
    ts_menu_auto_hide_pointer = QAction("""Auto &hide pointer when drawing""", mw, checkable=True)
    ts_menu_follow = QAction("""&Follow when scrolling (faster on big cards)""", mw, checkable=True)
    ts_menu_small_default = QAction("""&Small Canvas by default""", mw, checkable=True)
    ts_menu_zen_mode = QAction("""Enable Zen Mode(hide toolbar until this is disabled)""", mw, checkable=True)
    ts_menu_color = QAction("""Set &pen color""", mw)
    ts_menu_width = QAction("""Set pen &width""", mw)
    ts_menu_opacity = QAction("""Set pen &opacity""", mw)
    ts_toolbar_settings = QAction("""&Toolbar and canvas location settings""", mw)

    ts_toggle_seq = QKeySequence("Ctrl+r")
    ts_menu_switch.setShortcut(ts_toggle_seq)

    mw.addon_view_menu.addAction(ts_menu_switch)
    mw.addon_view_menu.addAction(ts_menu_dots)
    mw.addon_view_menu.addAction(ts_menu_auto_hide)
    mw.addon_view_menu.addAction(ts_menu_auto_hide_pointer)
    mw.addon_view_menu.addAction(ts_menu_follow)
    mw.addon_view_menu.addAction(ts_menu_small_default)
    mw.addon_view_menu.addAction(ts_menu_zen_mode)
    mw.addon_view_menu.addAction(ts_menu_color)
    mw.addon_view_menu.addAction(ts_menu_width)
    mw.addon_view_menu.addAction(ts_menu_opacity)
    mw.addon_view_menu.addAction(ts_toolbar_settings)

    ts_menu_switch.triggered.connect(ts_switch)
    ts_menu_dots.triggered.connect(ts_dots)
    ts_menu_auto_hide.triggered.connect(ts_change_auto_hide_settings)
    ts_menu_auto_hide_pointer.triggered.connect(ts_change_auto_hide_pointer_settings)
    ts_menu_follow.triggered.connect(ts_change_follow_settings)
    ts_menu_small_default.triggered.connect(ts_change_small_default_settings)
    ts_menu_zen_mode.triggered.connect(ts_change_zen_mode_settings)
    ts_menu_color.triggered.connect(ts_change_color)
    ts_menu_width.triggered.connect(ts_change_width)
    ts_menu_opacity.triggered.connect(ts_change_opacity)
    ts_toolbar_settings.triggered.connect(ts_change_toolbar_settings)

#
# ONLOAD SECTION
#
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

ts_onload()
