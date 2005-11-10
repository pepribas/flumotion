# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Flumotion - a streaming media server
# Copyright (C) 2004,2005 Fluendo, S.L. (www.fluendo.com). All rights reserved.

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.GPL" in the source distribution for more information.

# Licensees having purchased or holding a valid Flumotion Advanced
# Streaming Server license may use this file in accordance with the
# Flumotion Advanced Streaming Server Commercial License Agreement.
# See "LICENSE.Flumotion" in the source distribution for more information.

# Headers in this file shall remain intact.

"""
the job-side half of the worker-job connection
"""

import os
import resource

# I've read somewhere that importing the traceback module messes up the
# exception state, so it's better to import it globally instead of in the
# exception handler
import traceback

from twisted.cred import credentials
from twisted.internet import reactor
from twisted.python import reflect, failure
from twisted.spread import pb

from flumotion.common import config, errors, interfaces, log, registry, keycards
from flumotion.common import medium, package
from flumotion.component import component
from flumotion.twisted.defer import defer_generator_method

def getComponent(dict, moduleName, methodName):
    """
    @param dict:       the configuration dictionary
    @type  dict:       dict
    @param moduleName: name of the module to create the component from
    @type  moduleName: string
    @param methodName: the factory method to use to create the component
    @type  methodName: string
    """
    log.debug('component', 'Loading moduleName %s' % moduleName)
    try:
        module = reflect.namedAny(moduleName)
    except ValueError:
        raise config.ConfigError("module %s could not be found" % moduleName)
    except ImportError, e:
        raise config.ConfigError("module %s could not be imported (%s)" % (
            moduleName, e))
    except SyntaxError, e:
        raise config.ConfigError("module %s has a syntax error in %s:%d" % (
            moduleName, e.filename, e.lineno))
    except Exception, e:
        raise config.ConfigError(
            "Exception %r during import of module %s (%r)" % (
                e.__class__.__name__, moduleName, e.args))
        
    if not hasattr(module, methodName):
        log.warning('job', 'no %s in module %s' % (methodName, moduleName))
        return
        
    # Create the component with the specified configuration
    # directives. Note that this can't really be moved from here
    # since it gets called by the job from another process
    # and we don't want to create it in the main process, since
    # we're going to listen to ports and other stuff which should
    # be separated from the main process.

    log.debug('job', 'calling %s.%s(dict)' % (moduleName, methodName))
    try:
        component = getattr(module, methodName)(dict)
    except config.ConfigError:
        # already nicely formatted, so fall through
        raise
    except Exception, e:
        msg = log.getExceptionMessage(e)
        log.warning('job', msg)
        # FIMXE: we probably want another error raised here
        log.warning('job', 'raising config.ConfigError')
        raise config.ConfigError(msg)
    log.debug('job', 'returning component %r' % component)
    return component

