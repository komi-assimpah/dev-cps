# Bridges Kafka - Bases de données

## Consumer Kafka - Calcul Score - Bridge Kafka / TimescaleDB

S'abonne aux topics `<apt_id>.<room>.score_data`, regroupe les données et calcule les scores:
- IAQ_2h : la qualité de l'air des 2 dernières heures
  - calcule un score sur chaque metrique (co2, co, pm25, cov)
  - realise une moyenne ponderee mettant l'accent sur les hauts scores
  - donne un score entre 0 et 5, 0 étant une qualité de l'air parfaite, et 5 une qualité de l'air excécrable
- IIT : l'indice d'isolation thermique
  - le score n'est pas parfait et aurait besoin d'être paufiné
  - il se calcule ainsi : `conso_moyenne(kwh)/((temp_int-temp_ext)*surface(m2))`

Puis envoie ces scores dans la base de données TimescaleDB pour le monitoring

## Consumer Kafka - Stockage Client - Bridge Kafka / MongoDB

S'abonne aux topics `<apt_id>.<room>.score_data` ainsi que `<apt_id>.<room>.extra_data`, regroupe les données et les envoie sur MongoDB