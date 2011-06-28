from django.db import models

from properties_cache.models import PropertyCacheAbstract
from properties_cache.managers import PropertiesCacheManager


__all__ = ('PCRootModel', 'PCTestModel', 'PCTestChildModel')


class PCRootModel(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class PCTestModel(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(PCRootModel, related_name='children')

    def __unicode__(self):
        return self.name


class PCTestChildModel(PropertyCacheAbstract):
    test_model = models.ForeignKey(PCTestModel, related_name='test_models')
    name = models.CharField(max_length=255)

    objects = PropertiesCacheManager()

    def get_absolute_url(self):
        return "%s/%s/%s" % (self.test_model.parent.name,
                                    self.test_model.name, self.name)

    def test_method(self):
        return "Parent model: %s, current model: %s" % (\
                                        self.test_model.name, self.name)

    class PropertiesCache:
        cached_properties = [
        'get_absolute_url',
        'test_method',
        ]

        def update_on_pcrootmodel_change(instance):
            """This method shoudl return queryset of instances which should
            be updated or None"""
            return PCTestChildModel.objects.filter(\
                        test_model__parent=instance)

        update_on_pcrootmodel_change.config = {
            'model': PCRootModel,
            'properties': ['get_absolute_url'],
        }

        def update_on_pctestmodel_change(instance):
            return PCTestChildModel.objects.filter(\
                        test_model=instance)

        update_on_pctestmodel_change.config = {
            'model': PCTestModel,
            'properties': ['get_absolute_url', 'test_method'],
        }
