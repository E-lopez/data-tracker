from __future__ import annotations
from abc import ABC, abstractmethod
import locale
import math
from typing import List
from models.defaults.defaults_dict import document_defaults
from utils.functions import get_default
import re

loc = locale.getlocale()
locale.setlocale(locale.LC_MONETARY, loc)

class QuestionScoring():
  def __init__(self, strategy = None) -> None:
    self._strategy = self.select_scoring(strategy)

  def select_scoring(self, strategy):
    if strategy == 'demographics':
      return DemographicsScoring()
    else:
      return Default()

  def set_scoring(self, strategy: Strategy):
    self._strategy = strategy

  def use_scoring(self, *args):
    return self._strategy.score_question(*args)


class Strategy(ABC):
  @abstractmethod
  def score_question(self, *args: List):
    pass

  def apply_bias_correction(self, raw_score: float) -> float:
    """Apply statistical transformation to reduce central tendency bias"""
    # Normalize to 0-1 range
    normalized = (raw_score - 1) / 4
    # Apply sigmoid-like transformation to spread middle values
    corrected = 1 / (1 + math.exp(-6 * (normalized - 0.5)))
    # Scale back to 1-5 range with enhanced differentiation
    return 1 + (corrected * 8)  # Expanded to 1-9 range for better differentiation


class Default(Strategy):
  def __init__(self):
        self.count = 0
        self.data = {}

  def score_question(self, *args, i = 0):
    section_data = args[0]
    
    # Handle different input structures
    if isinstance(section_data, dict) and 'data' in section_data:
        # Questionnaire structure with metadata and data
        likert_data = section_data['data']
    else:
        # Direct data structure
        likert_data = section_data
    
    if len(self.data) == 0:
        self.data = {**self.data, **dict(likert_data)}
    
    if i == len(self.data):
        if len(self.data) == 0:
            return 5.0  # Default neutral score
        raw_avg = self.count / len(self.data)
        corrected_score = self.apply_bias_correction(raw_avg)
        print(f"Raw average: {raw_avg}, Bias-corrected score: {corrected_score}")
        return corrected_score
    
    key = list(self.data)[i]
    value = self.data[key]
    print(f"Scoring field: {key} with value: {value}")
    
    # Convert to int, default to 3 if not valid
    try:
        partial = int(value) if isinstance(value, (int, str)) and str(value).isdigit() else 3
    except (ValueError, TypeError):
        partial = 3
    
    self.count = self.count + partial
    print(f"Current count: {self.count}, Partial score: {partial}. Len: {len(self.data)}")
    return self.score_question(self, args, i = i+1)


class DemographicsScoring(Strategy):
  def __init__(self):
        self.count = 0
        self.data = {}
        self.gender_multiplier = 1.0

  def field_score(self, key) -> float:
    data = self.data[key]
    print(f"Scoring field: {key} with value: {data}")
    
    if key == 'gender':
      if data == 'F':
        self.gender_multiplier = 1.4  # 40% advantage for females
        return 8.0
      else:
        self.gender_multiplier = 1.0
        return 3.0
    elif key == 'occupation':
      if data == 'Empleado':
        return 8.0  # Boost for employed
      elif data == 'Desempleado':
        return 2.0  # Lower score for unemployed
      else:  # Independiente or other
        return 5.0
    else:
      return 0.0  # Ignore other demographic fields

  def score_question(self, *args, i = 0):
    if len(self.data) == 0:
        # Handle direct demographics data (no nested structure)
        self.data = {**self.data, **dict(args[0])}
    
    # Only process gender and occupation fields
    relevant_fields = ['gender', 'occupation']
    relevant_data = {k: v for k, v in self.data.items() if k in relevant_fields}
    
    if i == len(relevant_data):
        base_score = self.count / len(relevant_data) if len(relevant_data) > 0 else 4.0
        final_score = base_score * self.gender_multiplier
        print(f"Demographics base score: {base_score}, Gender multiplier: {self.gender_multiplier}, Final: {final_score}")
        return final_score
    
    key = list(relevant_data)[i]
    self.count = self.count + self.field_score(key)
    return self.score_question(self, args, i = i+1)
       