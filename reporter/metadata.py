# coding=utf-8
"""Module for InaSAFE metadata.
:copyright: (c) 2015 by Etienne Trimaille.
:license: GPLv3, see LICENSE for more details.
"""
import os
import re

from utilities import resource_base_path


def short_version(version):
    """Get a shorter version, only with the major and minor version.

    :param version: The version.
    :type version: str

    :return 'major.minor' version number.
    :rtype float
    """
    return float('.'.join(version.split('.')[0:2]))


def latest_xml_metadata_file(feature):
    """Get the latest version available of the XML metadata for the feature.

    :param feature: The type of feature:
        buildings, building-points, roads, potential-idp, boundary-[1,11]
    :type feature: str

    :return The latest version available.
    :rtype float
    """
    base_path = resource_base_path(feature)
    directory = os.path.dirname(os.path.abspath(base_path))
    files = os.listdir(directory)
    resource = os.path.basename(base_path)
    regexp = '^%s-(\d.\d)-en.xml' % resource

    max_version = None
    for one_file in files:
        r = re.search(regexp, one_file)
        if r:
            version = float(r.group(1))
            if not max_version or max_version < version:
                max_version = version
    return max_version


def metadata_file(extension, version, lang, feature):
    """Get the best metadata file.

    :param extension: The extension 'xml' or 'keywords' we expect.
    :rtype extension: str

    :param version: The InaSAFE version.
    :rtype version: float

    :param lang: The language of the user.
    :rtype lang: str

    :param feature: The feature type:
        buildings, building-points, roads, potential-idp, boundary-[1,11]
    :rtype feature: str

    :return: The filename.
    :rtype: str
    """
    base_path = resource_base_path(feature)

    if extension == 'keywords':
        # We check for only the localised file.
        prefix = '-%s.keywords' % lang
        source_path = '%s%s' % (base_path, prefix)
        if not os.path.isfile(source_path):
            # If not, we take the english version.
            prefix = '-en.keywords'

    else:
        # Extension is xml.
        # We check first for the perfect file (version and lang).
        prefix = '%s-%s.xml' % (version, lang)
        source_path = '%s%s' % (base_path, prefix)

        if not os.path.isfile(source_path):
            # If not, we check for the same version, but in english.
            prefix = '-%s-en.xml' % version
            source_path = '%s%s' % (base_path, prefix)

            if not os.path.isfile(source_path):
                # We check for the maximum version available and localised.
                latest = latest_xml_metadata_file(feature)

                prefix = '-%s-%s.xml' % (latest, lang)
                source_path = '%s%s' % (base_path, prefix)
                if not os.path.isfile(source_path):
                    # We take the maximum version available in english.
                    prefix = '-%s-en.xml' % latest
    return prefix


def metadata_files(version, lang, feature, output_prefix):
    """Get all metadata files which should be included in the zip.

    :param version: The InaSAFE version.
    :type version: str

    :param lang: The language desired for the labels in the legend.
    :type lang: str

    :param feature: The feature to extract.
    :type feature: str

    :param output_prefix: Base name for the metadata file.
    :type output_prefix: str

    :return: A dictionary with destination / source file.
    :rtype: dict
    """
    if version:
        version = short_version(version)

    xml_file = metadata_file('xml', version, lang, feature)
    keyword_file = metadata_file('keywords', version, lang, feature)
    if version is None:
        # no inasafe_version supplied, provide legacy keywords and XML.
        files = {
            '%s.keywords' % output_prefix: keyword_file,
            '%s.xml' % output_prefix: xml_file
        }
    elif version < 3.2:
        # keywords only.
        files = {
            '%s.keywords' % output_prefix: keyword_file
        }
    else:
        # version >= 3.2 : XML only.
        files = {
            '%s.xml' % output_prefix: xml_file
        }

    return files
