import statistics

# Econs / (temp moyenne * surface)
def isolation_score(conso_elec: float, surface: int, avg_temp: float):
    # def avg(data: list) -> float: return sum(data)/len(data)
  return conso_elec/(avg_temp*surface)

class CLIENT_ISOLATION_SCORE:
  def IIT_2h(self, conso_elec: float, surface: int, temp: list):
    avg_temp = statistics.mean(temp)
    return conso_elec/(avg_temp*surface)
    # values = list()
    # for i in avg_temp:
      # values.append(isolation_score(conso_elec, surface, i))
    # return statistics.mean(values)
# comment on fait le score client ? genre c'est juste une moyenne des scores user ?
# class CLIENT_ISOLATION_SCORE(USER_ISOLATION_SCORE):
#   def isolation_score(conso_elec, surface, temp_data):
#     return super().isolation_score(surface, temp_data)