
import sim_base as sim_g
import nowo1_base as nowo
import datetime as dt
import pandas as pd
import numpy as np
import ipywidgets as widgets
from IPython.display import display


class binary_node(nowo.sim_base):
    def __init__(self, name: str, 
                init_methode :  str = 'normal', **kwargs):
        kwargs.update({'ch_type' : nowo.gate_general})   
        super().__init__(name, init_methode, **kwargs)
        self.Gate_A = nowo.gate_general('Gate_A', self)
        self.Gate_B = nowo.gate_general('Gate_B', self)
        self.Gate_C = nowo.gate_general('Gate_C', self)

        self.A_ratio = nowo.sim_value('A_ratio', self, (float, int,)) 
        self.B_ratio = nowo.sim_value('B_ratio', self, (float, int,)) 
        self.A_portion = nowo.sim_value('A_portion', self, (float, int,)) 
        self.B_portion = nowo.sim_value('B_portion', self, (float, int,)) 
        
        #self.Info = nowo.sim_value('Info', self, (str,)) 

        self.calcflag : bool = True
        self._value_key : np.byte = 0b00000000
        
    
        self._checkstruct : dict = dict(
            {'one_val' : [0,1,2,4,8,16,32,64]}
        )

        self._value_keys : dict = {
            'A' :       0b01000000,
            'B' :       0b00100000,
            'C':      0b00010000,
            'A_ratio':  0b00001000,
            'B_ratio':  0b00000100,
            'A_portion':0b00000010,
            'B_portion':0b00000001
        }

        self._funcgate.update({
                self.Calc_A : self.Gate_A,
                self.Calc_B : self.Gate_B,
                self.Calc_C : self.Gate_C
                })


    def _sync_fullname(self):
        self.Gate_A.general._get_fullname()
        self.Gate_B.general._get_fullname()
        self.Gate_C.general._get_fullname()
        self.A_ratio._get_fullname()
        self.B_ratio._get_fullname()
        self.A_portion._get_fullname()
        self.B_portion._get_fullname()
        super()._sync_fullname()
      


    def _create_gui(self):
       # if self._GUI_is_create: return
        options =[
            (self.Gate_A.alias_name + '.' + self.Gate_A.general.alias_name, 'A'),
            (self.Gate_B.alias_name + '.' + self.Gate_B.general.alias_name, 'B'),
            (self.Gate_C.alias_name + '.' + self.Gate_C.general.alias_name, 'C'),
            (self.A_ratio.alias_name, 'A_ratio'),
            (self.B_ratio.alias_name, 'B_ratio'),
            (self.A_portion.alias_name, 'A_portion'),
            (self.B_portion.alias_name, 'B_portion'),
            ]


        layout_select = widgets.Layout()
        layout_valbox = widgets.Layout(padding = '1em 0  0  0')
        style_label = widgets.Layout(width = '100px')

        val_label_1 = widgets.HTML(
            value='extensive Größe:',
            layout = style_label
        )

        val_select_1 = widgets.Dropdown(options = options[:3], 
            value='A',  
            layout = layout_select
        )

        value_1 = widgets.FloatText(value = 1.0)
        val1_box = widgets.HBox([val_label_1, widgets.VBox([val_select_1, value_1])])


        val_label_2 = widgets.HTML(
            value='extensive oder <br> intensive Größe',
            layout = style_label
        )
        val_select_2 = widgets.Dropdown(options = options, 
            value='B', 
            layout = layout_select) 
        value_2 = widgets.FloatText(value = 1.0)    
        
       
        val2_box = widgets.HBox([val_label_2, widgets.VBox([val_select_2, value_2])], layout = layout_valbox)
      
        self._GUI_itemlist.update({
            'val_select_1' : val_select_1,
            'value_1' : value_1,
            'val_select_2' : val_select_2,
            'value_2' : value_2,
        })
        super()._create_gui()# Attention! --must-- because the widget get a parent attr.
        
        self.total_box.children = (val1_box, val2_box, *self.total_box.children)
        self.total_box.layout.width = '60%'
     


    def  Init_By_GUI(self):
      
        super().Init_By_GUI()
        para = {
           self._GUI_itemlist['val_select_1'].value :  self._GUI_itemlist['value_1'].value,
           self._GUI_itemlist['val_select_2'].value :  self._GUI_itemlist['value_2'].value
        }
     
        self.Init(**para)
        
    

    def Init(self, 
            A = np.nan,
            B = np.nan,
            C = np.nan,
            A_ratio = np.nan,
            B_ratio = np.nan,
            A_portion = np.nan,
            B_portion = np.nan,
        ):
       
        super().Init(para_from_Init = locals())
        self._value_key  = 0b00000000
        self.Gate_A.general.Init(A)
        self.Gate_B.general.Init(B)
        self.Gate_C.general.Init(C)
        self.A_ratio.Init(A_ratio)
        self.B_ratio.Init(B_ratio)
        self.A_portion.Init(A_portion)
        self.B_portion.Init(B_portion)
        #self.Info.Init('kein Kommentar')
        #self.Info._value = 'Oh mann'


    def _set_values(self):
       if not self._korr_key & 0b01000000: self.A = np.nan
       if not self._korr_key & 0b00100000: self.B = np.nan
       if not self._korr_key & 0b00010000: self.C = np.nan
       if not self._korr_key & 0b00001000: self.A_ratio = np.nan
       if not self._korr_key & 0b00000100: self.B_ratio = np.nan
       if not self._korr_key & 0b00000010: self.A_portion = np.nan
       if not self._korr_key & 0b00000001: self.B_portion = np.nan


    # es muss mindestens ein  A oder B oder C vorhanden sein aber nicht mehr wie zwei
    def _check_values(self, stepper : nowo.step_base):
        # Build zahl bei values 
        count : int = 0
        if not np.isnan(self.Gate_A.general.get_set(stepper)): 
            self._value_key = self._value_key   |self._value_keys['A']
            count = count + 1
        if not np.isnan(self.Gate_B.general.get_set(stepper)): 
            self._value_key = self._value_key   |self._value_keys['B']
            count = count + 1
        if not np.isnan(self.Gate_C.general.get_set(stepper)): 
            self._value_key = self._value_key   |self._value_keys['C']
            count = count + 1
        if not np.isnan(self.A_ratio.get_set(stepper)): 
            self._value_key = self._value_key   |self._value_keys['A_ratio']
            count = count + 1
        if not np.isnan(self.B_ratio.get_set(stepper)):
             self._value_key = self._value_key  |self._value_keys['B_ratio']
             count = count + 1
        if not np.isnan(self.A_portion.get_set(stepper)): 
            self._value_key = self._value_key   |self._value_keys['A_portion']
            count = count + 1
        if not np.isnan(self.B_portion.get_set(stepper)): 
            self._value_key = self._value_key   |self._value_keys['B_portion']
            count = count + 1

        if count < 2: 
           # self.Info._value = 'Es müssen mind. 2 unterschiedliche Werte angeben werden'
            return False
        elif count > 2:
           # self.Info._value = 'Es dürfen nicht mehr als 2 unterschiedliche Werte angeben werden'
            return False
         
        # Abfrage ob wenigstens eine Masse vorhanden ist
        if self._value_key < 16:
          #  self.Info._value = 'Es muss min. ein Strom (A, B oder C) angegeben werden'
            return False
        
        return True


    def Calc_A(self,  stepper : nowo.step_base, Gate_In: nowo.gate_general):
        self._calc(stepper, Gate_In)
        return self.Gate_A


    def Calc_B(self,  stepper : nowo.step_base, Gate_In: nowo.gate_general):
        self._calc(stepper, Gate_In)
        return self.Gate_B


    def Calc_C(self,  stepper : nowo.step_base, Gate_In: nowo.gate_general):
        self._calc(stepper, Gate_In)
        return self.Gate_C


    def _calc(self,  stepper : nowo.step_base, Gate_In: nowo.gate_general):
        if not self._check_values(stepper): return
        self.calcflag =  True
        while self.calcflag:
            self.calcflag = False
            self._calc_A_ratio()
            self._calc_B_ratio()
            self._calc_A_portion()
            self._calc_B_portion()
            self._calc_A()
            self._calc_B()  
            self._calc_C()        
          

    def _set_calcflag(self, flag):
        if not self.calcflag:
            self.calcflag = flag



    def _calc_A_ratio(self):
        if self._value_keys['A_ratio'] & self._value_key:
            self._set_calcflag(False)
            return
        
        try:
            if self._value_keys['A_portion'] & self._value_key:
                self.A_ratio._value = 1/(1/self.A_portion._value -1)  

            elif self._value_keys['B_ratio'] & self._value_key:
                self.A_ratio._value = 1/self.B_ratio._value  

            elif  self._value_keys['A'] & self._value_key and self._value_keys['B'] & self._value_key:     
                self.A_ratio._value = self.Gate_A.general._value / self.Gate_B.general._value  
            
            elif  self._value_keys['C'] & self._value_key and self._value_keys['A'] & self._value_key:
                self.A_ratio._value = self.Gate_A.general._value / (self.Gate_C.general._value - self.Gate_A.general._value)
            
            elif  self._value_keys['C'] & self._value_key and  self._value_keys['B'] & self._value_key:
                self.A_ratio._value = (self.Gate_C.general._value - self.Gate_B.general._value) / self.B
            
            else: 
                self._set_calcflag(False)
                return  
            self._set_calcflag(True)
            self._value_key = self._value_key |  self._value_keys['A_ratio'] 
        except ZeroDivisionError as error:
            pass
        except Exception as exception:
            pass



    def _calc_A_portion(self):
        if self._value_keys['A_portion'] & self._value_key: 
            self._set_calcflag(False)
            return
        try:
            if self._value_keys['A_ratio'] & self._value_key:
                self.A_portion._value = 1/(1/self.A_ratio._value +1)
            else: 
                self._set_calcflag(False)  
                return  
            self._set_calcflag(True)
            self._value_key = self._value_key |  self._value_keys['A_portion']   
        
        except ZeroDivisionError as error:
            pass
        except Exception as exception:
            pass



    def _calc_B_portion(self):
        if self._value_keys['B_portion'] & self._value_key: 
            self._set_calcflag(False)
            return
        
        try:
            if self._value_keys['B_ratio'] & self._value_key:
                self.B_portion._value = 1/(1/self.B_ratio._value +1)
                
            else: 
                self._set_calcflag(False)
                return    
            self._set_calcflag(True)
            self._value_key = self._value_key |  self._value_keys['B_portion'] 

        except ZeroDivisionError as error:
            pass
        except Exception as exception:
            pass
        
    

    def _calc_B_ratio(self):
        if self._value_keys['B_ratio'] & self._value_key:
            self._set_calcflag(False)
            return
        try:
            if self._value_keys['A_ratio'] & self._value_key:
                self.B_ratio._value = 1/self.A_ratio._value  
                
            elif self._value_keys['B_portion'] & self._value_key:
                self.B_ratio._value = 1/(1/self.B_portion._value -1)
                
            elif self._value_keys['A'] & self._value_key and self._value_keys['B'] & self._value_key:
                self.B_ratio._value = self.Gate_B.general._value / self.Gate_A.general._value
                
            elif self._value_keys['C'] & self._value_key and self._value_keys['B'] & self._value_key:
                self.B_ratio._value = self.Gate_B.general._value / (self.Gate_C.general._value - self.Gate_B.general._value)
                
            elif self._value_keys['C'] & self._value_key and self._value_keys['A'] & self._value_key:
                self.B_ratio._value = (self.Gate_C.general._value - self.Gate_A.general._value) / self.Gate_A.general._value
            else: 
                self._set_calcflag(False)
                return   
            self._set_calcflag(True)
            self._value_key = self._value_key |  self._value_keys['B_ratio'] 

        except ZeroDivisionError as error:
            pass
        except Exception as exception:
            pass



    def _calc_A(self):
        if self._value_keys['A'] & self._value_key: 
            self._set_calcflag(False)
            return

        try:
            if self._value_keys['C'] & self._value_key and self._value_keys['B'] & self._value_key:
                self.Gate_A.general._value = (self.Gate_C.general._value - self.Gate_B.general._value)
                
            elif self._value_keys['C'] & self._value_key and self._value_keys['A_portion'] & self._value_key:
                self.Gate_A.general._value = (self.Gate_C.general._value * self.A_portion._value)
                
            elif self._value_keys['C'] & self._value_key and self._value_keys['A_ratio'] & self._value_key:
                self.Gate_A.general._value = (self.Gate_C.general._value * self.A_portion._value)
                
            elif self._value_keys['B'] & self._value_key and self._value_keys['A_ratio'] & self._value_key:
                self.Gate_A.general._value = (self.Gate_B.general._value * self.A_ratio._value)
                
            else: 
                self._set_calcflag(False)
                return    
            self._set_calcflag(True)
            self._value_key = self._value_key |  self._value_keys['A'] 

        except ZeroDivisionError as error:
            pass
        except Exception as exception:
            pass

        
                                
    def _calc_B(self):
        if self._value_keys['B'] & self._value_key:#
            self._set_calcflag(False)
            return
        
        try:
            if self._value_keys['C'] & self._value_key and self._value_keys['A'] & self._value_key:
                self.Gate_B.general._value = (self.Gate_C.general._value - self.Gate_A.general._value)  
            elif self._value_keys['C'] & self._value_key and self._value_keys['B_portion'] & self._value_key:
                self.Gate_B.general._value = (self.Gate_C.general._value * self.B_portion._value)
            elif self._value_keys['A'] & self._value_key and self._value_keys['B_ratio'] & self._value_key:
                self.Gate_B.general._value = (self.Gate_A.general._value * self.B_ratio._value)
                
            else: 
                self._set_calcflag(False)
                return   
            self._set_calcflag(True)
            self._value_key = self._value_key |  self._value_keys['B'] 

        except ZeroDivisionError as error:
            pass
        except Exception as exception:
            pass

    

        
    def _calc_C(self):
        if self._value_keys['C'] & self._value_key:
            self._set_calcflag(False)
            return
        
        if self._value_keys['A'] & self._value_key and self._value_keys['B'] & self._value_key:
            self.Gate_C.general._value = (self.Gate_A.general._value + self.Gate_B.general._value)
            self._set_calcflag(True)
            self._value_key = self._value_key |  self._value_keys['C'] 
            return
        self._set_calcflag(False)    
    

    def _reset(self):
        self.Gate_A._reset()
        self.Gate_B._reset()
        self.Gate_C._reset()
        super()._reset()

    
    def _node_success(self, stepper: nowo.step_base):
        self.Gate_A._node_success(stepper)
        self.Gate_B._node_success(stepper)
        self.Gate_C._node_success(stepper)
        self.A_ratio._node_success(stepper)
        self.B_ratio._node_success(stepper)
        self.A_portion._node_success(stepper)
        self.B_portion._node_success(stepper)
       # self.Info._node_success(stepper)