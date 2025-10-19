# -----------------------------------------------------------------------------
# Name:        MidiFile.py
# Purpose:     MIDI file manipulation utilities
#
# Author:      Mark Conway Wirt <emergentmusics) at (gmail . com>
#
# Created:     2008/04/17
# Copyright:   (c) 2009-2016 Mark Conway Wirt
# License:     Please see License.txt for the terms under which this
#              software is distributed. 
#              https://github.com/MarkCWirt/MIDIUtil/blob/develop/License.txt
# -----------------------------------------------------------------------------
# PROPS https://github.com/MarkCWirt/MIDIUtil

from __future__ import division, print_function
import math
import struct
import warnings

__version__ = 'HEAD'

TICKSPERQUARTERNOTE = 960

controllerEventTypes = {'pan': 0x0a}

MAJOR = 0
MINOR = 1
SHARPS = 1
FLATS = -1

__all__ = ['MIDIFile', 'MAJOR', 'MINOR', 'SHARPS', 'FLATS']


class GenericEvent(object):
    evtname = None
    sec_sort_order = 0

    def __init__(self, tick, insertion_order):
        self.tick = tick
        self.insertion_order = insertion_order

    def __eq__(self, other):
        return (self.evtname == other.evtname and self.tick == other.tick)

    def __hash__(self):
        a = int(self.tick)
        a = (a + 0x7ed55d16) + (a << 12)
        a = (a ^ 0xc761c23c) ^ (a >> 19)
        a = (a + 0x165667b1) + (a << 5)
        a = (a + 0xd3a2646c) ^ (a << 9)
        a = (a + 0xfd7046c5) + (a << 3)
        a = (a ^ 0xb55a4f09) ^ (a >> 16)
        return a


class NoteOn(GenericEvent):
    evtname = 'NoteOn'
    midi_status = 0x90
    sec_sort_order = 3

    def __init__(self, channel, pitch, tick, duration, volume,
                 annotation=None, insertion_order=0):
        self.pitch = pitch
        self.duration = duration
        self.volume = volume
        self.channel = channel
        self.annotation = annotation
        super(NoteOn, self).__init__(tick, insertion_order)

    def __eq__(self, other):
        return (self.evtname == other.evtname and self.tick == other.tick and
                self.pitch == other.pitch and self.channel == other.channel)

    __hash__ = GenericEvent.__hash__

    def __str__(self):
        return 'NoteOn %d at tick %d duration %d ch %d vel %d' % (
            self.pitch, self.tick, self.duration, self.channel, self.volume)

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = self.midi_status | self.channel
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('>B', code)
        midibytes += struct.pack('>B', self.pitch)
        midibytes += struct.pack('>B', self.volume)
        return midibytes


class NoteOff (GenericEvent):
    evtname = 'NoteOff'
    midi_status = 0x80
    sec_sort_order = 2

    def __init__(self, channel, pitch, tick, volume,
                 annotation=None, insertion_order=0):
        self.pitch = pitch
        self.volume = volume
        self.channel = channel
        self.annotation = annotation
        super(NoteOff, self).__init__(tick, insertion_order)

    def __eq__(self, other):
        return (self.evtname == other.evtname and self.tick == other.tick and
                self.pitch == other.pitch and self.channel == other.channel)

    __hash__ = GenericEvent.__hash__

    def __str__(self):
        return 'NoteOff %d at tick %d ch %d vel %d' % (
            self.pitch, self.tick, self.channel, self.volume)

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = self.midi_status | self.channel
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('>B', code)
        midibytes += struct.pack('>B', self.pitch)
        midibytes += struct.pack('>B', self.volume)
        return midibytes


