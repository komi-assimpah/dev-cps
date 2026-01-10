# Econs / (temp moyenne * surface)
class USER_ISOLATION_SCORE:
  def isolation_score(conso_elec: float, surface: int, temp_data: list):
    def avg(data: list) -> float: return sum(data)/len(data)

    return (conso_elec)/avg(temp_data)*surface

# comment on fait le score client ? genre c'est juste une moyenne des scores user ?
# class CLIENT_ISOLATION_SCORE(USER_ISOLATION_SCORE):
#   def isolation_score(conso_elec, surface, temp_data):
#     return super().isolation_score(surface, temp_data)