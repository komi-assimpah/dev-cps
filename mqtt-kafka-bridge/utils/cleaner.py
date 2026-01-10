import numpy as np
from scipy.signal import medfilt

MAX_LEN_HISTORY = 50

def get_dynamic_threshold(history, k=5):
  median = np.median(history)
  mad = np.median(np.abs(history - median))
  return k * (mad * 1.4826)

def median_filter(new_data: float, data_type: str, history: list):
# global last_values, nb_outliers
  try:
    start_idx = len(history)
    history.append(new_data)

    if len(history) > MAX_LEN_HISTORY:
      history = history[-MAX_LEN_HISTORY:]
      start_idx = len(history) - 1
    
    if len(history) >= 20:
      arr_full = np.array(history, dtype=float)
      med_filtered = medfilt(history, kernel_size=5)

      threshold = get_dynamic_threshold(history)
      # print(f"[INFO] [THRESHOLD] [{data_type}] {threshold}")

      raw_new = arr_full[start_idx:]
      filtered_new = med_filtered[start_idx:]

      diff = np.abs(raw_new - filtered_new)
      outliers_detectes = diff > threshold

      outliers = raw_new[outliers_detectes].tolist()

      if len(outliers) > 0: print(f"[INFO] [{data_type}] Détection de {len(outliers)} outliers {outliers} dans {new_data}")

      return (med_filtered[-1:], outliers[0] if len(outliers) > 0 else None)
    else:
      return (new_data, None)
  except Exception as e:
    print(f"ERROR : {e}")
    return (new_data, None)

def avg(data: list) -> float:
  count = len(data) - data.count(None)
  if count == 0: return None
  mean = sum(dat for dat in data if dat != None)/count
  return round(mean, 3)

def remove_none_values(history):
  if len(history) < 2: return history
  new_history = history
  if history[-2] == history[-1] == None: return history
  if history[-1] == None: new_history[-1] = history[-2]
  return new_history
