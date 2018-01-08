

import types
from functools import lru_cache
from traitlets import traitlets
from ipytunnel.comm import Comm as CheapComm



def patch_has_descriptor(has_descriptor_cls, **overrides):
    for name, descriptor in overrides.items():
        setattr(has_descriptor_cls, name, descriptor)
        descriptor.class_init(has_descriptor_cls, name)



def optimize(optimize_comm=True, optimize_traits=True, cache_size=1024):
    if optimize_traits:

        @lru_cache(cache_size)
        def cache_cls_dir(cls):
            return dir(cls)

        @lru_cache(cache_size)
        def cache_trait_cls(cls, key):
            # Some descriptors raise AttributeError like zope.interface's
            # __provides__ attributes even though they exist.  This causes
            # AttributeErrors even though they are listed in dir(cls).
            try:
                value = getattr(cls, key)
            except AttributeError:
                pass
            else:
                if isinstance(value, traitlets.BaseDescriptor):
                    return value


        def quick_setup_instance(self, *args, **kwargs):
            # Optimizie by caching dir, getattr and isinstance calls
            self._cross_validation_lock = False
            cls = self.__class__
            for key in cache_cls_dir(cls):
                value = cache_trait_cls(cls, key)
                if value:
                    value.instance_init(self)

        traitlets.HasDescriptors.setup_instance = quick_setup_instance


        @lru_cache(cache_size)
        def cache_gen_traits(cls):
            # Cache to avoid getmembers/isinstance calls
            return dict([memb for memb in traitlets.getmembers(cls) if
                        isinstance(memb[1], traitlets.TraitType)])

        @lru_cache(cache_size)
        def can_cache_metadata(**metadata):
            # Whether the metadata arguments allow for caching of checks
            # If the value if a function type, the result is not guaranteed
            # to be independent of outside state, so then we cannot cache.
            for meta_name, meta_eval in metadata.items():
                if type(meta_eval) is types.FunctionType:
                    return False
            return True

        @lru_cache(cache_size)
        def cache_filter_traits(cls, **metadata):
            traits = cache_gen_traits(cls)
            result = {}
            for name, trait in traits.items():
                for meta_name, meta_eval in metadata.items():
                    if type(meta_eval) is not types.FunctionType:
                        meta_eval = traitlets._SimpleTest(meta_eval)
                    if not meta_eval(trait.metadata.get(meta_name, None)):
                        break
                else:
                    result[name] = trait

            return result

        def quick_traits(self, **metadata):
            if len(metadata) == 0:
                return cache_gen_traits(self.__class__)
            if can_cache_metadata(**metadata):
                return cache_filter_traits(self.__class__, **metadata)
            else:
                return cache_filter_traits.__wrapped__(self.__class__, **metadata)

        traitlets.HasTraits.traits = quick_traits

    if optimize_comm:

        import ipywidgets.widgets.widget as widget

        # Allow Widget.comm to either be default comm, or our cheap comm
        patch_has_descriptor(widget.Widget, comm=traitlets.Union(
            [
                traitlets.Instance(CheapComm, allow_none=widget.Widget.comm.allow_none),
                widget.Widget.comm,
            ],
            allow_none=widget.Widget.comm.allow_none
        ))
        widget.Comm = CheapComm
