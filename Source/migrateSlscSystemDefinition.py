import argparse
import base64
import re
import sys
import xml.etree.ElementTree as ET

def parseFile(inputFile, outputFile):
    print('Parsing ' + inputFile)
    tree = ET.parse(inputFile)
    root = tree.getroot()
    parseRoot(root)
    print('Writing ' + outputFile)
    tree.write(outputFile)

def parseRoot(root):
    version = root.find('./Version')
    parseVersion(version)

    targets = root.findall('./Root/TargetSections/Target')
    for target in targets:
        parseTarget(target)

    aliases = root.findall("./Root/Section/[@TypeGUID='e11f4519-09e6-4fb0-99df-2967c4313d67']/Alias")
    for alias in aliases:
        parseAlias(alias)

def parseVersion(version):
    attributes = version.attrib
    major = attributes['Major']
    minor = attributes['Minor']
    print('Version: ' + major + '.' + minor)
    if int(major) >= 2017:
        print('File is already up to date. Nothing to do.')
        raise SystemExit

def parseTarget(target):
    attributes = target.attrib
    print('Parsing ' + attributes['Name'])
    customDevices = target.find("Section/[@TypeGUID='03D3BB79-1485-13A6-5605EB7AFD7405AC']")
    legacySlscCustomDevice = customDevices.find("Section/[@TypeGUID='68d6ddc1-274e-40d9-a262-438cd80b3ca1']")
    if legacySlscCustomDevice is None:
        return

    hardware = target.find("Section/[@TypeGUID='775504AB-1485-13A6-560018C1F4E3EEE1']")
    newSlscCustomDevice = createSlscCustomDevice(hardware)

    parseSlscCustomDevice(legacySlscCustomDevice, newSlscCustomDevice)
    customDevices.remove(legacySlscCustomDevice)

def createSlscCustomDevice(hardware):
     slscCustomDevice = createSection(hardware, name='SLSC', typeGUID='3ea8ee87-daf4-4abc-a6e6-9c54a9452824')
     return slscCustomDevice

def parseSlscCustomDevice(legacySlscCustomDevice, newSlscCustomDevice):
    slscChassisList = legacySlscCustomDevice.findall("Section/[@TypeGUID='245650ba-7530-4e16-bde5-f4dcd94687da']")
    for slscChassis in slscChassisList:
        parseSlscChassis(slscChassis, newSlscCustomDevice)

def parseSlscChassis(slscChassis, newSlscCustomDevice):
    attributes = slscChassis.attrib
    name = attributes['Name']
    print('Parsing ' + name)
    codedString = slscChassis.find("Properties/Property/[@Name='user.CD.Chassis IP Address']/BinaryString").text.encode()
    ipAddress = base64.decodebytes(codedString).decode()
    newSlscChassis = createSlscChassis(newSlscCustomDevice, name, ipAddress)

    slscModules = slscChassis.findall('Section')
    slscModules.sort(key = getSlscModuleSlot)
    for slscModule in slscModules:
        slscChassis.remove(slscModule)
        parseSlscModule(newSlscChassis, slscModule)

def createSlscChassis(newSlscCustomDevice, name, ipAddress):
    slscChassis = createSection(newSlscCustomDevice, name, typeGUID='2d230194-1f79-4241-ad00-e5b0a0d634cb')
    createStringProperty(slscChassis, name='Chassis Type', text='SLSC-12001')
    createStringProperty(slscChassis, name='Chassis ID', text=ipAddress)
    createStringProperty(slscChassis, name='Username', text='anonymous')
    createStringProperty(slscChassis, name='Password',text='')
    createIntProperty(slscChassis, name='Chassis ID Type', text='1')
    createSection(slscChassis, name='Modules', typeGUID='96319964-d29d-4af0-9c60-b1a785679b5f')
    createSlscChassisChannels(slscChassis)
    return slscChassis

def createSlscChassisChannels(slscChassis):
    channels = createSection(slscChassis, name='Channels', typeGUID='fa98037a-a524-4a77-b7d2-13997631fa25')
    createSlscChassisBatteryVoltageChannels(channels)
    createSlscChassisFanVoltageChannels(channels)

def createSlscChassisBatteryVoltageChannels(channels):
    batteryVoltageSensor = createSection(channels, name='BatteryVoltageSensor', typeGUID='96faf7a1-7cab-4db2-971e-68b73536c883')
    createChannel(batteryVoltageSensor, name='SensorReading', defaultValue='0', description='The current voltage of the battery in unit voltage.')
    createChannel(batteryVoltageSensor, name='SensorNominal', defaultValue='3.6', description='The nomial voltage of the battery in unit voltage.')
    createChannel(batteryVoltageSensor, name='SensorLowerCritical', defaultValue='2.9', description='The lower battery threshold in unit voltage.')
    createChannel(batteryVoltageSensor, name='HealthState', defaultValue='-1', units='Enum', description='Health State of the chassis battery.\n', valueTable={'Unknown':'-1', 'Normal':'0', 'OutOfSpec':'1', 'RiskOfDamage':'2'})

