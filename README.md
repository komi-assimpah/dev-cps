# dev-cps

## utiliser le consumer kafka

```
python3 consumer.py APT_ID
```
exemple pour l'appartement APT_101
```
python3 consumer.py 1
```

## interagir avec la bdd dans un terminal

```
docker exec -it mon-timescale psql -U monuser -d sensor_scores
```

afficher les differentes tables 
```
\dt
```

on peut executer n'importe quelle requete SQL (ne pas oublier le `;`)