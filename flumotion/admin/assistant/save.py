# -*- Mode: Python; test-case-name: flumotion.test.test_wizard -*-
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
import re

from flumotion.admin.assistant.configurationwriter import ConfigurationWriter
from flumotion.admin.assistant.models import Muxer, AudioProducer, \
     VideoProducer, AudioEncoder, VideoEncoder, Decoder

_ = gettext.gettext
__version__ = "$Rev$"


class AssistantSaver(object):
    """I am used to link components together and generate XML for them.
    To use me, add some components by some of the methods and then call
    my getXML() method to get the xml configuration.
    """

    def __init__(self):
        self._existingComponentNames = []
        self._flowComponents = []
        self._atmosphereComponents = []
        self._muxers = {}
        self._flowName = None
        self._audioProducer = None
        self._videoProducer = None
        self._audioDecoder = None
        self._videoDecoder = None
        self._audioEncoder = None
        self._videoEncoder = None
        self._videoOverlay = None
        self._useCCLicense = False
        self._muxerType = None
        self._muxerWorker = None
        self._confXml = None

    # Public API

    def setFlowName(self, flowName):
        """Sets the name of the flow we're saving.
        @param flowName:
        @type flowName: string
        """
        self._flowName = flowName

    def setAudioProducer(self, audioProducer):
        """Attach a audio producer for this flow
        @param audioProducer: audio producer
        @type audioProducer: L{AudioProducer} subclass or None
        """
        if (audioProducer is not None and
            not isinstance(audioProducer, AudioProducer)):
            raise TypeError(
                "audioProducer must be a AudioProducer subclass, not %r" % (
                audioProducer, ))
        self._audioProducer = audioProducer

    def setVideoProducer(self, videoProducer):
        """Attach a video producer for this flow
        @param videoProducer: video producer
        @type videoProducer: L{VideoProducer} subclass or None
        """
        if (videoProducer is not None and
            not isinstance(videoProducer, VideoProducer)):
            raise TypeError(
                "videoProducer must be a VideoProducer subclass, not %r" % (
                videoProducer, ))
        self._videoProducer = videoProducer

    def setVideoDecoder(self, decoder):
        """Attach a decoder component for this flow
        @param decoder: decoder
        @type decoder: L{Decoder} subclass or None
        """
        if (decoder is not None and
            not isinstance(decoder, Decoder)):
            raise TypeError(
                "decoder must be a Decoder subclass, not %r" % (
                decoder, ))
        self._videoDecoder = decoder

    def setAudioDecoder(self, decoder):
        """Attach a decoder component for this flow
        @param decoder: decoder
        @type decoder: L{Decoder} subclass or None
        """
        if (decoder is not None and
            not isinstance(decoder, Decoder)):
            raise TypeError(
                "decoder must be a Decoder subclass, not %r" % (
                decoder, ))
        self._audioDecoder = decoder

    def setVideoOverlay(self, videoOverlay):
        if not self._videoProducer:
            raise ValueError(
                "You can't add a video overlay component without "
                "first setting a video producer")
        self._videoOverlay = videoOverlay

    def setAudioEncoder(self, audioEncoder):
        """Attach a audio encoder for this flow
        @param audioEncoder: audio encoder
        @type audioEncoder: L{AudioEncoder} subclass or None
        """
        if (audioEncoder is not None and
            not isinstance(audioEncoder, AudioEncoder)):
            raise TypeError(
                "audioEncoder must be a AudioEncoder subclass, not %r" % (
                audioEncoder, ))
        self._audioEncoder = audioEncoder

    def setVideoEncoder(self, videoEncoder):
        """Attach a video encoder for this flow
        @param videoEncoder: video encoder
        @type videoEncoder: L{VideoEncoder} subclass or None
        """
        if (videoEncoder is not None and
            not isinstance(videoEncoder, VideoEncoder)):
            raise TypeError(
                "videoEncoder must be a VideoEncoder subclass, not %r" % (
                videoEncoder, ))
        self._videoEncoder = videoEncoder

    def setMuxer(self, muxerType, muxerWorker):
        """Adds the necessary state to be able to create a muxer
        for this flow.
        @param muxerType:
        @type muxerType: string
        @param muxerWorker: name of the worker
        @type muxerWorker: string
        """
        self._muxerType = muxerType
        self._muxerWorker = muxerWorker

    def addMuxer(self, muxerType, muxer):
        """Adds an existing muxer to the flow. This way it will be reused and
        the saver won't create a new one. Used when adding a new streamer.
        @param muxerType: type of the muxer, one of audio/video/audio-video
        @type muxerType: str
        @param muxer: a muxer model
        @type muxer: L{Muxer}
        """
        self._muxers[muxerType] = muxer

    def addServerConsumer(self, server, consumerType):
        """Add a server consumer. Currently limited a to http-server
        server consumers
        @param server: server consumer
        @type server:
        @param consumerType: the type of the consumer, one of
          audio/video/audio-video
        @type consumerType: string
        """
        server.name = 'http-server-%s' % (consumerType, )
        self._atmosphereComponents.append(server)

    def addPorter(self, porter, consumerType):
        """Add a porter
        @param porter: porter
        @type porter:
        @param consumerType: the type of the consumer, one of
          audio/video/audio-video
        @type consumerType: string
        """
        porter.name = 'porter-%s' % (consumerType, )
        self._atmosphereComponents.append(porter)

    def addConsumer(self, consumer, consumerType):
        """Add a consumer
        @param consumer: consumer
        @type consumer:
        @param consumerType: the type of the consumer, one of
          audio/video/audio-video
        @type consumerType: string
        """
        # [disk,http,shout2]-[audio,video,audio-video]
        consumer.name = consumer.prefix + '-' + consumerType

        self._getMuxer(consumerType).link(consumer)
        self._flowComponents.append(consumer)

    def setUseCCLicense(self, useCCLicense):
        """Sets if we should use a Creative Common license on
        the created flow. This will overlay an image if we do
        video streaming.
        @param useCCLicense: if we should use a CC license
        @type useCCLicense: bool
        """
        self._useCCLicense = useCCLicense

    def getXML(self):
        """Creates an XML configuration of the state set
        @returns: the xml configuration
        @rtype: string
        """
        if self._confXml:
            return self._confXml

        self._handleProducers()
        self._handleMuxers()
        # Naming conflicts can only be solved after the rest is done,
        # since some components might get removed
        self._resolveNameConflicts()
        self._validateComponents()

        writer = ConfigurationWriter(self._flowName,
                                     self._flowComponents,
                                     self._atmosphereComponents)
        xml = writer.getXML()
        return xml

    def setFlowFile(self, xmlFile):
        self._confXml = open(xmlFile, 'r').read()

    def setExistingComponentNames(self, componentNames):
        """Tells the saver about the existing components available, so
        we can resolve naming conflicts before fetching the configuration xml
        @param componentNames: existing component names
        @type componentNames: list of strings
        """
        self._existingComponentNames = componentNames

    def getFlowComponents(self):
        """Gets the flow components of the save instance
        @returns: the flow components
        @rtype: list of components
        """
        return self._flowComponents

    def getAtmosphereComponents(self):
        """Gets the atmosphere components of the save instance
        @returns: the atmosphere components
        @rtype: list of components
        """
        return self._atmosphereComponents

    # Private API

    def _getAllComponents(self):
        return self._atmosphereComponents + self._flowComponents

    def _getMuxer(self, name):
        if name in self._muxers:
            muxer = self._muxers[name]
        else:
            muxer = Muxer()
            muxer.name = 'muxer-' + name
            muxer.componentType = self._muxerType
            muxer.worker = self._muxerWorker
            self._muxers[name] = muxer
        return muxer

    def _handleProducers(self):
        self._handleAudioProducer()
        self._handleVideoProducer()
        self._handleVideoOverlay()
        self._handleSameProducers()

    def _handleAudioProducer(self):
        if not self._audioProducer:
            return

        if not self._audioProducer.name:
            self._audioProducer.name = 'producer-audio'

        self._flowComponents.append(self._audioProducer)

        if self._audioEncoder is None:
            raise ValueError("You need to set an audio encoder")

        self._audioEncoder.name = 'encoder-audio'
        self._flowComponents.append(self._audioEncoder)

        if not self._audioDecoder:
            self._audioProducer.link(self._audioEncoder)
        else:
            self._audioDecoder.name = 'decoder-audio'
            self._flowComponents.append(self._audioDecoder)
            self._audioProducer.link(self._audioDecoder)
            self._audioDecoder.link(self._audioEncoder)

    def _handleVideoProducer(self):
        if not self._videoProducer:
            return

        if not self._videoProducer.name:
            self._videoProducer.name = 'producer-video'

        self._flowComponents.append(self._videoProducer)

        if self._videoEncoder is None:
            raise ValueError("You need to set a video encoder")

        self._videoEncoder.name = 'encoder-video'
        self._flowComponents.append(self._videoEncoder)

        if not self._videoDecoder:
            self._videoProducer.link(self._videoEncoder)
        else:
            self._videoDecoder.name = 'decoder-video'
            self._flowComponents.append(self._videoDecoder)
            self._videoProducer.link(self._videoDecoder)
            self._videoDecoder.link(self._videoEncoder)

    def _handleVideoOverlay(self):
        if not self._videoOverlay:
            return

        producer = self._videoDecoder or self._videoProducer
        producer.unlink(self._videoEncoder)

        producer.link(self._videoOverlay)
        self._videoOverlay.link(self._videoEncoder)
        self._flowComponents.append(self._videoOverlay)

        self._videoOverlay.name = 'overlay-video'

        if not self._videoOverlay.show_logo:
            return

        # FIXME: This should probably not be done here.
        self._videoOverlay.properties.fluendo_logo = True
        if self._muxerType == 'ogg-muxer':
            self._videoOverlay.properties.xiph_logo = True

        if self._useCCLicense:
            self._videoOverlay.properties.cc_logo = True

    def _handleSameProducers(self):
        # In the case video producer and audio producer is the same
        # component and on the same worker, remove the audio producer and
        # rename the video producer.
        video = self._videoProducer
        audio = self._audioProducer
        if (video is not None and
            audio is not None and
            video == audio):
            self._flowComponents.remove(self._audioProducer)
            if not audio.exists:
                self._audioProducer.name = 'producer-audio-video'
            if not video.exists:
                self._videoProducer.name = 'producer-audio-video'
            self._audioProducer = self._videoProducer
            if self._videoDecoder:
                self._videoDecoder.name = 'decoder-audio-video'
                self._audioDecoder = self._videoDecoder

    def _handleMuxers(self):
        for muxerName, components in [('audio', [self._audioEncoder]),
                                      ('video', [self._videoEncoder]),
                                      ('audio-video', [self._audioEncoder,
                                                       self._videoEncoder])]:
            muxer = self._getMuxer(muxerName)
            if muxer.feeders:
                self._flowComponents.append(muxer)
                for component in components:
                    component and component.link(muxer)

    def _resolveNameConflicts(self):
        for component in self._getAllComponents():
            self._resolveComponentName(component)

    def _resolveComponentName(self, component):
        # If the component already exists, do not suggest a new name,
        # since we want to link to it
        if component.exists:
            return
        name = component.name
        while name in self._existingComponentNames:
            name = self._suggestName(name)

        component.name = name
        self._existingComponentNames.append(name)

    def _suggestName(self, suggestedName):
        # Resolve naming conflicts, using a simple algorithm
        # First, find all the trailing digits, for instance in
        # 'audio-producer42' -> '42'
        pattern = re.compile('(\d*$)')
        match = pattern.search(suggestedName)
        trailingDigit = match.group()

        # Now if we had a digit in the end, convert it to
        # a number and increase it by one and remove the trailing
        # digits the existing component name
        if trailingDigit:
            digit = int(trailingDigit) + 1
            suggestedName = suggestedName[:-len(trailingDigit)]
        # No number in the end, use 2 the first one so we end up
        # with 'audio-producer' and 'audio-producer2' in case of
        # a simple conflict
        else:
            digit = 2
        return suggestedName + str(digit)

    def _validateComponents(self):
        for component in self._getAllComponents():
            # There's no need to validate existing components,
            # that allows us to provide 'fake' existing components,
            # which simplifies sending incremental configuration snippets
            # from the admin client
            if component.exists:
                continue
            component.validate()
