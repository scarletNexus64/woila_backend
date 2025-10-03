# Migration pour passer de driver_id a user_id/user_type (GenericForeignKey)
# Cette migration reflete les changements deja presents dans la base de donnees

from django.db import migrations, models
import django.db.models.deletion


def migrate_driver_id_to_generic(apps, schema_editor):
    """
    Migration de donnees : driver_id -> user_id avec user_type=UserDriver
    (Cette fonction ne sera pas executee car la migration sera fake)
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        # 1. Supprimer les modeles proxy non geres
        migrations.DeleteModel(
            name='OTPProxy',
        ),
        migrations.DeleteModel(
            name='ReferralCodeProxy',
        ),

        # 2. Ajouter user_type (ContentType) - nullable au debut
        migrations.AddField(
            model_name='referralcode',
            name='user_type',
            field=models.ForeignKey(
                null=True,  # Temporairement nullable
                on_delete=django.db.models.deletion.CASCADE,
                to='contenttypes.contenttype'
            ),
        ),

        # 3. Ajouter user_id - nullable au debut
        migrations.AddField(
            model_name='referralcode',
            name='user_id',
            field=models.PositiveIntegerField(null=True),  # Temporairement nullable
        ),

        # 4. Migrer les donnees de driver_id vers user_id/user_type
        migrations.RunPython(
            migrate_driver_id_to_generic,
            reverse_code=migrations.RunPython.noop,
        ),

        # 5. Rendre user_type et user_id obligatoires
        migrations.AlterField(
            model_name='referralcode',
            name='user_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='contenttypes.contenttype'
            ),
        ),
        migrations.AlterField(
            model_name='referralcode',
            name='user_id',
            field=models.PositiveIntegerField(),
        ),

        # 6. Supprimer driver_id
        migrations.RemoveField(
            model_name='referralcode',
            name='driver_id',
        ),

        # 7. Modifier le champ code (max_length 20 -> 8)
        migrations.AlterField(
            model_name='referralcode',
            name='code',
            field=models.CharField(max_length=8, unique=True),
        ),

        # 8. Modifier le champ otp_code dans OTPVerification (6 -> 4)
        migrations.AlterField(
            model_name='otpverification',
            name='otp_code',
            field=models.CharField(max_length=4),
        ),

        # 9. Ajouter la contrainte unique_together
        migrations.AlterUniqueTogether(
            name='referralcode',
            unique_together={('user_type', 'user_id')},
        ),
    ]
