# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# Flumotion - a streaming media server
# Copyright (C) 2004,2005,2006,2007,2008,2009 Fluendo, S.L.
# Copyright (C) 2010,2011 Flumotion Services, S.A.
# All rights reserved.
#
# This file may be distributed and/or modified under the terms of
# the GNU Lesser General Public License version 2.1 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.LGPL" in the source distribution for more information.
#
# Headers in this file shall remain intact.

import gettext
import os

from zope.interface import implements

from flumotion.admin.assistant.interfaces import IProducerPlugin
from flumotion.admin.assistant.models import AudioProducer
from flumotion.admin.gtk.basesteps import AudioProducerStep

__version__ = "$Rev$"
_ = gettext.gettext


class IcecastProducer(AudioProducer):
    componentType = 'icecast-producer'
    isEncoded = True

    def __init__(self):
        super(IcecastProducer, self).__init__()

        self.properties.url = 'http://scfire-mtc-aa03.stream.aol.com:80/stream/1048'
        self.properties.passthrough = True


class IcecastProducerStep(AudioProducerStep):
    name = 'IcecastProducer'
    title = _('Icecast Producer')
    icon = 'soundcard.png'
    gladeFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'wizard.glade')
    docSection = 'help-configuration-assistant-producer-icecast'
    docAnchor = ''
    docVersion = 'local'

    # WizardStep

    def setup(self):
        self.url.data_type = str

        self.add_proxy(self.model.properties, ['url'])


    def workerChanged(self, worker):
        self.model.worker = worker
        self.wizard.requireElements(worker, 'souphttpsrc')


class IcecastWizardPlugin(object):
    implements(IProducerPlugin)

    def __init__(self, wizard):
        self.wizard = wizard
        self.model = IcecastProducer()

    def getProductionStep(self, type):
        return IcecastProducerStep(self.wizard, self.model)
