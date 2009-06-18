from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.component import adapts
from zope.interface import Interface
from zope.security.proxy import removeSecurityProxy
from ZODB.utils import p64

from zodbbrowser.app import ZodbObject, ZodbObjectState


class BaseZodbView(BrowserView):

    def obj(self):
        if 'oid' not in self.request:
            return ZodbObject(self.context)
        else:
            oid = p64(int(self.request['oid']))
            jar = removeSecurityProxy(self.context)._p_jar
            obj = jar.get(oid)
            if 'tid' not in self.request:
                return ZodbObject(obj)
            else:
                tid = p64(int(self.request['tid']))
                state = jar.oldstate(obj, tid)
                return ZodbObjectState(obj, state, tid)


class ZodbTreeView(BaseZodbView):
    """Zodb info view"""

    adapts(Interface, IBrowserRequest)

    template = ViewPageTemplateFile('templates/zodbtree.pt')

    def __call__(self):
        self.update()
        return self.template()

    def update(self, show_private=False, *args, **kw):
        pass


class ZodbInfoView(BaseZodbView):
    """Zodb info view"""

    adapts(Interface, IBrowserRequest)

    template = ViewPageTemplateFile('templates/zodbinfo.pt')

    def __call__(self):
        self.update()
        return self.template()

    def update(self, show_private=False, *args, **kw):
        pass

