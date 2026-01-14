import statistics

# Econs / (temp moyenne * surface)
def isolation_score(conso_elec: float, surface: int, avg_temp: float):
    # def avg(data: list) -> float: return sum(data)/len(data)
  return conso_elec/(avg_temp*surface)

class CLIENT_ISOLATION_SCORE:
  def IIT_2h(self, conso_elec: float, surface: int, temp: list, temp_ext: list):
    avg_conso = statistics.mean(conso_elec)
    avg_temp = statistics.mean(temp)
    avg_temp_ext = statistics.mean(temp_ext)
    return round(1000*(avg_conso/((avg_temp - avg_temp_ext)*surface)),2)
    # values = list()
    # for i in avg_temp:
      # values.append(isolation_score(conso_elec, surface, i))
    # return statistics.mean(values)
# comment on fait le score client ? genre c'est juste une moyenne des scores user ?
# class CLIENT_ISOLATION_SCORE(USER_ISOLATION_SCORE):
#   def isolation_score(conso_elec, surface, temp_data):
#     return super().isolation_score(surface, temp_data)