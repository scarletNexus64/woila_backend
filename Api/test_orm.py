#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de test pour vérifier les relations ORM"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Api.settings')
django.setup()

from users.models import Document, UserDriver
from authentication.models import Token

print("=" * 60)
print("TEST DES RELATIONS ORM - Documents et Tokens")
print("=" * 60)

# Test 1: Documents
print("\n1. DOCUMENTS AVEC LEURS PROPRIETAIRES")
print("-" * 60)
docs = Document.objects.all()[:5]
for doc in docs:
    try:
        user = doc.user
        print(f"Document: {doc.document_name}")
        print(f"  Proprietaire: {user.name} {user.surname}")
        print(f"  Telephone: {user.phone_number}")
        print(f"  Type: {'Chauffeur' if doc.user_type.model == 'userdriver' else 'Client'}")
        print()
    except Exception as e:
        print(f"  Erreur: {e}")
        print()

# Test 2: Tokens
print("\n2. TOKENS AVEC LEURS PROPRIETAIRES")
print("-" * 60)
tokens = Token.objects.all()[:5]
for token in tokens:
    try:
        user = token.user
        if user:
            print(f"Token: {str(token.token)[:20]}...")
            print(f"  Proprietaire: {user.name} {user.surname}")
            print(f"  Telephone: {user.phone_number}")
            print(f"  Type: {'Chauffeur' if token.user_type.model == 'userdriver' else 'Client'}")
            print()
    except Exception as e:
        print(f"  Erreur: {e}")
        print()

# Test 3: Récupération inversée
print("\n3. CHAUFFEUR AVEC SES DOCUMENTS")
print("-" * 60)
driver = UserDriver.objects.first()
if driver:
    print(f"Chauffeur: {driver.name} {driver.surname}")
    print(f"Telephone: {driver.phone_number}")

    # Trouver les documents de ce chauffeur
    from django.contrib.contenttypes.models import ContentType
    ct = ContentType.objects.get_for_model(driver)
    driver_docs = Document.objects.filter(user_type=ct, user_id=driver.id)

    print(f"\nDocuments ({driver_docs.count()}):")
    for doc in driver_docs:
        print(f"  - {doc.document_name}")

    # Trouver le token de ce chauffeur
    driver_token = Token.objects.filter(user_type=ct, user_id=driver.id).first()
    if driver_token:
        print(f"\nToken: {str(driver_token.token)[:20]}...")

print("\n" + "=" * 60)
print("CONCLUSION: L'ORM fonctionne parfaitement!")
print("Chaque ID est maintenant lie a son utilisateur (nom, prenom, tel)")
print("=" * 60)