class Tempo(GenericEvent):
    evtname = 'Tempo'
    sec_sort_order = 3

    def __init__(self, tick, tempo, insertion_order=0):
        self.tempo = int(60000000 / tempo)
        super(Tempo, self).__init__(tick, insertion_order)

    def __eq__(self, other):
        return (self.evtname == other.evtname and
                self.tick == other.tick and
                self.tempo == other.tempo)

    __hash__ = GenericEvent.__hash__

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = 0xFF
        subcode = 0x51
        fourbite = struct.pack('>L', self.tempo)
        threebite = fourbite[1:4]
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('>B', code)
        midibytes += struct.pack('>B', subcode)
        midibytes += struct.pack('>B', 0x03)
        midibytes += threebite
        return midibytes


class Copyright(GenericEvent):
    evtname = 'Copyright'
    sec_sort_order = 1

    def __init__(self, tick, notice, insertion_order=0):
        self.notice = notice.encode("ISO-8859-1")
        super(Copyright, self).__init__(tick, insertion_order)

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = 0xFF
        subcode = 0x02
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('>B', code)
        midibytes += struct.pack('>B', subcode)
        payloadLength = len(self.notice)
        payloadLengthVar = writeVarLength(payloadLength)
        for i in payloadLengthVar:
            midibytes += struct.pack("b", i)
        midibytes += self.notice
        return midibytes


class Text(GenericEvent):
    evtname = 'Text'
    sec_sort_order = 1

    def __init__(self, tick, text, insertion_order=0):
        self.text = text.encode("ISO-8859-1")
        super(Text, self).__init__(tick, insertion_order)

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = 0xFF
        subcode = 0x01
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('>B', code)
        midibytes += struct.pack('>B', subcode)
        payloadLength = len(self.text)
        payloadLengthVar = writeVarLength(payloadLength)
        for i in payloadLengthVar:
            midibytes += struct.pack("B", i)
        midibytes += self.text
        return midibytes


class KeySignature(GenericEvent):
    evtname = 'KeySignature'
    sec_sort_order = 1

    def __init__(self, tick, accidentals, accidental_type, mode,
                 insertion_order=0):
        self.accidentals = accidentals
        self.accidental_type = accidental_type
        self.mode = mode
        super(KeySignature, self).__init__(tick, insertion_order)

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = 0xFF
        subcode = 0x59
        event_subtype = 0x02
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('>B', code)
        midibytes += struct.pack('>B', subcode)
        midibytes += struct.pack('>B', event_subtype)
        midibytes += struct.pack('>b', self.accidentals * self.accidental_type)
        midibytes += struct.pack('>B', self.mode)
        return midibytes


