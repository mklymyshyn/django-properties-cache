#from django.core.management import call_command
#from django.db.models import loading
from django import test
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_delete

from properties_cache.listeners import setup_signals, get_installed_methods
from properties_cache.models import PropertyCacheAbstract, PropertyCache

from properties_cache.tests.models import PCRootModel, PCTestModel, \
                                                        PCTestChildModel

from properties_cache.managers import fill_properties_cache


class PropertiesCacheTestsBase(test.TestCase):
    def setUp(self):
        # re-call setup signals
        setup_signals(PropertyCacheAbstract)

        # re-install listeners
        self.root_objects = [PCRootModel.objects.create(**{
        'name': 'test-%d' % i,
        }) for i in range(5)]

        self.first_level = [PCTestModel.objects.create(**{
        'name': 'test-%d' % i,
        'parent': self.root_objects[i],
        }) for i in range(5)]

        self.second_level = [PCTestChildModel.objects.create(**{
        'name': 'test-%d' % i,
        'test_model': self.first_level[i],
        }) for i in range(5)]


class PropertiesCacheTests(PropertiesCacheTestsBase):

    def test_cache_signals_init(self):
        """Test initialization of properties cache signals"""

        binded_listeners = get_installed_methods()
        # essentially here should be two listeners for two properties
        # which attched to same model
        should_be_pairs = [
            (PCTestChildModel, PCTestChildModel, ['get_absolute_url',
                                                  'test_method']),
            (PCTestChildModel, PCRootModel, ['get_absolute_url']),
            (PCTestChildModel, PCTestModel, ['get_absolute_url',
                                             'test_method']),
        ]
        for pair in should_be_pairs:
            self.assertTrue(pair in binded_listeners, \
                    "Some of signals pair not properly initialized: "\
                    "%s != %s" % (repr(pair), \
                        repr(binded_listeners)))

    def test_properties_func(self):
        """Test signal listeners"""
        from properties_cache.listeners import update_properties_set
        PropertyCache.objects.all().delete()

        instance = PCTestChildModel.objects.all()[0]

        def upd_func(instance):
            return PCTestChildModel.objects.all()[0:1]

        count = PropertyCache.objects.all().count()

        # check update properties signal
        update_properties_set(upd_func, ['get_absolute_url'])(
                sender=instance.__class__, instance=instance,
                created=False, signal=post_save)

        self.assertEqual(PropertyCache.objects.all().count(),
                                    count + 1)

        # check remove object/property signal
        update_properties_set(upd_func, ['get_absolute_url'])(
                sender=instance.__class__, instance=instance,
                signal=pre_delete)

        self.assertEqual(PropertyCache.objects.all().count(),
                                    count)

    def test_cache_update(self):
        """Test update properties chache"""

        content_type = ContentType.objects.get_for_model(PCTestChildModel)
        # ger ogirinal url of first level object (will need below)
        url = self.second_level[0].get_absolute_url()

        # get count of all properties cache, it should be increased
        # when we'll create new child object
        count = PropertyCache.objects.all().count()

        # check count of child objects too
        model_count = PCTestChildModel.objects.all().count()

        # get count of properties to cache
        cached_methods_count = len(PCTestChildModel\
                                        .PropertiesCache.cached_properties)

        obj = PCTestChildModel.objects.create(**{
        'name': 'test-5',
        'test_model': self.first_level[0],
        })

        # count of child models should be increased for 1
        self.assertEqual(PCTestChildModel.objects.all().count(),
                                                    model_count + 1)

        self.assertEqual(PropertyCache.objects.all().count(), \
            count + cached_methods_count)

        count = PropertyCache.objects.filter(content_type=content_type,
                                                 object_pk=obj.pk).count()

        self.second_level[0].name = 'another-name'
        self.second_level[0].save()

        # update property cache, check that before/after count are same
        upd_count = PropertyCache.objects.filter(content_type=content_type,
                                                 object_pk=obj.pk).count()
        self.assertEqual(upd_count, count)
        self.assertNotEqual(url, self.second_level[0].get_absolute_url())
        self.assertTrue('another-name' in \
                                self.second_level[0].get_absolute_url())

    def test_cache_delete(self):
        """Test deletion of properties on instance deletion"""
        PropertyCache.objects.all().delete()
        count = PropertyCache.objects.all().count()

        # check count of child objects too
        model_count = PCTestChildModel.objects.all().count()

        # get count of properties to cache
        cached_methods_count = len(PCTestChildModel\
                                        .PropertiesCache.cached_properties)

        obj = PCTestChildModel.objects.create(**{
        'name': 'test-6',
        'test_model': self.first_level[0],
        })

        # count of child models should be increased for 1
        self.assertEqual(PCTestChildModel.objects.all().count(),
                                                    model_count + 1)

        self.assertEqual(PropertyCache.objects.all().count(), \
            count + cached_methods_count)

        obj.delete()

        self.assertEqual(PCTestChildModel.objects.all().count(),
                                                    model_count)

        self.assertEqual(PropertyCache.objects.all().count(), \
            count)


class PropertiesManagerTests(PropertiesCacheTestsBase):
    def setUp(self):
        super(self.__class__, self).setUp()

        self.objs = PCTestChildModel.objects.all()
        self.content_type = ContentType.objects\
                                    .get_for_model(PCTestChildModel)
        self.properties = PropertyCache.objects.filter(
                                content_type=self.content_type,
                                object_pk__in=[obj.pk for obj in self.objs])
        self.props_list = PCTestChildModel.PropertiesCache.cached_properties
        
    def test_fill_cache_function_naked(self):
        content_type = self.content_type
        properties = self.properties
        props_list = self.props_list

        fill_properties_cache(PCTestChildModel, self.objs)

        for obj in self.objs:
            for prop in props_list:
                property_key = '_pcache_%s' % prop
                try:
                    cached_prop = [cp.value for cp in properties if \
                                cp.object_pk == obj.pk and cp.name == prop][0]
                except:
                    raise AssertionError("Can't find value `%s` for `%d`" % (
                    prop, obj.pk))

                self.assertEqual(getattr(obj, property_key), cached_prop)

    def test_manager(self):
        content_type = self.content_type
        objs = self.objs.properties()
        properties = self.properties
        props_list = self.props_list
    
        for obj in objs:
            for prop in props_list:
                property_key = '_pcache_%s' % prop
                try:
                    cached_prop = [cp.value for cp in properties if \
                                cp.object_pk == obj.pk and cp.name == prop][0]
                except:
                    raise AssertionError("Can't find value `%s` for `%d`" % (
                    prop, obj.pk))

                self.assertEqual(getattr(obj, property_key), cached_prop)
