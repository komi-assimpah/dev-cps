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
    
    # Assigner les pieces a TOUTES les cellules avec flood fill limite par distance
    self._assign_rooms_limited_flood_fill(flat, flat_sensors, max_distance=8)

    return flat
  
  def _assign_rooms_limited_flood_fill(self, flat, sensors, max_distance=8):
    """
    Assigne automatiquement les pieces a toutes les cellules
    en utilisant un flood fill LIMITE PAR DISTANCE depuis chaque capteur.
    
    Chaque capteur remplit seulement les cellules dans un rayon de max_distance.
    S'arrete aux murs et fenetres.
    """
    for sensor_name, sensor_info in sensors.items():
      room = sensor_info['room']
      start_x = sensor_info['pos_x']
      start_y = sensor_info['pos_y']
      
      # Flood fill avec distance
      queue = [(start_y, start_x, 0)]  # (y, x, distance)
      visited = set()
      
      while queue:
        y, x, dist = queue.pop(0)
        
        if (y, x) in visited:
          continue
        
        # Limiter la distance
        if dist > max_distance:
          continue
        
        # Verifier limites
        if y < 0 or y >= len(flat) or x < 0 or x >= len(flat[0]):
          continue
        
        cell = flat[y][x]
        
        # S'arreter aux murs et fenetres
        if cell.is_wall or cell.is_window:
          continue
        
        # IMPORTANT: Ne JAMAIS ecraser une cellule qui a un capteur
        if cell.sensor and cell.room and cell.room != room:
          continue
        
        # Ne pas ecraser une piece deja assignee par un autre capteur
        if cell.room is not None and cell.room != room:
          continue
        
        # Assigner la piece
        cell.room = room
        visited.add((y, x))
        
        # Ajouter les 4 voisins avec distance+1
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
          queue.append((y + dy, x + dx, dist + 1))
