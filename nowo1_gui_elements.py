import sim_base as sim_g
import nowo1_base as nowo

import ipywidgets as widgets
from IPython.display import display
import base64


# Download BUTTONS

class Download_Button_csv():
    def __init__(self, csv_filename = 'daten.csv') -> None:
        self.button  = widgets.HTML()
        self.csv_text : str = 'empty'
        self.csv_filename = csv_filename 
        self.payload : str = ''
        self.html_button = '''
        
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <a download="{filename}" href="data:text/csv;base64,{payload}" download>
                <button class="p-Widget jupyter-widgets jupyter-button widget-button ">Download File</button>
            </a>
        </body>
    </html>
    ''' 
        self.set_button()
        self.csv_filename = 'daten.csv'

    def _payload(self):
        b64 = base64.b64encode(self.csv_text.encode())
        self.payload = b64.decode() 


    def set_button(self, csv_text='empty'):
        self.csv_text = csv_text
        self._payload()
        html_str = self.html_button.format(payload=self.payload,filename=self.csv_filename)
        self.button.value = html_str


