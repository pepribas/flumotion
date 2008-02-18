# -*- Mode: Python; test-case-name: flumotion.test.test_wizard_models -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Flumotion - a streaming media server
# Copyright (C) 2008 Fluendo, S.L. (www.fluendo.com).
# All rights reserved.

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

import difflib
import os
import unittest

from flumotion.common import testsuite
from flumotion.wizard.models import Flow, Plug
from flumotion.wizard.save import XMLWriter, Component

__version__ = "$Rev: 6126 $"


class TestXMLWriter(testsuite.TestCase):
    def testEmpty(self):
        writer = XMLWriter('', [], [])
        testsuite.diffStrings(
            ("<planet>\n"
             "</planet>\n"),
            writer.getXML())

    def testFlowComponent(self):
        c = Component('name', 'streamer', 'worker')
        writer = XMLWriter('flow', [c], [])
        testsuite.diffStrings(
            ('<planet>\n'
             '  <flow name="flow">\n'
             '    <component name="name" type="streamer" '
             'project="flumotion" worker="worker" version="0.5.1.1">\n'
             '    </component>\n'
             '  </flow>\n'
             '</planet>\n'),
            writer.getXML())

    def testAtmosphereComponent(self):
        c = Component('name', 'streamer', 'worker', {'foo': 'bar'})
        writer = XMLWriter('', [], [c])
        testsuite.diffStrings(
            ('<planet>\n'
             '  <atmosphere>\n'
             '    <component name="name" type="streamer" '
             'project="flumotion" worker="worker" version="0.5.1.1">\n'
             '      \n'
             '      <property name="foo">bar</property>\n'
             '    </component>\n'
             '  </atmosphere>\n'
             '</planet>\n'),
            writer.getXML())

    def testComponentWithPlug(self):
        c = Component('name', 'streamer', 'worker')
        plug = Plug()
        plug.socket = 'PlugSocket'
        plug.plug_type = 'plug-type'
        plug.properties.foo = 'bar'
        c.plugs.append(plug)
        writer = XMLWriter('flow', [c], [])
        testsuite.diffStrings(
            ('<planet>\n'
             '  <flow name="flow">\n'
             '    <component name="name" type="streamer" '
             'project="flumotion" worker="worker" version="0.5.1.1">\n'
             '      \n'
             '      <plugs>\n'
             '        <plug socket="PlugSocket" type="plug-type">\n'
             '          \n'
             '          <property name="foo">bar</property>\n'
             '        </plug>\n'
             '      </plugs>\n'
             '    </component>\n'
             '  </flow>\n'
             '</planet>\n'),
            writer.getXML())

    def testComponentWithFeeders(self):
        c1 = Component('name', 'first', 'worker')
        c2 = Component('name', 'second', 'worker')
        c1.link(c2)

        writer = XMLWriter('flow', [c1, c2], [])
        testsuite.diffStrings(
            ('<planet>\n'
             '  <flow name="flow">\n'
             '    <component name="name" type="first" '
             'project="flumotion" worker="worker" version="0.5.1.1">\n'
             '      <eater name="default">\n'
             '        <feed>name</feed>\n'
             '      </eater>\n'
             '    </component>\n'
             '    <component name="name" type="second" '
             'project="flumotion" worker="worker" version="0.5.1.1">\n'
             '    </component>\n'
             '  </flow>\n'
             '</planet>\n'),
            writer.getXML())

if __name__ == '__main__':
    unittest.main()