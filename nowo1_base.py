import sys
import sim_base as sim_g
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
from typing import Any, Callable, List, Type
import math
import numpy as np
import ipywidgets as widgets
from IPython.display import display



Main_Modul = sys.modules['__main__']
Self_Modulname = globals()['__name__']
Self_Modul = sys.modules[Self_Modulname]


def get_attr_rek(names, start_obj=Main_Modul):
    """get attr / obj by list or str.

Keyword arguments:
names -- as str or list (example: 'obj.attr1.attr2'  or ['obj', 'attr1', 'attr2'])
start_obj -- obj where to search
"""
    if isinstance(names, str):
        name_list = names.split('.')
    elif isinstance(names, list):
        name_list = names
    else:
        return None

    obj = start_obj
    for name in name_list:
        if hasattr(obj, name):
            obj = getattr(obj, name)
        else:
            return None
    return obj


def analyse_func_old(func_to_analyse, sim_obj):
    if isinstance(func_to_analyse, str):
        func_name = func_to_analyse
        func = get_attr_rek(func_to_analyse)
        if not func: return None
        sim_obj = func.__self__

    elif callable(func_to_analyse):
        func = func_to_analyse
        func_name = func.__name__
        if hasattr(func, '__self__'):
            sim_obj = func.__self__ 
            func_name = sim_obj.name + '.' + func_name
        else:
            setattr(sim_obj, func_name, func)
        func_name = sim_obj.name + '.' + func_name
    else: return None

    return [sim_obj, func, func_name]


def analyse_func(func):
    if isinstance(func, str):
        func_name = func
        func = get_attr_rek(func)
        if not func: return None

    if callable(func):
        func_name = func.__name__
        sim_obj = None
        if hasattr(func, '__self__'):
            sim_obj = func.__self__ 
            func_name = sim_obj.name + '.' + func_name
        
    else: return None

    return [sim_obj, func, func_name]



class sim_value():
    def __init__(self, name: str, parent, value_type ):
        self.name = name
        self._parent = parent
        self._simparent =  getattr(self._parent, 'sim_parent', self._parent)
        if not self._simparent: self._simparent = self._parent
        value_type_list = list(value_type)
        value_type_list.append(type(None))
        self.value_type = tuple(value_type_list)
        self._value = None
        self._default_value = None
        self.unit = ''

        self.set = self._set # Überschreibbar durch callback funktion
        self.call_extern = None
        self.call_intern = None
        self._fullname = self._get_fullname()
        self._loggerlist : set = set()
        

    def _get_fullname(self):
        namelist = []
        if not self._simparent == self._parent:
            namelist.append(self._simparent.name)
        namelist.append(self._parent.name)
        namelist.append(self.name)
        return '.'.join(namelist)

    #TODO typen überprüfen
    def _set(self,  value):
        if not isinstance(value, self.value_type): raise Exception('ungültiger typ')
        self._value = value
        return self._value

    # Wird geändert über value erfolgt kein callback zugriff es wird nur
    #_value geändert oder zurückgegeben
    @property
    def value(self):
        return self._value


    @value.setter
    def value(self, value):
        if not isinstance(value, self.value_type): raise Exception('ungültiger typ')
        self._value = value   
    

    @property
    def default_value(self):
        return self._default_value


    @default_value.setter
    def default_value(self, value):
        self._default_value = value
        self._value = self._default_value 


    def get_set(self, stepper=None, value=None):
        if self.call_extern:
            self._value = self.call_extern(self, value, stepper) 
        elif self.call_intern:
            self._value = self.call_intern(value, stepper) 
        return self._value


   
    #TODO Warum Any würde hier nicht auch ein None genügen?
    def Init(self, value = Any, default = Any, unit = ''):
        #self._loggerlist : set = set()
        self.unit = unit
        self._default_value = default
        if isinstance(value, str): 
            value = get_attr_rek(value)
        if isinstance(value, Callable):
            if hasattr(value, '__self__') and (value.__self__ == self._simparent):
                self.call_intern = value
            else: self.call_extern = value
            self._value = self._default_value
            return
        elif isinstance(value, type(None)):
            self._value = value
            self.set = self._set
        elif isinstance(value, self.value_type):
            self._value = self.value_type[0](value)
            self.set = self._set
        return 

    
    def _add_logger(self, logger):
        self._simparent._add_logger(logger)
        self._loggerlist.add(logger)
        return self._fullname


    def _del_logger(self, logger):
        self._simparent._del_logger(logger)


    def _node_success(self, stepper):
        for logger in self._loggerlist:
            logger._add_value(self._fullname, self._value)


#-------------------------------------------------------------------
class gate_base:
    def __init__(self, name, sim_parent):
        self.name = name
        self.sim_parent = sim_parent
        self._success_flag : bool = True
       
    def set(self, value: Any, value_name: str = ''):pass
        
    def get(self, value_name: str = ''):pass
        
    def Init(self, values):pass
        
    def _reset(self): 
        self._success_flag : bool = True

    def _node_success(self, stepper): pass

    def log_all(self, logger):
        name_list = []
        for key, value in self.__dict__.items():
            if issubclass(type(value), sim_value):
                name_list.append(value._add_logger(logger))
        return name_list
         

#-------------------------------------------------------------------
class gate_time(gate_base):
    def __init__(self, name,  sim_parent):
        super().__init__(name,  sim_parent)
        self.time = sim_value('time', self, (dt.datetime,))

    def _node_success(self, timer):
        self.time._node_success(timer)  

    def _reset(self):
        super()._reset()
        self.time.set(dt.datetime(1, 1, 1, 0, 0, 0))

    def set(self, value):
        if isinstance(value, dt.datetime):
            self.time.value = value

    def get(self, value_name: str = ''):
        if not value_name:
            return self.time.value
        elif value_name == 'time':
            return self.time.value


