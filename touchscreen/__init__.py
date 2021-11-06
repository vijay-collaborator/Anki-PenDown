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
var line_width = 4;

canvas.onselectstart = function() { return false; };
wrapper.onselectstart = function() { return false; };

function switch_visibility()
{
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
    arrays_of_points.pop()
    if(!arrays_of_points.length)
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
    arrays_of_points=[];
	ts_redraw();
}

function stop_drawing(){
	isPointerDown = false;
	drawingWithPressurePenOnly = false;
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
	if(!pleaseRedrawEverything && startLine == arrays_of_points.length-1 && startPoint == arrays_of_points[startLine].length-1) return;
	
	var fullRedraw = false;//keep track if this call started a full redraw to unset pleaseRedrawEverything flag later.
	if (pleaseRedrawEverything) {// erase everything and draw from start
	fullRedraw = true;
	startLine = 0;
	startPoint = 0;
	ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
	}
	for(var i = startLine; i < arrays_of_points.length; i++){ 
		lastLine = i;
		///0,0,0; 0,0,1; 0,1,2 or x+1,x+2,x+3
		//take the 2 previous points in addition to current one at the start of the loop.
		p2 = arrays_of_points[i][startPoint > 1 ? startPoint-2 : 0];
		p3 = arrays_of_points[i][startPoint > 0 ? startPoint-1 : 0];
        for(var j = startPoint; j < arrays_of_points[i].length; j++){
			lastPoint = j;
			p1 = p2;
			p2 = p3;
			p3 = arrays_of_points[i][j];
			draw_path_at_some_point_async(p1[0],p1[1],p2[0],p2[1],p3[0],p3[1],p3[2]);
        }
		startPoint = 0;
    }
	if (fullRedraw) {//finished full redraw can unset redraw all flag so no more full redraws until necesarry
	pleaseRedrawEverything = false;
	fullRedraw = false;
	lastLine = 0;
	lastPoint = 0;
	}
}

var drawingWithPressurePenOnly = false; // hack for drawing with 2 main pointers when using a presure sensitive pen

canvas.addEventListener("pointerdown", function (e) {
	if (!e.isPrimary) { return; }
	if (e.pointerType[0] == 'p') { drawingWithPressurePenOnly = true }
	else if ( drawingWithPressurePenOnly) { return; }
    if(!isPointerDown){
        event.preventDefault();
        arrays_of_points.push([[
			e.offsetX,
			e.offsetY,
			e.pointerType[0] == 'p' ? (0.5 + e.pressure * line_width * 2) : line_width]]);
        ts_undo_button.className = "active"
		isPointerDown = true;
    }
});

canvas.addEventListener("pointermove", function (e) {
	if (!e.isPrimary) { return; }
	if (e.pointerType[0] != 'p' && drawingWithPressurePenOnly) { return; }
    if (isPointerDown && active) {
        arrays_of_points[arrays_of_points.length-1].push([
			e.offsetX,
			e.offsetY,
			e.pointerType[0] == 'p' ? (0.5 + e.pressure * line_width * 2) : line_width]);
    }
});

window.addEventListener("pointerup",function (e) {
    /* Needed for the last bit of the drawing. */
	if (!e.isPrimary) { return; }
	if (e.pointerType[0] != 'p' && drawingWithPressurePenOnly) { return; }
     if (isPointerDown && active) {
        arrays_of_points[arrays_of_points.length-1].push([
			e.offsetX,
			e.offsetY,
			e.pointerType[0] == 'p' ? (e.pressure * line_width * 2) : line_width]);
    } 
	stop_drawing();
});

document.addEventListener('keyup', function(e) {
    // Z or z
    if ((e.keyCode == 90 || e.keyCode == 122) && e.altKey) {
		e.preventDefault()
        ts_undo()
    }
    // /
    if (e.key === ".") {
        clear_canvas()
    }
	// ,
    if (e.key === ",") {
        switch_visibility()
    }
})


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
