# Shabaka AdScreen - Manuel Utilisateur

Ce guide est destiné aux gestionnaires d'établissements (bars, restaurants, centres commerciaux) et aux annonceurs souhaitant diffuser du contenu.

## 1. Pour les Propriétaires d'Écrans (Organisations)

Vous êtes gestionnaire d'un lieu accueillant du public et vous souhaitez monétiser vos écrans.

### 1.1 Accéder à votre Espace
Connectez-vous sur `/login` avec vos identifiants. Vous arrivez sur votre **Tableau de Bord** qui affiche :
*   Le nombre d'écrans actifs.
*   Les revenus générés sur la semaine en cours.
*   Les contenus en attente de validation.

### 1.2 Ajouter un Nouvel Écran
1.  Allez dans **Écrans** > **Ajouter**.
2.  Donnez un nom (ex: "Entrée Principale").
3.  Définissez la **résolution exacte** (ex: 1920x1080).
4.  Choisissez l'**orientation** (Paysage ou Portrait).
5.  Fixez le **Prix de base par minute** (ex: 1.00€). C'est ce tarif qui servira de base au calcul des créneaux.

### 1.3 Configurer les Prix
Une fois l'écran créé, configurez les options de vente :
*   **Créneaux (Time Slots)** : Définissez les durées vendables (10s, 15s, 30s). Le prix est calculé automatiquement mais peut être ajusté.
*   **Périodes (Time Periods)** : Appliquez des majorations selon l'heure.
    *   *Exemple : Créer une période "Happy Hour" de 18h à 21h avec un multiplicateur de x1.5.*

### 1.4 Gérer la Playlist
*   **Validation** : Lorsqu'un client réserve un créneau, vous recevez une notification. Allez dans **Contenus** > **À Valider**. Vérifiez que le visuel respecte votre charte éthique.
*   **Auto-Promo** : Vous pouvez diffuser vos propres publicités (Menu, Événements) gratuitement via l'onglet **Contenu Interne**. Ces contenus ont une priorité légèrement inférieure aux pubs payantes.
*   **Overlays** : Ajoutez des messages défilants (tickers) en bas d'écran pour des annonces rapides.

### 1.5 Facturation
Chaque dimanche soir, une facture est générée calculant la commission due à la plateforme (Shabaka).
1.  Allez dans **Facturation**.
2.  Téléchargez la facture en attente.
3.  Effectuez le virement du montant de la commission.
4.  Uploadez la preuve de virement dans l'interface pour débloquer votre compte.

---

## 2. Pour les Annonceurs (Clients)

Vous souhaitez diffuser une publicité sur un écran du réseau Shabaka.

### 2.1 Réserver un Espace
1.  Scannez le **QR Code** affiché sur l'écran ou cliquez sur le lien de réservation fourni par l'établissement.
2.  Vous accédez à la fiche de l'écran avec ses tarifs et disponibilités.

### 2.2 Choisir son Offre
*   **Type de Média** : Image fixe ou Vidéo.
*   **Durée** : Sélectionnez le temps d'affichage (ex: 15 secondes).
*   **Période** : Choisissez le moment de la journée (Matin, Midi, Soir).
*   **Récurrence** : Combien de fois votre pub doit passer ? (ex: 50 fois).

### 2.3 Uploader le Contenu
Respectez scrupuleusement les contraintes techniques affichées :
*   **Résolution** : Doit être identique à celle de l'écran (ex: 1920x1080).
*   **Poids** : Max 100 Mo (généralement).
*   **Format** : JPG/PNG pour les images, MP4 pour les vidéos.

*Astuce : Si votre image est refusée, vérifiez qu'elle n'est pas en 1921 pixels de large au lieu de 1920.*

### 2.4 Paiement et Validation
1.  Le système calcule le prix total TTC.
2.  Validez la commande.
3.  Téléchargez votre reçu (format ticket de caisse).
4.  Votre publicité passera en statut "En attente de validation". Dès que l'établissement l'approuve, elle commence à être diffusée.

---

## 3. Foire Aux Questions (FAQ)

**Q: Mon écran reste noir, que faire ?**
R: Vérifiez la connexion internet du player. S'il est hors ligne depuis plus de 2 minutes, il apparaît "Offline" dans le dashboard. Redémarrez le navigateur du player.

**Q: Puis-je diffuser de la TV en direct ?**
R: Oui, si l'option est activée sur l'écran. Allez dans la configuration de l'écran et activez le mode "IPTV". Vous devrez fournir une URL de flux (M3U8).

**Q: Comment sont calculés les prix ?**
R: Prix = (Prix base minute * (Durée slot / 60)) * Multiplicateur période.
*Exemple : Base 2€/min. Slot 30s (=1€). Période Soir (x1.5). Total par passage = 1.50€.*
