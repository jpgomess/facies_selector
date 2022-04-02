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

def onclick(event):
    global facie_to_select
    global objects_path
    global full_inputs
    global actual_mode
    global il_or_xl
    global inputs

    x = int(event.xdata)
    y = int(event.ydata)

    print('| %s | Button=%d | xdata=%f | ydata=%f |' %
          ('Double' if event.dblclick else 'Single', event.button, x, y))

    if il_or_xl == 'Inline': #Inline
        global iline_number
        iline = iline_number
        xline = None

    else: #Crossline
        global xline_number
        iline = None
        xline = xline_number

    input_dict = {
        'inline': iline,
        'crossline': xline,
        'x': x,
        'y': y,
    }
    
    if actual_mode == 'selector':

        plt.scatter(x, y, marker='.', linewidth=2, color='r', alpha=0.5)
        fig.canvas.draw()

        inputs[facie_to_select] += [input_dict]
        full_inputs += [input_dict]
    else:
        df = pd.DataFrame()

        df['inline'] = [input['inline'] for input in full_inputs]
        df['crossline'] = [input['crossline'] for input in full_inputs]
        df['x'] = [input['x'] for input in full_inputs]
        df['y'] = [input['y'] for input in full_inputs]
        df['dist'] = np.sqrt((df['x'] - input_dict['x']) ** 2 + (df['y'] - input_dict['y']) ** 2)

        df_sorted = df.sort_values('dist')

        nearest_input = dict(df_sorted.iloc[0,:-1])

        if df_sorted['dist'].to_list()[0] <= 50:    
            full_inputs.remove(nearest_input)
            print('Nearest selection removed!')
        else:
            print('There are no selections nearby... Nothing happened...')

def onclick_rec(event):

    if keyboard.is_pressed('r'):
        global rectangles_coord1

        x = int(event.xdata)
        y = int(event.ydata)

        rectangles_coord1 += [(x, y)]

        plt.scatter(x, y, linewidth=2, color='b', alpha=0.5)
        fig.canvas.draw()

        print('| %s | Button=%d | xdata=%f | ydata=%f |' %
            ('Double' if event.dblclick else 'Single', event.button, x, y))
          
def onrelease_rec(event):

    if keyboard.is_pressed('r'):
        global rectangles_coord1

        x = int(event.xdata)
        y = int(event.ydata)

        print('| %s | Button=%d | xdata=%f | ydata=%f |' %
            ('Double' if event.dblclick else 'Single', event.button, x, y))

        if il_or_xl == 'Inline': #Inline
            global iline_number
            iline = iline_number
            xline = None

        else: #Crossline
            global xline_number
            iline = None
            xline = xline_number

        plt.scatter(x, y, linewidth=2, color='b', alpha=0.5)
        fig.canvas.draw()

        x1 = rectangles_coord1[-1][0]
        y1 = rectangles_coord1[-1][1]
        x2 = x
        y2 = y

        step = 40

        qty = 0
        for x in range(x1, x2, step):
            for y in range(y1, y2, step):
                qty += 1

                input_dict = {
                    'inline': iline,
                    'crossline': xline,
                    'x': x,
                    'y': y,
                }
                inputs[facie_to_select] += [input_dict]
                plt.scatter(x, y, linewidth=2, color='green', alpha=0.5)
                fig.canvas.draw()

        print(f'{qty} points selected!')

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

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def delete_fig_agg(fig_agg):
    fig_agg.get_tk_widget().forget()
    plt.close('all')

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
        [sg.Button('Undo', key='UNDO'), sg.Button('Next', key='NEXT'), sg.Button('Change Facies', key='CHANGE'), sg.Button('End', key='END'), sg.VSeparator(), sg.Text('Actual Mode (Select/Delete):'), sg.Button('Select', key='MODE')]
    ]
    window = sg.Window('Getting Inputs', layout, element_justification='center', finalize=True, location=(0,0))
    return window

def config_window_loop():
    while True:
        window, events, values = sg.read_all_windows()

        if events == 'START':
            il_or_xl = values['LISTBOX_LINES'][0]
            
            if values['INPUT_FACIE'] != '':
                facie_to_select = values['INPUT_FACIE']
                
            else:
                facie_to_select = values['LISTBOX_FACIES'][0]
                
            window.hide()
            selection_window = open_selection_window()
            break

        elif events == sg.WINDOW_CLOSED or events == 'END':
            selection_window, il_or_xl, facie_to_select = None, None, None
            print('Closing Program...')
            break

    return selection_window, il_or_xl, facie_to_select

