def get_question_weight(key):
  if key == 'demographics':
    return 0.2
  elif key == 'section1':
    return 0.5
  elif key == 'section2':
    return 0.3
  else:
    return None