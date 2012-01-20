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

"""Flumotion interfaces used by the configuration assistant
"""

from zope.interface import Interface

__version__ = "$Rev$"


class IProducerPlugin(Interface):
    """A producer plugin is how you extend the production assistant page.
    The main purpose of the plugin is to get a assistant step specific
    to the plugin.
    This entry point should be defined in the xml for the component
    under the entry type "wizard".
    """

    def __call__(assistant):
        """Creates producer plugins
        @param assistant: the assistant
        @type assistant: L{ConfigurationAssistant}
        """

    def getProductionStep(type):
        """Asks the plugin for a step.
        type is the kind of plugin, it's useful for components such as
        firewire for which you can point both audio and video to the
        same plugin.
        @param type: audio or video
        @type type: string
        @returns: the assistant step
        @rtype: a L{WorkerWizardStep} subclass
        """


class IDecoderPlugin(Interface):

    def __call__(assistant):
        """Creates producer plugins
        @param assistant: the assistant
        @type assistant: L{ConfigurationAssistant}
        """

    def getDecodingStep(type):
        pass


class IEncoderPlugin(Interface):
    """An encoder plugin is how you extend the encoding assistant page.
    The main purpose of the plugin is to get a assistant step specific
    to the plugin.
    This entry point should be defined in the xml for the component
    under the entry type "wizard".
    """

    def __call__(assistant):
        """Creates encoder plugins
        @param assistant: the assistant
        @type assistant: L{ConfigurationAssistant}
        """

    def getConversionStep():
        """Asks the plugin for a step.
        @returns: the assistant step
        @rtype: a L{WorkerWizardStep} subclass
        """


class IConsumerPlugin(Interface):
    """A consumer plugin is how you extend the production assistant page.
    The main purpose of the plugin is to get a assistant step specific
    to the plugin.
    This entry point should be defined in the xml for the component
    under the entry type "wizard".
    """

    def __call__(assistant):
        """Creates producer plugins
        @param assistant: the assistant
        @type assistant: L{ConfigurationAssistant}
        """

    def getConsumptionStep(type):
        """Asks the plugin for a step.
        type is the kind of plugin.
        @param type: audio or video or audio-video
        @type type: string
        @returns: the assistant step
        @rtype: a L{WorkerWizardStep} subclass
        """


class IHTTPConsumerPlugin(Interface):
    """A http consumer plugin is how you extend the HTTP consumer page.
    The main purpose of the plugin is to get a consumer model
    (eg, a http server) specific for this plugin.
    This entry point should be defined in the xml for the component
    under the entry type "wizard".
    """

    def __call__(assistant, model):
        """Creates http consumer plugins
        @param assistant: the assistant
        @type assistant: L{ConfigurationAssistant}
        """

    def workerChanged(worker):
        """Called when the worker for the step changed.
        @param worker: the worker
        @type worker: L{WorkerComponentUIState}
        """

    def getPlugWizard(description):
        """Creates a plugin line for the consumer
        @param description: The text to appear in the line
        @type description: str
        @returns: wizard plugin line
        @rtype: a L{WizardPlugLine}
        """


class IHTTPConsumerPluginLine(Interface):

    def getConsumer(streamer, audio_producer, video_producer):
        """Asks the plugin line for a consumer model
        @param streamer: the http streamer
        @type streamer: L{HTTPStreamer} subclass
        @param audio_producer: audio producer for this stream
        @type audio_producer: L{AudioProducer} subclass
        @param video_producer: video producer for this stream
        @type video_producer: L{VideoProducer} subclass
        @returns: consumer
        @rtype: a L{HTTPServer} subclass
        """


class IHTTPServerPlugin(Interface):
    """A http server plugin allows to extend a HTTP server.
    The main purpose of the plugin is to get a wizard plug line that can be
    added into a plug area. The plugline should add/delete the plug from the
    http server model when activated/deactivated.
    This entry point should be defined in the xml for the plug
    under the entry type "wizard".
    """

    def __call__(assistant, component):
        """Creates http server plugins
        @param assistant: the assistant
        @type assistant: L{ConfigurationAssistant}
        @param component: the component that will receive the plug
        @type assistant: L{f.a.a.m.Component}
        """

    def workerChanged(worker):
        """Called when the worker for the step changed.
        @param worker: the worker
        @type worker: str
        """

    def getPlugWizard(description):
        """Creates a plugin line for the consumer
        @param description: The text to appear in the line
        @type description: str
        @returns: wizard plugin line
        @rtype: a L{WizardPlugLine}
        """


class IScenarioAssistantPlugin(Interface):
    """A pluggable scenario that can be listed at the first page of the wizard.
    It predefines the steps the wizard will take and the way it is saved.
    """

    def addSteps(assistant):
        """Called to add the required steps to the wizard.
        @param assistant: The assistant the steps have to be added to.
        @type  assistant: L{ConfigurationAssistant}
        """

    def save(assistant, saver):
        """Saves the scenario through an AdminSaver to get the configuration.
        @param assistant: The assistant the steps have to be added to.
        @type  assistant: L{ConfigurationAssistant}
        @param saver: The element which generates the xml configuration.
        @type  saver: L{AssistantSaver}
        """