#-------------------------------------------------------------------
class gate_general(gate_base):
    def __init__(self, name, sim_parent):
        super().__init__(name, sim_parent)
        self.general = sim_value('general', self, (float, int,))
        
       # self.time_factor = 0.0
        
       
    def _reset(self):
        super()._reset()
        #self.general.set(np.nan)
       

    def set(self, value):
        if isinstance(value, (float, int)):
            self.general.set(float(value))
        elif isinstance(value, type(self)):
            self.general.set(value.general.value)


    def get(self, value_name: str = ''):
        if not value_name:
            return self.general.value
        elif value_name == 'general':
            return self.general.value
    

    def _node_success(self, stepper): 
        if not self._success_flag: return
        self.general._node_success(stepper)
        self._success_flag = False


#-------------------------------------------------------------------
class gate_dynamic(gate_base):
    def __init__(self, name, sim_parent):
        super().__init__(name, sim_parent)
        self.Dyn_Values : dict = dict()
        

    def Init(self, values):
        super().Init(values)
        if not isinstance(values, dict): raise Exception('das ist kein Dictionary')
        for key, value in values.items():
            base_val = sim_value(key, self, value['type'])
            base_val.Init(value['value'], value['default'], value['unit'])
            self.Dyn_Values.update({key : base_val})
            setattr(self,key,base_val)


    def _reset(self):
        super()._reset()
        for val in self.Dyn_Values.values():
            val._value = val._default_value
       
      
    def set(self, value, value_name):
        if not isinstance(value_name, str): 
            raise Exception('Name nich korrekt')
        if not value_name in self.Dyn_Values.keys():
            raise Exception('Name nich korrekt')
        
        val = self.Dyn_Values[value_name]

        if not isinstance(value, val.value_type):
            raise Exception('Falscher typ')
        val.set(value)
        


    def get(self, value_name: str = ''):
        if not isinstance(value_name, str): 
            raise Exception('Name nich korrekt')
        if not value_name in self.Dyn_Values.keys():
            raise Exception('Name nich korrekt')
        
        return self.Dyn_Values[value_name]._value


    def _node_success(self, timer): 
        if not self._success_flag: return
        for val in self.Dyn_Values.values():
            val._value = val._node_success(timer)
        self._success_flag = False


    def _actual_values(self, timer):
        for val in self.Dyn_Values.values():
            val.get_set(timer)


class gate_dataframe(gate_base):
    def __init__(self, name, sim_parent):
        super().__init__(name, sim_parent)
        self.dataframe = sim_value('dataframe', self, (pd.DataFrame,))
    
       
    def _reset(self):
        super()._reset()
        #self.dataframe.set(0.0)


    def _add_logger(self, logger):
        super()._add_logger(logger)  


    def set(self, value):
        if isinstance(value, (float, int)):
            self.dataframe.set(float(value))
        elif isinstance(value, type(self)):
            self.dataframe.set(value.dataframe.value)


    def get(self, value_name: str = ''):
        if not value_name:
            return self.dataframe.value
        elif value_name == 'dataframe':
            return self.dataframe.value
    

    def _node_success(self, stepper): 
        if not self._success_flag: return
        self.dataframe._node_success(stepper)
        self._success_flag = False



#*****************************************************************
class step_base():
    def __init__(self, name : str,  GUI : bool = False):
        self.name = name
        self.step_nr: int = 0
        self.total_steps: int = 0
        self.work_objs = [ ] # Diese Objekte sind mit dem Timer verknüpft
        self.sim_funcs : dict = {}# Ersetzt self.work_objs und self.work_funcs
        self._loggerlist : set = set() 
        
        self._GUI_visible = GUI
        self._GUI_itemlist : dict = dict()
        self.GUI_Item =  self._create_gui()
        self._GUI_is_visible = False

        self.info = widgets.Output()



    def on_start_clicked(self, args):
        parent = args.parent
        parent.reset()
        #with self.info:
          #  print('Hier')
       
        # for obj in parent.work_objs:
        #     if obj._GUI_is_visible:
        #         obj.Init_Over_GUI()
        parent.work()
      

    def Show_GUI(self):
        for obj in self.work_objs:
            if obj._GUI_visible:
                obj.Show_GUI()
        if self.GUI_Item:
            self._GUI_is_visible = True
            display(self.GUI_Item, self.info)
            #with self.info:
            #    print('Na dann wollen wir mal')    


    def _create_gui(self):
        for widget in self._GUI_itemlist.values():
            setattr(widget, 'parent', self)
        return None
     

    def reset(self):
        self.step_nr = 0
        


    def Init(self, work_objs : list = []):
        self.step_nr = 0
        if not work_objs: raise Exception(f'obj : {self.name} |wenigstens eine start Methode muss angeben werden!')
        self.work_objs = [] # Diese Objekte sind mit dem Timer verknüpft
        
        for func_to_analyse in work_objs:
            func_info = analyse_func(func_to_analyse)
            if not func_info:raise Exception(f'obj : {self.name} Startfunktion nicht korrekt')
            if not isinstance(func_info[0], work_base):raise Exception(f'obj : {self.name} |node ist kein Type von work_base')
            self.work_objs.append(func_info[0])
            if not callable(func_info[1]): raise Exception(f'obj : {self.name} |node hat keine func_work methode')
            gate = func_info[0].ch_type('Timer_Summe', self)
            gate.set(0.0)
            self.sim_funcs.update(
                {func_info[1] : {
                    'obj' : func_info[0],
                    'gate' : gate}})
 

    def work(self):
        for obj in self.work_objs:
            if obj._GUI_is_visible:
                obj.Init_Over_GUI()

        for obj in self.work_objs:
            obj.ready_for_start(self)
        for logger in self._loggerlist:
            logger.ready_for_start(self)

        if self._GUI_visible: pass 
        while self.step() == 1:
            self._node_success()
            
        for obj in self.work_objs:
            obj.ready_for_end()

        for logger in self._loggerlist:
            logger.ready_for_end()
         

    def step(self):
        for obj in self.work_objs:
                obj._reset() #Todo ist das immer erforderlich?
           
        for func, values in self.sim_funcs.items():
            func(stepper = self, Gate_In = values['gate'])
            values['obj']._node_success(stepper = self)

        self.step_nr = self.step_nr + 1


    def _add_logger(self, logger):
        if isinstance(logger, set):
            self._loggerlist.update(logger)
        elif isinstance(logger, port_base):
            self._loggerlist.add(logger)


    def _del_logger(self, logger):
        self._loggerlist.remove(logger)


    def _node_success(self): pass 


