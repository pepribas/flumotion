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
from flumotion.admin.assistant.models import AudioProducer, VideoProducer
from flumotion.admin.gtk.basesteps import AudioProducerStep, VideoProducerStep

__version__ = "$Rev$"
_ = gettext.gettext


class FGDPProducer(AudioProducer, VideoProducer):
    componentType = 'fgdp-producer'
    prefix = 'fgdp'
    isEncoded = True

    def __init__(self):
        super(FGDPProducer, self).__init__()
        self.properties.port = 15000
        self.properties.username = 'user'
        self.properties.password = 'test'


class _FGDPCommon:
    gladeFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'wizard.glade')
    name = 'Flumotion Producer'
    title = _('Flumotion Producer')
    sidebarName = _('FGDP')
    docSection = 'help-configuration-assistant-fgdp-producer'
    docAnchor = ''
    docVersion = 'local'

    # WizardStep

    def setup(self):
        self.port.data_type = int
        self.username.data_type = str
        self.password.data_type = str

        self.add_proxy(self.model.properties,
                       ['port',
                        'username',
                        'password'])

    def workerChanged(self, worker):
        self.model.worker = worker
        self.wizard.checkElements(worker, 'fgdpsrc')


class FGDPVideoStep(_FGDPCommon, VideoProducerStep):

    def __init__(self, wizard, model):
        VideoProducerStep.__init__(self, wizard, model)


class FGDPAudioStep(_FGDPCommon, AudioProducerStep):

    def __init__(self, wizard, model):
        AudioProducerStep.__init__(self, wizard, model)


class FGDPProducerWizardPlugin(object):
    implements(IProducerPlugin)

    def __init__(self, wizard):
        self.wizard = wizard

    def getProductionStep(self, type):
        if type == 'audio':
            return FGDPAudioStep(self.wizard, FGDPProducer())
        elif type == 'video':
            return FGDPVideoStep(self.wizard, FGDPProducer())

