import cv2
import numpy as np
import matplotlib.pyplot as plt

class FlatConverter:
    def image_vers_grille(self, chemin_image, taille_grille=(20,20), seuil_detection=200):
        """
        Convertit une image de plan en grille numpy.
        
        :param chemin_image: Chemin vers le fichier image
        :param taille_grille: Tuple (hauteur, largeur) de la grille de sortie
        :param seuil_detection: Valeur (0-255) pour différencier les murs du fond (ajuster selon le contraste)
        :return: Une matrice numpy (la grille)
        """
        # 1. Charger l'image en niveaux de gris
        img = cv2.imread(chemin_image, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            raise ValueError("Impossible de charger l'image. Vérifiez le chemin.")

        # 2. Binarisation (Seuillage)
        # On inverse (THRESH_BINARY_INV) car souvent les murs sont noirs sur fond blanc.
        # Après ça : Murs = 255 (Blanc), Fond = 0 (Noir) pour faciliter le traitement.
        _, img_bin = cv2.threshold(img, seuil_detection, 255, cv2.THRESH_BINARY_INV)

        # Optionnel : Épaissir les murs s'ils sont trop fins pour être vus après redimensionnement
        kernel = np.ones((3,3), np.uint8)
        img_bin = cv2.dilate(img_bin, kernel, iterations=1)

        # 3. Redimensionnement vers la taille de la grille souhaitée
        # L'interpolation INTER_AREA est la meilleure pour réduire la taille sans perdre trop d'infos
        grille_redimensionnee = cv2.resize(img_bin, (taille_grille[1], taille_grille[0]), interpolation=cv2.INTER_AREA)

        # 4. Normalisation
        # Convertir les valeurs [0, 255] en [0, 1] (ou booléens)
        # Si le pixel > 0, on considère qu'il y a un mur
        grille_finale = (grille_redimensionnee > 50).astype(int)

        return grille_finale, img_bin

    # --- Utilisation ---
    def get_grid_from_image(self,file_name):
        # Remplacez par le nom de votre image
        try:
            # Exemple : Une grille de 30x30 cellules
            grille, _ = self.image_vers_grille(chemin_image = file_name, taille_grille=(20, 20))
            return grille

        except Exception as e:
            print(f"Erreur : {e}")
