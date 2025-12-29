import numpy

class USER_AIR_QUALITY:
  def co2_score(co2_quantity):
    if co2_quantity<800: return 0
    elif co2_quantity<1000: return 1.25
    elif co2_quantity<1500: return 2.5
    elif co2_quantity<2000: return 3.75
    else: return 5

  def co_score(co_quantity):
    if co_quantity==0: return 0
    elif co_quantity<10: return 1.25
    elif co_quantity<30: return 2.5
    elif co_quantity<50: return 3.75
    else: return 5
  
  def pm25_score(pm25_quantity):
    if pm25_quantity<=12: return 0
    elif pm25_quantity<=35: return 1
    elif pm25_quantity<=55: return 2
    elif pm25_quantity<=150: return 3
    elif pm25_quantity<=250: return 4
    else: return 5
  
  def cov_score(cov_quantity):
    if cov_quantity<=300: return 0
    elif cov_quantity<=1000: return 1.25
    elif cov_quantity<=2000: return 2.5
    elif cov_quantity<=3000: return  3.75
    else: return 5
  
  def IAQ(self, co2_quantity, co_quantity, pm25_quantity, cov_quantity):
    score = 0
    score += self.co2_score(co2_quantity)
    score += self.co_score(co_quantity)
    score += self.pm25_score(pm25_quantity)
    score += self.cov_score(cov_quantity)

SEUIL_ACCEPTABLE_CO2 = 1000 #ppm
SEUIL_CRITIQUE_CO2 = 1500 #ppm
SEUIL_CRITIQUE_CO = 50 #ppm
SEUIL_CO_1 = 10
SEUIL_CO_2 = 30

unit = "ug/m3"
n0 = 0
n1 = 0
n2 = 0
icone = -1

class CLIENT_AIR_QUALITY:
  def co2_score(co2_data):
    def f1(n0, n1, n2): return n1/(n0+n1+n2)
    def f2(n0, n1, n2): return n2/(n0+n1+n2)
    
    global n0, n1, n2
    for i in range(len(co2_data)):
      if float(co2_data[i]) <= SEUIL_ACCEPTABLE_CO2: n0+=1
      elif float(co2_data[i]) > SEUIL_CRITIQUE_CO2: n2+=1
      else: n1+=1
    return round((2.5/numpy.log10(2))*(numpy.log10(1 + f1(n0,n1,n2)+3 * f2(n0,n1,n2))), 2)
  
  def co_score(co_data, unit):
    total = 0
    for i in range(len(co_data)):
      if unit == 'ug/m3': data = co_data[i]/1145
      else: data = co_data[i]
      if float(data) >= SEUIL_CRITIQUE_CO: return 5
      total += (data*10)

    if 2500 <= total: return 4
    elif 1500 < total < 2500: return 3
    elif 300 < total <= 1500: return 2
    elif 50 < total <= 300: return 1
    else : return 0
  
  def pm25_score(pm_data):
    total=0
    for i in range(len(pm_data)):
      if pm_data[i]<=12: total+=0
      elif pm_data[i]<=35: total+=1
      elif pm_data[i]<=55: total+=2
      elif pm_data[i]<=150: total+=3
      elif pm_data[i]<=250: total+=4
      else: total+=5
    return round(total/12,2)

  def cov_score(cov_data):
    total=0
    for i in range(len(cov_data)):
      if cov_data[i]<=300: total+=0
      elif cov_data[i]<=1000: total+=1.25
      elif cov_data[i]<=2000: total+=2.5
      elif cov_data[i]<=3000: total+= 3.75
      else: total+=5
    return round(total/12,2)
  
  def IAQ(self, co2_data, co_data, unit, pm_data, cov_data):
    score = 0
    score += self.co2_score(co2_data)
    score += self.co_score(co_data, unit)
    score += self.pm25_score(pm_data)
    score += self.cov_score(cov_data)