class step_range(step_base):
    def __init__(self, name : str,  GUI : bool = False):
        super().__init__(name, GUI)
        self.total_steps = sim_value('total_steps', self, (float, int,)) 
        self.Gate_Step: gate_general = gate_general( 'Gate_Step', self)


    def Init(self, 
            work_objs : list = [],
            total_steps  = 1
            ):

        super().Init(work_objs=work_objs)
        self.total_steps.Init(total_steps, 1)
        self.step_nr = 0
       

    def _create_gui(self):
        
        start_button = widgets.Button(description='Calc')  
        start_button.on_click(self.on_start_clicked)
        total_box = widgets.VBox([start_button])

        self._GUI_itemlist.update({
            'start_button' : start_button
        })
        super()._create_gui()# Attention! --must-- because the widget get a parent attr.
        return  total_box
     



    # ergebnis 1 ein step
    # 0 kein step 
    def step(self):
        if self.step_nr <= self.total_steps.get_set(self):
            self.Gate_Step.set(self.step_nr)
            super().step()
            return 1
        else: return 0
        

    def _node_success(self): 
        super()._node_success()
        self.Gate_Step._node_success(self)



class step_single(step_base):
    def __init__(self, name : str,  GUI : bool = False):
        super().__init__(name, GUI)
        
        
    def Init(self,  work_objs : list = []):
        super().Init(work_objs=work_objs)
        self.step_nr = 0


    # Später im Parent
    def _create_gui(self):
        start_button = widgets.Button(description='Calc')  
        start_button.on_click(self.on_start_clicked)
        total_box = widgets.VBox([start_button])

        self._GUI_itemlist.update({
            'start_button' : start_button
        })
      
        super()._create_gui()# Attention! --must-- because the widget get a parent attr.
        return  total_box
     

    def step(self):
        if self.step_nr < 1:
            super().step()
            return 1
        else: return 0
        

# ------------------------------------------------------------------
class step_timer(step_base):
    def __init__(self, name : str,  GUI : bool = False):
        super().__init__(name, GUI)

        self.abs_start = dt.datetime(1, 1, 1, 0, 0, 0)
        self.start: dt.datetime = dt.datetime(1, 1, 1, 0, 0, 0)
        self.ende: dt.datetime = dt.datetime(1, 1, 1, 1, 0, 0)
        self.actual: dt.datetime = self.start
        self.step_width: str = 's'
        self.step_count: int = 0
        self.total_sec: int = 0
        self._max_sec: int = 0 
        self._step_sec : int = 0
        self.step_props = dict(s=1, m=60, h=3600, d=86400, m15=900)

        self.Gate_Time: gate_time = gate_time( 'Gate_Time', self)
           
        self.factor : float = self.step_props[self.step_width] / 3600.0 
       
              
    def Init(self, 
            work_objs : list = [],
            start = '0001-01-01 00:00:00',
            ende = '0001-01-01 01:00:00',
            stepwidth = 's'
            ):
        
        super().Init(work_objs=work_objs)
 
        self.start = dt.datetime.strptime(start, sim_g.timepattern)
        self.ende = dt.datetime.strptime(ende, sim_g.timepattern)
        if not self.start < self.ende: raise Exception('ende vor start')
        
        self.step_width = stepwidth
        if not self.step_width in self.step_props.keys():raise Exception('step_width nicht bekannt (s,m,h,d, m15)')    

        self.actual = self.start
        self._step_sec = self.step_props[self.step_width]
        self.Gate_Time.set(self.actual) 
        self.total_sec = 0
        self._max_sec = int((self.start - self.abs_start).total_seconds())
    
        self.total_steps = int(self._max_sec /self.step_props[self.step_width])
        self.factor : float = self.step_props[self.step_width] / 3600.0 

    # ergebnis 1 ein step
    # 0 kein step act_time < self.start
    # -1 kein step act_time > self.ende
    def step(self):
        relation_time = self.actual
        if relation_time < self.start: return 0
        
        if (relation_time >= self.start) and (relation_time < self.ende):
            # Mache einen step
            self.total_sec = self.total_sec + self.step_props[self.step_width]
            self.actual = self.actual + \
                dt.timedelta(seconds=self.step_props[self.step_width])
            self.Gate_Time.time.set(self.actual)
            super().step()
            return 1

        if self.actual >= self.ende: return -1
            


    def _node_success(self):
        super()._node_success()
        self.Gate_Time._node_success(self)
    


