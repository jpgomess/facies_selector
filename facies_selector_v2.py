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
        [sg.Button('Undo', key='UNDO'), sg.Button('<', key='PREV'), sg.Text(f'Actual Line Number: {line_number[il_or_xl]}', key='LINE_NUMBER'), sg.Button('>', key='NEXT'), sg.Text('Step:'), sg.Input(50, key='STEP', size=5), sg.Button('Change Facies', key='CHANGE'), sg.Button('End', key='END'), sg.VSeparator(), sg.Text(f'Actual Mode (Select/Delete):'), sg.Button('Select', key='MODE')]
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
	img = f3_seismic.iline[line_number[il_or_xl]].T if il_or_xl == 'Inline' else f3_seismic.xline[line_number[il_or_xl]].T

	fig, ax = plt.subplots(figsize=(10, 10*0.65))
	ax.imshow(img, cmap='gray_r', aspect='auto', vmin=vmin, vmax=vmax)

	canvas = selection_window['CANVAS'].TKCanvas

	fig_agg = draw_figure(canvas, fig)

	return fig, fig_agg

def delete_fig_agg():
    fig_agg.get_tk_widget().forget()
    plt.close('all')

def open_object():
    file = open(rf'{objects_path}/{facie_to_select}.obj', 'rb')
    object_file = pickle.load(file)
    file.close()

    return object_file

def load_points():
	x = [click['x'] for click in clicks if click[il_or_xl.lower()] == line_number[il_or_xl]]
	y = [click['y'] for click in clicks if click[il_or_xl.lower()] == line_number[il_or_xl]]

	if facie_to_select == 'Fault':
	    plt.scatter(x, y, marker='.', linewidth=2, color='r', alpha=0.5)
	elif facie_to_select == 'Non_Fault':
	    plt.scatter(x, y, marker='.', linewidth=2, color='g', alpha=0.5)
	else:
	    plt.scatter(x, y, marker='.', linewidth=2, color='yellow', alpha=0.5)

	fig.canvas.draw()

def onclick(event):
	global clicks

	x = int(event.xdata)
	y = int(event.ydata)

	print(f'Click X: {x} | Click Y: {y}')

	click_dict = {
		'inline': line_number['Inline'],
		'crossline': line_number['Crossline'],
		'x': x,
		'y': y
	}

	if actual_mode == 'Select':

		plt.scatter(x, y, marker='.', linewidth=2, color='r', alpha=0.5)
		fig.canvas.draw()

		clicks += [click_dict]
	else:
		df = pd.DataFrame()

		df['inline'] = [click['inline'] for click in clicks]
		df['crossline'] = [click['crossline'] for click in clicks]
		df['x'] = [click['x'] for click in clicks]
		df['y'] = [click['y'] for click in clicks]
		df['dist'] = np.sqrt((df['x'] - click_dict['x']) ** 2 + (df['y'] - click_dict['y']) ** 2)

		df_sorted = df.sort_values('dist')

		nearest_click = dict(df_sorted.iloc[0,:-1])

		if df_sorted['dist'].to_list()[0] <= 50:    
		    clicks.remove(nearest_click)
		    print('Nearest selection removed!')
		else:
		    print('There are no selections nearby... Nothing happened...')

#cube_path = r"C:\Users\jpgom\Documents\Jão\VS_Code\IC\Seismic_data_w_null.sgy"
cube_path = r'/home/gaia/jpedro/Seismic_data_w_null.sgy'
objects_path = os.getcwd()

actual_mode = 'Select'

f3_seismic = segyio.open(cube_path)
vmin = -4000
vmax = 4000

extension = '.obj'
list_dir = os.listdir(objects_path)
facies_list = [list_dir[i][:-len(extension)] for i in range(len(list_dir)) if list_dir[i].endswith(extension)]
facies_list.sort()

clicks, initial_clicks = None

config_window, selection_window, save_window = open_config_window(facies_list), None, None

while True:

	if selection_window != None:
		fig, fig_agg = load_figure()
		load_points()
		cid = fig.canvas.mpl_connect('button_press_event', onclick)

	window, events, values = sg.read_all_windows()
	
	if window == config_window:
		if events == sg.WIN_CLOSED:
			if clicks == initial_clicks:
				break
			else:
				config_window.hide()
				save_window = open_save_object_window()

		elif events == 'START':
			il_or_xl = values['LISTBOX_LINES'][0]
			facie_to_select = values['LISTBOX_FACIES'][0]

			line_number = {'Inline': f3_seismic.ilines[0], 'Crossline': None} if il_or_xl == 'Inline' else {'Inline': None, 'Crossline': f3_seismic.xlines[0]}

			clicks, initial_clicks = open_object(), open_object()
			
			config_window.hide()
			selection_window = open_selection_window()
		
	elif window == selection_window:
		if events == sg.WIN_CLOSED or events == 'END':
			if clicks == initial_clicks:
				break
			else:
				
	
		elif events == 'NEXT':
			delete_fig_agg()

			line_number[il_or_xl] += int(values['STEP'])

			window['LINE_NUMBER'].update(f'Actual Line Number: {line_number[il_or_xl]}')

		elif events == 'PREV':
			delete_fig_agg()

			line_number[il_or_xl] -= int(values['STEP'])
			window['LINE_NUMBER'].update(f'Actual Line Number: {line_number[il_or_xl]}')

		elif events == 'CHANGE':
			selection_window.close()
			config_window.un_hide()

		elif events == 'MODE':
			delete_fig_agg()

			actual_mode = 'Select' if actual_mode == 'Delete' else 'Delete'
			window['MODE'].update(actual_mode)
	
	elif window == save_window:
		pass

window.close()

# -- FIM -- #
