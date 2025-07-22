# Scripts utilitaires Woilà Backend

Ce dossier contient les scripts utilitaires pour le projet Woilà Backend.

## 📋 Scripts disponibles

### 🔧 `setup_project.py`
Script d'installation et configuration automatique du projet.

**Usage:**
```bash
cd Backend
python3 scripts/setup_project.py
```

**Fonctionnalités:**
- ✅ Application des migrations
- ✅ Chargement des configurations par défaut
- ✅ Vérification des superutilisateurs
- ✅ Guide d'utilisation post-installation

## 📁 Organisation

```
scripts/
├── README.md           # Ce fichier
├── setup_project.py    # Installation automatique
└── ...                 # Futurs scripts utilitaires
```

## 🎯 Bonnes pratiques

- Les scripts utilitaires vont dans ce dossier
- Chaque script doit avoir un docstring explicatif
- Les scripts doivent être exécutables depuis la racine du projet
- Documentation requise pour les nouveaux scripts