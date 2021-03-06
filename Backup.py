"""
Created on Dec 15, 2013
This application is used to backup a directory containing certain applications.
These applications are defined in the CONFIGURATION_FILE
Internal variables description:
APPLICATION_DIR: It is used only for testing
CONFIGURATION_FILE: The name of the xml configuration file
BACKUP_DIR: The directory where the backup will be stored
"""
__author__ = 'Constantin Rata'
__version__ = '1.03.00'
import os
import time
import shutil
import logging
import sys
import xml.etree.ElementTree as ET
import glob
import argparse

PROGRAM_DESCRIPTION = """
Backup the folder in which it is run based on the application description in ApplicationSignatures.xml
The backup folder name will begin with a date formated as follows YYYY-MM-DD_HHMISS
"""
APPLICATION_DIR = None
CONFIGURATION_FILE = 'ApplicationSignatures.xml'
BACKUP_DIR = os.path.join(os.path.dirname(os.getcwd()), 'mindbkp')
XML_CONFIGURATION_TREE = None

FILE_LOG_LEVEL = logging.DEBUG
CONSOLE_LOG_LEVEL = logging.INFO
LOG_SEPARATING_STRING = '*'*30
#TODO: Clean up debug messages. We don't need all of them. We write too much log


def get_working_backup_dir(backup_location, custom_name=''):
    """
    It calculates the current time and creates a folder out of it of the form YYYYMMDDHHMISS
    @param backup_location: String representing the directory where the backup will be stored
    @param custom_name: A string from the user that will be included in the name of the bkp folder
    @return: A string representing the location of the current location of the backup
    """
    current_time = time.strftime('%Y-%m-%d_%H%M%S')
    if custom_name == '':
        return os.path.join(backup_location, current_time)
    else:
        return os.path.join(backup_location, current_time+'_'+custom_name)


def is_dir_in_configuration(directory_name, configuration_xml):
    """
    @param directory_name: A string representing the name of the directory, without path
    @param configuration_xml: A Document object containing the configuration xml file
    @return: True if the directory is present ion the configuration, false otherwise
    """
    logger.debug('is_dir_in_configuration is called for directory '+directory_name)
    present = False
    for application_node in configuration_xml.findall("./signature"):
        if application_node.attrib['name'] == directory_name:
            present = True
            break
    return present


def return_match_in_xml(directory_name, content_list, xpath):
    """
    It matches files from content_list with the configuration specified by xpath
    @param directory_name: The current working directory
    @param content_list: The contents of the current directory
    @return: The list of files/folders to be ignored
    """
    ignored_list = set()
    for file in XML_CONFIGURATION_TREE.findall(xpath):
        xml_file_path = os.path.join(directory_name, file.text.lstrip(os.path.sep))
        logger.debug('File in xml='+xml_file_path)
        expanded_xml_path = glob.glob(xml_file_path)
        for fl in content_list:
            for xfl in expanded_xml_path:
                logger.debug('expanded '+str(xfl))
                if os.path.samefile(os.path.join(directory_name, fl), xfl):
                    logger.debug('Adding <%s> to ignored list', fl)
                    ignored_list.add(fl)
    logger.debug('The ignored list is '+str(ignored_list))
    return ignored_list


def generate_ignore_list(directory_name, content_list):
    """
    Generates the ignore list based on the current directory name and the list of files and folders inside it
    @param directory_name: The current working directory
    @param content_list: The contents of the current directory
    @return: The list of files/folders to be ignored
    """
    application_name = os.path.relpath(directory_name, APPLICATION_DIR).split(os.path.sep)[0]
    logger.debug('generate_ignore_list for directory_name ' + directory_name +
                 ' of application <' + application_name +
                 '> and content '+str(content_list))
    ignored_list = set()

    xpath_for_ignore = r"./general/file"
    logger.debug('xpath='+xpath_for_ignore)
    logger.debug('Doing the general match')
    ignored_list |= return_match_in_xml(directory_name, content_list, xpath_for_ignore)

    xpath_for_exceptions = r"./general/file[@ignore='false']"
    logger.debug('xpath='+xpath_for_ignore)
    logger.debug('Doing the general exceptions')
    ignored_list -= return_match_in_xml(directory_name, content_list, xpath_for_exceptions)

    xpath_for_ignore = r"./signature[@name='"+application_name+"']/file"
    logger.debug('Doing the particular match')
    ignored_list |= return_match_in_xml(directory_name, content_list, xpath_for_ignore)
    logger.debug('xpath='+xpath_for_ignore)

    xpath_for_exceptions = r"./signature[@name='"+application_name+"']/file[@ignore='false']"
    logger.debug('xpath='+xpath_for_ignore)
    logger.debug('Doing the particular exceptions')
    ignored_list -= return_match_in_xml(directory_name, content_list, xpath_for_exceptions)

    logger.debug(LOG_SEPARATING_STRING)

    return ignored_list


