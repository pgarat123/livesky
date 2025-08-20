**Nom du Projet :** Application Web de Station Météo IoT (Livesky)

**Vue d'ensemble du Projet :**
Il s'agit d'un projet IoT centré sur une station météo. L'application web sert d'interface pour communiquer avec les appareils ESP32, stocker les données des capteurs et les afficher aux clients. Elle se compose d'un frontend Vue.js et d'un backend Flask (Python), tous deux conteneurisés à l'aide de Docker.

**Configuration Docker :**
L'application est conteneurisée à l'aide de `docker-compose.yml`.
*   **Backend :** Exposé sur le port hôte `5001` (mappe au port conteneur `5000`).
*   **Frontend :** Exposé sur le port hôte `8080` (mappe au port conteneur `80`).
*   **Base de Données :** Service PostgreSQL (`db`) avec vérifications de santé.

**Notes Importantes pour l'Utilisateur :**

*   **Reconstruction Docker :** Après toute modification du code (en particulier dans le backend), il est crucial de reconstruire les images Docker pour que les changements prennent effet. Utilisez la commande : `docker-compose down && docker-compose up --build -d`.
*   **URL de l'API :** Le frontend est configuré pour se connecter à `http://192.168.1.20:5001`. Assurez-vous que cette adresse IP est correcte pour votre hôte Docker.
*   **Font Awesome :** Les icônes sont utilisées dans le frontend, chargées via CDN. Une connexion Internet est requise pour que les icônes s'affichent.
