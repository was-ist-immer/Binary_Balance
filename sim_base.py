import pathlib
import sys

# Globale Festlegungen
Main_Modul = sys.modules['__main__']
Self_Modulname = globals()['__name__']
Self_Modul = sys.modules[Self_Modulname]

#sim_obj_factory = Main_Modul.sim_obj_factory

timepattern = '%Y-%m-%d %H:%M:%S' 