from django.contrib.admin.apps import AdminConfig

class OptimizerAdminConfig(AdminConfig):
    #name = "administration"
    default_site = 'administration.admin.OptimizerAdminSite'
