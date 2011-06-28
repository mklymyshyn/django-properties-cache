from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType

from model_utils.managers import PassThroughManager

from properties_cache.models import PropertyCache


__all__ = ('PropertiesCacheManager', 'PropertiesCacheQuerySet',
           'fill_properties_cache')


CACHED_TYPES = {}


def fill_properties_cache(model, queryset):
    """Fill some generic queryset for specific model with properties cache"""
    # cache content type if it's not cached already
    if model not in CACHED_TYPES:
        CACHED_TYPES[model] = ContentType.objects.get_for_model(model)

    ctype = CACHED_TYPES[model]
    pks = [obj.pk for obj in queryset]
    pcache = PropertyCache.objects.filter(content_type=ctype,
                                          object_pk__in=pks)\
                                  .defer('object_pk', 'name', 'value')

    attrs = model.PropertiesCache.cached_properties

    for obj in queryset:
        cached_props = {}
        [cached_props.update({prop.name: prop.value})\
            for prop in pcache if prop.object_pk == obj.pk]

        for attr in attrs:
            setattr(obj, '_pcache_%s' % attr, cached_props.get(attr))

    return queryset


class PropertiesCacheQuerySet(QuerySet):
    def properties(self):
        return fill_properties_cache(self.model, self)


class PropertiesCacheManager(PassThroughManager):
    def get_query_set(self):
        return PropertiesCacheQuerySet(self.model, using=self._db)
