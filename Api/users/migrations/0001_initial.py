# Generated manually on 2025-10-03
# This migration reflects the current state of the database

from django.db import migrations, models
import users.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserDriver',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=15, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('name', models.CharField(max_length=100)),
                ('surname', models.CharField(max_length=100)),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female')], max_length=1)),
                ('age', models.IntegerField()),
                ('birthday', models.DateField()),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to=applications.users.models.profile_picture_upload_path, verbose_name='Photo de profil')),
                ('is_partenaire_interne', models.BooleanField(default=False, verbose_name='Partenaire Interne')),
                ('is_partenaire_externe', models.BooleanField(default=False, verbose_name='Partenaire Externe')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Chauffeur',
                'verbose_name_plural': 'Chauffeurs',
                'db_table': 'user_drivers',
            },
        ),
        migrations.CreateModel(
            name='UserCustomer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=15, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('name', models.CharField(blank=True, default='', max_length=100)),
                ('surname', models.CharField(blank=True, default='', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Client',
                'verbose_name_plural': 'Clients',
                'db_table': 'user_customers',
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(verbose_name='ID Utilisateur')),
                ('user_type', models.CharField(choices=[('driver', 'Chauffeur'), ('customer', 'Client')], max_length=10, verbose_name="Type d'utilisateur")),
                ('document_name', models.CharField(max_length=100, verbose_name='Nom du document')),
                ('file', models.FileField(upload_to=applications.users.models.document_upload_path, verbose_name='Fichier')),
                ('original_filename', models.CharField(max_length=255, verbose_name='Nom du fichier original')),
                ('file_size', models.IntegerField(verbose_name='Taille du fichier (bytes)')),
                ('content_type', models.CharField(max_length=100, verbose_name='Type de contenu')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name="Date d'import")),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
            ],
            options={
                'verbose_name': 'Document',
                'verbose_name_plural': 'Documents',
                'db_table': 'documents',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
