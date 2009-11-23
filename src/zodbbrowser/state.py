from persistent import Persistent
from persistent.dict import PersistentDict
from persistent.mapping import PersistentMapping
from zope.component import adapts, getMultiAdapter
from zope.interface import implements, Interface
from zope.proxy import removeAllProxies
from zope.traversing.interfaces import IContainmentRoot
from ZODB.utils import u64

# be compatible with Zope 3.4, but prefer the modern package structure
try:
    from zope.container.sample import SampleContainer
except ImportError:
    from zope.app.container.sample import SampleContainer # BBB
try:
    from zope.container.ordered import OrderedContainer
except ImportError:
    from zope.app.container.ordered import OrderedContainer # BBB

from zodbbrowser.interfaces import IStateInterpreter, IObjectHistory


class ZodbObjectState(object):
    implements(IStateInterpreter)

    def __init__(self, obj, tid=None, _history=None):
        self.obj = removeAllProxies(obj)
        if _history is None:
            _history = IObjectHistory(self.obj)
        else:
            assert _history._obj is self.obj
        self.history = _history
        self.tid = None
        self.requestedTid = tid
        self._load()

    def _load(self):
        self.tid = self.history.lastChange(self.requestedTid)
        loadedState = self.history.loadState(self.tid)
        self.state = getMultiAdapter((self.obj, loadedState,
                                      self.requestedTid),
                                     IStateInterpreter)

    def listAttributes(self):
        return self.state.listAttributes()

    def listItems(self):
        return self.state.listItems()

    def getParent(self):
        return self.state.getParent()

    def getName(self):
        name = self.state.getName()
        if name is None:
            # __name__ is not in the pickled state, but it may be defined
            # via other means (e.g. class attributes, custom __getattr__ etc.)
            name = getattr(self.obj, '__name__', None)
        if not name:
            name = '???'
        return name

    def asDict(self):
        return self.state.asDict()

    # These are not part of IStateInterpreter

    def getObjectId(self):
        return u64(self.obj._p_oid)

    def isRoot(self):
        return IContainmentRoot.providedBy(self.obj)

    def getParentState(self):
        parent = self.getParent()
        if parent is None:
            return None
        else:
            return ZodbObjectState(parent, self.requestedTid)


class GenericState(object):
    """Most persistent objects represent their state as a dict."""
    adapts(Interface, dict, None)
    implements(IStateInterpreter)

    def __init__(self, type, state, tid):
        self.state = state
        self.tid = tid

    def getName(self):
        return self.state.get('__name__')

    def getParent(self):
        parent = self.state.get('__parent__')
        if self.tid and isinstance(parent, Persistent):
            parent.__setstate__(IObjectHistory(parent).loadState(self.tid))
        return parent

    def listAttributes(self):
        return self.state.items()

    def listItems(self):
        return None

    def asDict(self):
        return self.state


class PersistentDictState(GenericState):
    """Convenient access to a persistent dict's items."""
    adapts(PersistentDict, dict, None)

    def listItems(self):
        return sorted(self.state.get('data', {}).items())


class PersistentMappingState(GenericState):
    """Convenient access to a persistent mapping's items."""
    adapts(PersistentMapping, dict, None)

    def listItems(self):
        return sorted(self.state.get('data', {}).items())


class SampleContainerState(GenericState):
    """Convenient access to a SampleContainer's items"""
    adapts(SampleContainer, dict, None)

    def listItems(self):
        data = self.state.get('_SampleContainer__data')
        if not data:
            return []
        # data will be something persistent, maybe a PersistentDict, maybe a
        # OOBTree -- SampleContainer itself uses a plain Python dict, but
        # subclasses are supposed to overwrite the _newContainerData() method
        # and use something persistent.
        loadedstate = IObjectHistory(data).loadState(self.tid)
        return getMultiAdapter((data, loadedstate, self.tid),
                               IStateInterpreter).listItems()


class OrderedContainerState(GenericState):
    """Convenient access to an OrderedContainer's items"""
    adapts(OrderedContainer, dict, None)

    def listItems(self):
        container = OrderedContainer()
        container.__setstate__(self.state)
        # _data will be a PersistentDict
        container._data.__setstate__(
            IObjectHistory(container._data).loadState(self.tid))
        # _order will be a PersistentList
        container._order.__setstate__(
            IObjectHistory(container._order).loadState(self.tid))
        return container.items()


class FallbackState(object):
    """Fallback when we've got no idea how to interpret the state"""
    adapts(Interface, Interface, None)
    implements(IStateInterpreter)

    def __init__(self, type, state, tid):
        self.state = state

    def getName(self):
        return None

    def getParent(self):
        return None

    def listAttributes(self):
        return [('pickled state', self.state)]

    def listItems(self):
        return None

    def asDict(self):
        return dict(self.listAttributes())

