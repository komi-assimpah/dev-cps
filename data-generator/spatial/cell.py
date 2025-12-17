from random import uniform

class Cell:
  def __init__(self, is_wall, is_outside, is_window):
    self.is_wall = is_wall and not is_window
    self.is_outside = is_outside
    self.is_window = is_window
    self.is_open = True
    self.sensor = None
    self.actuator = None
    self.room = None
    self.Qapports = 0
    if is_wall :
      self.temp = -1
      self.co = -1
      self.co2 = -1
      self.cov = -1
      self.pf = -1
    elif is_outside :
      #TODO: à adapter à data-generator qui fourni une température extérieure
      self.temp = round(uniform(14, 15),2)
      self.co = 2
      self.co2 = 2
      self.cov = 2
      self.pf = 2
    else:
      #TODO: à adapter à data-generator qui fourni une température intérieure
      self.temp = round(uniform(19, 20),2)
      self.co = 2
      self.co2 = 2
      self.cov = 2
      self.pf = 2
    
  def get_sensor_data(self):
    #TODO: à adapter à data-generator qui fourni une température extérieure
    if self.sensor == "SENSOR_TEMP":
      return self.temp
    elif self.sensor == "SENSOR_IAQ":
      return (self.co, self.co2, self.cov, self.pf)
    else:
      return -1
  
  def duplicate(self):
    res = Cell(self.is_wall, self.is_outside, self.is_window)
    res.is_open = self.is_open
    res.sensor = self.sensor
    res.actuator = self.actuator
    res.room = self.room
    res.Qapports = self.Qapports
    res.temp = self.temp
    res.co = self.co 
    res.co2 = self.co2
    res.cov = self.cov
    res.pf = self.pf
    return res