class ProgramChange(GenericEvent):
    evtname = 'ProgramChange'
    midi_status = 0xc0
    sec_sort_order = 1

    def __init__(self, channel, tick, programNumber,
                 insertion_order=0):
        self.programNumber = programNumber
        self.channel = channel
        super(ProgramChange, self).__init__(tick, insertion_order)

    def __eq__(self, other):
        return (self.evtname == other.evtname and
                self.tick == other.tick and
                self.programNumber == other.programNumber and
                self.channel == other.channel)

    __hash__ = GenericEvent.__hash__

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = self.midi_status | self.channel
        varTime = writeVarLength(self.tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('>B', code)
        midibytes += struct.pack('>B', self.programNumber)
        return midibytes


class SysExEvent(GenericEvent):
    evtname = 'SysEx'
    sec_sort_order = 1

    def __init__(self, tick, manID, payload, insertion_order=0):
        self.manID = manID
        self.payload = payload
        super(SysExEvent, self).__init__(tick, insertion_order)

    def __eq__(self, other):
        return False

    __hash__ = GenericEvent.__hash__

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = 0xF0
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('>B', code)

        payloadLength = writeVarLength(len(self.payload) + 2)
        for lenByte in payloadLength:
            midibytes += struct.pack('>B', lenByte)

        midibytes += struct.pack('>B', self.manID)
        midibytes += self.payload
        midibytes += struct.pack('>B', 0xF7)
        return midibytes


class UniversalSysExEvent(GenericEvent):
    evtname = 'UniversalSysEx'
    sec_sort_order = 1

    def __init__(self, tick, realTime, sysExChannel, code, subcode,
                 payload, insertion_order=0):
        self.realTime = realTime
        self.sysExChannel = sysExChannel
        self.code = code
        self.subcode = subcode
        self.payload = payload
        super(UniversalSysExEvent, self).__init__(tick, insertion_order)

    def __eq__(self, other):
        return False

    __hash__ = GenericEvent.__hash__

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = 0xF0
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('>B', code)

        payloadLength = writeVarLength(len(self.payload) + 5)
        for lenByte in payloadLength:
            midibytes += struct.pack('>B', lenByte)

        if self.realTime:
            midibytes += struct.pack('>B', 0x7F)
        else:
            midibytes += struct.pack('>B', 0x7E)

        midibytes += struct.pack('>B', self.sysExChannel)
        midibytes += struct.pack('>B', self.code)
        midibytes += struct.pack('>B', self.subcode)
        midibytes += self.payload
        midibytes += struct.pack('>B', 0xF7)
        return midibytes


class ControllerEvent(GenericEvent):
    evtname = 'ControllerEvent'
    midi_status = 0xB0
    sec_sort_order = 1

    def __init__(self, channel, tick, controller_number, parameter,
                 insertion_order=0):
        self.parameter = parameter
        self.channel = channel
        self.controller_number = controller_number
        super(ControllerEvent, self).__init__(tick, insertion_order)

    def __eq__(self, other):
        return False

    __hash__ = GenericEvent.__hash__

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = self.midi_status | self.channel
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('>B', code)
        midibytes += struct.pack('>B', self.controller_number)
        midibytes += struct.pack('>B', self.parameter)
        return midibytes


class ChannelPressureEvent(GenericEvent):
    evtname = 'ChannelPressure'
    midi_status = 0xD0
    sec_sort_order = 1

    def __init__(self, channel, tick, pressure_value, insertion_order=0):
        self.channel = channel
        self.pressure_value = pressure_value
        super(ChannelPressureEvent, self).__init__(tick, insertion_order)

    def __eq__(self, other):
        return (self.__class__.__name__ == other.__class__.__name__ and
                self.tick == other.tick and
                self.pressure_value == other.pressure_value and
                self.channel == other.channel)

    __hash__ = GenericEvent.__hash__

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = self.midi_status | self.channel
        vartick = writeVarLength(self.tick - previous_event_tick)
        for x in vartick:
            midibytes += struct.pack('>B', x)
        midibytes += struct.pack('>B', code)
        midibytes += struct.pack('>B', self.pressure_value)
        return midibytes


class PitchWheelEvent(GenericEvent):
    evtname = 'PitchWheelEvent'
    midi_status = 0xE0
    sec_sort_order = 1

    def __init__(self, channel, tick, pitch_wheel_value, insertion_order=0):
        self.channel = channel
        self.pitch_wheel_value = pitch_wheel_value
        super(PitchWheelEvent, self).__init__(tick, insertion_order)

    def __eq__(self, other):
        return False

    __hash__ = GenericEvent.__hash__

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = self.midi_status | self.channel
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes = midibytes + struct.pack('>B', timeByte)
        MSB = (self.pitch_wheel_value + 8192) >> 7
        LSB = (self.pitch_wheel_value + 8192) & 0x7F
        midibytes = midibytes + struct.pack('>B', code)
        midibytes = midibytes + struct.pack('>B', LSB)
        midibytes = midibytes + struct.pack('>B', MSB)
        return midibytes


class TrackName(GenericEvent):
    evtname = 'TrackName'
    sec_sort_order = 0

    def __init__(self, tick, trackName, insertion_order=0):
        self.trackName = trackName.encode("ISO-8859-1")
        super(TrackName, self).__init__(tick, insertion_order)

    def __eq__(self, other):
        return (self.evtname == other.evtname and
                self.tick == other.tick and
                self.trackName == other.trackName)

    __hash__ = GenericEvent.__hash__

    def serialize(self, previous_event_tick):
        midibytes = b""
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('B', 0xFF)
        midibytes += struct.pack('B', 0X03)
        dataLength = len(self.trackName)
        dataLengthVar = writeVarLength(dataLength)
        for i in dataLengthVar:
            midibytes += struct.pack("B", i)
        midibytes += self.trackName
        return midibytes


class TimeSignature(GenericEvent):
    evtname = 'TimeSignature'
    sec_sort_order = 0

    def __init__(self, tick, numerator, denominator, clocks_per_tick,
                 notes_per_quarter, insertion_order=0):
        self.numerator = numerator
        self.denominator = denominator
        self.clocks_per_tick = clocks_per_tick
        self.notes_per_quarter = notes_per_quarter
        super(TimeSignature, self).__init__(tick, insertion_order)

    def serialize(self, previous_event_tick):
        midibytes = b""
        code = 0xFF
        subcode = 0x58
        varTime = writeVarLength(self.tick - previous_event_tick)
        for timeByte in varTime:
            midibytes += struct.pack('>B', timeByte)
        midibytes += struct.pack('>B', code)
        midibytes += struct.pack('>B', subcode)
        midibytes += struct.pack('>B', 0x04)
        midibytes += struct.pack('>B', self.numerator)
        midibytes += struct.pack('>B', self.denominator)
        midibytes += struct.pack('>B', self.clocks_per_tick)
        midibytes += struct.pack('>B', self.notes_per_quarter)
        return midibytes


class MIDITrack(object):
    def __init__(self, removeDuplicates, deinterleave):
        self.headerString = struct.pack('cccc', b'M', b'T', b'r', b'k')
        self.dataLength = 0
        self.MIDIdata = b""
        self.closed = False
        self.eventList = []
        self.MIDIEventList = []
        self.remdep = removeDuplicates
        self.deinterleave = deinterleave

    def addNoteByNumber(self, channel, pitch, tick, duration, volume,
                        annotation=None, insertion_order=0):
        self.eventList.append(NoteOn(channel, pitch, tick, duration, volume,
                                     annotation=annotation,
                                     insertion_order=insertion_order))

        self.eventList.append(NoteOff(channel, pitch, tick + duration, volume,
                                      annotation=annotation,
                                      insertion_order=insertion_order))

    def addControllerEvent(self, channel, tick, controller_number, parameter,
                           insertion_order=0):
        self.eventList.append(ControllerEvent(channel, tick, controller_number,
                                              parameter,
                                              insertion_order=insertion_order))

    def addPitchWheelEvent(self, channel, tick, pitch_wheel_value, insertion_order=0):
        self.eventList.append(PitchWheelEvent(channel, tick, pitch_wheel_value, insertion_order=insertion_order))

    def addTempo(self, tick, tempo, insertion_order=0):
        self.eventList.append(Tempo(tick, tempo,
                                    insertion_order=insertion_order))

    def addSysEx(self, tick, manID, payload, insertion_order=0):
        self.eventList.append(SysExEvent(tick, manID, payload,
                                         insertion_order=insertion_order))

    def addUniversalSysEx(self, tick, code, subcode, payload,
                          sysExChannel=0x7F, realTime=False,
                          insertion_order=0):
        self.eventList.append(UniversalSysExEvent(tick, realTime, sysExChannel,
                                                  code, subcode, payload,
                                                  insertion_order=insertion_order))

    def addProgramChange(self, channel, tick, program, insertion_order=0):
        self.eventList.append(ProgramChange(channel, tick, program,
                                            insertion_order=insertion_order))

    def addChannelPressure(self, channel, tick, pressure_value, insertion_order=0):
        self.eventList.append(ChannelPressureEvent(channel, tick, pressure_value,
                                                   insertion_order=insertion_order))

    def addTrackName(self, tick, trackName, insertion_order=0):
        self.eventList.append(TrackName(tick, trackName,
                                        insertion_order=insertion_order))

    def addTimeSignature(self, tick, numerator, denominator, clocks_per_tick,
                         notes_per_quarter, insertion_order=0):
        self.eventList.append(TimeSignature(tick, numerator, denominator,
                                            clocks_per_tick, notes_per_quarter,
                                            insertion_order=insertion_order))

    def addCopyright(self, tick, notice, insertion_order=0):
        self.eventList.append(Copyright(tick, notice,
                                        insertion_order=insertion_order))

    def addKeySignature(self, tick, accidentals, accidental_type, mode,
                        insertion_order=0):
        self.eventList.append(KeySignature(tick, accidentals, accidental_type,
                                           mode,
                                           insertion_order=insertion_order))

    def addText(self, tick, text, insertion_order=0):
        self.eventList.append(Text(tick, text,
                                   insertion_order=insertion_order))

    def changeNoteTuning(self, tunings, sysExChannel=0x7F, realTime=True,
                         tuningProgam=0, insertion_order=0):
        payload = struct.pack('>B', tuningProgam)
        payload = payload + struct.pack('>B', len(tunings))
        for (noteNumber, frequency) in tunings:
            payload = payload + struct.pack('>B', noteNumber)
            MIDIFreqency = frequencyTransform(frequency)
            for byte in MIDIFreqency:
                payload = payload + struct.pack('>B', byte)

        self.eventList.append(UniversalSysExEvent(0, realTime, sysExChannel,
                                                  8, 2, payload, insertion_order=insertion_order))

    def processEventList(self):
        self.MIDIEventList = [evt for evt in self.eventList]
        self.MIDIEventList.sort(key=sort_events)

        if self.deinterleave:
            self.deInterleaveNotes()

    def removeDuplicates(self):
        s = set(self.eventList)
        self.eventList = list(s)
        self.eventList.sort(key=sort_events)

    def closeTrack(self):
        if self.closed:
            return
        self.closed = True

        if self.remdep:
            self.removeDuplicates()

        self.processEventList()

    def writeMIDIStream(self):
        self.writeEventsToStream()
        self.MIDIdata += struct.pack('BBBB', 0x00, 0xFF, 0x2F, 0x00)
        self.dataLength = struct.pack('>L', len(self.MIDIdata))

    def writeEventsToStream(self):
        previous_event_tick = 0
        for event in self.MIDIEventList:
            self.MIDIdata += event.serialize(previous_event_tick)

    def deInterleaveNotes(self):
        tempEventList = []
        stack = {}

        for event in self.MIDIEventList:
            if event.evtname in ['NoteOn', 'NoteOff']:
                noteeventkey = str(event.pitch) + str(event.channel)
                if event.evtname == 'NoteOn':
                    if noteeventkey in stack:
                        stack[noteeventkey].append(event.tick)
                    else:
                        stack[noteeventkey] = [event.tick]
                    tempEventList.append(event)
                elif event.evtname == 'NoteOff':
                    if len(stack[noteeventkey]) > 1:
                        event.tick = stack[noteeventkey].pop()
                        tempEventList.append(event)
                    else:
                        stack[noteeventkey].pop()
                        tempEventList.append(event)
            else:
                tempEventList.append(event)

        self.MIDIEventList = tempEventList

        self.MIDIEventList.sort(key=sort_events)

    def adjustTimeAndOrigin(self, origin, adjust):
        if len(self.MIDIEventList) == 0:
            return
        tempEventList = []
        internal_origin = origin if adjust else 0
        runningTick = 0

        for event in self.MIDIEventList:
            adjustedTick = event.tick - internal_origin
            event.tick = adjustedTick - runningTick
            runningTick = adjustedTick
            tempEventList.append(event)

        self.MIDIEventList = tempEventList

    def writeTrack(self, fileHandle):
        fileHandle.write(self.headerString)
        fileHandle.write(self.dataLength)
        fileHandle.write(self.MIDIdata)


class MIDIHeader(object):
    def __init__(self, numTracks, file_format, ticks_per_quarternote):
        self.headerString = struct.pack('cccc', b'M', b'T', b'h', b'd')
        self.headerSize = struct.pack('>L', 6)
        self.formatnum = struct.pack('>H', file_format)
        self.numeric_format = file_format
        self.numTracks = struct.pack('>H', numTracks)
        self.ticks_per_quarternote = struct.pack('>H', ticks_per_quarternote)

    def writeFile(self, fileHandle):
        fileHandle.write(self.headerString)
        fileHandle.write(self.headerSize)
        fileHandle.write(self.formatnum)
        fileHandle.write(self.numTracks)
        fileHandle.write(self.ticks_per_quarternote)


class MIDIFile(object):
    def __init__(self, numTracks=1, removeDuplicates=True, deinterleave=True,
                 adjust_origin=False, file_format=1,
                 ticks_per_quarternote=TICKSPERQUARTERNOTE, eventtime_is_ticks=False):
        self.tracks = list()
        if file_format == 1:
            self.numTracks = numTracks + 1
        else:
            self.numTracks = numTracks
        self.header = MIDIHeader(self.numTracks, file_format, ticks_per_quarternote)

        self.adjust_origin = adjust_origin
        self.closed = False

        self.ticks_per_quarternote = ticks_per_quarternote
        self.eventtime_is_ticks = eventtime_is_ticks
        if self.eventtime_is_ticks:
            self.time_to_ticks = lambda x: x
        else:
            self.time_to_ticks = self.quarter_to_tick

        for i in range(0, self.numTracks):
            self.tracks.append(MIDITrack(removeDuplicates, deinterleave))
        self.event_counter = 0

    def quarter_to_tick(self, quarternote_time):
        return int(quarternote_time * self.ticks_per_quarternote)

    def tick_to_quarter(self, ticknum):
        return float(ticknum) / self.ticks_per_quarternote

    def addNote(self, track, channel, pitch, time, duration, volume,
                annotation=None):
        if self.header.numeric_format == 1:
            track += 1
        self.tracks[track].addNoteByNumber(channel, pitch,
                                           self.time_to_ticks(time), self.time_to_ticks(duration),
                                           volume, annotation=annotation,
                                           insertion_order=self.event_counter)
        self.event_counter += 1

    def addTrackName(self, track, time, trackName):
        if self.header.numeric_format == 1:
            track += 1
        self.tracks[track].addTrackName(self.time_to_ticks(time), trackName,
                                        insertion_order=self.event_counter)
        self.event_counter += 1

    def addTimeSignature(self, track, time, numerator, denominator,
                         clocks_per_tick, notes_per_quarter=8):
        if self.header.numeric_format == 1:
            track = 0

        self.tracks[track].addTimeSignature(self.time_to_ticks(time), numerator, denominator,
                                            clocks_per_tick, notes_per_quarter,
                                            insertion_order=self.event_counter)
        self.event_counter += 1

    def addTempo(self, track, time, tempo):
        if self.header.numeric_format == 1:
            track = 0
        self.tracks[track].addTempo(self.time_to_ticks(time), tempo,
                                    insertion_order=self.event_counter)
        self.event_counter += 1

    def addCopyright(self, track, time, notice):
        if self.header.numeric_format == 1:
            track += 1
        self.tracks[track].addCopyright(self.time_to_ticks(time), notice,
                                        insertion_order=self.event_counter)
        self.event_counter += 1

    def addKeySignature(self, track, time, accidentals, accidental_type, mode,
                        insertion_order=0):
        if self.header.numeric_format == 1:
            track = 0
        self.tracks[track].addKeySignature(self.time_to_ticks(time), accidentals, accidental_type,
                                           mode, insertion_order=self.event_counter)
        self.event_counter += 1

    def addText(self, track, time, text):
        if self.header.numeric_format == 1:
            track += 1
        self.tracks[track].addText(self.time_to_ticks(time), text,
                                   insertion_order=self.event_counter)
        self.event_counter += 1

    def addProgramChange(self, tracknum, channel, time, program):
        if self.header.numeric_format == 1:
            tracknum += 1
        self.tracks[tracknum].addProgramChange(channel, self.time_to_ticks(time), program,
                                               insertion_order=self.event_counter)
        self.event_counter += 1

    def addChannelPressure(self, tracknum, channel, time, pressure_value):
        if self.header.numeric_format == 1:
            tracknum += 1
        track = self.tracks[tracknum]
        track.addChannelPressure(channel, self.time_to_ticks(time), pressure_value,
                                 insertion_order=self.event_counter)
        self.event_counter += 1

    def addControllerEvent(self, track, channel, time, controller_number,
                           parameter):
        if self.header.numeric_format == 1:
            track += 1
        self.tracks[track].addControllerEvent(channel, self.time_to_ticks(time), controller_number,
                                              parameter, insertion_order=self.event_counter)
        self.event_counter += 1

    def addPitchWheelEvent(self, track, channel, time, pitchWheelValue):
        if self.header.numeric_format == 1:
            track += 1
        self.tracks[track].addPitchWheelEvent(channel, self.time_to_ticks(time), pitchWheelValue,
                                              insertion_order=self.event_counter)
        self.event_counter += 1

    def makeRPNCall(self, track, channel, time, controller_msb, controller_lsb,
                    data_msb, data_lsb, time_order=False):
        tick = self.time_to_ticks(time)

        if self.header.numeric_format == 1:
            track += 1
        track = self.tracks[track]

        tick_incr = 1 if time_order else 0
        track.addControllerEvent(channel, tick, 101,
                                 controller_msb, insertion_order=self.event_counter)
        self.event_counter += 1
        tick += tick_incr
        track.addControllerEvent(channel, tick, 100,
                                 controller_lsb, insertion_order=self.event_counter)
        self.event_counter += 1
        tick += tick_incr
        track.addControllerEvent(channel, tick, 6,
                                 data_msb, insertion_order=self.event_counter)
        self.event_counter += 1
        tick += tick_incr
        if data_lsb is not None:
            track.addControllerEvent(channel, tick, 38,
                                     data_lsb, insertion_order=self.event_counter)
            self.event_counter += 1

    def makeNRPNCall(self, track, channel, time, controller_msb,
                     controller_lsb, data_msb, data_lsb, time_order=False):
        tick = self.time_to_ticks(time)

        if self.header.numeric_format == 1:
            track += 1
        track = self.tracks[track]

        tick_incr = 1 if time_order else 0
        track.addControllerEvent(channel, tick, 99,
                                 controller_msb, insertion_order=self.event_counter)
        self.event_counter += 1
        tick += tick_incr
        track.addControllerEvent(channel, tick, 98,
                                 controller_lsb, insertion_order=self.event_counter)
        self.event_counter += 1
        tick += tick_incr
        track.addControllerEvent(channel, tick, 6,
                                 data_msb, insertion_order=self.event_counter)
        self.event_counter += 1
        tick += tick_incr
        if data_lsb is not None:
            track.addControllerEvent(channel, tick, 38,
                                     data_lsb, insertion_order=self.event_counter)
            self.event_counter += 1

    def changeTuningBank(self, track, channel, time, bank, time_order=False):
        self.makeRPNCall(track, channel, time, 0, 4, 0, bank,
                         time_order=time_order)

    def changeTuningProgram(self, track, channel, time, program,
                            time_order=False):
        self.makeRPNCall(track, channel, time, 0, 3, 0, program,
                         time_order=time_order)

    def changeNoteTuning(self, track, tunings, sysExChannel=0x7F,
                         realTime=True, tuningProgam=0):
        if self.header.numeric_format == 1:
            track += 1
        self.tracks[track].changeNoteTuning(tunings, sysExChannel, realTime,
                                            tuningProgam,
                                            insertion_order=self.event_counter)
        self.event_counter += 1

    def addSysEx(self, track, time, manID, payload):
        tick = self.time_to_ticks(time)
        if self.header.numeric_format == 1:
            track += 1
        self.tracks[track].addSysEx(tick, manID, payload,
                                    insertion_order=self.event_counter)
        self.event_counter += 1

    def addUniversalSysEx(self, track, time, code, subcode, payload,
                          sysExChannel=0x7F, realTime=False):
        tick = self.time_to_ticks(time)
        if self.header.numeric_format == 1:
            track += 1
        self.tracks[track].addUniversalSysEx(tick, code, subcode, payload,
                                             sysExChannel, realTime,
                                             insertion_order=self.event_counter)
        self.event_counter += 1

    def writeFile(self, fileHandle):
        self.header.writeFile(fileHandle)

        self.close()

        for i in range(0, self.numTracks):
            self.tracks[i].writeTrack(fileHandle)

    def shiftTracks(self, offset=0):
        origin = 100000000
        tick_offset = self.time_to_ticks(offset)

        for track in self.tracks:
            if len(track.eventList) > 0:
                for event in track.eventList:
                    if event.tick < origin:
                        origin = event.tick

        for track in self.tracks:
            tempEventList = []

            for event in track.eventList:
                adjustedTick = event.tick - origin
                event.tick = adjustedTick + tick_offset
                tempEventList.append(event)

            track.eventList = tempEventList

    def close(self):
        if self.closed:
            return

        for i in range(0, self.numTracks):
            self.tracks[i].closeTrack()
            self.tracks[i].MIDIEventList.sort(key=sort_events)

        origin = self.findOrigin()

        for i in range(0, self.numTracks):
            self.tracks[i].adjustTimeAndOrigin(origin, self.adjust_origin)
            self.tracks[i].writeMIDIStream()

        self.closed = True

    def findOrigin(self):
        origin = 100000000

        for track in self.tracks:
            if len(track.MIDIEventList) > 0:
                if track.MIDIEventList[0].tick < origin:
                    origin = track.MIDIEventList[0].tick

        return origin


def writeVarLength(i):
    if i == 0:
        return [0]

    vlbytes = []
    hibit = 0x00
    while i > 0:
        vlbytes.append(((i & 0x7f) | hibit) & 0xff)
        i >>= 7
        hibit = 0x80
    vlbytes.reverse()
    return vlbytes


def readVarLength(offset, buffer):
    toffset = offset
    output = 0
    bytesRead = 0
    while True:
        output = output << 7
        byte = struct.unpack_from('>B', buffer, toffset)[0]
        toffset = toffset + 1
        bytesRead = bytesRead + 1
        output = output + (byte & 127)
        if (byte & 128) == 0:
            break
    return (output, bytesRead)


def frequencyTransform(freq):
    resolution = 16384
    freq = float(freq)
    dollars = 69 + 12 * math.log(freq / (float(440)), 2)
    firstByte = int(dollars)
    lowerFreq = 440 * pow(2.0, ((float(firstByte) - 69.0) / 12.0))
    centDif = 1200 * math.log((freq / lowerFreq), 2) if freq != lowerFreq else 0
    cents = round(centDif / 100 * resolution)
    secondByte = min([int(cents) >> 7, 0x7F])
    thirdByte = cents - (secondByte << 7)
    thirdByte = min([thirdByte, 0x7f])
    if thirdByte == 0x7f and secondByte == 0x7F and firstByte == 0x7F:
        thirdByte = 0x7e
    thirdByte = int(thirdByte)
    return [firstByte, secondByte, thirdByte]


def returnFrequency(freqBytes):
    resolution = 16384.0
    baseFrequency = 440 * pow(2.0, (float(freqBytes[0] - 69.0) / 12.0))
    frac = (float((int(freqBytes[1]) << 7) + int(freqBytes[2])) * 100.0) / resolution
    frequency = baseFrequency * pow(2.0, frac / 1200.0)
    return frequency


def sort_events(event):
    return (event.tick, event.sec_sort_order, event.insertion_order)