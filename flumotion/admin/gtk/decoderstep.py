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

from flumotion.admin.assistant.interfaces import IDecoderPlugin
from flumotion.admin.assistant.models import Decoder, VideoProducer, \
     AudioProducer
from flumotion.admin.gtk.workerstep import WorkerWizardStep

__version__ = "$Rev$"
_ = gettext.gettext


class GenericDecoder(Decoder):
    """I am a component which decodes an encoded stream
    """

    componentType = 'single-generic-decoder'

    def __init__(self, media_type='audio'):
        super(GenericDecoder, self).__init__()
        self.properties.media_type = media_type


class GenericDecoderStep(WorkerWizardStep):
    title = _('Generic Decoder')
    gladeFile = 'decoder-wizard.glade'
    docSection = 'help-configuration-assistant-generic-decoder'
    docAnchor = ''
    docVersion = 'local'
    mediaType = None

    def __init__(self, wizard, encodedProducer):
        if isinstance(encodedProducer, VideoProducer):
            self.name = 'VideoDecoder'
            self.mediaType = 'video'
        elif isinstance(encodedProducer, AudioProducer):
            self.name = 'AudioDecoder'
            self.mediaType = 'audio'
        self.model = GenericDecoder(self.mediaType)
        WorkerWizardStep.__init__(self, wizard)

    # Public API

    def getDecoder(self):
        return self.model

    # WizardStep

    def setup(self):
        pass

    def workerChanged(self, worker):
        self.model.worker = worker
        self.wizard.requireElements(worker, 'decodebin2')

    def getNext(self):
        if self.mediaType == 'video':
            from flumotion.admin.gtk.overlaystep import OverlayStep
            return OverlayStep(self.wizard, self.model)
        return None


class GenericDecoderPlugin(object):
    implements(IDecoderPlugin)

    def __init__(self, wizard):
        self.wizard = wizard
        self.model = GenericDecoder()

    def getDecodingStep(self, type):
        return GenericDecoderStep(self.wizard, self.model)
