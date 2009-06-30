from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.component import adapts
from zope.interface import Interface
from zope.security.proxy import removeSecurityProxy
from ZODB.utils import p64

from zodbbrowser.app import ZodbObject


class ZodbInfoView(BrowserView):
    """Zodb info view"""

    adapts(Interface, IBrowserRequest)

    template = ViewPageTemplateFile('templates/zodbinfo.pt')

    def __call__(self):
        self.update()
        return self.template()

    def update(self, show_private=False, *args, **kw):
        pass

    def obj(self):
        obj = None

        if 'oid' not in self.request:
            obj = ZodbObject(self.context)
        else:
            oid = p64(int(self.request['oid']))
            jar = removeSecurityProxy(self.context)._p_jar
            obj = ZodbObject(jar.get(oid))

        if 'tid' not in self.request:
            obj.load()
        else:
            obj.load(p64(int(self.request['tid'])))

        return obj
