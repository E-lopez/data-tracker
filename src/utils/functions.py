from math import ceil
from models.defaults.defaults_dict import document_defaults


def calculate_coords(values, key, presets):
  right_column = ['Renta2', 'Ganancias_ocasionales', 'Impuestos_renta_liquida', 'Liquidacion_privada', 'Retenciones']
  right_offset = ['Impuestos_renta_liquida', 'Retenciones']
  if key in ['informacion_general', 'pago_total', 'pie_de_pagina', 'obras_por_impuestos']:
    x0 = values[0]
    top = values[1]
    x1 = x0 + values[2]
    bottom = top + values[3]
    return (x0, top, x1, bottom)
  else:
    selected_preset = 'right' if key in right_column else 'left'
    x_offset = 15.09 if key in right_offset else 0

    x0, width, height = presets[selected_preset].values()
    x0 += x_offset
    width -= x_offset
    top = float(values)
    x1 = x0 + width
    bottom = top + height
    return (x0, top, x1, bottom)
      
     
def get_default(document, index, version):
    try:
      default = document_defaults[document][version][index]
      return default
    except KeyError:
      return 'n/a'
    

def map_risk_to_rate(value):
  # Updated for 0-100 normalized risk scale
  # Higher scores = lower risk = lower rates
  if value >= 90.0:  # Excellent (was 13-15)
    return 0.21
  if value >= 80.0:  # Excellent (was 13-15)
    return 0.22
  elif value >= 70.0:  # Good (was 10-13)
    return 0.23
  elif value >= 60.0:  # Average (was 7.5-10)
    return 0.24
  elif value >= 20.0:  # Below Average
    return 0.37
  else:  # Poor (0-20)
    return 0.40
    

def cast_value(key, value):
  if(key == 'user_risk'):
    return float(value)
  else:
    return int(value)
