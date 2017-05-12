# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 17:11:22 2017

@author: Paniker
"""

import sys

# need for plot rnd
import random

import pyperclip

from PyQt4 import QtGui

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np

class Window(QtGui.QMainWindow):
    
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        # window vars
        self.dialog = None
        self.menu = None
        
        self.grid = False
        self.cid = None
        
        self.moving_data = None
        self.click_xy = (0, 0)
        
        # ax settings
        self.legend_enable = False
        
        self.axisX_enable = False
        self.axisY_enable = False
        
        self.axisX_label = 'X'
        self.axisY_label = 'Y'
        
        self.title = 'Title'
        self.title_enable = False
        
        # legend construct
        self.handles = []
        
        # arrow styles
        self.arrow_styles = {'BarAB': '|-|',
                             'BracketA': ']-',
                             'BracketAB': ']-[',
                             'BracketB': '-[',
                             'Curve': '-',
                             'CurveA': '<-',
                             'CurveAB': '<->',
                             'CurveB': '->',
                             'CurveFilledA': '<|-',
                             'CurveFilledAB': '<|-|>',
                             'CurveFilledB': '-|>',
                             'Fancy': 'fancy',
                             'Simple': 'simple',
                             'Wedge': 'wedge',
                             }
        
        # user action
        self.user_action = None
        
        self.actions = {
            'none': None,
            'select': self.on_click_select,
            'draw_arrow': self.on_click_draw_arrow,
            'draw_text': self.on_click_draw_text,
            'draw_rect': self.on_click_draw_rect,
            'draw_circle': self.on_click_draw_circle,
        }

        # vars for select
        self.select_flag = 0
        self.select = None
        self.select_colors = []
        
        # parse function by type
        self.parse_functions = {
            'line': self.parse_line,
            'arrow': self.parse_arrow,
            'text': self.parse_text,
            'rect': self.parse_rect,
            'circle': self.parse_circle,
            }

        # a figure instance to plot on
        self.figure = plt.Figure()

        # Canvas displays the figure
        # it takes the figure instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # connect to canvas actions
        self.canvas.mpl_connect('button_press_event', self.on_click_moving)
        self.canvas.mpl_connect('button_release_event', self.on_click)
        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.canvas.mpl_connect('key_press_event', self.on_key)
        self.canvas.mpl_connect('scroll_event', self.canvas_zoom)        
        
        # ax
        self.ax = self.figure.add_subplot(111)

        # Creating GUI
        self.setCentralWidget(self.canvas)
        
    def arrow_copy(self):
        ''' Load arrow propeties to clipboard '''
        
        if self.select != None:
        
            # get selected line and line.data
            arrow = self.select     
        
            # do str
            line_str = "arrow";
            
            # geometry
            pos = arrow._posA_posB
            line_str += '\r\n' + str(pos[0][0]-pos[1][0])
            line_str += '\r\n' + str(pos[0][1]-pos[1][1])
            
            # style
            style = arrow.get_arrowstyle()
            line_str += '\r\n' + self.arrow_styles[type(style).__name__]
            
            # head width & length
            if 'head_width' in style.__dict__.keys():
                head_width = style.__dict__['head_width']
                head_length = style.__dict__['head_length']
            elif 'widthA' in style.__dict__.keys():
                head_width = style.__dict__['widthA']
                head_length = style.__dict__['lengthA']  
                
            line_str += '\r\n' + str(head_width)
            line_str += '\r\n' + str(head_length)
            
            # line style & color
            line_str += '\r\n' + arrow.get_ls()
            line_str += '\r\n' + str(arrow.get_lw())
            line_str += '\r\n' + mpl.colors.rgb2hex(arrow.get_facecolor())
            
            # other
            line_str += '\r\n' + str(arrow.get_picker())
            line_str += '\r\n' + str(arrow.get_label())
            
            # load str to clipboard
            pyperclip.copy(line_str)
        
    def arrow_cut(self):
        ''' copy&remove arrow '''
        
        self.arrow_copy()
        
        self.ax_delete()
        
    def arrow_new(self, x, y):
        ''' Create new anno with arrow '''
                           
        # update canvas
        self.canvas.draw()
        
        arrow = mpl.patches.FancyArrowPatch((x,y),(x,y))
        arrow.set_arrowstyle('Fancy',
                             head_length=5,
                             head_width=5,
                             )
        
        arrow.set_facecolor('#000000')
        arrow.set_picker(5)

        # return created arrow
        return arrow
        
    def arrow_menu(self):
        ''' Context menu for arrow '''
        
        # COPY & PAST
        self.menu = QtGui.QMenu(self)
        self.menu.addAction("Copy", self.arrow_copy)
        self.menu.addAction("Cut", self.arrow_cut)
        self.menu.addAction("Delete", self.ax_delete)
        self.menu.addSeparator()
        
        # LEGEND
        action = QtGui.QAction("Legendary", self.menu)
        action.setCheckable(True)
        action.setChecked(self.select in self.handles)
        action.triggered.connect(self.legend_construct)
        self.menu.addAction(action)
        
        ok_event = lambda: (self.ax_set_label(self.select), 
                            self.dialog.close(),
                            self.legend_update())
        self.menu.addAction("Label", lambda: self.create_modal(ok_event, 
                            text = self.select.get_label()))
        self.menu.addSeparator()
        
        # ARROW PROPS
        as_menu = self.menu.addMenu("Arrow style")

        as_menu_curve = as_menu.addMenu('Curve')
        as_menu_curve.addAction("A", lambda: self.arrow_set_style(self.select,'<-'))
        as_menu_curve.addAction("B", lambda: self.arrow_set_style(self.select,'->'))
        as_menu_curve.addAction("AB", lambda: self.arrow_set_style(self.select,'<->'))
        
        as_menu_curvefilled = as_menu.addMenu('Curve filled')
        as_menu_curvefilled.addAction("A", lambda: self.arrow_set_style(self.select,'<|-'))
        as_menu_curvefilled.addAction("B", lambda: self.arrow_set_style(self.select,'-|>'))
        as_menu_curvefilled.addAction("AB", lambda: self.arrow_set_style(self.select,'<|-|>'))
        
        as_menu_brack = as_menu.addMenu('Bracket')
        as_menu_brack.addAction("A", lambda: self.arrow_set_style(self.select,']-'))
        as_menu_brack.addAction("B", lambda: self.arrow_set_style(self.select,'-['))
        as_menu_brack.addAction("AB", lambda: self.arrow_set_style(self.select,']-['))
        
        as_menu.addAction("Fancy", lambda: self.arrow_set_style(self.select,'fancy'))
        as_menu.addAction("Simple", lambda: self.arrow_set_style(self.select,'simple'))
        as_menu.addAction("Wedge", lambda: self.arrow_set_style(self.select,'wedge'))
        as_menu.addAction("BarAB", lambda: self.arrow_set_style(self.select,'|-|'))
        
        as_menu.addAction("None", lambda: self.arrow_set_style(self.select,'-'))
        
        asize_menu = self.menu.addMenu('Arrow size')
        
        asize_menu_hw = asize_menu.addMenu('Head width')
        asize_menu_hw.addAction("1", 
                lambda: self.arrow_set_styleprop(self.select,'head_width',1))
        asize_menu_hw.addAction("2", 
                lambda: self.arrow_set_styleprop(self.select,'head_width',2)) 
        asize_menu_hw.addAction("3", 
                lambda: self.arrow_set_styleprop(self.select,'head_width',3))
        asize_menu_hw.addAction("4", 
                lambda: self.arrow_set_styleprop(self.select,'head_width',4))
        asize_menu_hw.addAction("5", 
                lambda: self.arrow_set_styleprop(self.select,'head_width',5))
        asize_menu_hw.addAction("Other")
        
        asize_menu_hl = asize_menu.addMenu('Head length')        
        asize_menu_hl.addAction("1", 
                lambda: self.arrow_set_styleprop(self.select,'head_length',1))
        asize_menu_hl.addAction("2", 
                lambda: self.arrow_set_styleprop(self.select,'head_length',2)) 
        asize_menu_hl.addAction("3", 
                lambda: self.arrow_set_styleprop(self.select,'head_length',3))
        asize_menu_hl.addAction("4", 
                lambda: self.arrow_set_styleprop(self.select,'head_length',4))
        asize_menu_hl.addAction("5", 
                lambda: self.arrow_set_styleprop(self.select,'head_length',5))
        asize_menu_hl.addAction("Other")        
        
        self.menu.addSeparator()
        
        # LINE PROPS
        lw_menu = self.menu.addMenu("Line width")
        lw_menu.addAction("1 px", lambda: self.arrow_set(self.select,lw=1))
        lw_menu.addAction("2 px", lambda: self.arrow_set(self.select,lw=2))
        lw_menu.addAction("3 px", lambda: self.arrow_set(self.select,lw=3))
        lw_menu.addAction("4 px", lambda: self.arrow_set(self.select,lw=4))
        lw_menu.addAction("5 px", lambda: self.arrow_set(self.select,lw=5))
        lw_menu.addAction("Other")
        
        ls_menu = self.menu.addMenu("Line style")
        ls_menu.addAction("Solid",      
                          lambda: self.arrow_set(self.select,ls='-'))
        ls_menu.addAction("Dash",       
                          lambda: self.arrow_set(self.select,ls='--'))
        ls_menu.addAction("Dash-dot",   
                          lambda: self.arrow_set(self.select,ls='-.'))
        ls_menu.addAction("dot",        
                          lambda: self.arrow_set(self.select,ls=':'))  
        
        lw_menu = self.menu.addMenu("Line color")
        lw_menu.addAction("Blue", 
                          lambda: self.arrow_set(self.select,color='b'))
        lw_menu.addAction("Green", 
                          lambda: self.arrow_set(self.select,color='g'))
        lw_menu.addAction("Red", 
                          lambda: self.arrow_set(self.select,color='r'))
        lw_menu.addAction("Cyan", 
                          lambda: self.arrow_set(self.select,color='c'))
        lw_menu.addAction("Magenta", 
                          lambda: self.arrow_set(self.select,color='m'))
        lw_menu.addAction("Yellow", 
                          lambda: self.arrow_set(self.select,color='y'))
        lw_menu.addAction("Black", 
                          lambda: self.arrow_set(self.select,color='k'))
        lw_menu.addAction("White", 
                          lambda: self.arrow_set(self.select,color='w'))
        lw_menu.addAction("Other")
        
        self.menu.exec_(QtGui.QCursor.pos())
        
    def arrow_set(self, arrow, **kwargs):
        ''' update arrow wit props kwargs'''
    
        # update
        arrow.update(kwargs)
            
        # update canvas
        self.canvas.draw()
        
    def arrow_set_pos(self,event):
        ''' Set new pos to arrow in self.select '''
        
        # try to set
        try:
            self.select._posA_posB = [(event.xdata+self.moving_data[0][0],
                                       event.ydata+self.moving_data[0][1]),
                                      (event.xdata+self.moving_data[1][0],
                                       event.ydata+self.moving_data[1][1])]
                                       
            self.canvas.draw()
            
        except Exception:
            
            # disconncct mouse motion event
            self.canvas.mpl_disconnect(self.cid)         
            
            # print error
            print('Error while set new arrow.pos')
        
    def arrow_set_style(self, arrow, style):
        ''' update arrow wit props kwargs'''
    
        # init head props
        head_width = 5
        head_length = 5
    
        # get fancy
        fancy = arrow.get_arrowstyle()
        
        # check fancy dict
        if 'head_width' in fancy.__dict__.keys():
            head_width = fancy.__dict__['head_width']
            head_length = fancy.__dict__['head_length']
        elif 'widthA' in fancy.__dict__.keys():
            head_width = fancy.__dict__['widthA']
            head_length = fancy.__dict__['lengthA']
            
        # set style
        arrow.set_arrowstyle(style)
        
        # reset props
        self.arrow_set_styleprop(arrow,'head_width',head_width)
        self.arrow_set_styleprop(arrow,'head_length',head_length)
            
        # update canvas
        self.canvas.draw()        
        
    def arrow_set_styleprop(self, arrow, prop, value):
        ''' Set one prop of arrow '''
        
        # get fancy
        fancy = arrow.get_arrowstyle()
        
        # check fancy dict
        if prop in fancy.__dict__.keys():
            fancy.__dict__[prop] = value
        else:
            
            try:
                if prop == 'head_width':
                    fancy.__dict__['widthA'] = value
                    fancy.__dict__['widthB'] = value
                elif prop == 'head_length':
                    fancy.__dict__['lengthA'] = value
                    fancy.__dict__['lengthB'] = value
            except  Exception:
                print('Set arrow style prop error')
                
        # apply style
        arrow.set_arrowstyle(fancy)
        
        # update canvas
        self.canvas.draw()
        
    def ax_delete(self):
        ''' Remove artist from canvas '''
        
        # save artist
        item = self.select
        
        # remove from legend
        if self.select in self.handles:
            self.legend_construct()
        
        # usnselect and remove
        self.ax_unselect()
        item.remove()
        
        # update
        self.canvas.draw()
        
    def ax_grid(self, state):
        ''' drid on/off '''
        
        # update flag
        self.grid = state
        
        # grid
        self.ax.grid(state)
        
        # update canvas
        self.canvas.draw()

    def ax_save_as(self):
        ''' Save fig as image'''
        
        supported_filetypes = self.canvas.get_supported_filetypes()
        filetypes = list(supported_filetypes.keys())
        
        filters = ';;'.join(supported_filetypes[filetype]+' (*.'+filetype+')' for filetype in filetypes)
        
            # create dialog with title
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save image as', '',
                                                     filters)
        self.figure.savefig(filename)

    def ax_select(self, item):
        ''' Event of select any object on canvas 
            Greying all ax.children except item'''
        
        # clear save colors
        self.select_colors = []
        
        # for all child of ax
        for child in self.ax.get_children():
        
            # child selected
            if child == item:
                self.select = child
                self.user_action = self.actions['select'] 
                self.select_flag = 1;
                
            # LINE
            if isinstance(child, plt.Line2D):
        
                # save colors
                self.select_colors.append(child.get_color())
                
                self.select_colors.append(child.get_markerfacecolor())
                self.select_colors.append(child.get_markeredgecolor())
 
                # if child is not select, grey
                if child != item:
                    
                    child.set_color('#d1d1d1')
                    
                    child.set_markerfacecolor('#d1d1d1')
                    child.set_markeredgecolor('#d1d1d1')
            
            # ARROW
            elif isinstance(child, mpl.patches.FancyArrowPatch):   
                    
                # save color
                self.select_colors.append(child.get_facecolor())
                self.select_colors.append(child.get_edgecolor())
                    
                # if child is not select, grey
                if child != item:
                    child.set_facecolor('#d1d1d1')
                    child.set_edgecolor('#d1d1d1')   
                    
            # TEXT
            elif isinstance(child, mpl.text.Text):
                
                # save color
                self.select_colors.append(child.get_color())
                
                if child != item:
                    child.set_color('#d1d1d1')
                        
            # RECTANGLE
            elif isinstance(child, mpl.patches.Rectangle):
                
                # check child for background Rect
                if hasattr(child, 'userData'):

                    # save color
                    self.select_colors.append(child.get_facecolor())
                    self.select_colors.append(child.get_edgecolor())
                        
                    # if child is not select, grey
                    if child != item:
                        child.set_facecolor('#d1d1d1')
                        child.set_edgecolor('#d1d1d1') 
            
            # ELLIPSE
            elif isinstance(child, mpl.patches.Ellipse):                            

                # save color
                self.select_colors.append(child.get_facecolor())
                self.select_colors.append(child.get_edgecolor())
                    
                # if child is not select, grey
                if child != item:
                    child.set_facecolor('#d1d1d1')
                    child.set_edgecolor('#d1d1d1') 
                     
        # update canvas
        self.canvas.draw()
        
    def ax_set_label(self, item):
        ''' set label from self.dialog to select item '''
        
        if item:
            
            if self.dialog:
                
                self.select.set_label(self.dialog.le.text())
                
    def ax_set_lim(self, axis):
        ''' set new from self.dialog.le.text '''
        
        # try parse string from dialog
        try:
            
            # parse string to [min, max]
            string = self.dialog.le.text().split(';')
            lim = [float(each) for each in string]
            
            # set lims
            if axis == 'x':
                self.ax.set_xlim(lim)
            elif axis == 'y':
                self.ax.set_ylim(lim)
                
            # update canvas
            self.canvas.draw()
            
        except Exception:
            print(Exception)
            return None
        
    def ax_unselect(self):
        ''' Event of unselect selected item
            Colorize all ax.children'''
        
        # for all child of ax
        for child in self.ax.get_children():
            
            # LINE
            if isinstance(child, plt.Line2D):
        
                # colorize child 
                if child != self.select:
                    child.set_color(self.select_colors[0])
                    child.set_markerfacecolor(self.select_colors[1])
                    child.set_markeredgecolor(self.select_colors[2])
                
                self.select_colors = self.select_colors[3:]
                    
            # ARROW
            elif isinstance(child, mpl.patches.FancyArrowPatch):
                    
                if child != self.select:
                    child.set_facecolor(self.select_colors[0])
                    child.set_edgecolor(self.select_colors[1])
                    
                self.select_colors = self.select_colors[2:]
               
            # TEXT
            elif isinstance(child, mpl.text.Text):
                
                # colorize child
                if child != self.select:
                    child.set_color(self.select_colors[0])
                    
                self.select_colors = self.select_colors[1:]
            
            # RECTANGLE
            elif isinstance(child, mpl.patches.Rectangle):
                
                # check child for background Rect
                if hasattr(child, 'userData'):
                    
                    # colorize child 
                    if child != self.select:
                        child.set_facecolor(self.select_colors[0])
                        child.set_edgecolor(self.select_colors[1])
                    self.select_colors = self.select_colors[2:]
            
            # ELLIPSE
            elif isinstance(child, mpl.patches.Ellipse):
                    
                # colorize child 
                if child != self.select:
                    child.set_facecolor(self.select_colors[0])
                    child.set_edgecolor(self.select_colors[1])
                self.select_colors = self.select_colors[2:]

        # unselect
        self.select = None
        self.user_action = None

        # update legend
        self.legend_update()

        # update canvas
        self.canvas.draw()
        
    def axis_enable(self, axis=None, state=True):
        ''' Change axis state
            axis is x,y,xy or None 
            will be changed to state'''
            
        # state
        if axis == 'x':
            self.axisX_enable = state
        elif axis == 'y':
            self.axisY_enable = state
        elif axis == 'xy':
            self.axisX_enable = state
            self.axisY_enable = state
            
        # x label
        if self.axisX_enable:
            self.ax.set_xlabel(self.axisX_label)
        else:
            self.ax.set_xlabel('')
            
        # y label
        if self.axisY_enable:
            self.ax.set_ylabel(self.axisY_label)
        else:
            self.ax.set_ylabel('')
            
        # update canvas
        self.canvas.draw()
        
    def axis_set_label(self,axis):
        ''' Ste label from dialog to axis '''      
        
        # get label
        label = self.dialog.le.text()
        
        # set label
        if axis == 'x':
            self.axisX_label = label
        elif axis == 'y':
            self.axisY_label = label
            
        # update it
        self.axis_enable()

    def btn_arrow_event(self):
        ''' Draw arrow on canvas '''
        
        if self.select:
            self.ax_unselect()
        
        #set user action
        self.user_action = self.actions['draw_arrow']
    
    def btn_circle_event(self):
        ''' Draw circle on canvas '''
        
        if self.select:
            self.ax_unselect()
            
        self.user_action = self.actions['draw_circle']
            
    def btn_plot_event(self):
        ''' Plot some random stuff '''
        
        if self.select:
            self.ax_unselect()
        
        # random data
        x = [i-5 for i in range(10)]
        y = [round(random.random()*100)/100 for i in range(10)]

        # discards the old graph
        self.ax.hold(True)

        # plot data
        self.ax.plot(x,y, '*-',picker = 5)

        # refresh canvas
        self.canvas.draw()
        
    def btn_text_event(self):
        ''' Text at mouse(x,y) on canvas '''
        
        if self.select:
            self.ax_unselect()
        
        self.user_action = self.actions['draw_text']
        
    def btn_rect_event(self):
        ''' Draw rect on canvas '''
        
        if self.select:
            self.ax_unselect()
            
        self.user_action = self.actions['draw_rect']
        
    def canvas_menu(self):
        ''' Context menu of canvas '''
        
        # create new menu
        self.menu = QtGui.QMenu(self)
        
        # add past action
        action = QtGui.QAction("Past", self.menu)
        action.triggered.connect(self.past_from_clipboard)
        if self.parse_clipboard() == None:
            action.setDisabled(True)
        self.menu.addAction(action)
            
        self.menu.addSeparator()
        
        # LEGEND
        action = QtGui.QAction("Legend", self.menu)
        action.setCheckable(True)
        action.setChecked(self.legend_enable)
        action.triggered.connect(self.legend_state)
        self.menu.addAction(action)  
        
        # GRID
        action = QtGui.QAction("Grid", self.menu)
        action.setCheckable(True)
        action.setChecked(self.grid)
        action.triggered.connect(lambda: (self.ax_grid(not(self.grid))))
        self.menu.addAction(action)       
        
        # Tight layout
        self.menu.addAction('Tight layout', lambda: (self.figure.tight_layout(), 
                                                     self.canvas.draw()))
        
        self.menu.addSeparator()
        
        # AXIS
        axis_menu = self.menu.addMenu("Axis")
        
            # x
        ax_menu = axis_menu.addMenu("X Axis")
        
                # x lim
        ax_menu_xlim_ok_event = lambda: (self.ax_set_lim('x'),
                                      self.dialog.close())
        ax_menu.addAction("Limits", lambda: self.create_modal(ax_menu_xlim_ok_event, 
                             text = ';'.join(str(each) for each in self.ax.get_xlim())))
                # x scale
        action = QtGui.QAction("Log scale", ax_menu)
        action.setCheckable(True)
        action.setChecked(self.ax.get_xscale()=='symlog')
        
        if self.ax.get_xscale()=='symlog':
            action.triggered.connect(lambda: (self.ax.set_xscale('linear'), 
                                              self.canvas.draw()))
        else:
            action.triggered.connect(lambda: (self.ax.set_xscale('symlog'),
                                              self.canvas.draw()))
            
        ax_menu.addAction(action)
        
                # x label enable
        action = QtGui.QAction("Enable", ax_menu)
        action.setCheckable(True)
        action.setChecked(self.axisX_enable)
        action.triggered.connect(lambda: self.axis_enable('x', ~self.axisX_enable))
        ax_menu.addAction(action)
        
                # x edit label
        ax_menu_ok_event = lambda: (self.axis_set_label('x'), 
                            self.dialog.close())
        ax_menu.addAction("Label", lambda: self.create_modal(ax_menu_ok_event, 
                            text = self.axisX_label))
        
            # y
        ay_menu = axis_menu.addMenu("Y Axis")        
        
                # y lim
        ay_menu_ylim_ok_event = lambda: (self.ax_set_lim('y'),
                                      self.dialog.close())
        ay_menu.addAction("Limits", lambda: self.create_modal(ay_menu_ylim_ok_event, 
                             text = ';'.join(str(each) for each in self.ax.get_ylim())))
                # y scale
        action = QtGui.QAction("Log scale", ay_menu)
        action.setCheckable(True)
        action.setChecked(self.ax.get_yscale()=='symlog')
        
        if self.ax.get_yscale()=='symlog':
            action.triggered.connect(lambda: (self.ax.set_yscale('linear'), 
                                              self.canvas.draw()))
        else:
            action.triggered.connect(lambda: (self.ax.set_yscale('symlog'),
                                              self.canvas.draw()))
            
        ay_menu.addAction(action)
        
                # y label enable
        action = QtGui.QAction("Enable", ay_menu)
        action.setCheckable(True)
        action.setChecked(self.axisY_enable)
        action.triggered.connect(lambda: self.axis_enable('y', ~self.axisY_enable))
        ay_menu.addAction(action)
        
                # y label edit
        ay_menu_ok_event = lambda: (self.axis_set_label('y'), 
                            self.dialog.close())
        ay_menu.addAction("Label", lambda: self.create_modal(ay_menu_ok_event, 
                            text = self.axisY_label))
            
        self.menu.addSeparator()
        
        # DRAW BTN
        
        draw_menu = self.menu.addMenu('Draw')
        
        draw_menu.addAction('Plot (rnd)', self.btn_plot_event)
        draw_menu.addAction('Arrow', self.btn_arrow_event)
        draw_menu.addAction('Rect', self.btn_rect_event)
        draw_menu.addAction('Circle', self.btn_circle_event)
        draw_menu.addAction('Text', self.btn_text_event)
        
        self.menu.addSeparator()

        self.menu.addAction('Save',self.ax_save_as)
        
        self.menu.exec_(QtGui.QCursor.pos())  
       
    def canvas_set_pos(self, event):
        ''' Shift the limx, limy by mouse moving '''
        ''' Use self.click_xy as previouse mouse pos '''
        
        # calc delta mouse pos
        dx = -(event.xdata-self.click_xy[0])
        dy = -(event.ydata-self.click_xy[1])
        
        # get lims
        limx = self.ax.get_xlim()
        limy = self.ax.get_ylim()
        
        # set new lim
        self.ax.set_xlim([limx[0]+dx, limx[1]+dx])
        self.ax.set_ylim([limy[0]+dy, limy[1]+dy])
        
        # save prev pos
        self.click_xy = (limx[0]+dx-(limx[0]-event.xdata), 
                         limy[0]+dy-(limy[0]-event.ydata))
        
        # update canvas
        self.canvas.draw()
       
    def canvas_zoom(self, event):
        ''' Zoom canvas '''
        ''' Some buggy when lim too little '''
        
        # xy point to zoom
        zoom_x = np.mean(self.ax.get_xlim())
        zoom_y = np.mean(self.ax.get_ylim())
        
        # range to zoom
        range_x = sum(abs(each) for each in self.ax.get_xlim())
        range_y = sum(abs(each) for each in self.ax.get_ylim())
        
        # scale
        scale = -event.step
        
        # set new range with relative by mouse pos
        self.ax.set_xlim([zoom_x-range_x/2*pow(2,scale),
                          zoom_x+range_x/2*pow(2,scale)])
        
        self.ax.set_ylim([zoom_y-range_y/2*pow(2,scale),
                          zoom_y+range_y/2*pow(2,scale)])
        
        # update canvas
        self.canvas.draw()
       
    def create_modal(self, event_ok = None, event_close = None, text = ''):
        ''' Create modal window with line edit '''
        
        self.dialog = QtGui.QDialog()
        
        # create layout
        layout = QtGui.QVBoxLayout()
        
        # add line edit widget to dialog
        le = QtGui.QLineEdit(self.dialog)
        le.setText(text)
        layout.addWidget(le)
        self.dialog.le = le
        
        # add buttons
        btn_ok = QtGui.QPushButton('Ok')
        if event_ok:
            btn_ok.clicked.connect(event_ok)
        else:
            btn_ok.setEnabled(False)
        
        btn_cancel = QtGui.QPushButton('Cancel')
        btn_cancel.clicked.connect(self.dialog.close)
        if event_close:
            self.dialog.closeEvent.connect(event_close)
        
        layout.addWidget(btn_ok)
        layout.addWidget(btn_cancel)
        
        # set layout to dialog, set modal and show
        self.dialog.setLayout(layout)
        self.dialog.setModal(True)
        self.dialog.show()
        
    def circle_copy(self):
        ''' Copy rect as text '''
        
        if self.select != None:
        
            # get selected line and line.data
            circle = self.select      
        
            # do str
            line_str = "circle"
            
            # geometry
            line_str += '\r\n' + str(circle.width)
            line_str += '\r\n' + str(circle.height)
            
            # props
                
                # border color & alpha
            line_str += '\r\n' + mpl.colors.rgb2hex(circle.get_edgecolor())
            line_str += '\r\n' + str(circle.get_edgecolor()[3])
            
                # border style
            line_str += '\r\n' + str(circle.get_lw())
            line_str += '\r\n' + circle.get_ls()
            
                # fill color & alpha
            line_str += '\r\n' + mpl.colors.rgb2hex(circle.get_facecolor())
            line_str += '\r\n' + str(circle.get_facecolor()[3])
            
            # other
            line_str += '\r\n' + str(circle.get_picker())
            line_str += '\r\n' + circle.get_label()
            
            # load str to clipboard
            pyperclip.copy(line_str)      
        
    def circle_cut(self):
        ''' Copy&remove rect '''
        
        self.circle_copy()
        self.ax_delete()
    
    def circle_menu(self):
        ''' Context menu for circle '''
        
        # COPY & PAST
        self.menu = QtGui.QMenu(self)
        self.menu.addAction("Copy", self.circle_copy)
        self.menu.addAction("Cut", self.circle_cut)
        self.menu.addAction("Delete", self.ax_delete)
        self.menu.addSeparator()
        
        # LEGEND
        action = QtGui.QAction("Legendary", self.menu)
        action.setCheckable(True)
        action.setChecked(self.select in self.handles)
        action.triggered.connect(self.legend_construct)
        self.menu.addAction(action)
        
        ok_event = lambda: (self.ax_set_label(self.select), 
                            self.dialog.close(),
                            self.legend_update())
        self.menu.addAction("Label", lambda: self.create_modal(ok_event, 
                            text = self.select.get_label()))
        self.menu.addSeparator()
        
        # RECT PROPS
        
            # rect background border
        circle_menu_border = self.menu.addMenu("Border")
    
            # text border removing
        circle_menu_border.addAction("Remove", 
                          lambda: self.circle_set(self.select,edgecolor='None'))        

        circle_menu_border.addSeparator()        

            # text background border color
        circle_menu_border_color = circle_menu_border.addMenu("Color")
        
        circle_menu_border_color.addAction("Blue", 
                          lambda: self.circle_set(self.select,edgecolor='b'))
        circle_menu_border_color.addAction("Green", 
                          lambda: self.circle_set(self.select,edgecolor='g'))
        circle_menu_border_color.addAction("Red", 
                          lambda: self.circle_set(self.select,edgecolor='r'))
        circle_menu_border_color.addAction("Cyan", 
                          lambda: self.circle_set(self.select,edgecolor='c'))
        circle_menu_border_color.addAction("Magenta", 
                          lambda: self.circle_set(self.select,edgecolor='m'))
        circle_menu_border_color.addAction("Yellow", 
                          lambda: self.circle_set(self.select,edgecolor='y'))
        circle_menu_border_color.addAction("Black", 
                          lambda: self.circle_set(self.select,edgecolor='k'))
        circle_menu_border_color.addAction("White", 
                          lambda: self.circle_set(self.select,edgecolor='w'))
        circle_menu_border_color.addAction("Other")
        
            # text background border lw
        circle_menu_border_color = circle_menu_border.addMenu("Line width")
        
        circle_menu_border_color.addAction("1px", 
                          lambda: self.circle_set(self.select,lw=1))
        circle_menu_border_color.addAction("2px", 
                          lambda: self.circle_set(self.select,lw=2))
        circle_menu_border_color.addAction("3px", 
                          lambda: self.circle_set(self.select,lw=3))
        circle_menu_border_color.addAction("4px", 
                          lambda: self.circle_set(self.select,lw=4))
        circle_menu_border_color.addAction("5px", 
                          lambda: self.circle_set(self.select,lw=5))
        circle_menu_border_color.addAction("Other")
        
            # text background border ls
        circle_menu_border_line = circle_menu_border.addMenu("Line style")
        
        circle_menu_border_line.addAction("Solid",      
                          lambda: self.circle_set(self.select,ls='-'))
        circle_menu_border_line.addAction("Dash",       
                          lambda: self.circle_set(self.select,ls='--'))
        circle_menu_border_line.addAction("Dash-dot",   
                          lambda: self.circle_set(self.select,ls='-.'))
        circle_menu_border_line.addAction("dot",        
                          lambda: self.circle_set(self.select,ls=':'))
        circle_menu_border_line.addAction("None",       
                          lambda: self.circle_set(self.select,ls='None'))  
        
            # text background fill color
        circle_menu_color = self.menu.addMenu("Fill color")
        
        circle_menu_color.addAction("None", 
                          lambda: self.circle_set(self.select,facecolor='None'))
        circle_menu_color.addAction("Blue", 
                          lambda: self.circle_set(self.select,facecolor='b'))
        circle_menu_color.addAction("Green", 
                          lambda: self.circle_set(self.select,facecolor='g'))
        circle_menu_color.addAction("Red", 
                          lambda: self.circle_set(self.select,facecolor='r'))
        circle_menu_color.addAction("Cyan", 
                          lambda: self.circle_set(self.select,facecolor='c'))
        circle_menu_color.addAction("Magenta", 
                          lambda: self.circle_set(self.select,facecolor='m'))
        circle_menu_color.addAction("Yellow", 
                          lambda: self.circle_set(self.select,facecolor='y'))
        circle_menu_color.addAction("Black", 
                          lambda: self.circle_set(self.select,facecolor='k'))
        circle_menu_color.addAction("White", 
                          lambda: self.circle_set(self.select,facecolor='w'))
        circle_menu_color.addAction("Other")
        
        self.menu.exec_(QtGui.QCursor.pos())
    
    def circle_new(self, x, y):
        ''' Create new circle on canvas '''
        
        circle = mpl.patches.Ellipse((x,y),width=0,height=0,fill=False)
        circle.set_picker(5)
        
        return circle
        
    def circle_set(self,rect,**kwargs):
        ''' Update rect by **kwargs '''
                
        rect.update(kwargs)
        
        if 'facecolor' in kwargs.keys():
            if kwargs['facecolor'] == 'None':
                rect.set_fill(False)
            else:
                rect.set_fill(True)
        
        self.legend_update()
        self.canvas.draw()

    def circle_set_pos(self, event):
        ''' set new pos to circle in self.select '''
        
        # try to set
        try:
            self.select.center = ((event.xdata+self.moving_data[0],
                                   event.ydata+self.moving_data[1]))
                                       
            self.canvas.draw()
            
        except Exception:
            
            # disconncct mouse motion event
            self.canvas.mpl_disconnect(self.cid)         
            
            # print error
            print('Error while set new circle.pos')
        
    def draw_arrow(self, event):
        ''' Drawing arrow '''
    
        # try to update
        try:
            
            # update
            if isinstance(self.select,mpl.patches.FancyArrowPatch):
                pos = self.select._posA_posB
                self.select.set_positions(pos[0],(event.xdata,event.ydata))
                
            # redraw canvas
            self.canvas.draw()
            
        except Exception:
            print('Draw arrow error')
            
    def draw_circle(self, event):
        ''' Drawing circle '''
        
            # try to update
        #try:
            
        # update
        if isinstance(self.select, mpl.patches.Ellipse):

            x,y = self.select.center
            self.select.width = (event.xdata-x)*2
            self.select.height = (event.ydata-y)*2
            
        # redraw canvas
        self.canvas.draw()
            
        #except Exception:
            #print('Draw circle error')
            
    def draw_text_dialog_apply(self):
        ''' Apply text from dialog '''
        
        # set text
        self.select.set_text(self.dialog.le.text())   
        
        # update canvas
        self.canvas.draw()
        
        self.dialog = None
        self.select = None
        self.user_action = None
        
    def draw_text_dialog_close(self):
        ''' Close dialog'''
        
        self.select.remove()
        
        self.canvas.draw()
        
        self.dialog = None
        self.select = None
        
        self.user_action = None
        
    def draw_rect(self, event):
        ''' Drawing rect '''
        
            # try to update
        try:
            
            # update
            if isinstance(self.select, mpl.patches.Rectangle):
                self.select.set_width(event.xdata-self.select.get_x())
                self.select.set_height(event.ydata-self.select.get_y())
                
            # redraw canvas
            self.canvas.draw()
            
        except Exception:
            print('Draw rect error')

    def legend_construct(self):
        ''' rebild legend with/without self.select '''
        
        if self.select in self.handles:
            self.handles.remove(self.select)
        else:
            self.handles.append(self.select)
            
        self.legend_update()
        
    def legend_state(self):
        ''' Show on/off legend '''
        
        self.legend_enable = ~self.legend_enable
        
        self.legend_update()
        
    def legend_update(self):
        ''' rebild legend '''
        
        labels = []
        
        for handle in self.handles:
            labels.append(handle.get_label())
            
        legend = self.ax.legend(self.handles, labels)
        
        if self.legend_enable == False:
            if legend:
                legend.remove()
        
        self.canvas.draw()

    def line_copy(self):
        ''' Load line propeties to clipboard '''
        
        if self.select != None:
        
            # get selected line and line.data
            line = self.select
            data = self.select.get_data()        
        
            # do str
            line_str = "line";
            
            # x and y
            line_str += '\r\n' + ','.join(str(val) for val in data[0].tolist())
            line_str += '\r\n' + ','.join(str(val) for val in data[1].tolist())
            
            # line
            line_str += '\r\n' + line.get_linestyle()
            line_str += '\r\n' + str(line.get_linewidth())
            line_str += '\r\n' + line.get_color()
            
            # marker
            line_str += '\r\n' + line.get_marker()
            line_str += '\r\n' + str(line.get_markersize())
            line_str += '\r\n' + line.get_markerfacecolor()
            line_str += '\r\n' + line.get_markeredgecolor()
            
            # other
            line_str += '\r\n' + str(line.pickradius)
            line_str += '\r\n' + line.get_label()
            
            # load str to clipboard
            pyperclip.copy(line_str)
            
    def line_cut(self):
        ''' Cut line from canvas '''

        self.line_copy()
        self.ax_delete()
        
    def line_delete(self):
        ''' Delete line from canvas '''
        
        self.ax_delete()
        
    def line_menu(self):
        ''' Context menu for lines '''
        
        # COPY & PAST
        self.menu = QtGui.QMenu(self)
        self.menu.addAction("Copy", self.line_copy)
        self.menu.addAction("Cut", self.line_cut)
        self.menu.addAction("Delete", self.ax_delete)
        self.menu.addSeparator()
        
        # DOTS
        
            # read data
        data = self.select.get_data()
        datax = data[0]
        datay = data[1]
        
            # create empty str of dots
        dots = ''
        
            # fill dots str
        for i in range(len(datax)):
            
            if len(dots):
                dots+=','
                
            point = str(datax[i])+';'+str(datay[i])
            dots += '['+point+']'
        
        ed_menu_action = lambda: (self.line_set_data(self.select), self.dialog.close())
        self.menu.addAction("Edit dots", lambda: self.create_modal(ed_menu_action,text = dots))
        
        # LEGEND
        action = QtGui.QAction("Legendary", self.menu)
        action.setCheckable(True)
        action.setChecked(self.select in self.handles)
        action.triggered.connect(self.legend_construct)
        self.menu.addAction(action)
        
        ok_event = lambda: (self.ax_set_label(self.select), 
                            self.dialog.close(),
                            self.legend_update())
        self.menu.addAction("Label", lambda: self.create_modal(ok_event, 
                            text = self.select.get_label()))
        self.menu.addSeparator()
        
        # LINE PROPS
        lw_menu = self.menu.addMenu("Line width")
        lw_menu.addAction("1 px", lambda: self.line_set(self.select,linewidth=1))
        lw_menu.addAction("2 px", lambda: self.line_set(self.select,linewidth=2))
        lw_menu.addAction("3 px", lambda: self.line_set(self.select,linewidth=3))
        lw_menu.addAction("4 px", lambda: self.line_set(self.select,linewidth=4))
        lw_menu.addAction("5 px", lambda: self.line_set(self.select,linewidth=5))
        lw_menu.addAction("Other")
        
        ls_menu = self.menu.addMenu("Line style")
        ls_menu.addAction("Solid",      
                          lambda: self.line_set(self.select,linestyle='-'))
        ls_menu.addAction("Dash",       
                          lambda: self.line_set(self.select,linestyle='--'))
        ls_menu.addAction("Dash-dot",   
                          lambda: self.line_set(self.select,linestyle='-.'))
        ls_menu.addAction("dot",        
                          lambda: self.line_set(self.select,linestyle=':'))
        ls_menu.addAction("None",       
                          lambda: self.line_set(self.select,linestyle='None'))  
        
        lw_menu = self.menu.addMenu("Line color")
        lw_menu.addAction("Blue", 
                          lambda: self.line_set(self.select,color='b'))
        lw_menu.addAction("Green", 
                          lambda: self.line_set(self.select,color='g'))
        lw_menu.addAction("Red", 
                          lambda: self.line_set(self.select,color='r'))
        lw_menu.addAction("Cyan", 
                          lambda: self.line_set(self.select,color='c'))
        lw_menu.addAction("Magenta", 
                          lambda: self.line_set(self.select,color='m'))
        lw_menu.addAction("Yellow", 
                          lambda: self.line_set(self.select,color='y'))
        lw_menu.addAction("Black", 
                          lambda: self.line_set(self.select,color='k'))
        lw_menu.addAction("White", 
                          lambda: self.line_set(self.select,color='w'))
        lw_menu.addAction("Other")
        
        self.menu.addSeparator()
        
        # MARKER PROPS
        
        mrkr_menu = self.menu.addMenu("Marker")
        mrkr_menu.addAction("Point", lambda: self.line_set(self.select,marker='.'))
        mrkr_menu.addAction("Pixel", lambda: self.line_set(self.select,marker=','))
        mrkr_menu.addAction("Circle", lambda: self.line_set(self.select,marker='o'))
        
        mrkr_menu_trian = mrkr_menu.addMenu("Triangle")
        mrkr_menu_trian.addAction("Right", lambda: self.line_set(self.select,marker='1'))
        mrkr_menu_trian.addAction("Up", lambda: self.line_set(self.select,marker='2'))
        mrkr_menu_trian.addAction("Left", lambda: self.line_set(self.select,marker='3'))
        mrkr_menu_trian.addAction("Down", lambda: self.line_set(self.select,marker='4'))
        
        mrkr_menu.addAction("Octagon", lambda: self.line_set(self.select,marker='8'))
        mrkr_menu.addAction("Square", lambda: self.line_set(self.select,marker='s'))
        mrkr_menu.addAction("Pentagon", lambda: self.line_set(self.select,marker='p'))
        mrkr_menu.addAction("Plus", lambda: self.line_set(self.select,marker='+'))
        mrkr_menu.addAction("Plus (filled)", lambda: self.line_set(self.select,marker='P'))
        mrkr_menu.addAction("Star", lambda: self.line_set(self.select,marker='*'))
        mrkr_menu.addAction("Hexagon", lambda: self.line_set(self.select,marker='h'))
        mrkr_menu.addAction("Hexagon (2)", lambda: self.line_set(self.select,marker='H'))
        mrkr_menu.addAction("x", lambda: self.line_set(self.select,marker='x'))
        mrkr_menu.addAction("Diamond", lambda: self.line_set(self.select,marker='D'))
        mrkr_menu.addAction("Diamond (Thin)", lambda: self.line_set(self.select,marker='d'))
        mrkr_menu.addAction("Vertical line", lambda: self.line_set(self.select,marker='|'))
        mrkr_menu.addAction("Horisontal line", lambda: self.line_set(self.select,marker='_'))
        mrkr_menu.addAction("None", lambda: self.line_set(self.select,marker='None'))
        
        ms_menu = self.menu.addMenu("Marker size")
        ms_menu.addAction("1 px", lambda: self.line_set(self.select,markersize=1))
        ms_menu.addAction("2 px", lambda: self.line_set(self.select,markersize=2))
        ms_menu.addAction("3 px", lambda: self.line_set(self.select,markersize=3))
        ms_menu.addAction("4 px", lambda: self.line_set(self.select,markersize=4))
        ms_menu.addAction("5 px", lambda: self.line_set(self.select,markersize=5))
        ms_menu.addAction("Other")
        
        mc_menu = self.menu.addMenu("Marker color")
        mc_menu.addAction("Blue", 
                          lambda: self.line_set(self.select,markerfacecolor='b'))
        mc_menu.addAction("Green", 
                          lambda: self.line_set(self.select,markerfacecolor='g'))
        mc_menu.addAction("Red", 
                          lambda: self.line_set(self.select,markerfacecolor='r'))
        mc_menu.addAction("Cyan", 
                          lambda: self.line_set(self.select,markerfacecolor='c'))
        mc_menu.addAction("Magenta", 
                          lambda: self.line_set(self.select,markerfacecolor='m'))
        mc_menu.addAction("Yellow", 
                          lambda: self.line_set(self.select,markerfacecolor='y'))
        mc_menu.addAction("Black", 
                          lambda: self.line_set(self.select,markerfacecolor='k'))
        mc_menu.addAction("White", 
                          lambda: self.line_set(self.select,markerfacecolor='w'))
        mc_menu.addAction("Other")  
        
        mew_menu = self.menu.addMenu("Marker edge width")
        mew_menu.addAction("None", lambda: self.line_set(self.select,markeredgewidth=0))
        mew_menu.addAction("1 px", lambda: self.line_set(self.select,markeredgewidth=1))
        mew_menu.addAction("2 px", lambda: self.line_set(self.select,markeredgewidth=2))
        mew_menu.addAction("3 px", lambda: self.line_set(self.select,markeredgewidth=3))
        mew_menu.addAction("4 px", lambda: self.line_set(self.select,markeredgewidth=4))
        mew_menu.addAction("5 px", lambda: self.line_set(self.select,markeredgewidth=5))
        mew_menu.addAction("Other")
        
        mec_menu = self.menu.addMenu("Marker edge color")
        mec_menu.addAction("Blue", 
                          lambda: self.line_set(self.select,markeredgecolor='b'))
        mec_menu.addAction("Green", 
                          lambda: self.line_set(self.select,markeredgecolor='g'))
        mec_menu.addAction("Red", 
                          lambda: self.line_set(self.select,markeredgecolor='r'))
        mec_menu.addAction("Cyan", 
                          lambda: self.line_set(self.select,markeredgecolor='c'))
        mec_menu.addAction("Magenta", 
                          lambda: self.line_set(self.select,markeredgecolor='m'))
        mec_menu.addAction("Yellow", 
                          lambda: self.line_set(self.select,markeredgecolor='y'))
        mec_menu.addAction("Black", 
                          lambda: self.line_set(self.select,markeredgecolor='k'))
        mec_menu.addAction("White", 
                          lambda: self.line_set(self.select,markeredgecolor='w'))
        mec_menu.addAction("Other")  
        
        self.menu.exec_(QtGui.QCursor.pos())
        
    def line_set(self, line, **kwargs):
        ''' Set line propeties and udate canvas '''
        
        # update line
        line.update(kwargs)
            
        # update canvas
        self.canvas.draw()
        
    def line_set_data(self, line):
        ''' Update line.data from self.dialog dots '''
        
        try:
            
            dots = self.dialog.le.text()
            datax = []
            datay = []
            
            # split dots by pairs of [x;y]
            dots = dots.split(',')
            
            # parse each pair
            for each in dots:
                
                # make '[x,y]' to [x,y]
                dot = ''.join(char for char in each if char not in '[]')
                dot = dot.split(';')
                dot = [float(each) for each in dot]
                
                # add to data
                datax.append(dot[0])
                datay.append(dot[1])
                
            # update line data
            line.update({'data': [np.array(datax),np.array(datay)]})
            
            # update canvas
            self.canvas.draw()
                
        except Exception:
            print('Error while update line data')
        
    def on_click(self, event):
        ''' Click event on figure '''
        
        # end moving
        if (self.user_action == self.actions['select'] or
            self.user_action == self.actions['none']):
            
            if self.moving_data != None:
                
                self.canvas.mpl_disconnect(self.cid)
                self.moving_data = None
            
        # set focus to canvas
        self.canvas.setFocus()
        
        self.click_xy = (event.xdata,event.ydata)
        
        # processing of click
        if self.user_action != None:
            self.user_action(event)
            
        else:
            
            # show menu of canvas
            if event.button == 3:
                self.canvas_menu()
                
    def on_click_draw_arrow(self, event):
        ''' Draw arrow on canvas '''
        
        # if left click
        if event.button == 1:
            
            # if have not yet created arrow
            if self.select == None:
                
                # create it and select
                arrow = self.arrow_new(event.xdata,event.ydata)
                self.ax.add_patch(arrow)
                self.select = arrow;
                
                # connect mouse_move event
                self.cid = self.canvas.mpl_connect('motion_notify_event',self.draw_arrow)
                
            # if already have created anything
            elif isinstance(self.select,mpl.patches.FancyArrowPatch):
                
                self.user_action = None
                
                # disconnect mouse_move event and unselect
                self.canvas.mpl_disconnect(self.cid)
                self.select = None
                
        elif event.button == 3:
            
            # f already have created anything
            if self.select:
                
                # remove and unselect
                self.canvas.mpl_disconnect(self.cid)
                self.select.remove()
                self.select = None
                
            # reset user action
            self.user_action = None
                
            # update
            self.canvas.draw()
            
    def on_click_draw_circle(self, event):
        ''' Draw circle on canvas '''
            
        # if left click
        if event.button == 1:
            
            # if have not yet created rect
            if self.select == None:
                
                # create it and select
                circle = self.circle_new(event.xdata,event.ydata)
                self.ax.add_patch(circle)
                self.select = circle;
                
                # connect mouse_move event
                self.cid = self.canvas.mpl_connect('motion_notify_event',self.draw_circle)
                
            # if already have created anything
            elif isinstance(self.select,mpl.patches.Ellipse):
                
                self.user_action = None
                
                # disconnect mouse_move event and unselect
                self.canvas.mpl_disconnect(self.cid)
                self.select = None
                
        elif event.button == 3:
            
            # f already have created anything
            if self.select:
                
                # remove and unselect
                self.canvas.mpl_disconnect(self.cid)
                self.select.remove()
                self.select = None
                
            # reset user action
            self.user_action = None
                
            # update
            self.canvas.draw()
            
    def on_click_draw_text(self, event):
        ''' Create text on mouse(x,y)'''
        
        # if left click
        if event.button == 1:
            
            # create text
            text = self.ax.text(event.xdata,event.ydata,'[text]')
            text.set_picker(5)
            self.select = text
            
            # create dialog window
            self.dialog = QtGui.QDialog()
            
            # create layout
            layout = QtGui.QVBoxLayout()
            
            # add line edit widget to dialog
            le = QtGui.QLineEdit(self.dialog)
            layout.addWidget(le)
            self.dialog.le = le
            
            # add buttons
            btn_ok = QtGui.QPushButton('Ok')
            btn_ok.clicked.connect(self.draw_text_dialog_apply)
            
            btn_cancel = QtGui.QPushButton('Cancel')
            btn_cancel.clicked.connect(self.draw_text_dialog_close)
            
            layout.addWidget(btn_ok)
            layout.addWidget(btn_cancel)
            
            # set layout to dialog, set modal and show
            self.dialog.setLayout(layout)
            self.dialog.setModal(True)
            self.dialog.show()
            
        elif event.button == 3:
            
            # f already have created anything
            if self.select:
                
                # remove and unselect
                self.select.remove()
                self.select = None
                
            # reset user action
            self.user_action = None
                
            # update
            self.canvas.draw()
            
    def on_click_draw_rect(self, event):
        ''' Draw rect on canvas '''
        
        # if left click
        if event.button == 1:
            
            # if have not yet created rect
            if self.select == None:
                
                # create it and select
                rect = self.rect_new(event.xdata,event.ydata)
                self.ax.add_patch(rect)
                self.select = rect;
                
                # connect mouse_move event
                self.cid = self.canvas.mpl_connect('motion_notify_event',self.draw_rect)
                
            # if already have created anything
            elif isinstance(self.select,mpl.patches.Rectangle):
                
                self.user_action = None
                
                # disconnect mouse_move event and unselect
                self.canvas.mpl_disconnect(self.cid)
                self.select = None
                
        elif event.button == 3:
            
            # f already have created anything
            if self.select:
                
                # remove and unselect
                self.canvas.mpl_disconnect(self.cid)
                self.select.remove()
                self.select = None
                
            # reset user action
            self.user_action = None
                
            # update
            self.canvas.draw()
            
    def on_click_moving(self,event):
        ''' If selected and not relesed mouse left
            Trying to move self.selected artist '''
            
        # update mouse event xy
        self.click_xy = (event.xdata,event.ydata)      
            
        # if (select action or none) and left btn
        if (self.user_action == self.actions['select'] or
            self.user_action == self.actions['none']) and event.button == 1:
            
            # if no selected artist to moving
            if self.select_flag == 0:
                
                self.moving_data = [event.xdata, event.ydata]
                self.cid = self.canvas.mpl_connect('motion_notify_event',self.canvas_set_pos)
            
            # if exist selected artist and pick event on this click
            elif self.select_flag == 1:
                
                # if arrow
                if isinstance(self.select,mpl.patches.FancyArrowPatch):
                    
                    # get arrow pos
                    pos = self.select._posA_posB
                    
                    # get delta from mouse_xy
                    self.moving_data = [(pos[0][0]-self.click_xy[0],
                                         pos[0][1]-self.click_xy[1]),
                                        (pos[1][0]-self.click_xy[0],
                                         pos[1][1]-self.click_xy[1])]
                                             
                    self.cid = self.canvas.mpl_connect('motion_notify_event',self.arrow_set_pos)
                    
                # if rectangle
                elif isinstance(self.select,mpl.patches.Rectangle):
                    
                    # get xy
                    x = self.select.get_x()
                    y = self.select.get_y()
                    
                    # get delta from mouse_xy
                    self.moving_data = [x-self.click_xy[0],
                                        y-self.click_xy[1]]
                        
                    self.cid = self.canvas.mpl_connect('motion_notify_event',self.rect_set_pos)
                    
                # if text
                elif isinstance(self.select, mpl.text.Text):
                    
                    # get xy
                    pos = self.select.get_position()
                    x = pos[0]
                    y = pos[1]
                    
                    # get delta from mouse_xy
                    self.moving_data = [x-self.click_xy[0],
                                        y-self.click_xy[1]]
                        
                    self.cid = self.canvas.mpl_connect('motion_notify_event',self.text_set_pos)
                
                elif isinstance(self.select, mpl.patches.Ellipse):
                    
                    # get xy
                    x, y = self.select.center
                    
                    # get delta from mouse_xy
                    self.moving_data = [x-self.click_xy[0],
                                        y-self.click_xy[1]]
                        
                    self.cid = self.canvas.mpl_connect('motion_notify_event',self.circle_set_pos)
                
    def on_click_select(self, event):
        ''' click when selected line '''
        
        # if was pick event
        if self.select_flag == 1:
            self.select_flag = 0
        
            # mooving timer
            if event.button == 1:
                return 0
            
            # show menu of selected artist
            if event.button == 3:
                
                # get type and call menu for type
                if isinstance(self.select, plt.Line2D):
                    self.line_menu()
                    
                elif isinstance(self.select, mpl.patches.FancyArrowPatch):
                    self.arrow_menu()
                    
                elif isinstance(self.select, mpl.text.Text):
                    self.text_menu()
                    
                elif isinstance(self.select, mpl.patches.Rectangle):
                    self.rect_menu()
                
                elif isinstance(self.select, mpl.patches.Ellipse):
                    self.circle_menu()
            
        # if wasn't pick event
        else:
            
            # unselect all artists
            self.ax_unselect()
            
            # reprocessing user action after uselect lines
            self.on_click(event)
                
    def on_key(self, event):
        ''' keyboard events '''        
        
        print(self.select)     
                
    def on_pick(self, event):
        ''' Pick event '''
        
        # if pick on left or right mouse btn
        if event.mouseevent.button == 1 or event.mouseevent.button == 3:
                    
            if (self.user_action != self.actions['draw_arrow'] and
                self.user_action != self.actions['draw_rect'] and 
                self.user_action != self.actions['draw_text'] ):
                    
                # if no select artist - select artist
                if self.select == None:
                    self.ax_select(event.artist)
                    
                # if exist selected artist
                else:
                    
                    # unselect all
                    self.ax_unselect()
                    
                    # select artist
                    self.ax_select(event.artist)
        
    def parse_arrow(self, data):
        ''' Parse line from clipboard;
            return FancyArrowPatch if success'''
        
        try:
            
            # create text
            arrow = mpl.patches.FancyArrowPatch((0,0),(0,0))
            
            # set geometry
            arrow._posA_posB = [(0,0),(float(data[1]),float(data[2]))]
            
            # set arrow style
            self.arrow_set_style(arrow,data[3])
            self.arrow_set_styleprop(arrow,'head_width',float(data[4]))
            self.arrow_set_styleprop(arrow,'head_length',float(data[5]))
            
            # ls & lw
            arrow.set_ls(data[6])
            arrow.set_lw(float(data[7]))
            
            # color
            arrow.set_color(data[8])
                
            # other
            arrow.set_picker(float(data[len(data)-2]))
            arrow.set_label(data[len(data)-1])
            
            return arrow
            
        except Exception:
            print('Error while parsing')
            
        return None   
        
    def parse_circle(self, data):
        ''' Parse text from clipboard;
            return text patch if success'''
            
        try:
            
            # create text
            circle = mpl.patches.Ellipse(self.click_xy,1,1)
            
            # set geometry
            circle.width = float(data[1])
            circle.height = float(data[2])
            
            # set colors & style
                
            edgecolor = mpl.colors.hex2color(data[3])
            edgecolor = (edgecolor[0],edgecolor[1],edgecolor[2],float(data[4]))
            circle.set_edgecolor(edgecolor)
                
            circle.set_lw(float(data[5]))
            circle.set_ls(data[6])
                
            facecolor = mpl.colors.hex2color(data[7])
            facecolor = (facecolor[0],facecolor[1],facecolor[2],float(data[8]))
            
            if float(data[8]) == 0:
                circle.set_fill(False)
                
            circle.set_facecolor(facecolor)
                
            # other
            circle.set_picker(float(data[len(data)-2]))
            circle.set_label(data[len(data)-1])
            
            return circle
            
        except Exception:
            print('Error while parsing')
            
        return None        
    
    def parse_clipboard(self):
        ''' parsing clipboard;
            return object if success'''
        
        # if clipboard has text
        if isinstance(pyperclip.paste(), str):
        
            # try parse it
            try:
                
                # read clip
                data = pyperclip.paste()
                
                # convert clip to list of parameters
                data = data.split('\r\n')
                
                # read function for artist type and call it
                parse_function = self.parse_functions[data[0]]
                return parse_function(data)
                
            # exeption console log
            except Exception:
                print('Error while parsing clipboard')
    
        return None
            
    def parse_line(self, data):
        ''' Parse line from clipboard;
            return line2D if success'''
        
        try:
            
            # read data and create line
            x = np.array(list(map(float, data[1].split(','))))
            y = np.array(list(map(float, data[2].split(','))))
            line = plt.Line2D(x,y)
            
            # set line style, width, color
            line.set_linestyle(data[3])
            line.set_linewidth(float(data[4]))
            line.set_color(data[5])
            
            # set marker style, width, colors
            line.set_marker(data[6])
            line.set_markersize(float(data[7]))
            line.set_markerfacecolor(data[8])
            line.set_markeredgecolor(data[9])
            
            # other
            line.set_picker(int(data[10]))
            line.set_label(data[11])
            
            return line
            
        except Exception:
            print('Error while parsing')
            
        return None
        
    def parse_rect(self, data):
        ''' Parse text from clipboard;
            return text patch if success'''
            
        try:
            
            # create text
            rect = plt.Rectangle(self.click_xy,1,1)
            
            # not canvas bg
            rect.userData = True
            
            # set geometry
            rect.set_width(float(data[1]))
            rect.set_height(float(data[2]))
            
            # set colors & style
                
            edgecolor = mpl.colors.hex2color(data[3])
            edgecolor = (edgecolor[0],edgecolor[1],edgecolor[2],float(data[4]))
            rect.set_edgecolor(edgecolor)
                
            rect.set_lw(float(data[5]))
            rect.set_ls(data[6])
                
            facecolor = mpl.colors.hex2color(data[7])
            facecolor = (facecolor[0],facecolor[1],facecolor[2],float(data[8]))
            
            if float(data[8]) == 0:
                rect.set_fill(False)
                
            rect.set_facecolor(facecolor)
                
            # other
            rect.set_picker(float(data[len(data)-2]))
            rect.set_label(data[len(data)-1])
            
            return rect
            
        except Exception:
            print('Error while parsing')
            
        return None        
        
    def parse_text(self, data):
        ''' Parse text from clipboard;
            return text patch if success'''
            
        try:
            
            # create text
            text = plt.Text()
            text.set_text(data[1])
            
            # set props
            text.set_color(data[2])
            text.set_fontsize(float(data[3]))
            text.set_fontstyle(data[4])
            
            # halign & valing
            text.set_ha(data[5])
            text.set_va(data[6])
            
            # if bg enable
            if data[7] == 'True':
                
                edgecolor = mpl.colors.hex2color(data[8])
                edgecolor = (edgecolor[0],edgecolor[1],edgecolor[2],float(data[9]))
                
                lw = float(data[10])
                ls = data[11]
                
                facecolor = mpl.colors.hex2color(data[12])
                facecolor = (facecolor[0],facecolor[1],facecolor[2],float(data[13]))
                
                bbox_dict = {'edgecolor': edgecolor,
                             'facecolor': facecolor,
                             'lw': lw,
                             'ls': ls,
                             }
                             
                text.set_bbox(bbox_dict)
                
            text.set_picker(float(data[len(data)-1]))
            
            return text
            
        except Exception:
            print('Error while parsing')
            
        return None
        
    def past_from_clipboard(self):
        ''' Past something from clipboard to canvas '''        
        
        try:
            
            # get parsed artist
            artist = self.parse_clipboard()
            
            # get type and add it
            if isinstance(artist, plt.Line2D):
                self.ax.add_line(artist)
            
            elif isinstance(artist, plt.Text):
                self.ax.add_artist(artist)
                artist.set_position(self.click_xy)
                
            elif isinstance(artist, plt.Rectangle):
                self.ax.add_artist(artist)
                artist.set_x(self.click_xy[0]-artist.get_width()/2)
                artist.set_y(self.click_xy[1]-artist.get_height()/2)
                
            elif isinstance(artist, mpl.patches.Ellipse):
                self.ax.add_artist(artist)
                artist.center = self.click_xy
                
            elif isinstance(artist, mpl.patches.FancyArrowPatch):
                self.ax.add_artist(artist)
                artist._posA_posB = [(self.click_xy[0]+artist._posA_posB[1][0]/2,
                                      self.click_xy[1]+artist._posA_posB[1][1]/2),
                                     (self.click_xy[0]-artist._posA_posB[1][0]/2,
                                      self.click_xy[1]-artist._posA_posB[1][1]/2)]
            
            # update canvas
            self.canvas.draw()
            
        except Exception:
            print("Can't past to canvas from clipboard")
    
    def plot(self,*args,**kwargs):
        ''' plot new line2d on ax '''
        
        if self.select:
            self.ax_unselect()
        
        # plot
        self.ax.plot(*args, picker = 5, **kwargs)
        
        # update canvas
        self.canvas.draw()
    
    def rect_copy(self):
        ''' Copy rect as text '''
        
        if self.select != None:
        
            # get selected line and line.data
            rect = self.select      
        
            # do str
            line_str = "rect"
            
            # geometry
            line_str += '\r\n' + str(rect.get_width())
            line_str += '\r\n' + str(rect.get_height())
            
            # props
                
                # border color & alpha
            line_str += '\r\n' + mpl.colors.rgb2hex(rect.get_edgecolor())
            line_str += '\r\n' + str(rect.get_edgecolor()[3])
            
                # border style
            line_str += '\r\n' + str(rect.get_lw())
            line_str += '\r\n' + rect.get_ls()
            
                # fill color & alpha
            line_str += '\r\n' + mpl.colors.rgb2hex(rect.get_facecolor())
            line_str += '\r\n' + str(rect.get_facecolor()[3])
            
            # other
            line_str += '\r\n' + str(rect.get_picker())
            line_str += '\r\n' + rect.get_label()
            
            # load str to clipboard
            pyperclip.copy(line_str)      
        
    def rect_cut(self):
        ''' Copy&remove rect '''
        
        self.rect_copy()
        self.ax_delete()
    
    def rect_menu(self):
        ''' Context menu for rect '''
        
        # COPY & PAST
        self.menu = QtGui.QMenu(self)
        self.menu.addAction("Copy", self.rect_copy)
        self.menu.addAction("Cut", self.rect_cut)
        self.menu.addAction("Delete", self.ax_delete)
        self.menu.addSeparator()
        
        # LEGEND
        action = QtGui.QAction("Legendary", self.menu)
        action.setCheckable(True)
        action.setChecked(self.select in self.handles)
        action.triggered.connect(self.legend_construct)
        self.menu.addAction(action)
        
        ok_event = lambda: (self.ax_set_label(self.select), 
                            self.dialog.close(),
                            self.legend_update())
        self.menu.addAction("Label", lambda: self.create_modal(ok_event, 
                            text = self.select.get_label()))
        self.menu.addSeparator()
        
        # RECT PROPS
        
            # rect background border
        rect_menu_border = self.menu.addMenu("Border")
    
            # text border removing
        rect_menu_border.addAction("Remove", 
                          lambda: self.rect_set(self.select,edgecolor='None'))        

        rect_menu_border.addSeparator()        

            # text background border color
        rect_menu_border_color = rect_menu_border.addMenu("Color")
        
        rect_menu_border_color.addAction("Blue", 
                          lambda: self.rect_set(self.select,edgecolor='b'))
        rect_menu_border_color.addAction("Green", 
                          lambda: self.rect_set(self.select,edgecolor='g'))
        rect_menu_border_color.addAction("Red", 
                          lambda: self.rect_set(self.select,edgecolor='r'))
        rect_menu_border_color.addAction("Cyan", 
                          lambda: self.rect_set(self.select,edgecolor='c'))
        rect_menu_border_color.addAction("Magenta", 
                          lambda: self.rect_set(self.select,edgecolor='m'))
        rect_menu_border_color.addAction("Yellow", 
                          lambda: self.rect_set(self.select,edgecolor='y'))
        rect_menu_border_color.addAction("Black", 
                          lambda: self.rect_set(self.select,edgecolor='k'))
        rect_menu_border_color.addAction("White", 
                          lambda: self.rect_set(self.select,edgecolor='w'))
        rect_menu_border_color.addAction("Other")
        
            # text background border lw
        rect_menu_border_color = rect_menu_border.addMenu("Line width")
        
        rect_menu_border_color.addAction("1px", 
                          lambda: self.rect_set(self.select,lw=1))
        rect_menu_border_color.addAction("2px", 
                          lambda: self.rect_set(self.select,lw=2))
        rect_menu_border_color.addAction("3px", 
                          lambda: self.rect_set(self.select,lw=3))
        rect_menu_border_color.addAction("4px", 
                          lambda: self.rect_set(self.select,lw=4))
        rect_menu_border_color.addAction("5px", 
                          lambda: self.rect_set(self.select,lw=5))
        rect_menu_border_color.addAction("Other")
        
            # text background border ls
        rect_menu_border_line = rect_menu_border.addMenu("Line style")
        
        rect_menu_border_line.addAction("Solid",      
                          lambda: self.rect_set(self.select,ls='-'))
        rect_menu_border_line.addAction("Dash",       
                          lambda: self.rect_set(self.select,ls='--'))
        rect_menu_border_line.addAction("Dash-dot",   
                          lambda: self.rect_set(self.select,ls='-.'))
        rect_menu_border_line.addAction("dot",        
                          lambda: self.rect_set(self.select,ls=':'))
        rect_menu_border_line.addAction("None",       
                          lambda: self.rect_set(self.select,ls='None'))  
        
            # text background fill color
        rect_menu_color = self.menu.addMenu("Fill color")
        
        rect_menu_color.addAction("None", 
                          lambda: self.rect_set(self.select,facecolor='None'))
        rect_menu_color.addAction("Blue", 
                          lambda: self.rect_set(self.select,facecolor='b'))
        rect_menu_color.addAction("Green", 
                          lambda: self.rect_set(self.select,facecolor='g'))
        rect_menu_color.addAction("Red", 
                          lambda: self.rect_set(self.select,facecolor='r'))
        rect_menu_color.addAction("Cyan", 
                          lambda: self.rect_set(self.select,facecolor='c'))
        rect_menu_color.addAction("Magenta", 
                          lambda: self.rect_set(self.select,facecolor='m'))
        rect_menu_color.addAction("Yellow", 
                          lambda: self.rect_set(self.select,facecolor='y'))
        rect_menu_color.addAction("Black", 
                          lambda: self.rect_set(self.select,facecolor='k'))
        rect_menu_color.addAction("White", 
                          lambda: self.rect_set(self.select,facecolor='w'))
        rect_menu_color.addAction("Other")
        
        self.menu.exec_(QtGui.QCursor.pos())
    
    def rect_new(self,x,y):
        ''' Create new rect on canvas '''
        
        rect = plt.Rectangle((x,y),0,0,fill=False)
        rect.userData = True
        rect.set_picker(5)
        
        return rect
        
    def rect_set(self,rect,**kwargs):
        ''' Update rect by **kwargs '''
                
        rect.update(kwargs)
        
        if 'facecolor' in kwargs.keys():
            if kwargs['facecolor'] == 'None':
                rect.set_fill(False)
            else:
                rect.set_fill(True)
        
        self.legend_update()
        self.canvas.draw()
        
    def rect_set_pos(self,event):
        ''' set new pos to rect in self.select '''
        
        # try to set
        try:
            self.select.set_xy((event.xdata+self.moving_data[0],
                                event.ydata+self.moving_data[1]))
                                       
            self.canvas.draw()
            
        except Exception:
            
            # disconncct mouse motion event
            self.canvas.mpl_disconnect(self.cid)         
            
            # print error
            print('Error while set new rect.pos')
        
    def text_bg_remove(self,text):
        ''' remove text bg '''
        
        # remove bg
        text.set_bbox(text.get_bbox_patch().set_visible(False)) 
        
        # update canvas
        self.canvas.draw()
        
    def text_bg_set_prop(self,text,prop,value):
        ''' set prop to rect of text '''
        
        # get bg bbox
        bbox = text.get_bbox_patch()
        
        # if it exist init bbox wioth updated props and set it
        if isinstance(bbox,mpl.patches.FancyBboxPatch):
            
            bbox_dict = dict(edgecolor=bbox.get_edgecolor(),
                             facecolor=bbox.get_facecolor(),
                             lw=bbox.get_lw(),
                             ls=bbox.get_ls())
        
        else:
            bbox_dict = dict(edgecolor='k',
                             facecolor='None')
            
        bbox_dict[prop] = value
        
        text.set_bbox(bbox_dict)
            
        self.canvas.draw()
        
    def text_copy(self):
        ''' copy text with props '''
        
        if self.select != None:
        
            # get selected line and line.data
            text = self.select      
        
            # do str
            line_str = "text";
            
            # string
            line_str += '\r\n' + text.get_text()
            
            # font props
            line_str += '\r\n' + text.get_color()
            line_str += '\r\n' + str(text.get_size())
            line_str += '\r\n' + text.get_fontstyle()
            line_str += '\r\n' + text.get_ha()
            line_str += '\r\n' + text.get_va()
            
            # background check
            bbox = text.get_bbox_patch()
            
            # bg enable
            if bbox == None:
                line_str += '\r\n' + 'False'
            else:
                line_str += '\r\n' + 'True'
                
                # bg props
                
                    # border color & alpha
                line_str += '\r\n' + mpl.colors.rgb2hex(bbox.get_edgecolor())
                line_str += '\r\n' + str(bbox.get_edgecolor()[3])
                
                    # border style
                line_str += '\r\n' + str(bbox.get_lw())
                line_str += '\r\n' + bbox.get_ls()
                
                    # fill color & alpha
                line_str += '\r\n' + mpl.colors.rgb2hex(bbox.get_facecolor())
                line_str += '\r\n' + str(bbox.get_facecolor()[3])
            
            # other
            line_str += '\r\n' + str(text.get_picker())
            
            # load str to clipboard
            pyperclip.copy(line_str)
        
    def text_cut(self):
        ''' copy&remove text '''
        
        self.text_copy()
        self.ax_delete()
        
    def text_menu(self):
        ''' Context menu for text '''
        
        # COPY & PAST
        self.menu = QtGui.QMenu(self)
        self.menu.addAction("Copy", self.text_copy)
        self.menu.addAction("Cut", self.text_cut)
        self.menu.addAction("Delete", self.ax_delete)
        self.menu.addSeparator()
        
        # TEXT PROPS
        
            # text color
        tc_menu = self.menu.addMenu("Color")
        tc_menu.addAction("Blue", 
                          lambda: self.text_set(self.select,color='b'))
        tc_menu.addAction("Green", 
                          lambda: self.text_set(self.select,color='g'))
        tc_menu.addAction("Red", 
                          lambda: self.text_set(self.select,color='r'))
        tc_menu.addAction("Cyan", 
                          lambda: self.text_set(self.select,color='c'))
        tc_menu.addAction("Magenta", 
                          lambda: self.text_set(self.select,color='m'))
        tc_menu.addAction("Yellow", 
                          lambda: self.text_set(self.select,color='y'))
        tc_menu.addAction("Black", 
                          lambda: self.text_set(self.select,color='k'))
        tc_menu.addAction("White", 
                          lambda: self.text_set(self.select,color='w'))
        tc_menu.addAction("Other")
        
            # fontstyle
        tstyle_menu = self.menu.addMenu("Style")
        tstyle_menu.addAction("Normal", lambda: self.text_set(self.select, fontstyle='normal'))
        tstyle_menu.addAction("Italic", lambda: self.text_set(self.select, fontstyle='italic'))
        tstyle_menu.addAction("Oblique", lambda: self.text_set(self.select, fontstyle='oblique'))
        
            # text size
        ts_menu = self.menu.addMenu("Size")
        ts_menu.addAction("14px", lambda: self.text_set(self.select, fontsize=14))
        ts_menu.addAction("16px", lambda: self.text_set(self.select, fontsize=16))
        ts_menu.addAction("18px", lambda: self.text_set(self.select, fontsize=18))
        ts_menu.addAction("20px", lambda: self.text_set(self.select, fontsize=20))
        ts_menu.addAction("25px", lambda: self.text_set(self.select, fontsize=25))
        ts_menu.addAction("Other")
        
            # text halign
        th_menu = self.menu.addMenu("Halign")
        th_menu.addAction("Left", lambda: self.text_set(self.select, ha='left'))
        th_menu.addAction("Center", lambda: self.text_set(self.select, ha='center'))
        th_menu.addAction("Right", lambda: self.text_set(self.select, ha='right'))
        
            # text valign
        tv_menu = self.menu.addMenu("Valign")
        tv_menu.addAction("Top", lambda: self.text_set(self.select, va='top'))
        tv_menu.addAction("Center", lambda: self.text_set(self.select, va='center'))
        tv_menu.addAction("Bottom", lambda: self.text_set(self.select, va='bottom'))
        tv_menu.addAction("Baseline", lambda: self.text_set(self.select, va='baseline'))
        
        self.menu.addSeparator()   
        
        # BACKGROUND PROPS
        tb_menu = self.menu.addMenu("Background")
        
        tb_menu.addAction("Remove", 
                          lambda: self.text_bg_remove(self.select))
        
            # text background border
        tb_menu_border = tb_menu.addMenu("Border")
    
            # text border removing
        tb_menu_border.addAction("Remove", 
                          lambda: self.text_bg_set_prop(self.select,'edgecolor','None'))        

        tb_menu_border.addSeparator()        

            # text background border color
        tb_menu_border_color = tb_menu_border.addMenu("Color")
        
        tb_menu_border_color.addAction("Blue", 
                          lambda: self.text_bg_set_prop(self.select,'edgecolor','b'))
        tb_menu_border_color.addAction("Green", 
                          lambda: self.text_bg_set_prop(self.select,'edgecolor','g'))
        tb_menu_border_color.addAction("Red", 
                          lambda: self.text_bg_set_prop(self.select,'edgecolor','r'))
        tb_menu_border_color.addAction("Cyan", 
                          lambda: self.text_bg_set_prop(self.select,'edgecolor','c'))
        tb_menu_border_color.addAction("Magenta", 
                          lambda: self.text_bg_set_prop(self.select,'edgecolor','m'))
        tb_menu_border_color.addAction("Yellow", 
                          lambda: self.text_bg_set_prop(self.select,'edgecolor','y'))
        tb_menu_border_color.addAction("Black", 
                          lambda: self.text_bg_set_prop(self.select,'edgecolor','k'))
        tb_menu_border_color.addAction("White", 
                          lambda: self.text_bg_set_prop(self.select,'edgecolor','w'))
        tb_menu_border_color.addAction("Other")
        
            # text background border lw
        tb_menu_border_color = tb_menu_border.addMenu("Line width")
        
        tb_menu_border_color.addAction("1px", 
                          lambda: self.text_bg_set_prop(self.select,'lw',1))
        tb_menu_border_color.addAction("2px", 
                          lambda: self.text_bg_set_prop(self.select,'lw',2))
        tb_menu_border_color.addAction("3px", 
                          lambda: self.text_bg_set_prop(self.select,'lw',3))
        tb_menu_border_color.addAction("4px", 
                          lambda: self.text_bg_set_prop(self.select,'lw',4))
        tb_menu_border_color.addAction("5px", 
                          lambda: self.text_bg_set_prop(self.select,'lw',5))
        tb_menu_border_color.addAction("Other")
        
            # text background border ls
        tb_menu_border_color = tb_menu_border.addMenu("Line style")
        
        tb_menu_border_color.addAction("Solid",      
                          lambda: self.text_bg_set_prop(self.select,'ls','-'))
        tb_menu_border_color.addAction("Dash",       
                          lambda: self.text_bg_set_prop(self.select,'ls','--'))
        tb_menu_border_color.addAction("Dash-dot",   
                          lambda: self.text_bg_set_prop(self.select,'ls','-.'))
        tb_menu_border_color.addAction("dot",        
                          lambda: self.text_bg_set_prop(self.select,'ls',':'))
        tb_menu_border_color.addAction("None",       
                          lambda: self.text_bg_set_prop(self.select,'ls','None'))  
        
            # text background fill color
        tb_menu_color = tb_menu.addMenu("Fill color")
        
        tb_menu_color.addAction("None", 
                          lambda: self.text_bg_set_prop(self.select,'facecolor','None'))
        tb_menu_color.addAction("Blue", 
                          lambda: self.text_bg_set_prop(self.select,'facecolor','b'))
        tb_menu_color.addAction("Green", 
                          lambda: self.text_bg_set_prop(self.select,'facecolor','g'))
        tb_menu_color.addAction("Red", 
                          lambda: self.text_bg_set_prop(self.select,'facecolor','r'))
        tb_menu_color.addAction("Cyan", 
                          lambda: self.text_bg_set_prop(self.select,'facecolor','c'))
        tb_menu_color.addAction("Magenta", 
                          lambda: self.text_bg_set_prop(self.select,'facecolor','m'))
        tb_menu_color.addAction("Yellow", 
                          lambda: self.text_bg_set_prop(self.select,'facecolor','y'))
        tb_menu_color.addAction("Black", 
                          lambda: self.text_bg_set_prop(self.select,'facecolor','k'))
        tb_menu_color.addAction("White", 
                          lambda: self.text_bg_set_prop(self.select,'facecolor','w'))
        tb_menu_color.addAction("Other")
        
        self.menu.exec_(QtGui.QCursor.pos())
        
    def text_set(self, text, **kwargs):
        ''' Set line propeties and udate canvas '''
        
        # update line
        text.update(kwargs)
            
        # update canvas
        self.canvas.draw()
        
    def text_set_pos(self,event):
        ''' set new pos to rect in self.select '''
        
        # try to set
        try:
            self.select.set_position((event.xdata+self.moving_data[0],
                                      event.ydata+self.moving_data[1]))
                                       
            self.canvas.draw()
            
        except Exception:
            
            # disconncct mouse motion event
            self.canvas.mpl_disconnect(self.cid)         
            
            # print error
            print('Error while set new text.pos')
            
def plot(*args,**kwargs):
    ''' plot line with *kwargs
        return window '''
    
    window = Window()
    window.show()
    window.plot(*args,**kwargs)
    
    return window

if __name__ == '__main__':
    '''
    app = QtGui.QApplication(sys.argv)

    main = Window()
    main.show()

    sys.exit(app.exec_())
    '''
    app = QtGui.QApplication(sys.argv)
    
    # random data
    x = [i-5 for i in range(10)]
    y = [round(random.random()*100)/100 for i in range(10)]
    
    win1 = plot(x,y)
    win1.show()
    win2 = plot(x,y)
    win2.show()
    
    sys.exit(app.exec_())