#*****************************************************************
class work_base():
    def __init__(self, name: str, GUI : bool = False, **kwargs):
        
        self.name = name
        self._ctrl_ok : bool = False
        
        self._GUI_visible = GUI
        self._GUI_itemlist : dict = dict()
        self.GUI_Item =  None
        self._GUI_is_visible = False

        self.info = widgets.Output()
   
    def Init(self): pass
       
    def ready_for_start(self, timer: step_timer): pass
       
    def ready_for_end(self):pass


    def _create_gui(self):
        for widget in self._GUI_itemlist.values():
            setattr(self, 'parent', widget)
        return None
     

    def Show_GUI(self):
        #display(self.info)
        if not self.GUI_Item:
            self.GUI_Item =  self._create_gui()
        self._GUI_is_visible = True
        display(self.GUI_Item)


class gui_base(work_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        super().__init__(name, GUI, **kwargs)
       

    def ready_for_start(self, stepper: step_base):pass
    
    def ready_for_end(self):pass
        
    def Init(self): super().Init()
       
    def Init_by_dataframe(self, dataframe): pass



# ------------------------------------------------------------------
class port_base(work_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        super().__init__(name, GUI, **kwargs)
        self.buffer_data: dict = dict()
        self.col_name : list = list()
        self.Gui_For_Data : gui_base = None


    def clear_buffer(self):
        for key in self.buffer_data.keys():
            self.buffer_data[key] = []


    def ready_for_start(self, stepper: step_base):
        self.clear_buffer()


    def ready_for_end(self):pass
        
        #with self.info:
        #    print('ready_for_end')


    def reset_ports(self, port_parentname: str):
        if port_parentname in self.ports.keys():
            self.ports[port_parentname] = dict()


    def Init(self,  
            Values = [],
            Gui_For_Data  = None,
        ):
        super().Init()
        self.Gui_For_Data = Gui_For_Data
        self.buffer_data: dict = dict()
        for value in Values:
            if isinstance(value, sim_value):
                name = value._add_logger(self)
                self.buffer_data.update({name: []})
            elif isinstance(value, Callable):
                for item in value(self):
                    self.buffer_data.update({item: []})
        self.col_name = list(self.buffer_data.keys())     


    def _add_value(self, name, value):
        if name in self.buffer_data.keys():
            self.buffer_data[name].append(value)


# -------------------------------------------------------------------
class sim_base(work_base):

    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        super().__init__(name, GUI, **kwargs)
        self.time_factor: float = 0.0
        self.ch_type: gate_base = None
        
        if 'ch_type' in kwargs.keys():
            self.ch_type = kwargs['ch_type']
            if isinstance(self.ch_type, str):
                self.ch_type = Main_Modul.sim_obj_factory.get_classtype_by_name(
                    self.ch_type)

            if not issubclass(self.ch_type, gate_base): raise Exception('ist nicht vom Type gate_base abgeleitet')
           
        self._loggerlist : set = set()
        self._funcgate : dict = {}

       
        
    def _getgate_func(self, func : Callable):
        if func in self._funcgate.keys():
            return self._funcgate[func]
        return None
  
    def _node_success(self, timer: step_timer):pass
      

    def _reset(self):pass


    def _add_logger(self, logger):
        self._loggerlist.add(logger)


    def _del_logger(self, logger):
        self._loggerlist.remove(logger)


    def ready_for_start(self, stepper: step_base):
        super().ready_for_start(stepper)
        self._reset()
        if isinstance(stepper, step_timer):
            self.time_factor = stepper.factor
        stepper._add_logger(self._loggerlist)


    def log_all(self, logger):
        name_list = []
        for key, value in self.__dict__.items(): 
            if issubclass(type(value), sim_value):   
                name_list.append(value._add_logger(logger))
            elif issubclass(type(value), gate_base):
                name_list = name_list + value.log_all(logger)
        return name_list


        
    def Init_Over_GUI(self): pass
       
       
      

class ctrl_base():
    def __init__(self, name : str, gate_type : gate_base):
        super().__init__()
        self._parent = None
        self.name = name
        self.Gate_Ctrl = gate_type('Gate_Ctrl', self)
       

    def Do(self,  timer: step_timer, Summe: gate_general):
        pass

    def _init(self, parent):
        self._parent = parent
        return self.Do

    def ready_for_start(self, timer: step_timer): pass
       
    def ready_for_end(self):pass
    
    def _reset(self):
        self.Gate_Ctrl.reset() 

#*****************************************************************#--------------------------------------------------------------------
class ctrl_general_factor(ctrl_base):
    def __init__(self, name : str = 'ctrl_general_factor', gate_type : gate_base = gate_general, Factor = 1.0):
        super().__init__(name, gate_type)
        self.Factor = sim_value('Factor', self, (float, int,))
        self.Factor.Init(Factor)


    def Do(self,  timer: step_timer, Gate_In: gate_general):
        self.Gate_Ctrl.general._value = Gate_In.general._value * self.Factor.get_set(stepper=timer)
        return self.Gate_Ctrl


class ctrl_general_rest(ctrl_base):
    def __init__(self, name : str = 'ctrl_general_rest', gate_type : gate_base = gate_general):
        super().__init__(name, gate_type)
        
      
    def Do(self,  timer: step_timer, Gate_In: gate_general):
        sum = self._parent.Gate_In.general._value
        for gate  in self._parent._sequence_work[self._parent.Sequence_Key]['gates']:
            sum = sum + gate.general._value
        self.Gate_Ctrl.set(sum)
        #self._parent.Gate_Node.set(sum)
        return self.Gate_Ctrl


class ctrl_general_set(ctrl_base):
    def __init__(self, name : str = 'ctrl_general_rest', gate_type : gate_base = gate_general, Value = 0.0):
        super().__init__(name, gate_type)
        self.Value = sim_value('Factor', self, (float, int,))
        self.Value.Init(Value)
      

    def Do(self,  timer: step_timer, Gate_In: gate_general):
        self.Gate_Ctrl.general._value = self.Value.get_set(timer)
        return self.Gate_Ctrl  
       

class ctrl_general_zero(ctrl_general_rest):
    def __init__(self, name : str = 'ctrl_general_zero', gate_type : gate_base = gate_general):
        super().__init__(name, gate_type)
      

    def Do(self,  timer: step_timer, Gate_In: gate_general):
        super().Do(timer = timer, Gate_In = Gate_In)
        if (abs(self.Gate_Ctrl.general._value) < 0.0000001): 
            self._parent._ctrl_ok = True 
        return self.Gate_Ctrl


class ctrl_general_step(ctrl_base): 
    def __init__(self, name : str = 'ctrl_general_step', gate_type : gate_base = gate_general):
        super().__init__(name, gate_type)
        self.Gate_In = gate_general('Gate_In', self)
        self._Gate_Step = gate_general('_Gate_Step', self)
        self._sequence_work : dict = None
        self.Sequence_Key : str = ''


    def _init(self, parent):
        super()._init(parent)
        self._sequence_work = parent._sequence_work
        self.Sequence_Key = parent.Sequence_Key

    def Do(self, timer: step_timer, Gate_In: gate_general):
            self._ctrl_ok = False
            self.Gate_In.general._value = Gate_In.general._value
            self._Gate_Step.general._value = Gate_In.general._value
            for gate_func in self._sequence_work[self.Sequence_Key]['funcs']:
                gate = gate_func(timer, self.Summe)
                self._Gate_Step.general._value = gate.general._value
                if self._ctrl_ok: 
                    self.Gate_Ctrl.set(0.0)
                    return self.Gate_Ctrl
                
            sum = 0
            for gate  in self._sequence_work[self.Sequence_Key]['gates']:
                sum = sum + gate.general._value
            self.Gate_Ctrl.set(sum)
            return self.Gate_Ctrl


#*****************************************************************
class sim_dynamic(sim_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        kwargs.update({'ch_type' : gate_general}) 
        super().__init__(name, GUI, **kwargs)
        
        self.Gate_Dynamic = gate_dynamic('Gate_Dynamic', self)
        self.Feature : dict = None
        self._funcgate.update({
                self.Do : self.Gate_Dynamic})
        
        
    def _reset(self):
        self.Gate_Dynamic._reset()
        super()._reset()


    def _node_success(self, timer: step_timer):
        self.Gate_Dynamic._node_success(timer)


    def Init(self, Feature : None):
        super().Init()  
        self.Feature = Feature
        self.Gate_Dynamic.Init(self.Feature)


    def Do(self,  timer: step_timer, Gate_In: gate_general):
        self.Gate_Dynamic._actual_values(timer)
        return self.Gate_Dynamic


#--------------------------------------------------------------------  
class sim_general_node(sim_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        kwargs.update({'ch_type' : gate_general}) 
        super().__init__(name, GUI, **kwargs)   
        
        self._iterat_counter : int = 0
        self.Max_Iterat = sim_value('Max_Iterat', self, (int,)) 
        self.Gate_Node = gate_general('Gate_Node', self)
        self.Summe = gate_general('Summe', self)
        self.Gate_In = gate_general('Gate_In', self)

        #Controll Strukturen
        self._ctrl_nodeok : bool = False
        
        self.Sequence: dict = dict() # beinhaltet den vollen Namen und die Instance
        self.Sequence_Key: str = ''

        self._sequence_work : dict = dict() # beinhaltet verschiedene Informationen für verschiedene Aufgaben wird gebildet
        self._sequence_sims : set = set() # speichert alle verlinken sims
        self._sims_gates : dict = dict()
        self.Joker : sim_general_joker = None

        self._funcgate.update({
                self.Step : self.Gate_Node,
                self.StepRec : self.Gate_Node,
                self.SumEqual : self.Gate_Node})


    def Init(self, 
                Sequence = None,
                Sequence_Key = '',
                Joker = False,
                Max_Iterat = -1
                ):

        super().Init()
        self.Max_Iterat.Init(Max_Iterat)

        if Joker:  self.Joker = sim_general_joker(self.name + '.joker')
           
        if not isinstance(Sequence, dict): 
            raise Exception(f'Sequence ist kein dict')
        self.Sequence = Sequence
       

        for sequence_name, sequence_list in self.Sequence.items():
            self._sequence_work.update({sequence_name : {
                'func_names' : [],
                'funcs' : [],
                'sims' : set(),
                'gates' : set()
            }})
         
            for seq_item in sequence_list:
                if isinstance(seq_item, ctrl_base):
                    seq_item = seq_item._init(self)

                func_info = analyse_func(seq_item)
                if not func_info:
                    raise Exception(f'obj : {self.name} Startfunktion nicht korrekt')
                if not isinstance(func_info[0], (work_base, ctrl_base,)):

                    raise Exception(f'obj : {self.name} | {func_info[0].name}|node ist kein Type von work_base')
                if not callable(func_info[1]): 
                    raise Exception(f'obj : {self.name} |node hat keine func_work methode')
                     
                self._sequence_work[sequence_name]['func_names'].append(func_info[2])
                self._sequence_work[sequence_name]['funcs'].append(func_info[1])
                if isinstance(func_info[0], work_base):
                    self._sequence_work[sequence_name]['sims'].add(func_info[0])
                self._sequence_sims.add(func_info[0])
                
        if not Sequence_Key :  
            self.Sequence_Key = next(iter(self._sequence_work)) # Der erste wird gewählt
        elif Sequence_Key in self._sequence_str.keys():
            self.Sequence_Key = Sequence_Key
        else: raise Exception(f'Sequence_Key {Sequence_Key} nicht vorhanden!')
         

    def ready_for_start(self, timer: step_timer):
        super().ready_for_start(timer)
        for sim_obj in self._sequence_sims:
            if sim_obj == self: 
                continue
            sim_obj.ready_for_start(timer)
        
        for func in self._sequence_work[self.Sequence_Key]['funcs']:
            for sim_obj in self._sequence_work[self.Sequence_Key]['sims']:
                gate = sim_obj._getgate_func(func)
                if isinstance(gate, gate_base):
                    self._sequence_work[self.Sequence_Key]['gates'].add(gate)
                    break
            
            #raise Exception('gate to Funktion not found')      
   
   
    #----------------------- Simulations Steps ---------------------------------
    def _reset(self):
        super()._reset()
        self.Gate_Node._reset()
        self.Gate_In._reset()
        self.Summe._reset()
        self._iterat_counter = 0
        for sim_obj in self._sequence_work[self.Sequence_Key]['sims']:
            if sim_obj == self: 
                continue
            sim_obj._reset()
        if not self.Joker == None:
            self.Joker._reset()


    def _calc_node(self):
        sum = 0.0
        for gate  in self._sequence_work[self.Sequence_Key]['gates']:
            sum = sum + gate.get()
          
        sum = sum - self.Gate_Node.get()
        self.Summe.set(sum)
        if (abs(sum) < 0.0000001):
            return True
        return False


    def _node_success(self, timer: step_timer):
        for sim_obj in self._sequence_work[self.Sequence_Key]['sims']:
            if sim_obj == self: continue
            sim_obj._node_success(timer)
        
        if not self.Joker == None:
            self.Joker._node_success(timer)

        super()._node_success(timer)
        self.Gate_Node._node_success(timer)
        self.Gate_In._node_success(timer)



    def sum_master(self, timer: step_timer, Summe: gate_base = None):
        master_gate : gate_general =  gate_general('master_gate', self)
        master_sum : gate_general = gate_general('master_sum', self)
        
        if isinstance(Summe, self.ch_type):
            self.Summe.set(Summe)
            self.Gate_Node.set(Summe)
        else:
            self.Summe.set(0.0)
        
        old_master = 0.0
        new_master = 0.0
        master_sum.set(old_master)
        while True:
            master_func = self._sequence_work[self.Sequence_Key]['funcs'][0]
            value = master_func(timer,  master_sum).general.value
            master_gate.set(-value)
            for gate_func in self._sequence_work[self.Sequence_Key]['funcs'][1:]:
                gate_func(timer, master_gate)
                   
            if self._calc_node():
                self._node_success(timer)
                return self.Gate_Node
            
            new_master = master_gate.general.value + self.Summe.general.value
            master_sum.general.value = new_master
            if abs(new_master - old_master) < 0.0000001:
                break
           
            old_master = new_master
        
        if self.Joker:
            self.Joker.Var(timer, self.Summe)
            #if self._calc_node():
            self._node_success(timer)
        return self.Gate_Node
        

    def SumEqual(self, timer: step_timer, Summe: gate_base = None):
        self.Summe.general.value = Summe.general.value
        # Hier eine Zählschleife um weitere Informationen über den Ablauf zu erhalten
        
        for gate_func in self._sequence_work[self.Sequence_Key]['funcs']:
            gate_func(timer, self.Summe)
            if self._ctrl_nodeok:
               return self._ctrl_nodeok
           

        if self.Joker:
            self.Joker.Var(timer, self.Summe)
        return self.Gate_Node


   
    def Step(self, timer: step_timer, Gate_In: gate_base = None):
        self._ctrl_ok = False
        self.Gate_In.general._value = Gate_In.general._value
        self.Summe.general._value = Gate_In.general._value
        for gate_func in self._sequence_work[self.Sequence_Key]['funcs']:
            if gate_func == self.Step: # Verhindern von  rekursiven Aufrufs
                continue
            gate = gate_func(timer, self.Summe)
            self.Summe.general._value = gate.general._value
            if self._ctrl_ok: 
                self.Gate_Node.set(0.0)
                return self.Gate_Node
               
        #sum = self.In.general._value
        sum = 0
        for gate  in self._sequence_work[self.Sequence_Key]['gates']:
            sum = sum + gate.general._value
        self.Gate_Node.set(sum)
        return self.Gate_Node
  
      
    #Rekursiver aktiver Chanal von Step
    # ruft sich selber auf wenn kein 0 erreicht ist am Ende 
    def StepRec(self, timer: step_timer, Gate_In: gate_base = None, counter : int = 0):
        max_iterat = self.Max_Iterat.get_set(timer)
        
        self._ctrl_ok = False
        self.Gate_In.general._value = Gate_In.general._value
        self.Summe.general._value = Gate_In.general._value
        for gate_func in self._sequence_work[self.Sequence_Key]['funcs']:
            gate = gate_func(timer, self.Summe)
            if gate_func == self.Step: # Verhindern von  rekursiven Aufrufs
                continue
                
            self.Summe.general._value = gate.general._value
            if self._ctrl_ok: # rekursion beenden
                self.Gate_Node.set(0.0)
                return self.Gate_Node
       
        counter = counter + 1
        if (max_iterat >= 0) and (counter < max_iterat):
            for sim_obj in self._sequence_work[self.Sequence_Key]['sims']:
                if sim_obj == self: continue
                sim_obj._reset()
            self.StepRec(timer=timer, Gate_In=Gate_In, counter = counter)     
            

        sum = 0
        for gate  in self._sequence_work[self.Sequence_Key]['gates']:
            sum = sum + gate.general._value
        self.Gate_Node.set(sum)
        return self.Gate_Node



    def ready_for_end(self):
        super().ready_for_end()
        for sim_obj in self._sequence_sims:
            if sim_obj == self:continue 
            sim_obj.ready_for_end()


class sim_general_chanal(sim_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        kwargs.update({'ch_type' : gate_general}) 
        super().__init__(name, GUI, **kwargs)
        
        self.Gate_Set = gate_general('Gate_Set', self)
        self.Gate_Get = gate_general('Gate_Get', self)
        self.Gate_Chanal = gate_general('Gate_Chanal', self)
        
        self._funcgate.update({
                self.Set : self.Gate_Set,
                self.Get : self.Gate_Get})


    def Init(self, Gate_Set = None, Gate_Get = None):
        super().Init()
        self.Gate_Set.Init(Gate_Set)
        self.Gate_Get.Init(Gate_Get)
        self.Gate_Chanal.Init(None)

        

    def Set(self,  timer: step_timer, Gate_In: gate_general):
        self.Gate_Set.general._value = -Gate_In.general._value
        self.Gate_Chanal.general._value = Gate_In.general._value
        self.Gate_Get.general._value = 0
        return self.Gate_Set


    def Get(self,  timer: step_timer, Gate_In: gate_general):
        self.Gate_Get.general._value = -self.Gate_Set.general._value
        self.Gate_Set.general._value = 0
        return self.Gate_Get

    
    def _reset(self):
        self.Gate_Set._reset()
        self.Gate_Get._reset()
        self.Gate_Chanal._reset()
        super()._reset()


    def _node_success(self, timer: step_timer):
        self.Gate_Set._node_success(timer)
        self.Gate_Get._node_success(timer)
        self.Gate_Chanal._node_success(timer)



class sim_general_user(sim_base):
    def __init__(self, name: str, **kwargs):
        
        kwargs.update({'ch_type' : gate_general})   
        super().__init__(name, **kwargs)
        self.Gate_User = gate_general('Gate_User', self)
        self.User_Func = sim_value('UserFunc', self, (float, int,)) 
        self._funcgate.update({
                self.User : self.Gate_User})
        
       
    def Init(self,  
            User_Func = None,
            Gate_User = None
        ):

        super().Init()
        self.Gate_User.Init(Gate_User)
        self.User_Func.Init(User_Func)
      

    def User(self,  timer: step_timer, Gate_In: gate_general):
        gate = self.User_Func.get_set(stepper = timer, value = Gate_In)
        self.Gate_User.general._value = gate.general._value
        return self.Gate_User

    
    def _reset(self):
        self.Gate_User._reset()
        super()._reset()


    def _node_success(self, timer: step_timer):
        self.Gate_User._node_success(timer)



#TODO ergänzen um pulswidth von 0..1 
#TODO absolute zeit bezogen auf s einführen
#TODO verschiedene Formen auswählen
class sim_general_signal(sim_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        kwargs.update({'ch_type' : gate_general}) 
        super().__init__(name, GUI, **kwargs)
        
        self.Gate_Signal = gate_general('Gate_Signal', self)
        
        self.Frequency = sim_value('Frequency', self, (float, int,)) 
        self.Amplitude = sim_value('Amplitude', self, (float, int,)) 
        self.Offset = sim_value('Offset', self, (float, int,)) 
        
        self._max_val: float = 0
        self._min_val: float = 0
        self._funcgate.update({
                self.Fix : self.Gate_Signal})
        
       
    def Init(self,  
            Amplitude = None,
            Frequency = None,
            Offset = None,
            Gate_Signal = None
        ):

        super().Init()
        self.Gate_Signal.Init(Gate_Signal)
        self.Amplitude.Init(Amplitude)
        self.Frequency.Init(Frequency)
        self.Offset.Init(Offset)

        self._max_val = self.Amplitude.value - self.Offset.value
        self._min_val = self.Offset.value


    def Fix(self,  timer: step_timer, Gate_In: gate_general):
        value = int(timer.step_nr / self.Frequency.value)
        if value % 2:  # ungrade
            self.Gate_Signal.set(self._min_val)
        else:  # grade
            self.Gate_Signal.set(self._max_val)
        return self.Gate_Signal

    
    def _reset(self):
        self.Gate_Signal._reset()
        super()._reset()


    def _node_success(self, stepper: step_base):
        self.Gate_Signal._node_success(stepper)


#--------------------------------------------------------------------
class sim_general_joker(sim_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        kwargs.update({'ch_type' : gate_general}) 
        super().__init__(name, GUI, **kwargs)
      

    def Init(self,
        Gate = None):
        super().Init()
        self.Gate.Init(Gate)


    def _reset(self):
        self.Gate._reset()
        super()._reset()


    def _node_success(self, timer: step_timer):
        self.Gate._node_success(timer)


    def Var(self,  timer: step_timer, Summe: gate_general):
        self.Gate.general.set(-Summe.general.value)
        return self.Gate

#TODO ch_type raus
#--------------------------------------------------------------------
class sim_general_store(sim_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        kwargs.update({'ch_type' : gate_general}) 
        super().__init__(name, GUI, **kwargs)
        
        self.Gate_Store = gate_general('Gate_Store', self)
        self.Gate_Leak = gate_general('Gate_Leak', self)
        self.Capacity_Actual = sim_value('Capacity_Actual', self, (float, int,))
        self.Leak_Capacity_Actual = sim_value('Leak_Capacity_Actual', self, (float, int,))

        self.Capacity_Max = sim_value('Capacity_Max', self, (float, int,))  # Wenn None dann unendlich +
        self.Capacity_Min = sim_value('Capacity_Min', self, (float, int,))  # Wenn None dann unendlich -
        self.Load_Max = sim_value('Load_Max', self, (float, int,))  # Wenn None dann unendlich schnelles beladen
        self.Unload_Max = sim_value('Unload_Max', self, (float, int,))  # Wenn None dann unendlich schnelles entladen
        self.Leak_Rate = sim_value('Leak_Rate', self, (float, int,))
        self.Factor = sim_value('Factor', self, (float, int,))
        self.Invert = sim_value('invert', self, (bool,))

        self.func_leak : dict = {'leak_rate' : 0.0}

        self._funcgate.update({self.Var : self.Gate_Store})
       


    def Init(self, 
                Capacity_Max = None,
                Capacity_Min = None,
                Load_Max = None,
                Unload_Max = None,
                Leak_Rate = 0.0,
                Gate_Store = 0.0, 
                Gate_Leak = 0.0,
                Capacity_Actual = 0.0,
                Factor = 1.0,
                Invert = False              
                ):
        """ Initialisiert den Speicher 

        Keyword Arguments:
            Capacity_Max {float oder funktion} -- maximale Kapazität des Speichers (default: {None})
                Kein Wert (None) Speichergröße im positiven Bereich unbegrenzt
            Capacity_Min {[type]} -- [description] (default: {None})
            Load_Max {[type]} -- [description] (default: {None})
            Unload_Max {[type]} -- [description] (default: {None})
            Gate_Store {[type]} -- [description] (default: {None})
            Gate_Leak {[type]} -- [description] (default: {None})
            Capacity_Actual {[type]} -- [description] (default: {None})
            Factor{[float, int]} Bereich üblicherweise zwischen 0.0 und 1.0
        """        
               
        super().Init()

        self.Gate_Store.Init(Gate_Store)
        self.Capacity_Actual.Init(Capacity_Actual, default = 0.0)
        self.Gate_Leak.Init(Gate_Leak)
        self.Capacity_Max.Init(Capacity_Max)
        self.Capacity_Min.Init(Capacity_Min)
        self.Load_Max.Init(Load_Max)
        self.Unload_Max.Init(Unload_Max)
        
        self.Factor.Init(Factor, default = 1.0)
        self.Invert.Init(Invert, default = False)
        if isinstance(Leak_Rate, (float, int,)):
            self.func_leak['leak_rate'] = Leak_Rate 
            Leak_Rate = self._leak
        self.Leak_Rate.Init(Leak_Rate, default = 0.0)
        
      

    def _reset(self):
        self.Gate_Store._reset()
        super()._reset()

    # Es wird die Differenz berechnet
    def _leak(self, value = None, timer : step_timer = None):
        rate = self.func_leak['leak_rate']
        akt_cap = self.Capacity_Actual.value
        if rate == 0.0:
            return 0.0
        new_cap = akt_cap * math.exp(-rate * timer.total_sec)
        return akt_cap - new_cap
      


    def calc_loadcapacity(self, value: float):
        if not isinstance(self.Capacity_Max._value, (float, int,)):
            return value
        full_diff = (self.Capacity_Max._value -
                           self.Capacity_Actual._value) / self.time_factor
        if full_diff > value:
            return value
        elif full_diff == 0.0:
            return 0.0
        else:
            return full_diff



    def calc_unloadcapacity(self, value: float):
        if not isinstance(self.Capacity_Min._value, float):
            return value
        empty_diff = -(self.Capacity_Min._value -
                             self.Capacity_Actual._value) / self.time_factor
        if empty_diff >= -value:
            return value
        elif empty_diff == 0:
            return 0.0
        else:
            return -empty_diff

    #TODO es sollte noch eine variante zu Var geben, um z.B. einfach Verluste Widerstände zu simulieren
    def Var(self, timer: step_timer, Gate_In: gate_general):
        aim_value = -Gate_In.general.value * self.Factor.get_set(timer)
        if self.Invert.value : aim_value = -aim_value
        if aim_value >= 0:  # Beladen
            max_value = self.Load_Max.get_set(stepper=timer)
            if max_value == None: # Keine Begrenzung
                real_value = aim_value 
            elif max_value >= 0 and max_value > aim_value:
                real_value = aim_value 
            elif max_value >= 0 and max_value <= aim_value:
                real_value =  max_value  
            elif max_value < 0:
                real_value =  max_value
        else:
            max_value = self.Unload_Max.get_set(stepper=timer)
            if max_value == None: # Keine Begrenzung
                real_value = aim_value 
            elif max_value <= 0 and max_value < aim_value:
                real_value = aim_value 
            elif max_value <= 0 and max_value >= aim_value:
                real_value =  max_value  
            elif max_value > 0:
                real_value =  max_value

        if real_value >= 0:  # Beladen
            real_value = self.calc_loadcapacity(real_value)
        else:  # Entladen
            real_value = self.calc_unloadcapacity(real_value)
        
        self.Gate_Store.set(real_value) #Todo Set verbessern damit auch ein Callback erfolgt
        return self.Gate_Store


    # Immer den gleichen Wert speichern
    def Fix_Load(self,  timer: step_timer, Summe: gate_general):
        self.Gate_Store.set(self.Load_Max)
        return self.Gate_Store, True


    # Immer den gleichen Wert entladen
    def Fix_Unload(self,  timer: step_timer, Summe: gate_general):
        self.Gate_Store.set(self.Unload_Max)
        return self.Gate_Store, True


    def _node_success(self, timer: step_timer):
        super()._node_success(timer)
        
        corr_value = self.Gate_Store.get() * self.time_factor
        value = self.Capacity_Actual._value + corr_value
        self.Capacity_Actual._value = value 

        diff = self.Leak_Rate.get_set(stepper=timer) 
        self.Capacity_Actual._value = self.Capacity_Actual._value - diff
        #self.Leak_Capacity_Actual._value = self.Leak_Capacity_Actual._value + diff

        self.Gate_Store._node_success(timer)
        self.Capacity_Actual._node_success(timer)
        self.Gate_Leak._node_success(timer)
