import yaml
import spatial.converter as fc
from spatial.cell import Cell
import numpy as np

class FlatLoader():
  def get_yaml_file(self, file_name):
    with open(file_name,'r') as file:
      return yaml.safe_load(file)

  def load_flat(self, appart_path):
    """
    Charge un appartement depuis son dossier de configuration.
    
    :param appart_path: Chemin vers le dossier de l'appartement (ex: 'config/apartments/APT_101')
    :return: Grille 2D de Cell objects
    """
    flat_config = self.get_yaml_file(appart_path+'/config.yml')
    flat_actuators = flat_config.get('actuators', {})
    flat_sensors = flat_config.get('sensors', {})
    grid = fc.FlatConverter().get_grid_from_image(appart_path+'/plan.png')

    grid = np.insert(grid, 0, 0, axis=0)

    flat = list()

    for i in range(len(grid)):
      line = list()
      for j in range(len(grid[i])):
        line.append(Cell(grid[i][j] == 1, [j,i] in flat_config.get('outside', []), [j,i] in flat_config.get('windows', [])))
      flat.append(line)

    for sensor in flat_sensors:
      cur_sensor = flat_sensors[sensor]
      flat[cur_sensor['pos_y']][cur_sensor['pos_x']].sensor = cur_sensor['type']
      flat[cur_sensor['pos_y']][cur_sensor['pos_x']].room = cur_sensor['room']
    
    for actuator in flat_actuators:
      cur_actuator = flat_actuators[actuator]
      flat[cur_actuator['pos_y']][cur_actuator['pos_x']].actuator = cur_actuator['type']
      flat[cur_actuator['pos_y']][cur_actuator['pos_x']].room = cur_actuator['room']

    return flat
