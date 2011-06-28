import logging
import copy

from django.db.models.signals import pre_delete, post_save
from django.db.models import get_models

from django.contrib.contenttypes.models import ContentType


__all__ = ('setup_signals', 'get_installed_methods', 'update_properties_set')


LOGGING_FORMAT = "properties_cache(%(levelname)s): %(asctime)-15s "\
                 "%(filename)s:%(lineno)s %(message)s"
logging.basicConfig(format=LOGGING_FORMAT)

HANDLERS_PROPERTIES = {}
INSTALLED_METHODS = []


class UpdatePropertiesHandlerBase(object):
    def __new__(cls, sender, instance, *args, **kwargs):
        from properties_cache.models import PropertyCache
        item_type = ContentType.objects.get_for_model(instance.__class__)

        logging.debug("Updating properties in %(instance)s (%(model)s) "\
                        "with %(func)s and props: %(props)s" % {
        'func': repr(cls.config['fnc']),
        'props': repr(cls.config['props']),
        'instance': instance,
        'model': sender,
        })

        #TODO: it's wrong, need to be rewritten
        object_pk = instance.pk

        # get bunch of target items to update
        items_to_update = cls.config['fnc'](instance)

        # interrupt properties update if no
        # related items available
        if not items_to_update:
            logging.debug("Interruption of updating of items "\
                          "because of no items to update")
            return

        # update list of items
        for item in items_to_update:
            for target_prop in cls.config['props']:
                # here we'll remove property in case
                # if listener called not post_save signal
                if kwargs['signal'] != post_save:
                    PropertyCache.objects.filter(
                                        content_type=item_type,
                                        object_pk=object_pk,
                                        name=target_prop).delete()
                    logging.debug("DELETE object %s with "\
                            "PK=%s" % (repr(instance), str(instance.pk)))
                    continue

                value = getattr(item, target_prop, None)
                if callable(value):
                    value = value()

                logging.debug(" >> Updating item %(item)s and "\
                              "property `%(property)s`='%(value)s" % {
                                'item': repr(item),
                                'property': target_prop,
                                'value': value,
                                })
                property, created = PropertyCache.objects.get_or_create(
                                    content_type=item_type,
                                    object_pk=object_pk,
                                    name=target_prop,
                                    defaults={
                                    'name': target_prop,
                                    'content_type': item_type,
                                    'object_pk': object_pk,
                                    'value': value,
                                    })
                # update only if not created
                if not created:
                    property.value = value
                    property.save()


def update_properties_set(fnc, props):
    """This decorator should update a set of properties which provided
    by list of methods in PropertiesCache class."""

    UpdatePropertiesHandler = copy.deepcopy(UpdatePropertiesHandlerBase)

    UpdatePropertiesHandler.config = {
    'fnc': fnc,
    'props': props,
    }

    return UpdatePropertiesHandler


def setup_self_handler(model, properties):
    """This method setup handler to update cache on own signals"""
    # setup signal for own model
    class UpdateSelfHandler(object):
        def __new__(cls, instance):
            return cls.model.objects.filter(pk__in=[instance.pk])

    UpdateSelfHandler.model = model
    UpdateSelfHandler.properties = properties
    UpdateSelfHandler.config = {
    'model': model,
    'properties': properties,
    }

    return UpdateSelfHandler


def check_config(config):
    """This method will check configuration and will fire exception
    in case with wrong configuration keys"""

    if not 'model' in config:
        # Raise configuration error
        raise Exception(u"You have to specify model which "\
                        u"signal should be attached to")

    if not 'properties' in config:
        # Raise configuration error
        raise Exception(u"You have to specify list of properties"\
                        u" which should be updated")


def setup_signals(base_class):
    """Setup signals based from PropertiesCache configuration in any model"""

    # go trough all models and find out PropertiesCache configs
    for model in get_models():
        logging.debug("Initializing PropertiesCache for %s" % repr(model))
        if hasattr(model, 'PropertiesCache'):
            if not hasattr(model.PropertiesCache, 'cached_properties'):
                continue

            # parse configuration and setup signals
            config = model.PropertiesCache
            config.update_self = setup_self_handler(model,
                                        config.cached_properties)

            # iterate over PropertiesCache class
            # and get all update handler functions
            for attr, val in config.__dict__.iteritems():
                # if attribute is method
                is_func = lambda aval: isinstance(aval, type(lambda: 0)) or \
                                       isinstance(aval, object)

                if not is_func(val) or (is_func(val) and \
                                        not hasattr(val, 'config')):
                    continue

                upd_func = val
                upd_config = val.config

                check_config(upd_config)

                target_model = upd_config['model']
                target_props = upd_config['properties']

                # connect additional model
                pair = (model, target_model, target_props)

                key = 'propscache_%s_%s' % (repr(target_model), repr(model))

                # add create/update/delete listeners
                post_save.connect(
                    update_properties_set(upd_func, target_props),
                    sender=target_model,
                    dispatch_uid='propscache_%s' % key)

                pre_delete.connect(
                    update_properties_set(upd_func,
                        target_props),
                    sender=target_model,
                    dispatch_uid='propscache_del_%s' % key)

                INSTALLED_METHODS.append(pair)


def get_installed_methods():
    """Return list of methods/models with added cache listeners"""
    return INSTALLED_METHODS