def create_objects(objects_path, object, facie_to_select):
    path_to_save = rf'{objects_path}/{facie_to_select}.obj'
    #path_to_save = rf'{facie_to_select}.obj'

    file_inputs = open(path_to_save, 'wb')
    pickle.dump(object, file_inputs)
    file_inputs.close()

    print(f'{facie_to_select}.obj successfully created!')
    print('='*40)

def update_objects(objects_path, object, facie_to_select):
    path_to_save = rf'{objects_path}/{facie_to_select}.obj'
    #path_to_save = rf'{facie_to_select}.obj'
    file_to_append = open(path_to_save, 'rb')
    object_file = pickle.load(file_to_append)
    file_to_append.close()
    for click in object:
        object_file += [click]

    file_inputs = open(path_to_save, 'wb')
    pickle.dump(object_file, file_inputs)
    file_inputs.close()

    print(f'{facie_to_select}.obj successfully updated!')
    print('='*40)

def open_objects(objects_path, facie_to_select):
    file = open(rf'{objects_path}/{facie_to_select}.obj', 'rb')
    #file = open(rf'{facie_to_select}.obj', 'rb')
    object_file = pickle.load(file)
    file.close()

    return object_file

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

def save_object_window_loop(objects_path, inputs, facie_to_select):
    while True:
        window, events, values = sg.read_all_windows()

        if events == 'UPDATE':
            try:
                update_objects(objects_path, inputs[facie_to_select], facie_to_select)

                window.hide()
                break
            except:
                print(f'{facie_to_select}.obj does not exist...')
                print('-'*40)

        elif events == 'CREATE':
            create_objects(objects_path, inputs[facie_to_select], facie_to_select)

            window.hide()
            break

        elif events == sg.WINDOW_CLOSED:
            window.hide()
            break

    return 

def load_points(full_inputs, inputs, objects_path, facie_to_select, fig):
    try:
        object_file = open_objects(objects_path, facie_to_select)

        if il_or_xl == 'Inline':
            #x = [click['x'] for click in object_file if click['inline'] == iline_number]
            #x += [click['x'] for click in inputs[facie_to_select] if click['inline'] == iline_number]
            x = [click['x'] for click in full_inputs if click['inline'] == iline_number]

            #y = [click['y'] for click in object_file if click['inline'] == iline_number]
            #y += [click['y'] for click in inputs[facie_to_select] if click['inline'] == iline_number]
            y = [click['y'] for click in full_inputs if click['inline'] == iline_number]
        else:
            #x = [click['x'] for click in object_file if click['crossline'] == xline_number]
            #x += [click['x'] for click in inputs[facie_to_select] if click['crossline'] == xline_number]
            x = [click['x'] for click in full_inputs if click['crossline'] == xline_number]

            #y = [click['y'] for click in object_file if click['crossline'] == xline_number]
            #y += [click['y'] for click in inputs[facie_to_select] if click['crossline'] == xline_number]
            y = [click['y'] for click in full_inputs if click['crossline'] == xline_number]

        if facie_to_select == 'Fault':
            plt.scatter(x, y, marker='.', linewidth=2, color='r', alpha=0.5)
        elif facie_to_select == 'Non_Fault':
            plt.scatter(x, y, marker='.', linewidth=2, color='g', alpha=0.5)
        else:
            plt.scatter(x, y, marker='.', linewidth=2, color='yellow', alpha=0.5)

        fig.canvas.draw()

        print('-'*40)
        print('Previous points drew!')
        print('='*40)
    except Exception as e:
        print(e)
        print('-'*40)
        print(f"No previous points to draw... \n{facie_to_select}.obj does not exist or is empty...")
        print('='*40)

#cube_path = rf'/mnt/hgfs/shared_folder/Seismic_data_w_null.sgy'
#cube_path = rf'/home/gaia/jpedro/Seismic_data_w_null.sgy'
cube_path = rf"C:\Users\jpgom\Documents\Jão\VS_Code\IC\Seismic_data_w_null.sgy"
objects_path = os.getcwd()

actual_mode = 'selector'