def do_backup(application_installation_dir, backup_dir, files_to_backup):
    """
    Doe backup of all the mind application in the application_installation_dir based on CONFIGURATION_FILE
    @param application_installation_dir: This is a string representing the installation path of the mind applications
    @backup_dir: The folder where to copy the backup
    @files_to_backup: The list of files/folders to be backup.
    @return:
    """
    logger.info('Beginning to backup the directory ' + application_installation_dir)
    for fl in files_to_backup:
        if is_dir_in_configuration(fl, XML_CONFIGURATION_TREE):
            logger.info('Doing backup for <'+fl+'>')
            try:
                shutil.copytree(os.path.join(application_installation_dir, fl),
                                os.path.join(backup_dir, fl),
                                ignore=generate_ignore_list)
                pass
            except Exception:  # TODO: Not very happy with this. Will have to do tests and catch errors better
                logger.exception('Some exception occurred ' + str(sys.exc_info()))
        else:
            logger.warning('Directory <'+fl +
                           '> is not in the configured list of mind applications and it will not be backed up')
    logger.info("You will find your backup at this location: "+backup_dir)


def read_xml_signature_file(file_path):
    """
    Reads and transforms the xml document.
    Currently it only makes the file separator os independent
    @param file_path: A string representing the location of the configuration xml
    @return: It returns an xml.etree.ElementTree
    """
    logger.info("Reading the xml file")
    logger.debug("the file path is "+str(file_path))
    paths = [r".//file"]

    tree = ET.parse(file_path)
    logger.debug('OS path separator = '+str(os.path.sep))
    for bad_path in paths:
        for node in tree.findall(bad_path):
            logger.debug("before path sep replacement "+str(node.text))
            node.text = node.text.replace('\\', os.path.sep)
            node.text = node.text.replace('/', os.path.sep)
            logger.debug("after "+str(node.text))
    return tree


def setup_args():
    parser = argparse.ArgumentParser(description=PROGRAM_DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--description",
                        help="Give a description to your backup."
                             "This will be appended to the name of the created backup folder")
    parser.add_argument("-b", "--backupdir",
                        help="The path of the folder where the backup will be stored")
    parser.add_argument("-a", "--applist",
                        help="The list of application from the current dir to be backed up", nargs='*')
    return parser


def setup_logging():
    logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        filename=os.path.basename(sys.argv[0])+'.log',
                        datefmt='%m-%d-%y %H:%M',
                        level=FILE_LOG_LEVEL)
    console = logging.StreamHandler()
    console.setLevel(CONSOLE_LOG_LEVEL)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    __logger__ = logging.getLogger(os.path.basename(sys.argv[0]))
    __logger__.addHandler(console)
    return __logger__


def validate_args(arguments):
    arg_dict = {}
    for argument in vars(arguments):
        arg_dict[argument] = vars(arguments)[argument]
    #process --applist
    if arg_dict['applist'] is not None:
        for app in arg_dict['applist'][:]:
            if app not in os.listdir(os.getcwd()):
                logger.warning('File <%s> is not a valid file/directory and it will not be backup', app)
                arg_dict['applist'].remove(app)
    else:
        arg_dict['applist'] = []
    return arg_dict

if __name__ == '__main__':
    logger = setup_logging()
    args = validate_args(setup_args().parse_args())
    APPLICATION_DIR = os.getcwd()

    if args['backupdir']:
        if os.path.isdir(args['backupdir']):
            BACKUP_DIR = args['backupdir']
            logger.info("Creating the backup in folder: "+BACKUP_DIR)
        else:
            logger.warning("The backup directory does not exist."
                           "Using the default backup folder: "+BACKUP_DIR)

    logger.debug("Starting the script")
    logger.debug("Current working dir is "+os.getcwd())

    try:
        XML_CONFIGURATION_TREE = read_xml_signature_file(os.path.join(APPLICATION_DIR, CONFIGURATION_FILE))
    except FileNotFoundError:
        XML_CONFIGURATION_TREE = read_xml_signature_file(os.path.join(os.path.dirname(sys.argv[0]), CONFIGURATION_FILE))
    logger.debug("After reading the xml file")
    if len(args['applist']) == 0:
        application_to_backup = os.listdir(APPLICATION_DIR)
    else:
        application_to_backup = args['applist']

    if args['description']:
        do_backup(APPLICATION_DIR, get_working_backup_dir(BACKUP_DIR, args['description']), application_to_backup)
    else:
        do_backup(APPLICATION_DIR, get_working_backup_dir(BACKUP_DIR), application_to_backup)