class JobMedium(medium.BaseMedium):
    """
    I am a medium between the job and the worker's job avatar.
    I live in the job process.
    """
    logCategory = 'jobmedium'

    __implements__ = interfaces.IJobMedium,

    def __init__(self):
        self.avatarId = None
        self.logName = None
        self.component = None
        self.worker_name = None
        self.manager_host = None
        self.manager_port = None
        self.manager_transport = None
        self.manager_keycard = None

    ### pb.Referenceable remote methods called on by the WorkerBrain
    def remote_bootstrap(self, workerName, host, port, transport, keycard,
            packagePaths):
        """
        I receive the information on how to connect to the manager. I also set
        up package paths to be able to run the component.
        
        Called by the worker's JobAvatar.
        
        @param workerName:   the name of the worker running this job
        @type  workerName:   str
        @param host:         the host that is running the manager
        @type  host:         str
        @param port:         port on which the manager is listening
        @type  port:         int
        @param transport:    'tcp' or 'ssl'
        @type  transport:    string
        @param keycard:      credentials used to log in to the manager
        @type  keycard:      L{flumotion.common.keycards.Keycard}
        @param packagePaths: ordered list of (package name, package path) tuples
        @type  packagePaths: list of (str, str)
        """
        assert isinstance(workerName, str)
        assert isinstance(host, str)
        assert isinstance(port, int)
        assert transport in ('ssl', 'tcp')
        assert isinstance(keycard, keycards.Keycard)
        assert isinstance(packagePaths, list)

        self.debug('bootstrap')
        self.worker_name = workerName
        self.manager_host = host
        self.manager_port = port
        self.manager_transport = transport
        self.manager_keycard = keycard
        
        packager = package.getPackager()
        for name, path in packagePaths:
            self.debug('registering package path for %s' % name)
            self.log('... from path %s' % path)
            packager.registerPackagePath(path, name)

    def remote_start(self, avatarId, type, moduleName, methodName, config,
        feedPorts):
        """
        I am called on by the worker's JobAvatar to start a component.
        
        @param avatarId:   avatarId for component to log in to manager
        @type  avatarId:   string
        @param type:       type of component to start
        @type  type:       string
        @param moduleName: name of the module to create the component from
        @type  moduleName: string
        @param methodName: the factory method to use to create the component
        @type  methodName: string
        @param config:     the configuration dictionary
        @type  config:     dict
        @param feedPorts:  feedName -> port
        @type  feedPorts:  dict
        """
        self.avatarId = avatarId
        self.logName = avatarId

        self._runComponent(avatarId, type, moduleName, methodName, config,
            feedPorts)

    def remote_stop(self):
        self.debug('remote_stop() called')
        # stop reactor from a callLater so this remote method finishes
        # nicely
        reactor.callLater(0, self.shutdown)

    ### our methods
    def shutdown(self):
        """
        Shut down the job process completely, cleaning up the component
        so the reactor can be left from.
        """
        if self.component:
            self.debug('stopping component')
            self.component.stop()
            self.debug('stopped component')
        self.debug('stopping reactor')
        reactor.stop()
        self.debug('reactor stopped, exiting process')

        # FIXME: temporary hack
        os._exit(0)

    def _set_nice(self, nice):
        if not nice:
            return
        
        try:
            os.nice(nice)
        except OSError, e:
            self.warning('Failed to set nice level: %s' % str(e))
        else:
            self.debug('Nice level set to %d' % nice)

    def _enable_core_dumps(self):
        soft, hard = resource.getrlimit(resource.RLIMIT_CORE)
        if hard != resource.RLIM_INFINITY:
            self.warning('Could not set unlimited core dump sizes, '
                         'setting to %d instead' % hard)
        else:
            self.debug('Enabling core dumps of unlimited size')
            
        resource.setrlimit(resource.RLIMIT_CORE, (hard, hard))
        
    def _runComponent(self, avatarId, type, moduleName, methodName, config,
        feedPorts):
        """
        @param avatarId:   avatarId component will use to log in to manager
        @type  avatarId:   string
        @param type:       type of component to start
        @type  type:       string
        @param moduleName: name of the module that contains the entry point
        @type  moduleName: string
        @param methodName: name of the factory method to create the component
        @type  methodName: string
        @param config:     the configuration dictionary
        @type  config:     dict
        @param feedPorts: feedName -> port
        @type  feedPorts: dict
        """
        
        self.info('Starting component "%s" of type "%s"' % (avatarId, type))
        #self.info('setting up signals')
        #signal.signal(signal.SIGINT, signal.SIG_IGN)

        self.debug('Starting on pid %d of type %s' % (os.getpid(), type))

        self._set_nice(config.get('nice', 0))
        self._enable_core_dumps()
        
        self.debug('_runComponent(): config dictionary is: %r' % config)
        self.debug('_runComponent(): feedPorts is: %r' % feedPorts)

        # FIXME: we put avatarId in the config for now
        # but it'd be nicer to do this outside of config, so do this
        config['avatarId'] = avatarId
        try:
            comp = getComponent(config, moduleName, methodName)
        except Exception, e:
            msg = "Exception %s during getComponent: %s" % (
                e.__class__.__name__, " ".join(e.args))
            traceback.print_exc()
            self.warning("raising ComponentStart(%s)" % msg)
            raise errors.ComponentStart(msg)

        # we have components without feed ports, and without this function
        if feedPorts:
            comp.set_feed_ports(feedPorts)

        comp.setWorkerName(self.worker_name)
        comp.setConfig(config)

        # make component log in to manager
        manager_client_factory = component.ComponentClientFactory(comp)
        keycard = self.manager_keycard
        keycard.avatarId = avatarId
        manager_client_factory.startLogin(keycard)

        host = self.manager_host
        port = self.manager_port
        transport = self.manager_transport
        if transport == "ssl":
            from twisted.internet import ssl
            self.info('Connecting to manager %s:%d with SSL' % (host, port))
            reactor.connectSSL(host, port, manager_client_factory,
                ssl.ClientContextFactory())
        elif self.manager_transport == "tcp":
            self.info('Connecting to manager %s:%d with TCP' % (host, port))
            reactor.connectTCP(host, port, manager_client_factory)
        else:
            self.error('Unknown transport protocol %s' % self.manager_transport)

        self.component_factory = manager_client_factory
        self.component = comp
        
class JobClientFactory(pb.PBClientFactory, log.Loggable):
    """
    I am a client factory that logs in to the WorkerBrain.
    I live in the flumotion-worker job process.
    """
    logCategory = "job"

    def __init__(self, id):
        """
        @param id:      the avatar id used for logging into the workerbrain
        @type  id:      string
        """
        pb.PBClientFactory.__init__(self)
        
        self.medium = JobMedium()
        self.logName = id
        self.login(id)
            
    ### pb.PBClientFactory methods
    # FIXME: might be nice if jobs got a password to use to log in to brain
    def login(self, username):
        self.info('Logging in to worker')
        d = pb.PBClientFactory.login(self, 
            credentials.UsernamePassword(username, ''),
            self.medium)
        yield d
        try:
            remoteReference = d.value()
            self.info('Logged in to worker')
            self.debug('perspective %r connected' % remoteReference)
            self.medium.setRemoteReference(remoteReference)
        except Exception, e:
            from flumotion.common import debug; debug.print_stack()
            print ('ERROR connecting job to worker [%d]: %s'
                   % (os.getpid(), log.getExceptionMessage(e)))
            # raise error
    login = defer_generator_method(login)
    
    # the only way stopFactory can be called is if the WorkerBrain closes
    # the pb server.  Ideally though we would have gotten a notice before.
    def stopFactory(self):
        self.debug('shutting down medium')
        self.medium.shutdown()
        self.debug('shut down medium')
