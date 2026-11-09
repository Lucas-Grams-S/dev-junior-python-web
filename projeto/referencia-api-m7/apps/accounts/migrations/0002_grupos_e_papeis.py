from django.contrib.auth.management import create_permissions
from django.db import migrations

PAPEIS = {
    "Estoquista": ["catalog.view_product", "catalog.change_product"],
    "Gerente": [
        "catalog.view_product", "catalog.add_product", "catalog.change_product", "catalog.delete_product",
        "catalog.view_category", "catalog.add_category", "catalog.change_category",
    ],
}


def criar_grupos(apps, schema_editor):
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    for nome, codigos in PAPEIS.items():
        grupo, _ = Group.objects.get_or_create(name=nome)
        grupo.permissions.set([Permission.objects.get(content_type__app_label=c.split(".")[0], codename=c.split(".")[1]) for c in codigos])


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial"), ("catalog", "0001_initial"), ("auth", "0012_alter_user_first_name_max_length")]
    operations = [migrations.RunPython(criar_grupos, migrations.RunPython.noop)]
