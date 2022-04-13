# -- INÍCIO -- #

from importlib.resources import path
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

def get_facies_list(extension):
	list_dir = os.listdir(objects_path)
	facies_list = [list_dir[i][:-len(extension)] for i in range(len(list_dir)) if list_dir[i].endswith(extension)]
	facies_list.sort()
	
	return facies_list

def open_config_window():
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
    window = sg.Window('Facies Selector', layout, element_justification='center', finalize=True, location=(0,0))
    return window

def open_save_window():
    width = 300
    height = 150

    layout = [
        [sg.Text('Save Changes?')],
        [sg.Button('Yes', key='SAVE'), sg.Button('No', key='NOT_SAVE')]
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
    
def save_window_loop():
	save_window = open_save_window()
	while True:
		window, events, values = sg.read_all_windows()
		
		if events == sg.WIN_CLOSED or events == 'NOT_SAVE':
			break

		elif events == 'SAVE':
			create_object()
			break
			
	save_window.close()

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def load_figure():
	img = f3_seismic.iline[line_number[il_or_xl]].T if il_or_xl == 'Inline' else f3_seismic.xline[line_number[il_or_xl]].T

	fig, ax = plt.subplots(figsize=(7, 7*0.65))
	ax.imshow(img, cmap='gray_r', aspect='auto', vmin=vmin, vmax=vmax)

	canvas = selection_window['CANVAS'].TKCanvas

	fig_agg = draw_figure(canvas, fig)

	return fig, ax, fig_agg

def delete_fig_agg():
    fig_agg.get_tk_widget().forget()
    plt.close('all')

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

def open_object():
	file = open(rf'{objects_path}/{facie_to_select}.obj', 'rb')
	object_file = pickle.load(file)
	file.close()

	return object_file

def create_object():
	
	file = open(f'{objects_path}/{facie_to_select}.obj', 'wb')
	pickle.dump(clicks, file)
	file.close()

	print(f'{facie_to_select}.obj successfully created!')
	print('='*40)

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

def zoom_factory(ax, base_scale = 2.):
    def zoom_fun(event):
    
        # get the current x and y limits
        cur_xmin = ax.get_xlim()[0]
        cur_xmax = ax.get_xlim()[1]
        cur_ymin = ax.get_ylim()[0]
        cur_ymax = ax.get_ylim()[1]
        
        xdata = event.xdata # get event x location
        ydata = event.ydata # get event y location
        
        cur_xrange_right = abs(cur_xmax - xdata)
        cur_xrange_left = abs(cur_xmin - xdata)
        cur_yrange_up = abs(cur_ymax - ydata)
        cur_yrange_down = abs(cur_ymin - ydata)
        
        if event.button == 'up':
            # deal with zoom in
            scale_factor = 1/base_scale
        elif event.button == 'down':
            # deal with zoom out
            scale_factor = base_scale
        else:
            # deal with something that should never happen
            scale_factor = 1
            print(event.button)
            
        # set new limits
        ax.set_xlim([xdata - cur_xrange_left * scale_factor,
                     xdata + cur_xrange_right * scale_factor])
        ax.set_ylim([ydata + cur_yrange_down * scale_factor,
                     ydata - cur_yrange_up * scale_factor])
        plt.draw() # force re-draw

    fig = ax.get_figure() # get the figure of interest
    # attach the call back
    fig.canvas.mpl_connect('scroll_event',zoom_fun)

    #return the function
    return zoom_fun

#cube_path = r"C:\Users\jpgom\Documents\Jão\VS_Code\IC\Seismic_data_w_null.sgy"
#cube_path = r'/home/gaia/jpedro/Seismic_data_w_null.sgy'
cube_path = '/mnt/hgfs/shared_folder/Seismic_data_w_null.sgy'

#objects_path = r"C:\Users\jpgom\Documents\Jão\git\facies_selector"
#objects_path = r"C:\Users\jpgom\Documents\Jão\git\facies_selector"
objects_path = r"/home/jpgomess/code/git/facies_selector"

actual_mode = 'Select'

f3_seismic = segyio.open(cube_path)
vmin = -4000
vmax = 4000

facies_list = get_facies_list(extension='.obj')

clicks = initial_clicks = []

config_window, selection_window, save_window = open_config_window(), None, None

while True:

	if selection_window != None:
		fig, ax, fig_agg = load_figure()
		load_points()
		cid = fig.canvas.mpl_connect('button_press_event', onclick)
		zoom = zoom_factory(ax, base_scale = 1.2)

	window, events, values = sg.read_all_windows()
	
	# EVENT LOOPS

	if window == config_window:
		if events == sg.WIN_CLOSED or events == 'END':
			break

		elif events == 'START':
			il_or_xl = values['LISTBOX_LINES'][0]
			
			facie_to_select = values['LISTBOX_FACIES'][0] if values['INPUT_FACIE'] == '' else values['INPUT_FACIE']
			print(facie_to_select)
			if facie_to_select not in facies_list:
				create_object()

			line_number = {'Inline': f3_seismic.ilines[0], 'Crossline': None} if il_or_xl == 'Inline' else {'Inline': None, 'Crossline': f3_seismic.xlines[0]}

			clicks, initial_clicks = open_object(), open_object()
			
			config_window.hide()
			selection_window = open_selection_window()
		
	elif window == selection_window:
		if events == sg.WIN_CLOSED or events == 'END':
			if clicks == initial_clicks:
				break
			else:
				selection_window.hide()
				save_window_loop()
				break
				
		elif events == 'UNDO':
			delete_fig_agg()
			
			if len(initial_clicks) > 0:
				initial_clicks.pop(-1)
			if len(clicks) > 0:
				clicks.pop(-1)
			else:
				print('Object is already empty...')
	
		elif events == 'NEXT':
			delete_fig_agg()

			line_number[il_or_xl] += int(values['STEP'])

			window['LINE_NUMBER'].update(f'Actual Line Number: {line_number[il_or_xl]}')

		elif events == 'PREV':
			delete_fig_agg()

			line_number[il_or_xl] -= int(values['STEP'])
			window['LINE_NUMBER'].update(f'Actual Line Number: {line_number[il_or_xl]}')

		elif events == 'CHANGE':
			selection_window.hide()
			selection_window = None
			
			facies_list = get_facies_list(extension='.obj')
			
			if clicks != initial_clicks:
				save_window_loop()
				
			clicks = initial_clicks = []
				
			config_window = open_config_window()

		elif events == 'MODE':
			delete_fig_agg()

			actual_mode = 'Select' if actual_mode == 'Delete' else 'Delete'
			window['MODE'].update(actual_mode)

window.close()

# -- FIM -- #