f3_seismic = segyio.open(cube_path)
vmin = -4000
vmax = 4000

extension = '.obj'
list_dir = os.listdir(os.getcwd())
facies_list = [list_dir[i][:-len(extension)] for i in range(len(list_dir)) if list_dir[i].endswith(extension)]
facies_list.sort()

#inputs = dict()
#for facie in facies_list:
#    inputs[facie] = []

iline_number = f3_seismic.ilines[0]
xline_number = f3_seismic.xlines[0]

rectangles_coord1 = []

print(f3_seismic.xlines[-1], f3_seismic.ilines[-1])

config_window = open_config_window(facies_list)
selection_window = None
selection_window, il_or_xl, facie_to_select = config_window_loop()

inputs = {facie_to_select : []}
full_inputs = open_objects(objects_path, facie_to_select)

if facie_to_select not in facies_list:
	create_objects(objects_path, inputs[facie_to_select], facie_to_select)
	print(f'{facie_to_select}.obj does not exist... Therefore, {facie_to_select}.obj was created!')

while selection_window != None:

    print('='*40)
    print(f'Facies to select: {facie_to_select}')

    if il_or_xl == 'Inline': #Inline
        print(f'Actual Inline number: {iline_number}')
        img = f3_seismic.iline[iline_number]
    else: #Crossline
        print(f'Actual Crossline number: {xline_number}')
        img = f3_seismic.xline[xline_number]

    img = img.T

    fig, ax = plt.subplots(figsize=(7, 7*0.65))
    ax.imshow(img, cmap='gray_r', aspect='auto', vmin=vmin, vmax=vmax)

    zoom = zoom_factory(ax, base_scale = 1.2)

    load_points(full_inputs, inputs, objects_path, facie_to_select, fig)

    canvas = selection_window['CANVAS'].TKCanvas
    cursor = Cursor(ax, horizOn=True, vertOn=True, useblit=True, color='r', linewidth=1)
    cid = fig.canvas.mpl_connect('button_press_event', onclick)

    if facie_to_select == 'Non_Fault':
        cid = fig.canvas.mpl_connect('button_press_event', onclick_rec)
        cid = fig.canvas.mpl_connect('button_release_event', onrelease_rec)

    fig_agg = draw_figure(canvas, fig)

    # LOAD WINDOWS
    window, events, values = sg.read_all_windows()

    if events == 'button_press_event':
        delete_fig_agg(fig_agg)

    if events == 'MODE':
        delete_fig_agg(fig_agg)

        if actual_mode == 'selector':
            window['MODE'].Update('Delete')
            actual_mode = 'eraser'
        else:
            window['MODE'].Update('Select')
            actual_mode = 'selector'

    if events == 'UNDO':
        delete_fig_agg(fig_agg)

        full_inputs.pop(-1)
        print('Last point was deleted!')

    elif events == 'NEXT':
        delete_fig_agg(fig_agg)

        if il_or_xl == 'Inline':
            if iline_number == f3_seismic.ilines[-1]:
                il_or_xl = 'Crossline'
            iline_number += 50
            if iline_number > f3_seismic.ilines[-1]:
                iline_number = f3_seismic.ilines[-1]
        else:
            if xline_number == f3_seismic.xlines[-1]:
                il_or_xl = 'Inline'
            xline_number += 50
            if xline_number > f3_seismic.xlines[-1]:
                xline_number = f3_seismic.xlines[-1]

    elif iline_number == f3_seismic.ilines[-1] and xline_number == f3_seismic.xlines[-1]:
        print(f'All Crosslines and Inlines were analysed.\nFacies: {facie_to_select}.')
        events = 'CHANGE'

    elif events == 'CHANGE':
        selection_window.close()

        save_object_window = open_save_object_window()
        save_object_window_loop(objects_path, inputs, facie_to_select)

        config_window.un_hide()
        selection_window, il_or_xl, facie_to_select = config_window_loop()
        iline_number = f3_seismic.ilines[0]
        xline_number = f3_seismic.xlines[0]

    elif events == sg.WINDOW_CLOSED or events == 'END':
        selection_window.close()

        save_object_window = open_save_object_window()
        save_object_window_loop(objects_path, inputs, facie_to_select)

        print('Closing Program...')
        print('='*40)
        break

# -- FIM -- #
