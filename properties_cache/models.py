from django.db import models
from django.contrib.contenttypes import generic

from picklefield import PickledObjectField

from listeners import setup_signals


class PropertyCache(models.Model):
    name = models.CharField(max_length=64)
    value = PickledObjectField()

    content_type = models.ForeignKey('contenttypes.ContentType',
                    related_name='urls', verbose_name='content type')
    object_pk = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_pk')

    def __unicode__(self):
        return "Property cache %s for %s" % (\
                self.name, unicode(self.content_object))

    class Meta:
        # one property cache for one model instance
        unique_together = ('content_type', 'object_pk', 'name')


class PropertyCacheAbstract(models.Model):
    _props = {}
    '''
    # try to get property from cache if its available
    def __getattr__(self, name):
        # return property from chache if property available
        if name in self._props_cache:
            return self._props_cache[name]

        # return default
        return models.Model.__getattribute__(self, name)
    '''
    def set_cached_properties(self, properties):
        for prop in properties:
            self._props[prop.name] = prop.value

    class Meta:
        abstract = True


setup_signals(PropertyCacheAbstract)