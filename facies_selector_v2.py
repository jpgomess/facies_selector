# -- INÍCIO -- #

from PySimpleGUI.PySimpleGUI import read_all_windows
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt
import PySimpleGUI as sg
import pandas as pd
import numpy as np
import keyboard
import pickle
import segyio
import os

def open_config_window(facies_list):
    width = 300
    height = 250
    layout = [
        [sg.Text('Start with:')],
        [sg.Listbox(['Crossline', 'Inline'], key='LISTBOX_LINES', expand_y=True)],
        [sg.Text('Select a facies below:')],
        [sg.Listbox([facie for facie in facies_list], key='LISTBOX_FACIES', expand_y=True), sg.Text('or'), sg.Input(key='INPUT_FACIE')],
        [sg.Button('Start', key='START'), sg.Button('End', key='END')]
    ]
    window = sg.Window(
        'Configuration',
        layout,
        element_justification='center',
        finalize=True,
        location=(683 - width/2, 360 - height/2),
        size=(width, height)
        )
    return window

def open_selection_window():

    layout = [
        [sg.Canvas(key='CANVAS')],
        [sg.Button('Undo', key='UNDO'), sg.Button('<', key='PREV'), sg.Text('Line Number: ', key='LINE_NUMBER'), sg.Button('>', key='NEXT'), sg.Button('Change Facies', key='CHANGE'), sg.Button('End', key='END'), sg.VSeparator(), sg.Text('Actual Mode (Select/Delete):'), sg.Button('Select', key='MODE')]
    ]
    window = sg.Window('Getting Inputs', layout, element_justification='center', finalize=True, location=(0,0))
    return window

def open_save_object_window():
    width = 300
    height = 150

    layout = [
        [sg.Button('Update Object', key='UPDATE'), sg.Button('Create Object', key='CREATE')]
    ]

    window = sg.Window(
        'Save Object',
        layout,
        element_justification='center',
        finalize=True,
        location=(683 - width/2, 360 - height/2),
        size=(width, height)
        )

    return window

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def load_figure():
    if il_or_xl == 'Inline': #Inline
        print(f'Actual Inline number: {line_number[il_or_xl]}')
        img = f3_seismic.iline[line_number[il_or_xl]]
    else: #Crossline
        print(f'Actual Crossline number: {line_number[il_or_xl]}')
        img = f3_seismic.xline[line_number[il_or_xl]]

    img = img.T

    fig, ax = plt.subplots(figsize=(7, 7*0.65))
    ax.imshow(img, cmap='gray_r', aspect='auto', vmin=vmin, vmax=vmax)

    canvas = selection_window['CANVAS'].TKCanvas

    fig_agg = draw_figure(canvas, fig)

    return fig_agg

def delete_fig_agg():
    fig_agg.get_tk_widget().forget()
    plt.close('all')

cube_path = rf"C:\Users\jpgom\Documents\Jão\VS_Code\IC\Seismic_data_w_null.sgy"
objects_path = os.getcwd()

actual_mode = 'selector'

f3_seismic = segyio.open(cube_path)
vmin = -4000
vmax = 4000

extension = '.obj'
list_dir = os.listdir(objects_path)
facies_list = [list_dir[i][:-len(extension)] for i in range(len(list_dir)) if list_dir[i].endswith(extension)]
facies_list.sort()

line_number = {'Inline': f3_seismic.ilines[0], 'Crossline': f3_seismic.xlines[0]}
line_step = 50

config_window, selection_window, save_window = open_config_window(facies_list), None, None

while True:

    if selection_window != None:
        fig_agg = load_figure()

    window, events, values = sg.read_all_windows()

    if events == sg.WIN_CLOSED or events == 'END':
        window.close()
        break

    elif events == 'START':
        config_window.hide()
        selection_window = open_selection_window()

        il_or_xl = values['LISTBOX_LINES'][0]
        facie_to_select = values['LISTBOX_FACIES'][0]

    elif events == 'NEXT':
        delete_fig_agg()

        line_number[il_or_xl] += line_step
        window['LINE_NUMBER'].update(f'Line Number: {line_number[il_or_xl]}')

    elif events == 'PREV':
        delete_fig_agg()

        line_number[il_or_xl] -= line_step
        window['LINE_NUMBER'].update(f'Line Number: {line_number[il_or_xl]}')

