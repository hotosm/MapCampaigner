# coding=utf-8
import unittest
from campaign_manager.utilities import (
    cast_element_ids_to_s
)


class UtilitiesTestCase(unittest.TestCase):
    """Test Utilities functions"""

    def test_cast_element_ids_with_empty_elements(self):
        """
        When there isnt node, relation or way in elements
        It should return an empty string
        """
        elements = {
            'node': [],
            'relation': [],
            'way': []
        }

        expected_elements_parameters = str()
        elements_parameters = cast_element_ids_to_s(elements)
        self.assertEqual(elements_parameters, expected_elements_parameters)

    def test_cast_element_ids_to_s_with_only_node_elements(self):
        """
        when elements only contain node ids
        It should only return node ids
        """
        elements = {
            'node': [1234, 5678, 9123],
            'relation': [],
            'way': []
        }

        expected_elements_parameters = 'node(id:1234,5678,9123);'
        elements_parameters = cast_element_ids_to_s(elements)
        self.assertEqual(elements_parameters, expected_elements_parameters)

    def test_cast_element_ids_to_s_with_only_relation_elements(self):
        """
        when elements only contain relation ids
        It should only return relation ids
        """

        elements = {
            'node': [],
            'relation': [1234, 5678, 9123],
            'way': []
        }

        expected_elements_parameters = 'relation(id:1234,5678,9123);'
        elements_parameters = cast_element_ids_to_s(elements)
        self.assertEqual(elements_parameters, expected_elements_parameters)

    def test_cast_element_ids_to_s_with_only_way_elements(self):
        """
        when elements only contain way ids
        It should only return way ids
        """

        elements = {
            'node': [],
            'relation': [],
            'way': [1234, 5678, 9123]
        }

        expected_elements_parameters = 'way(id:1234,5678,9123);'
        elements_parameters = cast_element_ids_to_s(elements)
        self.assertEqual(elements_parameters, expected_elements_parameters)

    def test_cast_element_ids_to_s_with_all_elements(self):
        """
        when elements contains node, relation and way
        It should node, relation and way ids
        """

        elements = {
            'node': [1234, 5678, 9012],
            'relation': [2345, 6789, 1124],
            'way': [3456, 7890, 1123]
        }

        expected_elements_parameters = 'node(id:1234,5678,9012);' + \
            'relation(id:2345,6789,1124);' + \
            'way(id:3456,7890,1123);'
        elements_parameters = cast_element_ids_to_s(elements)
        self.assertEqual(elements_parameters, expected_elements_parameters)