def createSlscChassisFanVoltageChannels(channels):
    fanVoltageSensor = createSection(channels, name='FanVoltageSensor', typeGUID='96faf7a1-7cab-4db2-971e-68b73536c883')
    createChannel(fanVoltageSensor, name='SensorReading', defaultValue='0', description='The current voltage of the fan in unit voltage.')
    createChannel(fanVoltageSensor, name='SensorLowerCritical', defaultValue='0.08', description="The fan's lower threshold of the operating voltage in unit voltage.")
    createChannel(fanVoltageSensor, name='SensorUpperCritical', defaultValue='0.12', description="The fan's upper threshold of the operating voltage in unit voltage.")
    createChannel(fanVoltageSensor, name='HealthState', defaultValue='-1', units='Enum', description='Health State of the chassis fan.\n', valueTable={'Unknown':'-1', 'Normal':'0', 'OutOfSpec':'1', 'RiskOfDamage':'2'})

def getSlscModuleSlot(slscModule):
    slot = slscModule.find("Properties/Property/[@Name='user.CD.Slot #']/I32").text
    return int(slot)

def parseSlscModule(slscChassis, slscModule):
    attributes = slscModule.attrib
    name = attributes['Name']
    typeGUID = attributes['TypeGUID']
    print('Parsing ' + name)
    slscModules = slscChassis.find("Section/[@TypeGUID='96319964-d29d-4af0-9c60-b1a785679b5f']")

    if typeGUID == '168e3b1f-bb45-4207-8830-40e21915deae':
        createSection(slscModules, name, typeGUID='8a754f70-4d3d-42e2-9846-157cb4981bb4')
    elif typeGUID == 'c474772f-1eb5-4c79-98d9-8846819e1c09':
        parseSlscModuleProperties(slscModule)
        slscModules.append(slscModule)
    else:
        raise Exception('Unknown SLSC module')

def parseSlscModuleProperties(slscModule):
    updateProperty(slscModule, 'user.CD.productNum', 'user.CD.productNumber')
    updateProperty(slscModule, 'user.CD.vendorNum', 'user.CD.vendorNumber')
    dependentFiles = slscModule.findall('Properties/Property/DependentFile')
    for dependentFile in dependentFiles:
        attributes = dependentFile.attrib
        path = attributes['Path']
        dependentFile.attrib['Path'] = path.replace('Custom Devices\\SLSC Plug-ins', 'SLSC Plugins\\Modules')
        destination = dependentFile.find('RTDestination')
        path = destination.text
        destination.text = path.replace('Custom Devices\\SLSC Plug-ins', 'SLSC Plugins\\Modules')

def parseAlias(alias):
     attributes = alias.attrib
     print('Parsing ' + attributes['Name'])
     dependendNode = alias.find('Properties/Property/DependentNode')
     path = dependendNode.attrib['Path']
     match = re.search('^Targets\/Controller\/Custom Devices\/SLSC\/(.*?)\/(.*?)$', path)
     if match is None:
        return
     path = 'Targets/Controller/Hardware/SLSC/' + match.group(1) + '/Modules/' + match.group(2)
     dependendNode.attrib['Path'] = path

def createSection(parent, name, typeGUID):
     section = ET.SubElement(parent, 'Section', attrib={'Name':name, 'TypeGUID':typeGUID})
     ET.SubElement(section, 'Description')
     ET.SubElement(section, 'Properties')
     ET.SubElement(section, 'Errors')
     return section

def createChannel(section, name, defaultValue, units='Double', description='', valueTable = {}):
     channel = ET.SubElement(section, 'Channel', attrib={'Name':name, 'TypeGUID':'92ef77b2-7367-42f8-a914-3eb37c710e2e', 'RowDim':'1', 'ColDim':'1', 'Units':units, 'BitFields':'1'})
     descriptionElement = ET.SubElement(channel, 'Description')
     descriptionElement.text = description
     for key, value in valueTable.items():
        descriptionElement.text += '\n' + value + ': ' + key
     ET.SubElement(channel, 'Properties')
     createValueTableProperty(channel, valueTable)
     ET.SubElement(channel, 'Errors')
     createDefaultValue(channel, defaultValue)

def createStringProperty(section, name, text):
    createProperty(section, name, 'String', text)

def createIntProperty(section, name, text):
    createProperty(section, name, 'I32', text)

def createProperty(section, name, dataType, text):
    properties = section.find('Properties')
    newProperty = ET.SubElement(properties, 'Property', attrib={'Name':name})
    newDataType = ET.SubElement(newProperty, dataType)
    newDataType.text = text

def createValueTableProperty(section, valueTable):
    if len(valueTable) == 0:
        return
    properties = section.find('Properties')
    newProperty = ET.SubElement(properties, 'Property', attrib={'Name':'Value Table'})
    newDictionary = ET.SubElement(newProperty, 'Dictionary')
    for key, value in valueTable.items():
        newElement = ET.SubElement(newDictionary, 'Elem', attrib={'Key':key})
        newDataType = ET.SubElement(newElement, 'Double')
        newDataType.text = value

def updateProperty(section, oldName, newName, oldDataType='I32', newDataType='U32'):
    oldProperty = section.find("Properties/Property/[@Name='" + oldName + "']")
    oldProperty.attrib['Name'] = newName
    oldDataType = oldProperty.find(oldDataType)
    oldDataType.tag = newDataType

def createDefaultValue(section, defaultValue):
    newDefaultValue = ET.SubElement(section, 'DefaultValue')
    newElement = ET.SubElement(newDefaultValue, 'Elem')
    newElement.text = defaultValue

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='source sytem definition file')
    parser.add_argument('output', help='destination system definition file')
    args = parser.parse_args()
    inputFile = args.input
    outputFIle = args.output
    parseFile(inputFile, outputFIle)

# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()